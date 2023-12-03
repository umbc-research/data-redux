from sys import exit

from matplotlib import pyplot as plt

#Authored packages
from Observation import Redux

redux = Redux()

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

            figure = plt.figure(figsize=(12,8))
            plt.imshow(finalLight.data, \
                       vmin = finalLight.mean - finalLight.std, vmax = finalLight.mean + finalLight.std, \
                       cmap='gray'
                      )
            
            plt.title(f"Min,Max: {finalLight.min:0.1f}, {finalLight.max:0.1f}; Median: {finalLight.median:0.1f};"+\
                      f"Mean: {finalLight.mean:0.1f}; STD: {finalLight.std:0.1f}\n{finalLight}")
            plt.tight_layout()
            figure.canvas.manager.window.move(0,0)
            plt.show()
            


                


