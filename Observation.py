import logging
from datetime import datetime
from glob import glob
import pprint

import argparse
from tqdm import tqdm

from scipy.optimize import curve_fit


#Photometry Utilities
from photutils.detection import DAOStarFinder

from astropy.io import fits

import numpy as np

class Redux(dict):

    def __init__(self):
        self.setProgramArguments()

    def __str__(self):
        return pprint.pformat(vars(self), indent=1, depth=5)

    def makeLog(self):
        logging.basicConfig(filename='{}/redux_{}.log'.format(self.outdir, datetime.now().strftime("%Y%m%dT%H%M%S")),\
            encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s', \
            datefmt='%Y%m%dT%H%M%S')
        
        self.logger = logging.getLogger(__name__)
        if self.level == 'DEBUG': 
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO) 

        self.logger.info(f"Created logger object.")
        self.logger.debug(f"Logger made with debugging level set.")

    def findFITS(self):
        self.logger.debug("Got to: findFITS function")
        
        #Assume all raw light and all calibration frames are in some directory (indir)
        fitsFileList = glob(f"{self.datadir}/**/*.fits", recursive=True) + glob(f"{self.caldir}/**/*.fits", recursive=True)
        self.logger.info(f"Found {len(fitsFileList)} FITS files.")

        #Go through each fits file and create a Frame object for each \
        #   and construct FrameList objects
        for fitsFile in tqdm(fitsFileList, desc="Finding FITS"):
            with fits.open(fitsFile) as hdul:
                hdu = hdul[0]
                #Carve-out for bias and dark frames for which header does not report filter
                try:
                    #Check to see if this filter was specified to be skipped
                    if hdu.header['FILTER'].upper() in self.excludeFilter[0]:
                        continue
                    if hdu.header['FRAMETYP'].lower() == "flat" and self.no_flat:
                        continue

                    frame = Frame(hdu.data, hdu.header['FRAMETYP'].lower(), hdu.header['FILTER'].upper(), \
                                hdu.header['GAIN'], hdu.header['EXPTIME'], hdu.header
                                )
                    
                    #print(f"Added frame {str(frame)}")
                except Exception as e: #We expect bias and dark frames to fail to resolve the 'FILTER' key in the header
                    #print(e)
                    frame = Frame(hdu.data, hdu.header['FRAMETYP'].lower(), None, \
                                   hdu.header['GAIN'], hdu.header['EXPTIME'], hdu.header
                                 )
                    #print(f"Added frame {str(frame)}")
                    
                #Create all of the dictionaries!
                try:
                    #If frameList for filter is alr defined ...
                    self[frame.type][frame.filter][frame.gain][frame.intTime].append(frame)
                    #print(f"Added frame {str(frame)} to dictionary!")
                except KeyError as e: #Couldn't find FrameList for that intTime, trying to add new FrameList for intTime
                    try:
                        self[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame, self)
                    except KeyError as e: #Couldn't find gain, trying to add gain to filter dict
                        try:
                            self[frame.type][frame.filter] = {}
                            self[frame.type][frame.filter][frame.gain] = {}
                            self[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame, self)
                        except KeyError as e: #Couldn't find intTime, trying to add intTime to type dict
                            try: 
                                self[frame.type] = {}
                                self[frame.type][frame.filter] = {}
                                self[frame.type][frame.filter][frame.gain] = {}
                                self[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame, self)
                            except KeyError as e: #Couldn't find type dict, trying to add type dict
                                self.logger.exception(e)         

    def setProgramArguments(self):
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

        parser.parse_args(namespace=self)

    def getDarks(self, frameList):
        self.logger.debug("Got to: getDarks function")
        #Get Darks with filter=None, gain=frameList.gain, intTime=frameList.intTime
        #  If none, found raise exception
        #  If gain is issue, alert and modify dark gain
        #  If int time is issue, subtract biases out and scale thermal signal
        # for now, assume all will work ...
        gain = frameList[0].gain
        intTime = frameList[0].intTime
        try:
            darks = self['dark'][None][gain][intTime]
        except KeyError as e:
            self.logger.exception(e)
            self.logger.info("\tIssue with Dark for Flats")
            darks = self['dark'][None][gain][intTime]
            print("in getDarks w/ error")
            print(darks)
            try:
                self['dark']
            except KeyError as e:
                self.logger.info("Unable to find darks. Exiting.")
                exit()
            try:
                self['dark'][None]
            except KeyError as e:
                self.logger.info("Dark dictionary improperly formatted. Filter is not None. Exiting.")
                exit()
            try:
                self['dark'][None][gain]
            except KeyError as e:
                #TODO: Provide override flag for just goofing around!
                self.logger.info("Dark has different gain. Can proceed if --force flag used.")
                if  self.force:
                    self.logger.info("Functionality for proceeding with unequal gains not available yet.")
                    exit()
            try:
                self['dark'][None][gain][intTime]
            except KeyError as e:
                #TODO: Provide override flag for just goofing around!
                self.logger.info("Dark has different integration time. Can proceed to scale thermal signal if --force flag used.")
                if  self.force:
                    self.logger.info("Functionality providing thermal scaling not available yet")
                    exit()
                else:
                    self.logger.info(f"No darks provided that with equal integration time for {frameList}.")
                    self.logger.info(" You can force the computation to proceed by rerunning with --force flag.")
                    self.logger.info(" The result will likely not be useful for estimating physical parameters.")
        except Exception as e:
            self.logger.exception(e)
            exit()
        return darks

class FrameList(list):
    def __init__(self, frame, redux):
        self.append(frame)
        self.redux = redux

        self._darkFrame = 0
        self._flatFrame = 1
        self._master = None

    def setDarkFrame(self, darkFrame):
        self._darkFrame = darkFrame
        self.__call__()

    def setFlatFrame(self, flatFrame):
        self._flatFrame = flatFrame
        self.__call__()

    def __call__(self): #Calculate master frame
        darkCorr = False
        flatCorr = False
        #TODO: Remove logging from this function, wrap calling functions with logging
        if self._darkFrame == 0:
            self.redux.logger.debug(f"_darkFrame is 0, {self._darkFrame}")
            self.redux.logger.debug("Deriving Master Dark")
            data = np.median([s() for s in self], axis=0)
        else: # does not include functionality for mismatched dark/thermal frame integration times
            self.redux.logger.debug(f"_darkFrame is non-0, {self._darkFrame}")
            self.redux.logger.debug("Deriving Master Dark")
            data = np.median([s()-self._darkFrame() for s in self], axis=0)
            darkCorr = True

        self.redux.logger.debug(f"Dark Done. Checking on Flats")
        if self._flatFrame != 1:
            self.redux.logger.debug(f"_flatFrame is not 1, {self._flatFrame}")
            data /= (self._flatFrame() / self._flatFrame.max)
            flatCorr = True
        else:
            self.redux.logger.debug(f"_flatFrame is 1 -- doing nothing., {self._darkFrame}")

        self.redux.logger.debug(f"Creating Master Frame Obj is 0, {self._darkFrame}")
        self._master = Frame(data, 'master', self[0].filter, self[0].gain, self[0].intTime, self[0].header)
        self._master.flatCorr = flatCorr
        self._master.darkCorr = darkCorr
        self.redux.logger.debug(f"Completing FrameList() call, {self}")

    def getMaster(self):
        self.redux.logger.debug(f"Retrieving Master, {self._master}")
        return self._master
    
    def append(self, frame):
        #If this is the first frame to be added to the list
        if len(self) == 0:
            #add the frame to the obj(list)
            super(FrameList, self).append(frame)
        else: #if this is not the first frame in the list
            #build a set of conditions to check            
            typeCond = self[0].type == frame.type
            filterCond = self[0].filter == frame.filter 
            gainCond = self[0].gain == frame.gain
            intTimeCond = self[0].intTime == frame.intTime

            #check if conditions are all met
            if typeCond and filterCond and gainCond and intTimeCond:
                #if frame belongs here, add it
                super(FrameList, self).append(frame)  
            else: #If frame doesn't belong in this list, say why
                raise Exception("This frame has different parameters than others in this list.\n"+\
                                 f"  Frame Type Match: {typeCond}"+\
                                 f"  Filter Match: {filterCond}\n"+\
                                 f"  Gain Match: {gainCond}\n"+\
                                 f"  Integration Time Match: {intTimeCond}"\
                                )
    
    def __str__(self):
        """Return string with basic information on FrameList object."""
        if self._master == None:
            s = f"FrameList. {len(self)}x({self[0]})"
        else:
            s = f"FrameList. {len(self)}x({self._master})"
        return s
    
    def getFrameInfo(self):
        """Return large string of frame information strings"""
        s = ""
        for frame in self:
            s += frame.getInfo() + "\n"
        return s

# class SubFrameList(list):
#     def __init__(self, subFrame):
#         self.append(subFrame)
#         self.R2List = []
#         self.loc = []
#         self.

class Frame:
    """The Frame Class defines a few class variables that are extracted
    from the associated FITS HDU. These are:
    data - the HDU Data unit as np.ndarray
    type - lower-case string (light|flat|dark|bias|master)
    filter - Upper-case string restrictded to single-letter Johnson Filter Set
    gain - integer gain level reported by SharpCap
    intTime - float exposure time used to collect frame

    Further, the header portion of the associated FITS HDU is stored for 
    later access/modification.

    Finally, some statistics are calculated and stored along with each 
    Frame object.

    Importantly, calling an instance of a Frame object returns the data 
    portion of the assocated FITS HDU.
    """
    
    def __init__(self, data, type, filter, gain, intTime, header):
        self.data = data
        self.type = type
        self.filter = filter
        self.gain = gain
        self.intTime = intTime
        self.header = header

        if self.type == 'master':
            self.subFrameList = None

        filter = np.where((data<65000) & (data>0))

        self.std = np.std(data[filter])
        self.mean = np.mean(data[filter])
        self.median = np.median(data[filter])
        self.max = np.max(data[filter])
        self.min = np.min(data[filter])

        self.darkCorr = False
        self.flatCorr = False

    def __call__(self):
        """Return the data portion of the FITS HDU (np.ndarray; d=2)"""
        return self.data
    
    def getInfo(self):
        """Return a more verbose string with more header information"""
        return f"{self.header['INSTRUME']} T={self.header['CCD-TEMP']} Obs on {self.header['DATE-OBS']}\n"+\
            f"Min,Max:{self.min},{self.max} Mean,Median:{self.mean},{self.median} STD: {self.std}\n"+\
            str(self)
    
    def __str__(self):
        """Return simple string with basic information for reduction"""
        s = f"Frame. Type:{self.type}, Filter:{self.filter}, Gain:{self.gain}, IntTime:{self.intTime}s"
        if self.darkCorr:
            s += ", Dark Applied"
        else:
            s += ", No Dark Applied" 
        if self.flatCorr:
            s += ", Flat Applied"
        else:
            s += ", No Flat Applied"
        return s
    
    def __repr__(self):
        return self.__str__()
    
    @staticmethod
    def fitGaussian1D(radialData, p0, pixelLocs):
        # p0 behaves by taking a best guess at params (mu, sigma, amplitude, offset)
        params, _ = curve_fit(Frame.gaussian1D, pixelLocs, radialData, p0)

        #Calculate coefficient of determination
        res = radialData - Frame.gaussian1D(pixelLocs, *params)
        sumSqrs_res = np.sum(res*res)
        totSumSqrs = np.sum((radialData-np.mean(radialData))**2)
        R2 = 1.0 - (sumSqrs_res / totSumSqrs)

        return params, R2
    
    @staticmethod
    def gaussian1D(x, mu, sigma, amplitude, offset):
        #Model function as gaussian with amplitude A and offset G
        return amplitude * np.exp( -((x-mu)/sigma)**2/2 ) + offset

    @staticmethod
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

