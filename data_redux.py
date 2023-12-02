import argparse
from sys import exit

from matplotlib import pyplot as plt

#Authored packages
from Observation import Redux

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

# Exclude Filter
parser.add_argument('--excludeFilter', '-x', '-excludeFilters', '-E', '-X', metavar="[]", \
                    action="append", required=False, nargs='+', help="Exclude filters",\
                    choices=['U', 'B', 'V', 'R', 'I'])

# Force Flag
parser.add_argument('--force', default=False, action='store_true',\
                    help="Force computations without darks or matching gains"
                    )

# Skip Flat Flag
parser.add_argument('--no-flat', default=False, action='store_true',\
                    help="Force reduction pipeline to not use flats"
                    )

# Specify Version flag
parser.add_argument('--version', '-V', '-version', action='version', version='%(prog)s Version 0.0, 20231129')

## REQUIRED ARGUMENTS
required = parser.add_argument_group('required arguments')

# Specify Src Data FITS directory
required.add_argument("--datadir",'-D', '-datadir', action="store", metavar='dir',type=str, required=True,\
                    help="Directory containing all raw light frames",\
                    )

# Specify Calibration  FITS directory
required.add_argument("--caldir",'-C', '-caldir', action="store", metavar='dir',type=str, required=True,\
                    help="Directory containing all calibration frames",\
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

print("Done sorting files")
print()


#Note self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime]
for lightFilter in redux.frameListDict['light'].keys():
    print("Starting work on new master light frame.")
    print(f"  Working with light filter: {lightFilter}")
    for lightGain in redux.frameListDict['light'][lightFilter].keys():
        print(f"  Working with light gain: {lightGain}")

        for lightIntTime in redux.frameListDict['light'][lightFilter][lightGain]:
            print(f"  Working with light integration time: {lightIntTime}")

            lights = redux.frameListDict['light'][lightFilter][lightGain][lightIntTime]
            print(f"    Got lights: {lights}")

            if not redux.no_flat:
                #TODO: Wrap this in try/except in cases where filter doesn't match -- fail in this case
                #TODO: Wrap this in tr/except in cases where gain doesn't match -- alert in this case and modify flat Gain
                #Assume there is only one integration time for this combination
                flatGain = lightGain
                flatIntTime = list(redux.frameListDict['flat'][lightFilter][flatGain].keys())[0]

                #TODO: This should not fail if the above didn't exception-out, modify for flat gain issues
                flats =  redux.frameListDict['flat'][lightFilter][flatGain][flatIntTime]
                print(f"    Got flats: {flats}")

                #Get Darks with filter=None, gain=lightGain, intTime=flatIntTime
                #  If none, found raise exception
                #  If gain is issue, alert and modify dark gain
                #  If int time is issue, subtract biases out and scale thermal signal
                # for now, assume all will work ...
                try:
                    darksForFlats = redux.frameListDict['dark'][None][lightGain][flatIntTime]
                except KeyError as e:
                    print(e,)
                    print(" Issue with Dark for Flats")
                    try:
                        redux.frameListDict['dark']
                    except KeyError as e:
                        print("Unable to find darks. Exiting.")
                        exit()
                    try:
                        redux.frameListDict['dark'][None]
                    except KeyError as e:
                        print("Dark dictionary improperly formatted. Filter is not None. Exiting.")
                        exit()
                    try:
                        redux.frameListDict['dark'][None][lightGain]
                    except KeyError as e:
                        #TODO: Provide override flag for just goofing around!
                        print("Dark has different gain. Can proceed if --force flag used.")
                        if  redux.force:
                            print("Functionality for proceeding with unequal gains not available yet.")
                            exit()
                    try:
                        redux.frameListDict['dark'][None][lightGain][flatIntTime]
                    except KeyError as e:
                        #TODO: Provide override flag for just goofing around!
                        print("Dark has different integration time. Can proceed to scale thermal signal if --force flag used.")
                        if  redux.force:
                            print("Functionality providing thermal scaling not available yet")
                            exit()
                        else:
                            print(f"No darks provided that with equal integration time for {flats}.\n"+\
                                " You can force the computation to proceed by rerunning with --force flag.\n"+\
                                " The result will likely not be useful for estimating physical parameters.")
                except Exception as e:
                    print(e)
                    exit()
                print(f"    Got darks for flats: {darksForFlats}")

                masterDarkForFlat = darksForFlats()
                flats.setDarkFrameObj(masterDarkForFlat)


            #Get Darks with filter=None, gain=lightGain, intTime=lightIntTime
            #  If none, found raise exception
            #  If gain is issue, alert and modify dark gain
            #  If int time is issue, subtract biases out and scale thermal signal
            # for now, assume all will work ...
            try:
                darksForLights = redux.frameListDict['dark'][None][lightGain][lightIntTime]
            except KeyError as e:
                print(e,)
                print(" Issue with Dark for Lights")
                try:
                    redux.frameListDict['dark']
                except KeyError as e:
                    print("Unable to find darks. Exiting.")
                    exit()
                try:
                    redux.frameListDict['dark'][None]
                except KeyError as e:
                    print("Dark dictionary improperly formatted. Filter is not None. Exiting.")
                    exit()
                try:
                    redux.frameListDict['dark'][None][lightGain]
                except KeyError as e:
                    #TODO: Provide override flag for just goofing around!
                    print("Dark has different gain. Filter is not None. Can proceed if --force flag used.")
                    if  redux.force:
                        pass
                print("Seems gain or integration times aren't matching with darks/flats.\n"+\
                      "Further investigation is needed to determine whether darks must be scaled.\n" + e)
                
            print(f"    Got darks for lights: {darksForLights}")

 
            lights.setDarkFrameObj(darksForLights())
            if not redux.no_flat:
                lights.setFlatFrameObj(flats())


            finalLight = lights()

            plt.figure(figsize=(12,8))
            plt.imshow(finalLight.data, \
                       vmin = finalLight.mean - finalLight.std, vmax = finalLight.mean + finalLight.std, \
                       cmap='gray'
                      )
            
            plt.title(f"Min,Max: {finalLight.min:0.1f}, {finalLight.max:0.1f}; Median: {finalLight.median:0.1f};"+\
                      f"Mean: {finalLight.mean:0.1f}; STD: {finalLight.std:0.1f}\n{finalLight}")
            plt.tight_layout()
            plt.show()
            



            


