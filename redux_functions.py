import glob, tqdm, astropy
import numpy as np

from scipy.optimize import curve_fit

import argparse

from Frame import Frame
from FrameList import FrameList


def setProgramArguments(params):
    """
    This function takes care of setting the program arguments that are read-in at runtime.
    It's a bit terse, but the various argument settings are specified once and then argparse
        takes care of a help message and other items that are useful to users
    As a final action, it creates an object (params) that is effectively the dictionary of all 
        program paramters. This will be used throughout the program.
    """
    description = \
    """
    Data Reduction Pipeline for UMBC Observatory
    Reduces raw light frames to top-of-atmosphere instrument magnitudes.
    Currently works only for point sources.
    """

    parser = argparse.ArgumentParser(\
                        prog='data_redux', allow_abbrev=True,\
                        #usage="python %(prog)s arguments",\
                        description=description,\
                        epilog='Submit github issue with any quesitons or concerns.')

    ## OPTIONAL ARGUMENTS
    # Exclude Filter
    parser.add_argument('--excludeFilter', '-x', metavar="[]", \
                        action="append", required=False, nargs='+', help="Exclude filters",\
                        choices=['U', 'B', 'V', 'R', 'I'])

    #Set logging level
    parser.add_argument('--level', '-level', metavar="[]", \
                        action="store", required=False, \
                        help="Set Logging level to either INFO or DEBUG",\
                        choices=['INFO', 'DEBUG'], default='INFO')

    # Save Flag
    parser.add_argument('--save', default="", action='store', metavar="title",\
                        help="Save PNG of final light frame to analysis directory",\
                        type=str
                        )

    # Force Flag
    parser.add_argument('--force', default="False", action='store_true',\
                        help="Force computations without darks or matching gains"
                        )

    # Skip Flat Flag
    parser.add_argument('--no-flat', default=False, action='store_true',\
                        help="Force reduction pipeline to not use flats"
                        )

    # Skip Dark Flag
    parser.add_argument('--no-dark', default=False, action='store_true',\
                        help="Force reduction pipeline to not use darks"
                        )

    # Specify Version flag
    parser.add_argument('--version', '-V', '-version', action='version', version='%(prog)s Version 0.0, 20231129')

    ## REQUIRED ARGUMENTS
    required = parser.add_argument_group('required arguments')

    # Specify Src Data FITS directory
    required.add_argument("--datadir",'-D', '-datadir', action="store", metavar='dir',type=str, required=True,\
                        help="Directory containing all raw light frames",\
                        )

    # Specify Calibration  FITS directory
    required.add_argument("--caldir",'-C', '-caldir', action="store", metavar='dir',type=str, required=True,\
                        help="Directory containing all calibration frames",\
                        )

    # Specify output directory
    required.add_argument("--outdir", '-O', '-outdir', metavar="dir", action="store", type=str, required=True,\
                        help="Directory where log, analysis, and new FITS will be written.",\
                        )

    # Specify radius of aperture used to extract counts for magnitude estimation
    required.add_argument("--radius", '-R', '-radius', metavar="int", action="store", type=int, required=True,\
                        help="Integer number of pixels to extract around all source centroids for magnitude estimation. ~15 \nNot to be confused with subFrame size.",\
                        )

    # Specify side-length of subFrame
    required.add_argument("--length", '-L', '-length', metavar="int", action="store", type=int, required=True,\
                        help="Integer number of pixels for subframe extraction. ~50",\
                        )
    # Specify sigma used for Gaussian smoothing of frames
    required.add_argument("--smoothing", "-S", "-smoothing", metavar="float", action="store", type=float, required=True,\
                        help="Float value in range [0,inf) used for STD of Gaussian Smoothing Filter")

    parser.parse_args(namespace=params)

def findFITS(params):
    fitsFiles = dict()
    params.logger.debug("Got to: findFITS function")
    
    #Assume all raw light and all calibration frames are in some directory (indir)
    fitsFileList = glob.glob(f"{params.datadir}/**/*.fits", recursive=True) + glob.glob(f"{params.caldir}/**/*.fits", recursive=True)
    params.logger.info(f"Found {len(fitsFileList)} FITS files.")

    #Go through each fits file and create a Frame object for each \
    #   and construct FrameList objects
    for fitsFile in tqdm.tqdm(fitsFileList, desc="Finding FITS"):
        with astropy.io.fits.open(fitsFile) as hdul:
            hdu = hdul[0]
            #Carve-out for bias and dark frames for which header does not report filter
            try:
                #Check to see if this filter was specified to be skipped
                if hdu.header['FILTER'].upper() in params.excludeFilter[0]:
                    continue
                if hdu.header['FRAMETYP'].lower() == "flat" and params.no_flat:
                    continue

                frame = Frame(hdu.data, hdu.header['FRAMETYP'].lower(), hdu.header['FILTER'].upper(), \
                            hdu.header['GAIN'], hdu.header['EXPTIME'], hdu.header
                            )
                
                #print(f"Added frame {str(frame)}")
            except Exception as e: #We expect bias and dark frames to fail to resolve the 'FILTER' key in the header
                #print(e)
                frame = Frame(hdu.data, type=hdu.header['FRAMETYP'].lower(), filter=None, \
                                gain=hdu.header['GAIN'], intTime=hdu.header['EXPTIME'], header=hdu.header
                                )
                #print(f"Added frame {str(frame)}")
                
            #Create all of the dictionaries!
            try:
                #If frameList for filter is alr defined ...
                fitsFiles[frame.type][frame.filter][frame.gain][frame.intTime].append(frame)
                #print(f"Added frame {str(frame)} to dictionary!")
            except KeyError as e: #Couldn't find FrameList for that intTime, trying to add new FrameList for intTime
                try:
                    fitsFiles[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                except KeyError as e: #Couldn't find gain, trying to add gain to filter dict
                    try:
                        fitsFiles[frame.type][frame.filter] = {}
                        fitsFiles[frame.type][frame.filter][frame.gain] = {}
                        fitsFiles[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                    except KeyError as e: #Couldn't find intTime, trying to add intTime to type dict
                        try: 
                            fitsFiles[frame.type] = {}
                            fitsFiles[frame.type][frame.filter] = {}
                            fitsFiles[frame.type][frame.filter][frame.gain] = {}
                            fitsFiles[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                        except KeyError as e: #Couldn't find type dict, trying to add type dict
                            params.logger.exception(e)
    return fitsFiles

def getDarks(params, frameList):
        params.logger.debug("Got to: getDarks function")
        #Get Darks with filter=None, gain=frameList.gain, intTime=frameList.intTime
        #  If none, found raise exception
        #  If gain is issue, alert and modify dark gain
        #  If int time is issue, subtract biases out and scale thermal signal
        # for now, assume all will work ...
        gain = frameList[0].gain
        intTime = frameList[0].intTime
        try:

            darks = params.fitsFiles['dark'][None][gain][intTime]
        except KeyError as e:
            params.logger.exception(e)
            params.logger.info("\tIssue with Dark for Flats")
            darks = params.fitsFiles['dark'][None][gain][intTime]

            try:
                params.fitsFiles['dark']
            except KeyError as e:
                params.logger.info("Unable to find darks. Exiting.")
                exit()
            try:
                params.fitsFiles['dark'][None]
            except KeyError as e:
                params.logger.info("Dark dictionary improperly formatted. Filter is not None. Exiting.")
                exit()
            try:
                params.fitsFiles['dark'][None][gain]
            except KeyError as e:
                #TODO: Provide override flag for just goofing around!
                params.logger.info("Dark has different gain. Can proceed if --force flag used.")
                if  params.fitsFiles.force:
                    params.logger.info("Functionality for proceeding with unequal gains not available yet.")
                    exit()
            try:
                params.fitsFiles['dark'][None][gain][intTime]
            except KeyError as e:
                #TODO: Provide override flag for just goofing around!
                params.logger.info("Dark has different integration time. Can proceed to scale thermal signal if --force flag used.")
                if  params.fitsFiles.force:
                    params.logger.info("Functionality providing thermal scaling not available yet")
                    exit()
                else:
                    params.logger.info(f"No darks provided that with equal integration time for {frameList}.")
                    params.logger.info(" You can force the computation to proceed by rerunning with --force flag.")
                    params.logger.info(" The result will likely not be useful for estimating physical parameters.")
        except Exception as e:
            params.logger.exception(e)
            exit()
        return darks

def fitGaussian1D(radialData, p0, pixelLocs):
    # p0 behaves by taking a best guess at params (mu, sigma, amplitude, offset)
    params, _ = curve_fit(gaussian1D, pixelLocs, radialData, p0)

    #Calculate coefficient of determination
    res = radialData - gaussian1D(pixelLocs, *params)
    sumSqrs_res = np.sum(res*res)
    totSumSqrs = np.sum((radialData-np.mean(radialData))**2)
    R2 = 1.0 - (sumSqrs_res / totSumSqrs)

    return params, R2

def gaussian1D(x, mu, sigma, amplitude, offset):
    #Model function as gaussian with amplitude A and offset G
    return amplitude * np.exp( -((x-mu)/sigma)**2/2 ) + offset

def extractRadialData(subFrame, xC, yC):
    #Get matrix of integer indices associated with subFrame
    y, x = np.indices((subFrame.shape))

    #Generate matrix of radius values
    r = np.sqrt((x - xC)**2 + (y - yC)**2)

    #Force integer values (np.sqrt gives floats)
    r = r.astype(int)

    #Generate a histogram of radius bin, each weighed by corresponding counts
    weightedRadiusHistogram = np.bincount(r.ravel(), weights=subFrame.ravel())
    unweightedRadiusHistogram = np.bincount(r.ravel())

    #Get average for each radius bin
    averageCountsPerRadiusBin = weightedRadiusHistogram / unweightedRadiusHistogram
    return averageCountsPerRadiusBin


#returns a tuple, (data, badpixelmap)
def accumulate(frameList,listType=None):
    #Number of Standard Deviations from the Mean that are "good" pixels
    numStd = 3

    #Generate an all-true pixel mask to start with
    #  This would mean a pixel mask where all pixels are labelled as "good"
    goodMask = np.full(frameList[0].data.shape, True)

    #Darks and Flats have good pixel masks for each frame
    if listType == "dark" or listType == "flat":
        for f in frameList:
            pixAvg = np.average(f.data)
            sigma  = np.std(f.data)
            frameMin, frameMax = pixAvg - (numStd*sigma), pixAvg + (numStd*sigma)
            #There is a more pythonic way to accomplish this, but it looks right for now
            for i in range(f.data.shape[0]):
                for j in range(f.data.shape[1]):
                    pixVal=f.data[i,j]
                    if (pixVal >= frameMax) or (pixVal <= frameMin):
                        goodMask[i][j]=False

            # #Test to see if equivalent to the above
            # #figger out where this goes
            # testMask = ~np.logical_or(f.data < frameMin, f.data > frameMax )
            # print("DArks, Flats: ", testMask == goodMask)

    #Lights have good pixel masks for each master frame
    if listType=="light":
        for j in range(frameList[0].data.shape[0]):
            for k in range(frameList[0].data.shape[1]):
                pixelColumn = [f.data[j,k] for f in frameList]
                pixAvg = np.average( pixelColumn )
                sigma  = np.std( pixelColumn )
                colMin, colMax = pixAvg - (numStd*sigma), pixAvg + (numStd*sigma)
                #There is a more pythonic way to accomplish this, but it looks right for now
                for f in frameList:
                    pixVal = f.data[j,k]
                    if (pixVal >= colMax ) or (pixVal <= colMin ) or (sigma == 0) or (pixVal == 0):
                        goodMask[j][k] = False 
             
        #Test to see if equivalent to the above
        # testPixAvg = np.average(frameList, axis=0)
        # testSigma = np.std(frameList, axis=0)
        # colWiseMin, colWiseMax = testPixAvg - (numStd*testSigma), testPixAvg + (numStd*testSigma)
        # testMask = np.logical_or.reduce(frameList < colWiseMin, frameList > colWiseMax, testSigma == 0, pixVal == 0)
        # print("Lights: ", testMask == goodMask)

    print(f'Percent of Bad Pixels: \t {100*(goodMask.size- np.count_nonzero(goodMask))/goodMask.size}')
    return  (np.median( [f.data for f in frameList], axis=0 ),goodMask)
