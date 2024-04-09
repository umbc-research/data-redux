##########################################
#####  Imports
##########################################

# Installed Imports
import numpy as np

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

    def __init__(self, data, type, filter, gain, intTime, header, badMap=None):
        self.data = data
        self.type = type
        self.filter = filter
        self.gain = gain
        self.intTime = intTime
        self.header = header
        #TODO: Add x,y dimensions as private parameter to check in append of FrameList

        if self.type == 'master':
            self.subFrameList = None
        # TODO: Repalce this histFilter with a bad-pixel filter

#         histFilter = np.where((self.data<65535) & (self.data>0))
#         print(np.where((self.data<65535) & (self.data>0)))
# 
#         self.std = np.std(self.data[histFilter])
#         self.mean = np.mean(self.data[histFilter])
#         self.median = np.median(self.data[histFilter])
#         self.max = np.max(self.data[histFilter])
#         self.min = np.min(self.data[histFilter])
        self.badMap = badMap
#        self.std = np.std(self.data[histFilter])
#        self.mean = np.mean(self.data[histFilter])
#        self.median = np.median(self.data[histFilter])
#        self.max = np.max(self.data[histFilter])
#        self.min = np.min(self.data[histFilter])
        self.std = np.std(self.data)
        self.mean = np.mean(self.data)
        self.median = np.median(self.data)
        self.max = np.max(self.data)
        self.min = np.min(self.data)
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

    def __add__(self, obj):
        return self.data + obj.data

    def __sub__(self, obj):
        return self.data - obj.data

    def __mul__(self, obj):
        return self.data * obj.data
    
    def __trudiv__(self, obj):
        return self.data / obj.data
    


