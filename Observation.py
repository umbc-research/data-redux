import logging
from datetime import datetime
from glob import glob

from astropy.io import fits

class Redux:

    def __init__(self):
        self.lightLists = []
        self.darkLists = []
        self.flatLists = []
        self.biasLists = []

        self.level = 'INFO'

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
        
        fitsFileList = glob(f"{self.indir}/**/*.fits", recursive=True)
        self.logger.info(f"Found {len(fitsFileList)} FITS files in {self.indir}.")

        for fitsFile in fitsFileList:
            with fits.open(fitsFile)[0] as hdu:
                try:
                    frame = Frame(hdu.data, hdu.header['EXPTIME'], \
                              hdu.header['FILTER'].upper(), hdu.header['GAIN'], hdu.header['FRAMETYP'].lower())
                except Exception as e:
                    print(e)
                    #We expect bias frames to fail to resolve the 'FILTER' key in the header
                    frame = Frame(hdu.data, hdu.header['EXPTIME'], \
                              None, hdu.header['GAIN'], hdu.header['FRAMETYP'].lower())
                
                if frame.type == 'light':
                    pass

class FrameList(list):
        def __init__(self):
            self.first= True
            self._darksObj = None
            self._intTime = None
            self._filter = None
            self._gain = None
            self._type = None

            self._std = None
            self._mean = None
            self._max = None

        def append(self, frame):
            if not self.first:
                timeCond = self._intTime == frame.intTime
                gainCond = self._gain == frame.gain
                filterCond = self._filter == frame.filter 

                if timeCond and gainCond and filterCond:
                    self.super(Lights, self).append(frame)
                else:
                    raise Exception("This frame has different parameters than others in this list.\n"+\
                                    f"  Integration Time Match: {timeCond}\n"+\
                                    f"  Gain Match: {gainCond}\n"+\
                                    f"  Filter Match: {filterCond}\n")
            else:
                self.first = False
                self._intTime = frame.intTime
                self._gain = frame.gain
                self.filter = frame.filter
                self.super(Lights, self).append(frame)

        def __repr__(self):
            return (self._type, len(self))
        
class Lights(FrameList):

    def __init__(self, frame=None):
        self._reducedFrame = None

    def setDark(self, darksObj):
        self.darksObj = darksObj

    def getFilter(self):
        return self._filter

    def __repr__(self):
        return ("light", len(self))


class Biases(FrameList):

class Darks(FrameList):
    
class Flats(FrameList):


class Frame(list):
    def __init__(self, data, intTime, filter, gain, type):
        self.append(data)
        self.intTime = intTime
        self.filter = filter
        self.gain = gain
        self.type = type

      