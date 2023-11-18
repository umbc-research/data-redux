#Plotting
from matplotlib import pyplot as plt
from matplotlib.patches import Circle

#Numerical bits
from scipy.ndimage import gaussian_filter
from scipy.optimize import curve_fit
import numpy as np

#Photometry Utilities
from photutils.detection import DAOStarFinder

#File Handling
from glob import glob
from astropy.io import fits

def gaussian_1d(x, mu, sigma, amplitude, offset):
    #Model function as gaussian with amplitude A and offset G
    return amplitude * np.exp( -((x-mu)/sigma)**2/2 ) + offset

def fit_gaussian_1d(x_data, y_data, p0):
    #p0 behaves by taking a best guess at params (mu, sigma, amplitude, offset)
    params, _ = curve_fit(gaussian_1d, x_data, y_data, p0)

    #Calculate coefficient of determination
    res = y_data - gaussian_1d(x_data, *params)
    sumSqrs_res = np.sum(res*res)
    totSumSqrs = np.sum((y_data-np.mean(y_data))**2)
    R2 = 1.0 - (sumSqrs_res / totSumSqrs)

    return params, R2

def extract_radial_data(data, xC, yC):
    #Get matrix of integer indices associated with subFrame
    y, x = np.indices((data.shape))

    #Generate matrix of radius values
    r = np.sqrt((x - xC)**2 + (y - yC)**2)

    #Force integer values (np.sqrt gives floats)
    r = r.astype(int)

    #Generate a histogram of radius bin, each weighed by corresponding counts
    weightedRadiusHistogram = np.bincount(r.ravel(), weights=data.ravel())
    unweightedRadiusHistogram = np.bincount(r.ravel())

    #Get average for each radius bin
    averageCountsPerRadiusBin = weightedRadiusHistogram / unweightedRadiusHistogram
    return averageCountsPerRadiusBin

def getLightFrames(config, vars):
    vars['lightFiles'] = glob(config['LIGHT_DIR']+"/**/*.fits", recursive=True)
    for i, lightFile in enumerate(vars['lightFiles']):
        with fits.open(lightFile) as hdul_light:
            if i == 0:
                vars['rows'] = hdul_light[0].header['NAXIS2'] #repetitive, but whatever
                vars['cols'] = hdul_light[0].header['NAXIS1']
                vars['gain'] = hdul_light[0].header['GAIN']
            else:
                if not vars['rows'] == hdul_light[0].header['NAXIS2']: raise Exception(f"{lightFile} Conflicting Frame Size")
                if not vars['cols'] == hdul_light[0].header['NAXIS1']: raise Exception(f"{lightFile} Conflicting Frame Size")
                if not vars['gain'] == hdul_light[0].header['GAIN']: raise Exception(f"{lightFile} Conflicting Gain Values")

            vars['intTimes'].append(hdul_light[0].header['EXPTIME'])
            vars['filters'].append(hdul_light[0].header['FILTER'])
        vars['intTimes'] = list(set(vars['intTimes']))
        vars['filters'] = list(set(vars['filters']))
    return vars

def getBiasFrames(config, vars):
    vars['biasFiles'] = glob(config['BIAS_DIR']+"/**/*.fits", recursive=True)
    for biasFile in vars['biasFiles']:
        with fits.open(biasFile) as hdul_bias:
            if not vars['rows'] == hdul_bias[0].header['NAXIS2']: raise Exception(f"{biasFile} Conflicting Frame Size")
            if not vars['cols'] == hdul_bias[0].header['NAXIS1']: raise Exception(f"{biasFile} Conflicting Frame Size")
            if not vars['gain'] == hdul_bias[0].header['GAIN']: raise Exception(f"{biasFile} Conflicting Gain Values")
    return vars

def getFlatFrames(config, vars):
    vars['flatFiles'] = glob(config['FLAT_DIR']+"/**/*.fits", recursive=True)
    neededFlats = []
    for flatFile in vars['flatFiles']:
        with fits.open(flatFile) as hdul_flat:
            filter = hdul_flat[0].header['FILTER']
            if filter in vars['filters']:
                if not vars['rows'] == hdul_flat[0].header['NAXIS2']: raise Exception(f"{flatFile} Conflicting Frame Size")
                if not vars['cols'] == hdul_flat[0].header['NAXIS1']: raise Exception(f"{flatFile} Conflicting Frame Size")
                if not vars['gain'] == hdul_flat[0].header['GAIN']: raise Exception(f"{flatFile} Conflicting Gain Values")

                neededFlats.append(flatFile)

    for flatFile in neededFlats:
        with fits.open(flatFile) as hdul_flat:
            vars['intTimes'].append(hdul_flat[0].header['EXPTIME'])

    vars['intTimes'] = list(set(vars['intTimes']))
    vars['flatFiles'] = neededFlats
    return vars

def getDarkFrames(config, vars):
    vars['darkFiles'] = glob(config['DARK_DIR']+"/**/*.fits", recursive=True)
    neededDarks = []
    for darkFile in  vars['darkFiles']:
        with fits.open(darkFile) as hdul_dark:
            intTime = hdul_dark[0].header['EXPTIME']
            if intTime in vars['intTimes']:
                if not vars['rows'] == hdul_dark[0].header['NAXIS2']: raise Exception(f"{darkFile} Conflicting Frame Size")
                if not vars['cols'] == hdul_dark[0].header['NAXIS1']: raise Exception(f"{darkFile} Conflicting Frame Size")
                if not vars['gain'] == hdul_dark[0].header['GAIN']: raise Exception(f"{darkFile} Conflicting Gain Values")

                neededDarks.append(darkFile)

    vars['darkFiles']  = neededDarks
    return vars


def generateMasterBias(config, vars):
    biasStack = []
    for biasFile in vars['biasFiles']:
        with fits.open(biasFile) as hdul_bias:
            biasStack.append(hdul_bias[0].data)

    #Basic outlier detection. Not fleshed out yet :( 
    # means = np.mean(biasStack, axis=(1,2))
    # medians = np.median(biasStack, axis=(1,2))
    # stds = np.std(biasStack, axis=(1,2))

    # meanSTD = np.std(means)
    # if len(means[means - np.median(means) > 3*meanSTD]) > 0:
    #     print("Outlier in Bias Frame Means")

    # medianSTD = np.std(medians)
    # if len(medians[medians - np.median(medians) > 3*medianSTD]) > 0:
    #     print("Outlier in Bias Frame Medians")

    # stdSTD = np.std(stds)
    # if len(stds[stds - np.median(stds) > 3*stdSTD]) > 0:
    #     print("Outlier in Bias Frame STDs")
    
    if not config['MASTER_SMOOTH_SIGMA'] == 0:
        vars['masterBias'] = gaussian_filter(np.median(biasStack, axis=0), sigma=config['MASTER_SMOOTH_SIGMA'])
    else:
        vars['masterBias'] = np.median(biasStack, axis=0)

def generateMasterDark(config, vars, intTime):
    darkStack = []
    for darkFile in vars['darkFiles']:
        with fits.open(darkFile) as hdul_dark:
            darkStack.append(hdul_dark[0].data)

    if not config['MASTER_SMOOTH_SIGMA'] == 0:
        return gaussian_filter(np.median(darkStack, axis=0), sigma=config['MASTER_SMOOTH_SIGMA'])
    else:
        return np.median(darkStack, axis=0)

def generateMasterFlat(config, vars):
    if vars['masterDark'] == None: 
        raise Exception("Master Darks not defined yet.")
    
    flatStack = []
    for i, flatFile in enumerate(vars['flatFiles']):
        with fits.open(flatFile) as hdul_flat:
            intTime = hdul_flat[0].header['EXPTIME']
            flatIntTime = intTime
            try:
                flatStack[i] = hdul_flat[0].data - vars['masterDark'][flatIntTime] 
            except:
                raise Exception(f"Master Dark of integration time {flatIntTime} not defined.")
                          
    if not config['MASTER_SMOOTH_SIGMA'] == 0:
        vars['masterFlat'] = gaussian_filter(np.median(flatStack, axis=0), sigma=config['MASTER_SMOOTH_SIGMA'])
    else:
        vars['masterFlat'] = np.median(flatStack, axis=0)

    vars['flatConstant'] = np.mean(vars['masterFlat'])
