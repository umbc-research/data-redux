from sys import exit
from tqdm import tqdm

from matplotlib import pyplot as plt
from matplotlib.patches import Circle

#Yet to be implemented
#from scipy.ndimage import gaussian_filter

#Authored packages
from Observation import Redux, Frame

if __name__ == "__main__":
    redux = Redux()

    try:
        redux.makeLog()

        redux.logger.info(redux)

        # Read in all FITS file from specified directory
        redux.findFITS()
        redux.logger.info("Done sorting files")

        #Print entire Frame/FrameList dictionary to log
        redux.logger.debug(redux)

        #Note self.frameListDict[frame.type][frame.filter][frame.gain][frame.intTime]
        for lightFilter in tqdm(redux['light'].keys(), desc="Calibrating Light Frames"):
            redux.logger.info("Starting work on new master light frame")
            redux.logger.info(f"\tFilter {lightFilter}")

            for lightGain in redux['light'][lightFilter].keys():
                redux.logger.info(f"\tGain: {lightGain}")

                for lightIntTime in redux['light'][lightFilter][lightGain]:
                    redux.logger.info(f"\tIntegration time: {lightIntTime}")

                    lights = redux['light'][lightFilter][lightGain][lightIntTime]
                    redux.logger.info(f"\tIdentified light frameList {lights}")

                    redux.logger.info(f"\tFlats")
                    if not redux.no_flat:
                        redux.logger.info(f"\t\tLooking up flats taken in filter {lightFilter}")
                        #TODO: Wrap this in try/except in cases where filter doesn't match -- fail in this case
                        #TODO: Wrap this in tr/except in cases where gain doesn't match -- alert in this case and modify flat Gain
                        #Assume there is only one integration time for this combination
                        flatGain = lightGain
                        flatIntTime = list(redux['flat'][lightFilter][flatGain].keys())[0]

                        #TODO: This should not fail if the above didn't exception-out, modify for flat gain issues
                        flats =  redux['flat'][lightFilter][flatGain][flatIntTime]
                        redux.logger.info(f"\t\tGot flats for filter {lightFilter}: {flats}")
                        
                        redux.logger.info(f"\t\tDarks for Flats")
                        if not redux.no_dark:
                            redux.logger.info(f"\t\t\tLooking up darks to dark correct flats")

                            darksForFlats = redux.getDarks(flats)
                            redux.logger.info(f"\t\t\tFound darks for dark correcting flats")
                            redux.logger.info(f"\t\t\t{darksForFlats}")
                            darksForFlats()
                            masterDarkForFlat = darksForFlats.getMaster()
                            redux.logger.info(f"\t\t\tGenerated master dark for dark correcting flats")
                            flats.setDarkFrame(masterDarkForFlat)
                            redux.logger.info(f"\t\t\tSet flats Dark Frame to {masterDarkForFlat}")
                            redux.logger.info(f"\t\t\t{flats}")
                        else:
                            redux.logger.info(f"\tSkipping dark correction for flats based on user input")
                        lights.setFlatFrame(flats.getMaster())
                    else:
                        redux.logger.info(f"\t\tSkipping flat correction based on user input")

                    redux.logger.info(f"\tDarks for Light Frames")
                    if not redux.no_dark:
                        redux.logger.info(f"\t\tLooking up darks to dark correct light frames")

                        darksForLight = redux.getDarks(lights)
                        redux.logger.info(f"\t\tFound darks for dark correcting light frames")
                        darksForLight()
                        masterDarkForLight = darksForLight.getMaster()
                        redux.logger.info(f"\t\tGenerated master dark for dark correcting light frames")
                        lights.setDarkFrame(masterDarkForLight)
                        redux.logger.info(f"\t\tSet flats Dark Frame to {masterDarkForLight}")
                        
                    else:
                        redux.logger.info(f"\tSkipping dark correction for light frames based on user input")
                    
                    redux.logger.info(f"Lights: {lights}")

                    #Make the call to lights frameList to perform reduction
                    finalLight = lights.getMaster()
                    redux.logger.info(f"Master Light: {finalLight}")

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

        Y, X = np.ogrid[:redux.length*2, :redux.length*2]
        dist = np.sqrt((X-redux.length*2)**2 + (Y-redux.length*2)**2)
        ones = np.ones((redux.length*2, redux.length*2))

        plt.figure(1)
        plt.imshow(finalLight.data-finalLight.mean, cmap='gray_r', \
                   origin='upper', vmin=finalLight.mean-2*finalLight.std, vmax=finalLight.mean+2*finalLight.std)

        for source in tqdm(sourceList, desc=f"Extracting Sources for Filter {finalLight.filter}"):
            sourceID = source[0]
            xc, yc = source[2], source[1]
            loc = (xc, yc)
            subFrame = finalLight.data[int(xc-redux.length):int(xc+redux.length),int(yc-redux.length):int(yc+redux.length)]
            radial_data_raw = Frame.extractRadialData(subFrame, xC=redux.length, yC=redux.length)[:redux.length]
            radialData = np.concatenate((radial_data_raw[::-1], radial_data_raw))

            p0 = [redux.length, 2, finalLight.max, finalLight.mean]
            pixelLocs = np.linspace(0, redux.length*2, redux.length*2).astype(int)

            params, R2 = Frame.fitGaussian1D(radialData, p0, pixelLocs)

            background = params[-1]
            print(f"background: {background}")
            counts = np.sum(subFrame - background, where=dist<redux.radius)
            countsw = np.sum(subFrame, where=dist<redux.radius)
            print(f"counts w/ background: {countsw}")
            print(f"counts w/o background: {counts}")
            nPix = np.sum(ones, where=dist<redux.radius)
            print(f"nPix: {nPix}")
            countFlux = ((counts/nPix) )/finalLight.intTime
            print(f"count flux: {countFlux}")
            instMag = 0#-2.5*np.log10(countFlux)

            plt.figure(2)
            plt.subplot(1,2,1)
            plt.imshow(subFrame-background, cmap='gray')

            plt.gca().add_patch(Circle((redux.length, redux.length),radius=redux.radius, fill=False, edgecolor='m', alpha=0.5, zorder=100, lw=2.0, linestyle="--"))

            xLabels = np.concatenate((np.linspace(0,redux.length,5)[::-1], np.linspace(0,redux.length, 5)[1:])).astype(int)

            plt.xticks(np.linspace(0,redux.length*2,len(xLabels)), xLabels, rotation=45)
            plt.yticks(np.linspace(0,redux.length*2,len(xLabels)), xLabels)

            plt.subplot(1,2,2)
            plt.plot(pixelLocs, radialData-background, 'b.')
            plt.plot(pixelLocs, Frame.gaussian1D(pixelLocs, *params[:-1], 0), 'r')
            plt.grid(1)

            plt.axvline(x = params[0]-redux.radius, color = 'm', linestyle="--")
            plt.axvline(x = params[0]+redux.radius, color = 'm', linestyle="--")

            plt.xticks(np.linspace(0, redux.length*2, len(xLabels)), xLabels, rotation=45)
            plt.suptitle(f"Filter {finalLight.filter} PhotUtils Source ID {sourceID} w/o Background\nFit $R^2=${R2:0.4f}; $m={instMag:0.3f}$")
            plt.savefig(f"{redux.outdir}/subframe_{redux.save}_{sourceID}_{finalLight.filter}.png")

            plt.close(2)
            plt.figure(1)
            plt.scatter(loc[1], loc[0], facecolors='none', edgecolors='b', s=50)
            plt.text(loc[1]+5, loc[0]+5, "{}, $m_{{inst}}=${:0.3f}".format(sourceID, instMag), color='k')
        plt.figure(1)
        plt.savefig('{}/finder_{}_{}_{}_{}_{}.png'.format(redux.outdir, redux.save, finalLight.type,\
                                    finalLight.filter, f"{int(finalLight.gain):d}", f"{finalLight.intTime:0.1f}".replace('.','-')))
        plt.close(1)

    except Exception as e:
        redux.logger.info("Something went wrong:")
        redux.logger.exception(e)
        redux.logger.info("Exiting ...")
        exit()
    redux.logger.info(f"Arrived at end of program. Exiting.")