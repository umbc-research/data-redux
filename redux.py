import logging
from sys import argv, exit
from datetime import datetime

from matplotlib import pyplot as plt
from matplotlib.patches import Circle

from scipy.ndimage import gaussian_filter
import numpy as np

#Author-defined imports
from redux_funcs import gaussian_1d

if __name__ == "__main__":
    logging.basicConfig(filename='redux_{}.log'.format(datetime.now().strftime("%Y%m%dT%H")),\
        encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s', \
        datefmt='%Y%m%dT%H%M%S',level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"Created logger object in {argv[0]}")

    # Get Frames
    ## Get Light Frames

    ## Get Bias Frames

    ## Get Dark Frames

    ## Get Flat Frames

    # Generate Master Frames
    ## Master Bias

    ## Master Darks

    ## Master Flat

    # Generate Data Frame
    ## Apply Calibration Frames

    # Estimate Instrument Magnitude
    ## Find Sources

    ## Extract SubFrames

    ## Extract Radial Profile

    ## Fit Radial Profile

    ## Subtract Sky Brightness

    ## Sum Counts

    ## Calculate Instrument Magnitude

    # Plots

    
