##############################################
#####  Imports 
##############################################

# Native Imports
import pprint, datetime, glob, csv
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



### different directory weirdness
import sys
sys.path.insert(1, '../')


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
            /darks/
            /flats/
                /flat_u/
                /flat_b/
                /flat_v/
                /flat_r/
                /flat_i/
        /light/
            /obj1_u/
            /obj1_b/
            /obj1_v/
            /obj1_r/
            /obj1_i/
        knownInformation.csv
            knownInformation.csv to contain:
             known total counts with pixel mask, counts  without pixel mask, bad pixel count, 
             bad pixel locations
"""

## 
testDir = "testObj1"
print(f'Running fits-test with {testDir}')






badPixTotal=0
countsNoMask=0
countsMask=0


knownCountNoMask=0
knownCountMask=0
badPixLocations=[]
with open(f'{testDir}/knownInformation.csv','r') as csvfile:
    # known total counts with pixel mask, counts  without pixel mask, bad pixel locations
    # skip headers
    reader=csv.reader(csvfile)
    next(reader)
    mainRow=next(reader)
    # save count information
    knownCountMask=int(mainRow[0])
    knownCountNoMask=int(mainRow[1])
    print(f'\n{knownCountNoMask}\t{knownCountMask}')
    #grab all bad pixel locations
    for row in reader:
        if len(row)>0 and row[0]:
            badPixLocations.append(row[0])


print(f"Bad Pixels not found:\t {len(badPixLocations) - badPixTotal}\n \
Counts without pixelMask diff:\t {countsNoMask-knownCountNoMask}\n \
Counts with pixelMask diff:\t{countsMask-knownCountMask}\n")

print("testing script finished with no errors")
