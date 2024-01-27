##########################################
#####  Imports
##########################################

# Installed Imports
import numpy as np

#Locally authored classes
from Frame import Frame

class FrameList(list):
    def __init__(self, frame, redux):
        self.append(frame)
        self.redux = redux

        self._darkFrame = 0
        self._flatFrame = 1
        self._master = None

    def setDarkFrame(self, darkFrame):
        self._darkFrame = darkFrame

    def setFlatFrame(self, flatFrame):
        self._flatFrame = flatFrame


    def __call__(self): #Calculate master frame
        #This is where all of the master frame accumulation is done 
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
