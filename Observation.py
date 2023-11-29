import logging
from datetime import datetime
from glob import glob

class Redux:

    def __init__(self):
        self.OBS = []
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



class Observation:

    def __init__(self):
        pass