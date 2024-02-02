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

# Define placeholder class structure to hold program parameters
#  Only a single object will be created at runtime.
class params:
    pass

    def __str__(self):
        return pprint.pformat(vars(self), indent=1, depth=5)



##############################################
#####  Set Arguments and Logging
##############################################

######   COMMAND LINE ARGUMENTS   ######
redux_functions.setProgramArguments(params)

######   LOGGER OBJECT   ######
# Configure logging object, prior to creation
#  Set the filename to be within the specified OUTDIR directory, with date-stamped filename and specific formats
logging.basicConfig(filename='{}/redux_{}.log'.format(params.outdir, datetime.datetime.now().strftime("%Y%m%dT%H%M%S")),\
    encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s', \
    datefmt='%Y%m%dT%H%M%S')

# Actually create the logger object
params.logger = logging.getLogger(__name__)

# Set logging debug level (info isn't as verbose as debug)
if params.level == 'DEBUG':
    params.logger.setLevel(logging.DEBUG)
else:
    params.logger.setLevel(logging.INFO) 

# Print some messages to the log
params.logger.info(f"Created logger object.")
params.logger.debug(f"Logger made with debugging level set.")

# Print the entire parameter dictionary to the log (as it is now)
params.logger.info(params)


##############################################
#####  Search for FITS files and sort (type)
##############################################
# Read in all FITS file from specified directory
# THIS FUNCTION DOES A LOT
# It associates a (type, filter, gain, intTime) tuple with a FRAMELIST
#    that matches all of those.
# The FrameList object is also the object/class that does all the actual math.
# The FrameList object __call__ function is called when FrameListObj() is written
# This is the call that does the actual calibration. Everything before that just puts
#   the pieces in place. I.e., setting flats, setting darks
params.fitsFiles = redux_functions.findFITS(params)
params.logger.info("Done finding and sorting files")

try:
    ##############################################
    #####  Main Calibration Loop
    ##############################################

    ######   Loop through each filter   ###### 
    # Note: fitsFiles Dict structure: fitsFiles[frame.type][frame.filter][frame.gain][frame.intTime]
    for lightFilter in tqdm(params.fitsFiles['light'].keys(), desc="Calibrating Light Frames"):
        params.logger.info("Starting work on new master light frame")
        params.logger.info(f"\tFilter: {lightFilter}")

        ######   Loop through each gain setting   ###### 
        for lightGain in params.fitsFiles['light'][lightFilter].keys():
            params.logger.info(f"\tGain: {lightGain}")

            ######   Loop through each integration time   ###### 
            for lightIntTime in params.fitsFiles['light'][lightFilter][lightGain]:
                params.logger.info(f"\tIntegration time: {lightIntTime}s")

                lights = params.fitsFiles['light'][lightFilter][lightGain][lightIntTime]
                params.logger.info(f"\tIdentified light frameList\n\t {lights}")



                ##############################################
                #####  Calibrate Flat Frames
                ##############################################
                params.logger.info(f"\tNow generating Flat Master Frame")
                params.logger.info(f"\t\tLooking up flats taken in filter {lightFilter}")
                #TODO: Wrap this in try/except in cases where filter doesn't match -- fail in this case
                #TODO: Wrap this in tr/except in cases where gain doesn't match -- alert in this case and modify flat Gain
                #Assume there is only one integration time for this combination
                flatGain = lightGain  #These should always be equal ... but we should check!

                #Find the integration time for the flat frame in this filter and gain setting
                # Refactor this, some of it is meaningless or can be cleaned up
                flatIntTime = list(params.fitsFiles['flat'][lightFilter][flatGain].keys())[0]

                #TODO: This should not fail if the above didn't exception-out, modify for flat-gain mismatches
                #  This is because we use the light gain to sort the flats earlier on when we sort the FITS by type
                flats =  params.fitsFiles['flat'][lightFilter][flatGain][flatIntTime]
                params.logger.info(f"\t\tGot flats for filter {lightFilter}\n\t\t\t {flats}")
                    
                params.logger.info(f"\t\tLooking up darks for flat calibration")

                # This gets all of the dark frames that should apply to this FrameList of flats
                darksForFlats = redux_functions.getDarks(params, flats)
                params.logger.info(f"\t\t\tFound darks for flat calibration")
                params.logger.info(f"\t\t\t{darksForFlats}")

                ### ACCUMULATE DARKS FOR FLATS ### 
                masterDarkForFlat = redux_functions.accumulate(darksForFlats)
                masterDarkForFlatFrame = Frame( masterDarkForFlat ,\
                                type='master', filter=darksForFlats[0].filter, gain=darksForFlats[0].gain, \
                                intTime=darksForFlats[0].intTime, header=darksForFlats[0].header)
                darksForFlats.setMaster( masterDarkForFlatFrame )

                
                params.logger.info(f"\t\t\tGenerated Master Dark for Flat Calibration\n\t\t\t\t {masterDarkForFlatFrame}")

                # For the flat FrameList, set the appropriate master dark frame
                flats.setDarkFrame( masterDarkForFlatFrame )

                ### ACCUMULATE Flats ### 
                masterFlat = redux_functions.accumulate( [f.data-masterDarkForFlatFrame.data for f in flats] )
                flat_C = np.median(masterFlat)

                #Normalize flat frame
                masterFlat /= flat_C
                masterFlatFrame = Frame( masterFlat , \
                                type='master', filter=flats[0].filter, gain=flats[0].gain, \
                                intTime=flats[0].intTime, header=flats[0].header)
                params.logger.info(f"\t\t\t Generated master flat\n\t\t\t\t {masterFlatFrame}")
                flats.setMaster( masterFlatFrame )

                lights.setFlatFrame(masterFlatFrame)
                
                

                ######   Work on applying darks to light frames   ######
                params.logger.info(f"\tWorking to generate Master Dark for light calibration")

                ##############################################
                #####  Calibrate Light Frames
                ##############################################
                params.logger.info(f"\t\tLooking up darks for light frame calibration")

                # This finds all of the dark frames for this FrameList of light frames
                darksForLight = redux_functions.getDarks(params, lights)
                params.logger.info(f"\t\tFound darks for dark correcting light frames")
                masterDarkForLights = redux_functions.accumulate( darksForLight )
                masterDarkForLightsFrame = Frame( masterDarkForLights , \
                                type='master', filter=darksForLight[0].filter, gain=darksForLight[0].gain, \
                                intTime=darksForLight[0].intTime, header=darksForLight[0].header)
                params.logger.info(f"\t\t\tSet master dark for lights to {masterDarkForLightsFrame}")
                darksForLight.setMaster( masterDarkForLightsFrame )

                params.logger.info(f"\t\tGenerated master dark for light frame calibration")

                lights.setDarkFrame(masterDarkForLightsFrame)
                masterLight = redux_functions.accumulate( [(l-masterDarkForLightsFrame)/(masterFlatFrame.data) for l in lights] )

                masterLightFrame = Frame( masterLight , \
                                type='master', filter=lights[0].filter, gain=lights[0].gain, \
                                intTime=lights[0].intTime, header=lights[0].header)
                params.logger.info(f"\t\t\tSet master light to {masterLightFrame}")
                lights.setMaster( masterLightFrame )


                # plt.figure(figsize=(12,8))
                # plt.imshow(finalLight.data, \
                #         vmin = finalLight.mean - finalLight.std, vmax = finalLight.mean + finalLight.std, \
                #         cmap='gray'
                #         )

                # plt.title(f"(Min,Max): ({finalLight.min:0.1f}, {finalLight.max:0.1f}); Median: {finalLight.median:0.1f}; "+\
                #             f"Mean: {finalLight.mean:0.1f}; STD: {finalLight.std:0.1f}\n{finalLight}"
                #             )
                # plt.tight_layout()

                # if redux.save:
                #     plt.savefig('{}/{}_{}_{}_{}_{}.png'.format(redux.outdir, redux.save, finalLight.type,\
                #                 finalLight.filter, f"{int(finalLight.gain):d}", f"{finalLight.intTime:0.1f}".replace('.','-')))
                # else:
                #     plt.show()
    

    ##############################################
    #####  Begin Source Extraction
    ##############################################
                
    finalLight = masterLightFrame
    starFind = DAOStarFinder(threshold=finalLight.median, fwhm=20.0, \
                            sky=finalLight.mean, exclude_border=True, \
                            brightest=10, peakmax=finalLight.max
                            )
    sourceList = starFind(finalLight.data)

    Y, X = np.ogrid[:params.length*2, :params.length*2]
    dist = np.sqrt((X-params.length)**2 + (Y-params.length)**2)
    ones = np.ones((params.length*2, params.length*2))

    plt.figure(1)
    plt.imshow(finalLight.data-finalLight.mean, cmap='gray_r', \
                origin='upper', vmin=finalLight.mean-2*finalLight.std, vmax=finalLight.mean+2*finalLight.std)

    for source in tqdm(sourceList, desc=f"Extracting Sources for Filter {finalLight.filter}"):
        sourceID = source[0]
        xc, yc = source[2], source[1]
        loc = (xc, yc)
        subFrame = finalLight.data[int(xc-params.length):int(xc+params.length),int(yc-params.length):int(yc+params.length)]
        radial_data_raw = redux_functions.extractRadialData(subFrame, xC=params.length, yC=params.length)[:params.length]
        radialData = np.concatenate((radial_data_raw[::-1], radial_data_raw))

        p0 = [params.length, 2, finalLight.max, finalLight.mean]
        pixelLocs = np.linspace(0, params.length*2, params.length*2).astype(int)

        fitparams, R2 = redux_functions.fitGaussian1D(radialData, p0, pixelLocs)

        background = fitparams[-1]
        counts = np.sum(subFrame, where=dist<params.radius)
        nPix = np.sum(ones, where=dist<params.radius)
        countFlux = counts/nPix/finalLight.intTime
        instMag = -2.5*np.log10(countFlux)

        plt.figure(2)
        plt.subplot(1,2,1)
        plt.imshow(subFrame-background, cmap='gray')

        plt.gca().add_patch(Circle((params.length, params.length),radius=params.radius, fill=False, edgecolor='m', alpha=0.5, zorder=100, lw=2.0, linestyle="--"))

        xLabels = np.concatenate((np.linspace(0,params.length,5)[::-1], np.linspace(0,params.length, 5)[1:])).astype(int)

        plt.xticks(np.linspace(0,params.length*2,len(xLabels)), xLabels, rotation=45)
        plt.yticks(np.linspace(0,params.length*2,len(xLabels)), xLabels)

        plt.subplot(1,2,2)
        plt.plot(pixelLocs, radialData-background, 'b.')
        plt.plot(pixelLocs, redux_functions.gaussian1D(pixelLocs, *fitparams[:-1], 0), 'r')
        plt.grid(1)

        plt.axvline(x = fitparams[0]-params.radius, color = 'm', linestyle="--")
        plt.axvline(x = fitparams[0]+params.radius, color = 'm', linestyle="--")

        plt.xticks(np.linspace(0, params.length*2, len(xLabels)), xLabels, rotation=45)
        plt.suptitle(f"Filter {finalLight.filter} PhotUtils Source ID {sourceID} w/o Background\nFit $R^2=${R2:0.4f}; $m={instMag:0.3f}$")
        plt.savefig(f"{params.outdir}/subframe_{params.save}_{sourceID}_{finalLight.filter}.png")

        plt.close(2)
        plt.figure(1)
        plt.scatter(loc[1], loc[0], facecolors='none', edgecolors='b', s=50)
        plt.text(loc[1]+5, loc[0]+5, "{}, $m_{{inst}}=${:0.3f}".format(sourceID, instMag), color='k')
    plt.figure(1)
    plt.savefig('{}/finder_{}_{}_{}_{}_{}.png'.format(params.outdir, params.save, finalLight.type,\
                                finalLight.filter, f"{int(finalLight.gain):d}", f"{finalLight.intTime:0.1f}".replace('.','-')))
    plt.close(1)

except Exception as e:
    params.logger.info("Something went wrong:")
    params.logger.exception(e)
    params.logger.info("Exiting ...")
    exit()
params.logger.info(f"Arrived at end of program. Exiting.")

