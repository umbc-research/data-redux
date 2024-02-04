# data-redux
Code base of routines and the entire reduction pipeline for UMBC Observatory equipment

# TO RUN:
python3 main.py -r 15 -o analysis -d ../../fits/inst-mag-ngc/ -c calibration -length 50 -S 0 --level DEBUG --force -x U B R I
-d is data directory
-c is calibration directory (if seperate)
-O is output directory
--save is base name of file
-S is smoothing (set to 0 for now)

# Pipeline
See [Redux Pipeline](https://obs-web.rs.umbc.edu/doku.php?id=wiki:astronomy:observational_astronomy:data_reduction_telescope) on UMBC Observatory Wiki.
This code base requires a directory of light frames, dark frames (and/or bias and thermal frames), and flat frames. Light frames and flat frames of multiple filters can be in the same directory.

## Local Effects Equation
$$L_{ij}(\lambda) = \Bigl[\epsilon_{ij}(\lambda)I_{ij}(\lambda) + T_{ij}\Bigr]t + B_{ij}$$

With ... 
$L_{ij}(\lambda)$ being the detected counts in the pixel located in row $i$ and column $j$ in filter sensitive to $\lambda$.
$\epsilon_{ij}(\lambda)$ being the wavelength-sensitive pixel-by-pixel measure of the deviation from uniform sensitivity.
$I_{ij}(\lambda)$ being the counts/second delivered to the pixel located in row $i$ and column $j$ related to photoelectrons liberated by photons of wavelength $\lambda$.
$t$ being the integration time during which the detector allowed electrons to be collected.
$T_{ij}(\lambda)$ being the counts/second delivered to the pixel located in row $i$ and column $j$ related to thermally-liberated electrons.
$B_{ij}(\lambda)$ being the counts delivered to the pixel located in row $i$ and column $j$ related to electrons liberated by the placement of a bias voltage across the pixel that is required to collect liberated electrons.

We aim to isolate $I_{ij}(\lambda)t$ through the careful use of calibration frames.

### Calibration Frames
#### Dark Frames
We calibrate the thermal signal and bias signal ( $T_{ij}t$ and $B_{ij}$ ) away by identifying Dark Frames.
Dark Frames are taken with $I_{ij}(\lambda)=0~\forall~i,j,\lambda$ with the same integration time. Such that ...
$$L_{ij} = \Bigl[\epsilon_{ij}(\lambda)0 + T_{ij}\Bigr]t + B_{ij}$$
$$L_{ij} = T_{ij}t + B_{ij} = D_{ij}$$
Dark Frames are not wavelength (filter) dependent!

#### Flat Frames
We calibrate for the inter-pixel sensitivity by carefully collecting Flat Frames.
We collect these by providing a uniform illumination across the entire detector array (all $i,j$).
That is ... $I_{ij}(\lambda)=C~\forall~i,j,\lambda$
$$L_{ij}(\lambda) = \Bigl[\epsilon_{ij}(\lambda)C + T_{ij}\Bigr]t + B_{ij}$$
Flat Frames ARE wavelength (filter) dependent!
As such, Flat Frames contain their own Dark Signals that must be calibrated away.

#### Master Frames
Since the Flat Frames and Dark Frames both represent samplings of random distributions of thermal agitations which are Maxwellian-distributed and counting statistics which are Poissonian-distributed, 
a few dozen of each type of calibration frame should be taken. We must find some measure of central tendancy that summarizes the effect for each calibration frame.

The Master Dark Frame should be the pixel-wise median of this few dozen frames.

The Master Flat Frame should be the pixel-wise median of this few dozen frames, with its own Master Dark Frame subtracted. Further, thie Master Flat Frame should be divided by the constant of illumination scaled by the integration time.

The resulting data representing $(I_{ij}(\lambda)t)$ should be the pixel-wise average of each light frame, absent the Master Dark and divided by the constant-scaled Master Flat.

Note that $(I_{ij}(\lambda)t)$ cannot be further separated, the counts have been detected over an integration time, $t$.

## Sky Brightness
The sky brightness should be removed from either the entire image if assumed to be uniform through the FoV OR removed from a subframe over which the sky brightness can be assumed to be uniform.
Use a radial profile fit with a constant offset to identify the background sky brightness as that constant offset.

I.e., use a model function: $M(r;\mu,\sigma,A,G) = A*f(r;\mu,\sigma) + G$ and subtract $G$ from each pixel in the subframe, provided some metric of the model-fit meets some threshold criteria.

## Instrument Magnitude
The instrument magnitude is based on the pixel-wise sum of counts within some aperture of radius $R$. The pixel-wise sum of counts should be divided by the integration time.
$$m_{inst} = -2.5\log{\Biggl[\sum_i\sum_j (I_{ij}t)/t\Biggr]}$$
$$\forall~i,j\|\sqrt{(i-i_c)^2-(j-j_c)^2} < R$$

# How to Run


## Example Run
```bash
tree -d
.
├── analysis
├── calibration
│   ├── bias
│   │   └── 22_16_40
│   ├── darks
│   │   ├── darks_08
│   │   │   └── 22_14_40
│   │   ├── darks_117
│   │   │   └── 21_41_38
│   │   ├── darks_140
│   │   │   └── 21_46_36
│   │   ├── darks_147
│   │   │   └── 21_55_57
│   │   ├── darks_150
│   │   │   └── 22_09_11
│   │   ├── darks_20
│   │   │   └── 22_08_08
│   │   ├── darks_50
│   │   │   └── 22_01_21
│   │   ├── darks_56
│   │   │   └── 22_05_52
│   │   └── darks_63
│   │       └── 22_03_13
│   └── flats
│       ├── flat_b_
│       │   └── 21_09_24
│       ├── flat_i_
│       │   ├── 21_13_47
│       │   └── 21_25_01
│       ├── flat_r_
│       │   └── 21_11_54
│       ├── flat_u_
│       │   └── 21_29_41
│       └── flat_v_
│           └── 21_11_10
├── ngc7790
│   ├── ngc7790_b_011_agon
│   │   └── 19_10_48
│   ├── ngc7790_i_011_agon
│   │   └── 19_25_27
│   ├── ngc7790_r_011_agon
│   │   └── 19_19_07
│   ├── ngc7790_u_011_agon
│   │   └── 19_03_40
│   └── ngc7790_v_011_agon
│       └── 19_15_11
├── pg2213
│   ├── pg2213_b_011_agon
│   │   └── 20_29_42
│   ├── pg2213_i_011_agon
│   │   └── 20_39_29
│   ├── pg2213_r_011_agon
│   │   └── 20_36_15
│   ├── pg2213_u_011_agon
│   │   └── 20_21_37
│   └── pg2213_v_011_agon
│       └── 20_32_41
└── sa20
    ├── sa20_b_011_agon
    │   └── 19_58_55
    ├── sa20_i_011_agon
    │   └── 20_13_16
    ├── sa20_r_011_agon
    │   └── 20_09_15
    ├── sa20_u_011_agon
    │   └── 19_50_38
    └── sa20_v_011_agon
        └── 20_03_44

neutron•livova-laptop ./data-redux
ls                                                                  
analysis/  analysis-ngc/  FrameList.py  Frame.py  main.py  __pycache__/  README.md  redux_functions.py

neutron•livova-laptop ./data-redux
python3 main.py -r 15 -o analysis-ngc -d ../../fits/inst-mag-ngc/ -c calibration -length 50 -S 0 --level DEBUG --force -x U B R I
Finding FITS: 100%|█████████████████████████████████████████████████████████████████████████| 411/411 [00:23<00:00, 17.83it/s]
Calibrating Light Frames: 100%|█████████████████████████████████████████████████████████████████| 1/1 [00:04<00:00,  4.15s/it]
Extracting Sources for Filter V: 100%|████████████████████████████████████████████████████████| 10/10 [00:02<00:00,  4.21it/s]
```


# Requirements
UNSURE. But this is the output of my `pip3 list`. I'll refine this later!
neutron•livova-laptop ./data-redux
pip3 list                                                                                                   
Package         Version
--------------- -------
astropy         5.3.4
contourpy       1.2.0
cycler          0.12.1
DateTime        5.4
fonttools       4.47.2
kiwisolver      1.4.5
matplotlib      3.8.2
mkl-fft         1.3.8
mkl-random      1.2.4
mkl-service     2.4.0
numpy           1.26.3
packaging       23.1
photutils       1.10.0
pillow          10.2.0
pip             23.3.1
pyerfa          2.0.0
pyparsing       3.1.1
python-dateutil 2.8.2
pytz            2023.4
PyYAML          6.0.1
scipy           1.11.4
setuptools      68.2.2
six             1.16.0
tqdm            4.66.1
wheel           0.41.2
zope.interface  6.1
