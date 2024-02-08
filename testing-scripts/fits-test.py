##############################################
#####  Imports 
##############################################

# Native Imports
import pprint, datetime, glob
"""
$ python3 -V   
Python 3.9.6
$
"""

# Installed imports
import numpy as np

import logging
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
from photutils.detection import DAOStarFinder
from tqdm import tqdm
"""
    $ python3
"""

##############################################
#####  Local Class Defintions
##############################################

# Locally authored classes
#  These are in different files just because
import redux_functions
from Frame import Frame
from FrameList import FrameList


"""
    GOALS:
        test out pixel maps with a source of known dead pixels
        have a playground ish thing to mess with fits files without the whole script running 
"""


"""
Set up this directory the following way:
    ./testDir/
        /calibration/
        /light/
        knownInformation.csv
            knownInformation.csv to contain a known total counts with pixel mask,
             without pixel mask, bad pixel locations
"""

## 
testDir = "testObj1"
print(f'running fits-test with {testFile}')






