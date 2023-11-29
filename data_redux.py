import argparse

#Authored packages
from Observation import Redux, Observation

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

# Specify Version flag
parser.add_argument('--version', '-V', '-version', action='version', version='%(prog)s Version 0.0, 20231129')


## REQUIRED ARGUMENTS
required = parser.add_argument_group('required arguments')

# Specify FITS directory
required.add_argument("--indir",'-I', '-indir', action="store", metavar='dir',type=str, required=True,\
                    help="Directory containing all raw light and calibration frames",\
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

redux = Redux()
parser.parse_args(namespace=redux)
redux.makeLog()

#Debug: print state of vars
redux.logger.debug(vars(redux))

# Read in all FITS file from specified directory
redux.findFITS()
