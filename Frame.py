import numpy as np
from scipy.optimize import curve_fit


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

