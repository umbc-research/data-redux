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
config['MASTER_SMOOTH_SIGMA'] = float(config['MASTER_SMOOTH_SIGMA'])
config['DL'] = int(config['DL'])
config['APERTURE_PIX'] = int(config['APERTURE_PIX'])

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
    logger.info(f"Identified light integration time as {vars['lightIntTime']}")
    logger.info(f"Identified filter as {vars['filters']}")
    
    ## Get Flat Frames
    logger.info(f"Gathering Flat Frames for each filter")
    vars = redux_funcs.getFlatFrames(config, vars)
    
    logger.info(f"Full list of integration times identified as {vars['flatIntTime']}")

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
## Generate Master Bias
logger.info(f"Working on master bias frame.")
vars = redux_funcs.generateMasterBias(config, vars)

### Log Bias Frame Specs
mean, median, std, max = redux_funcs.frameSpecs(vars['masterBias'])
logger.info(f"Bias Frame Mean: {mean}")
logger.info(f"Bias Frame Median: {median}")
logger.info(f"Bias Frame STD: {std}")
logger.info(f"Bias Frame Max: {max}")
redux_funcs.plotFrame(vars['masterBias'], f"Bias Frame \nMean:{mean:0.2f}; Median:{median:0.2f}; STD:{std:0.2f}; Max:{max:0.2f}", "bias")

## Generate Master Darks
for intTime in vars['intTimes']:
    logger.info(f"Working on master dark frame for integration time {intTime}.")
    vars['masterDark'][intTime] = redux_funcs.generateMasterDark(config, vars, intTime)

### Log Dark Frame Specs
for intTime in vars['intTimes']:
    mean, median, std, max = redux_funcs.frameSpecs(vars['masterDark'][intTime])
    logger.info(f"Dark Frame [{intTime}s] Mean: {mean}")
    logger.info(f"Dark Frame [{intTime}s] Median: {median}")
    logger.info(f"Dark Frame [{intTime}s] STD: {std}")
    logger.info(f"Dark Frame [{intTime}s] Max: {max}")
    redux_funcs.plotFrame(vars['masterDark'][intTime], f"{intTime:0.2f}s Dark Frame  \nMean:{mean:0.2f}; Median:{median:0.2f}; STD:{std:0.2f}; Max:{max:0.2f}", f"dark_{'-'.join(str(intTime).split('.'))}")

## Generate Master Flat
try:
    logger.info(f"Working on master flat frame.")
    vars = redux_funcs.generateMasterFlat(config, vars)
except Exception as e:
    logger.warning(e)
    exit()

### Log Flat Frame Specs
mean, median, std, max = redux_funcs.frameSpecs(vars['masterFlat']/vars['flatConstant'])
logger.info(f"Flat Frame Mean: {mean}")
logger.info(f"Flat Frame Median: {median}")
logger.info(f"Flat Frame STD: {std}")
logger.info(f"Flat Frame Max: {max}")
redux_funcs.plotFrame(vars['masterFlat']/vars['flatConstant'], f"Flat Frame \nMean:{mean:0.2f}; Median:{median:0.2f}; STD:{std:0.2f}; Max:{max:0.2f}", f"flat_{'-'.join(str(vars['flatIntTime']).split('.'))}_{vars['filters'][0]}")

# Generate Data Frame
## Apply Calibration Frames
try:
    logger.info(f"Applying all calibration frames.")
    vars = redux_funcs.generateDataFrame(config, vars)
except Exception as e:
    logger.warning(e)
    exit()

### Log Data Frame Specs
mean, median, std, max = redux_funcs.frameSpecs(vars['dataFrame'])
logger.info(f"Data Frame Mean: {mean}")
logger.info(f"Data Frame Median: {median}")
logger.info(f"Data Frame STD: {std}")
logger.info(f"Data Frame Max: {max}")
redux_funcs.plotFrame(vars['dataFrame'], f"Data Frame with Background \nMean:{mean:0.2f}; Median:{median:0.2f}; STD:{std:0.2f}; Max:{max:0.2f}", f"data_{'-'.join(str(vars['lightIntTime']).split('.'))}_{vars['filters'][0]}")



# Estimate Instrument Magnitude
## Extract Sources, SubFrames, Radial Profile Parameters
logger.info(f"Extracting Sources, SubFrames, and Radial Profile Parameters")
vars = redux_funcs.findSources(config, vars)

## Calculate Instrument Magnitude
logger.info(f"Estimating Instrument Magnitudes")
vars = redux_funcs.getMagnitudes(config, vars)

# Plots
redux_funcs.plotFinder(config, vars, f"data_finder_{'-'.join(str(vars['lightIntTime']).split('.'))}_{vars['filters'][0]}")

for sourceID in vars['subFrames']:
    subFrame, loc, radialData, params, R2, instMag, countFlux = vars['subFrames'][sourceID]
    redux_funcs.plotSubFrame(config, vars, sourceID)
    logger.info(f"PhotUtils Source {sourceID} at (i,j) {loc[0]},{loc[1]}\n"+\
                f"  Model Fit: Center {params[0]}; STD {params[1]} pix; Amp {params[2]} counts; Offset {params[3]} counts\n"+\
                f"  Model Fit Coefficient of Determination (R^2) {R2}\n"+\
                f"  Filter {vars['filters'][0]}; instrument magnitude {instMag:0.6f}; countFlux {countFlux:0.2f}")

for key in vars:
    logger.info(f"{key}: {vars[key]}")

logger.info(f"Fin.")