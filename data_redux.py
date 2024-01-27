##########################################
#####  Imports 
##########################################

# Native Imports
import pprint, datetime, glob
"""
$ python3 -V   
Python 3.9.6
$
"""

# Installed imports
import astropy

import logging
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
from photutils.detection import DAOStarFinder
from tqdm import tqdm
"""
    $ python3
"""

##########################################
#####  Local Class Defintions
##########################################

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






##########################################
#####  Begin Program
##########################################


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



######   SEARCH FOR FITS AND SORT BY TYPE   ###### 
# Read in all FITS file from specified directory
params.fitsFiles = redux_functions.findFITS(params)
params.logger.info("Done finding and sorting files")


try:
    #Note self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime]
    print(params.fitsFiles['light'].keys())
    for lightFilter in tqdm(params.fitsFiles['light'].keys(), desc="Calibrating Light Frames"):
        params.logger.info("Starting work on new master light frame")
        params.logger.info(f"\tFilter {lightFilter}")

        for lightGain in params.fitsFiles['light'][lightFilter].keys():
            params.logger.info(f"\tGain: {lightGain}")

            for lightIntTime in params.fitsFiles['light'][lightFilter][lightGain]:
                params.logger.info(f"\tIntegration time: {lightIntTime}")

                lights = params.fitsFiles['light'][lightFilter][lightGain][lightIntTime]
                params.logger.info(f"\tIdentified light frameList {lights}")

                params.logger.info(f"\tFlats")
                if not params.no_flat:
                    params.logger.info(f"\t\tLooking up flats taken in filter {lightFilter}")
                    #TODO: Wrap this in try/except in cases where filter doesn't match -- fail in this case
                    #TODO: Wrap this in tr/except in cases where gain doesn't match -- alert in this case and modify flat Gain
                    #Assume there is only one integration time for this combination
                    flatGain = lightGain
                    flatIntTime = list(params.fitsFiles['flat'][lightFilter][flatGain].keys())[0]

                    #TODO: This should not fail if the above didn't exception-out, modify for flat gain issues
                    flats =  params.fitsFiles['flat'][lightFilter][flatGain][flatIntTime]
                    params.logger.info(f"\t\tGot flats for filter {lightFilter}: {flats}")
                    
                    params.logger.info(f"\t\tDarks for Flats")
                    if not params.no_dark:
                        params.logger.info(f"\t\t\tLooking up darks to dark correct flats")

                        darksForFlats = redux_functions.getDarks(params, flats)
                        params.logger.info(f"\t\t\tFound darks for dark correcting flats")
                        params.logger.info(f"\t\t\t{darksForFlats}")
                        darksForFlats()
                        masterDarkForFlat = darksForFlats.getMaster()
                        params.logger.info(f"\t\t\tGenerated master dark for dark correcting flats")
                        flats.setDarkFrame(masterDarkForFlat)
                        params.logger.info(f"\t\t\tSet flats Dark Frame to {masterDarkForFlat}")
                        params.logger.info(f"\t\t\t{flats}")
                    else:
                        params.logger.info(f"\tSkipping dark correction for flats based on user input")
                    lights.setFlatFrame(flats.getMaster())
                else:
                    params.logger.info(f"\t\tSkipping flat correction based on user input")

                params.logger.info(f"\tDarks for Light Frames")
                if not params.no_dark:
                    params.logger.info(f"\t\tLooking up darks to dark correct light frames")

                    darksForLight = redux_functions.getDarks(params, lights)
                    params.logger.info(f"\t\tFound darks for dark correcting light frames")
                    darksForLight()
                    masterDarkForLight = darksForLight.getMaster()
                    params.logger.info(f"\t\tGenerated master dark for dark correcting light frames")
                    lights.setDarkFrame(masterDarkForLight)
                    params.logger.info(f"\t\tSet flats Dark Frame to {masterDarkForLight}")
                    
                else:
                    params.logger.info(f"\tSkipping dark correction for light frames based on user input")
                
                params.logger.info(f"Lights: {lights}")

                #Make the call to lights frameList to perform reduction
                finalLight = lights.getMaster()
                params.logger.info(f"Master Light: {finalLight}")

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
    
    #Source Extraction
    from photutils.detection import DAOStarFinder
    import numpy as np
    starFind = DAOStarFinder(threshold=finalLight.median, fwhm=20.0, \
                            sky=finalLight.mean, exclude_border=True, \
                            brightest=10, peakmax=finalLight.max
                            )
    sourceList = starFind(finalLight.data)

    Y, X = np.ogrid[:params.length*2, :params.length*2]
    dist = np.sqrt((X-params.length*2)**2 + (Y-params.length*2)**2)
    ones = np.ones((params.length*2, params.length*2))

    plt.figure(1)
    plt.imshow(finalLight.data-finalLight.mean, cmap='gray_r', \
                origin='upper', vmin=finalLight.mean-2*finalLight.std, vmax=finalLight.mean+2*finalLight.std)

    for source in tqdm(sourceList, desc=f"Extracting Sources for Filter {finalLight.filter}"):
        sourceID = source[0]
        xc, yc = source[2], source[1]
        loc = (xc, yc)
        subFrame = finalLight.data[int(xc-params.length):int(xc+params.length),int(yc-params.length):int(yc+params.length)]
        radial_data_raw = Frame.extractRadialData(subFrame, xC=params.length, yC=params.length)[:params.length]
        radialData = np.concatenate((radial_data_raw[::-1], radial_data_raw))

        p0 = [params.length, 2, finalLight.max, finalLight.mean]
        pixelLocs = np.linspace(0, params.length*2, params.length*2).astype(int)

        fitparams, R2 = Frame.fitGaussian1D(radialData, p0, pixelLocs)

        background = fitparams[-1]
        print(f"background: {background}")
        counts = np.sum(subFrame - background, where=dist<params.radius)
        countsw = np.sum(subFrame, where=dist<params.radius)
        print(f"counts w/ background: {countsw}")
        print(f"counts w/o background: {counts}")
        nPix = np.sum(ones, where=dist<params.radius)
        print(f"nPix: {nPix}")
        countFlux = ((counts/nPix) )/finalLight.intTime
        print(f"count flux: {countFlux}")
        instMag = 0#-2.5*np.log10(countFlux)

        plt.figure(2)
        plt.subplot(1,2,1)
        plt.imshow(subFrame-background, cmap='gray')

        plt.gca().add_patch(Circle((params.length, params.length),radius=params.radius, fill=False, edgecolor='m', alpha=0.5, zorder=100, lw=2.0, linestyle="--"))

        xLabels = np.concatenate((np.linspace(0,params.length,5)[::-1], np.linspace(0,params.length, 5)[1:])).astype(int)

        plt.xticks(np.linspace(0,params.length*2,len(xLabels)), xLabels, rotation=45)
        plt.yticks(np.linspace(0,params.length*2,len(xLabels)), xLabels)

        plt.subplot(1,2,2)
        plt.plot(pixelLocs, radialData-background, 'b.')
        plt.plot(pixelLocs, Frame.gaussian1D(pixelLocs, *fitparams[:-1], 0), 'r')
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

