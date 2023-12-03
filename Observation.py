import logging
from datetime import datetime
from glob import glob

import argparse
from tqdm import tqdm

from astropy.io import fits

import numpy as np

class Redux:

    def __init__(self):
        self.frameListDict = {}
        self.level = 'INFO'

        self.setProgramArguments()

    def makeLog(self):
        LVL = logging.DEBUG if self.level == 'DEBUG' else logging.INFO
        logging.basicConfig(filename='{}/redux_{}.log'.format(self.outdir, datetime.now().strftime("%Y%m%dT%H%M")),\
            encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s', \
            datefmt='%Y%m%dT%H%M%S',level=LVL)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Created logger object.")
        self.logger.debug(f"Logger made with debugging level set.")

    def findFITS(self):
        self.logger.debug("Got to findFITS function in Redux Class")
        
        #Assume all raw light and all calibration frames are in some directory (indir)
        fitsFileList = glob(f"{self.datadir}/**/*.fits", recursive=True) + glob(f"{self.caldir}/**/*.fits", recursive=True)
        self.logger.info(f"Found {len(fitsFileList)} FITS files.")

        #Go through each fits file and create a Frame object for each \
        #   and construct FrameList objects
        for fitsFile in tqdm(fitsFileList):
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
                    self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime].append(frame)
                    self.FrameLists.append(self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime])
                    #print(f"Added frame {str(frame)} to dictionary!")
                except KeyError as e: #Couldn't find FrameList for that intTime, trying to add new FrameList for intTime
                    try:
                        self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                        self.FrameLists.append(self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime])
                    except KeyError as e: #Couldn't find gain, trying to add gain to filter dict
                        try:
                            self.frameListDict[frame.type][frame.filter] = {}
                            self.frameListDict[frame.type][frame.filter][frame.gain] = {}
                            self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                            self.FrameLists.append(self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime])
                        except KeyError as e: #Couldn't find intTime, trying to add intTime to type dict
                            try: 
                                self.frameListDict[frame.type] = {}
                                self.frameListDict[frame.type][frame.filter] = {}
                                self.frameListDict[frame.type][frame.filter][frame.gain] = {}
                                self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime] = FrameList(frame)
                                self.FrameLists.append(self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime])
                            except KeyError as e: #Couldn't find type dict, trying to add type dict
                                print(e)         

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
        # Logging Level
        parser.add_argument("--level", metavar="[]", action="store", type=str, required=False,\
                            help="Logging Level. Info or Debug. Debug is more verbose.",\
                            choices=['INFO', 'DEBUG'])

        # Exclude Filter
        parser.add_argument('--excludeFilter', '-x', '-excludeFilters', '-E', '-X', metavar="[]", \
                            action="append", required=False, nargs='+', help="Exclude filters",\
                            choices=['U', 'B', 'V', 'R', 'I'])

        # Force Flag
        parser.add_argument('--force', default=False, action='store_true',\
                            help="Force computations without darks or matching gains"
                            )

        # Skip Flat Flag
        parser.add_argument('--no-flat', default=False, action='store_true',\
                            help="Force reduction pipeline to not use flats"
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

    def __str__(self):
        return f"{self.FrameLists}"

class FrameList(list):
    def __init__(self, frame):
        self.append(frame)

        self._darkFrameObj = 0
        self._flatFrameObj = 1
        self._master = None

    def setDarkFrameObj(self, darkFrameObj):
        self._darkFrameList = darkFrameObj

    def setFlatFrameObj(self, flatFrameObj):
        self._flatFrameObj = flatFrameObj

    def __call__(self): #Calculate master frame
        if self._darkFrameObj == 0:
            data = np.median([s() for s in self], axis=0)
        else:
            data = np.median(self - self._darkFrameObj(), axis=0)

        if self._flatFrameObj != 1:
            data /= (self._flatFrameObj() / self._flatFrameObj.max)
        
        self._master = Frame(data, 'master', self[0].filter, self[0].gain, self[0].intTime, self[0].header)

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
        return f"{len(self)}x(Type:{self[0].type}, Filter:{self[0].filter}, Gain:{self[0].gain}, IntTime:{self[0].intTime})"
    
    def getFrameInfo(self):
        """Return large string of frame information strings"""
        s = ""
        for frame in self:
            s += frame.getInfo() + "\n"
        return s

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

        self.std = np.std(data)
        self.mean = np.mean(data)
        self.median = np.median(data)
        self.max = np.max(data)
        self.min = np.min(data)

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
        return f"Type:{self.type}, Filter:{self.filter}, Gain:{self.gain}, IntTime:{self.intTime}"



