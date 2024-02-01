##########################################
#####  Imports
##########################################

# Installed Imports
import numpy as np

#Locally authored classes
from Frame import Frame

class FrameList(list):
    def __init__(self, frame):
        self.append(frame)
        self._master = None
        self._masterFlat = None
        self._masterDark = None

    def setDarkFrame(self, darkFrame):
        self._darkFrame = darkFrame

    def setFlatFrame(self, flatFrame):
        self._flatFrame = flatFrame

    def setMaster(self, frame):
        self._master = frame

    def getMaster(self):
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
            #TODO: Add additional check on x,y dimensions
                # Check ndarray.shape matches between original frame and appended
                # Check header x, y matches with original frame (should be priv variable)
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
