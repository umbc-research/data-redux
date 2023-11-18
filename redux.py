#Administrative Pkgs, logging
import logging
from sys import argv, exit
from datetime import datetime
from dotenv import load_dotenv, dotenv_values

#Author-defined imports
import redux_funcs

logging.basicConfig(filename='redux_{}.log'.format(datetime.now().strftime("%Y%m%dT%H%M")),\
    encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s', \
    datefmt='%Y%m%dT%H%M%S',level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Created logger object in {argv[0]}")

#Load dotenv file and print config (.env) to log
load_dotenv()
config = dotenv_values(".env")
config['MASTER_SMOOTH_SIGMA'] = int(config['MASTER_SMOOTH_SIGMA'])
config['DL'] = int(config['DL'])
for key in config:
    logger.info(f"{key}, {config[key]}")

#Runtime variables
vars = {'rows':0, 'cols':0, 'gain':-1, 'lightIntTime':-1, 'flatIntTime':-1,\
        'intTimes':[], 'filters':[], 'flatConstant':-1,\
        'lightFiles':[], 'biasFiles':[], 'darkFiles':[], 'flatFiles':[],\
        'masterBias':None, 'masterDark':{}, 'masterFlat':None, 'dataFrame':None,\
        'subFrames':{}, 'radii':None}

# Get Frames
#   Make sure the files pass header uniformity checks (frame size and reported gain)
try:
    ## Get Light Frames
    logger.info(f"Gathering Light Frames")
    vars = redux_funcs.getLightFrames(config, vars)
    logger.info(f"Idenfitied frame shape as (rows x cols) {vars['rows']} {vars['cols']}")
    logger.info(f"Idenfitied frame gain (SharpCap-reported) as {vars['gain']}")
    logger.info(f"Identified light integration time as {vars['intTimes']}")
    logger.info(f"Identified filter as {vars['filters']}")
    
    ## Get Flat Frames
    logger.info(f"Gathering Flat Frames for each filter")
    vars = redux_funcs.getFlatFrames(config, vars)
    
    logger.info(f"Full list of integration times identified as {vars['intTimes']}")

    ## Get Dark Frames
    logger.info(f"Gathering Dark Frames for each integration time")

    vars = redux_funcs.getDarkFrames(config, vars)

    ## Get Bias Frames
    logger.info(f"Gathering Bias Frames just in case, I guess? Recall that if there are\n"+\
                " intTimes for flats and lights that correspond to darks, then Bias Frames\n"+\
                " are unneeded. i.e., Bias Frames are only needed if you need to scale Thermal Frames.")
    vars = redux_funcs.getBiasFrames(config, vars)

except Exception as e:
    logger.warning(e)
    exit()

# Dump some info to the log
logger.info(f"Found {len(vars['lightFiles'])} light frame files.")
logger.info(f"Found {len(vars['flatFiles'])} flat frame files.")
logger.info(f"Found {len(vars['darkFiles'])} dark frame files.")
logger.info(f"Found {len(vars['biasFiles'])} bias frame files.")


# Generate Master Frames
## Master Bias
logger.info(f"Working on master bias frame.")
vars = redux_funcs.generateMasterBias(config, vars)

## Master Darks
for intTime in vars['intTimes']:
    logger.info(f"Working on master dark frame for integration time {intTime}.")
    vars['masterDark'][intTime] = redux_funcs.generateMasterDark(config, vars, intTime)

## Master Flat
try:
    logger.info(f"Working on master flat frame.")
    vars = redux_funcs.generateMasterFlat(config, vars)
except Exception as e:
    logger.warning(e)
    exit()

# Generate Data Frame
## Apply Calibration Frames
try:
    logger.info(f"Applying all calibration frames.")
    vars = redux_funcs.generateMasterFlat(config, vars)
except Exception as e:
    logger.warning(e)
    exit()


# Estimate Instrument Magnitude
## Find Sources


## Extract SubFrames

## Extract Radial Profile

## Fit Radial Profile

## Subtract Sky Brightness

## Sum Counts

## Calculate Instrument Magnitude

# Plots


logger.info(f"Fin.")