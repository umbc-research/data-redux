# data-redux
Code base of routines and the entire reduction pipeline for UMBC Observatory equipment

# TO RUN:
python3 data_redux.py -D pg2213 -C calibration -O analysis -R 15 -L 25 -S 0 -x U B R I --save pg2213
-D is data directory
-C is calibration directory
-O is output
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

[proutyr1@/Users/proutyr1/Documents/git/data-redux]
ls
Observation.py README.md      analysis       calibration    data_redux.py  ngc7790        pg2213         redux.py       redux_funcs.py sa20
[proutyr1@/Users/proutyr1/Documents/git/data-redux]

[proutyr1@/Users/proutyr1/Documents/git/data-redux]
python3 data_redux.py -r 15 -o analysis -d pg2213 -c calibration -l 50 -S 0 --level DEBUG --force -x U B R I --no-flat 
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 411/411 [00:04<00:00, 102.25it/s]
Done sorting files

Starting work on new master light frame.
  Working with light filter: V
  Working with light gain: 150
  Working with light integration time: 5
    Got lights: 25x(Type:light, Filter:V, Gain:150, IntTime:5)
    Got darks for lights: 20x(Type:dark, Filter:None, Gain:150, IntTime:5)
[proutyr1@/Users/proutyr1/Documents/git/data-redux]
```


# Requirements
UNSURE. But this is the output of my `pip3 list`. I'll refine this later!
pip3 list
Package                  Version
------------------------ ------------------
aiocron                  1.8
aiohttp                  3.8.4
aiosignal                1.3.1
altair                   5.0.1
altgraph                 0.17.2
anyio                    3.6.2
appnope                  0.1.3
APScheduler              3.10.1
argon2-cffi              21.3.0
argon2-cffi-bindings     21.2.0
arrow                    1.2.3
astroplan                0.9.dev68+g374ebb4
astropy                  5.2.1
astroquery               0.4.6
asttokens                2.2.1
async-timeout            4.0.2
attrs                    22.2.0
backcall                 0.2.0
beautifulsoup4           4.12.2
bleach                   6.0.0
certifi                  2023.5.7
cffi                     1.15.1
charset-normalizer       3.1.0
comm                     0.1.3
configobj                5.0.8
contourpy                1.0.7
coverage                 7.1.0
croniter                 1.3.15
cycler                   0.11.0
debugpy                  1.6.7
decorator                5.1.1
defusedxml               0.7.1
discord.py               2.2.3
exceptiongroup           1.1.0
executing                1.2.0
fastjsonschema           2.16.3
fonttools                4.38.0
fqdn                     1.5.1
frozenlist               1.3.3
future                   0.18.2
h5py                     3.10.0
html5lib                 1.1
hypothesis               6.68.1
idna                     3.4
imageio                  2.25.0
importlib-metadata       6.6.0
iniconfig                2.0.0
ipykernel                6.23.0
ipython                  8.13.2
ipython-genutils         0.2.0
ipywidgets               8.0.6
isoduration              20.11.0
jaraco.classes           3.3.0
jedi                     0.18.2
Jinja2                   3.1.2
joblib                   1.2.0
jsonpointer              2.3
jsonschema               4.17.3
jupyter                  1.0.0
jupyter_client           8.2.0
jupyter-console          6.6.3
jupyter_core             5.3.0
jupyter-events           0.6.3
jupyter_server           2.5.0
jupyter_server_terminals 0.4.4
jupyterlab-pygments      0.2.2
jupyterlab-widgets       3.0.7
keyring                  24.2.0
kiwisolver               1.4.4
ldap3                    2.9.1
macholib                 1.15.2
MarkupSafe               2.1.2
matplotlib               3.6.3
matplotlib-inline        0.1.6
mistune                  2.0.5
more-itertools           10.1.0
multidict                6.0.4
nbclassic                1.0.0
nbclient                 0.7.4
nbconvert                7.4.0
nbformat                 5.8.0
nest-asyncio             1.5.6
notebook                 6.5.4
notebook_shim            0.2.3
numpy                    1.24.1
packaging                23.0
pandas                   2.0.1
pandocfilters            1.5.0
parso                    0.8.3
pexpect                  4.8.0
photutils                1.6.0
pickleshare              0.7.5
Pillow                   9.4.0
pip                      23.2.1
platformdirs             3.5.0
pluggy                   1.0.0
prettytable              3.6.0
prometheus-client        0.16.0
prompt-toolkit           3.0.38
psutil                   5.9.4
ptyprocess               0.7.0
pure-eval                0.2.2
pyasn1                   0.4.8
pycparser                2.21
pyerfa                   2.0.0.1
Pygments                 2.15.1
pyparsing                3.0.9
pyraf                    2.2.1
pyrsistent               0.19.3
pytest                   7.2.1
pytest-arraydiff         0.5.0
pytest-astropy           0.10.0
pytest-astropy-header    0.2.2
pytest-cov               4.0.0
pytest-doctestplus       0.12.1
pytest-filter-subpackage 0.1.2
pytest-mock              3.10.0
pytest-openfiles         0.5.0
pytest-remotedata        0.4.0
python-dateutil          2.8.2
python-dotenv            1.0.0
python-json-logger       2.0.7
pytz                     2022.7.1
pyvo                     1.4.2
PyYAML                   6.0
pyzmq                    25.0.2
qtconsole                5.4.3
QtPy                     2.3.1
requests                 2.31.0
rfc3339-validator        0.1.4
rfc3986-validator        0.1.1
scikit-learn             1.2.2
scipy                    1.10.0
seaborn                  0.12.2
Send2Trash               1.8.2
setuptools               58.0.4
six                      1.15.0
sklearn                  0.0.post4
sniffio                  1.3.0
sortedcontainers         2.4.0
soupsieve                2.4.1
stack-data               0.6.2
tabulate                 0.9.0
terminado                0.17.1
threadpoolctl            3.1.0
tinycss2                 1.2.1
tomli                    2.0.1
tomorrow-io              0.0.3
toolz                    0.12.0
tornado                  6.3.1
traitlets                5.9.0
typing_extensions        4.5.0
tzdata                   2023.3
tzlocal                  5.0.1
uri-template             1.2.0
urllib3                  1.26.16
wcwidth                  0.2.6
webcolors                1.13
webencodings             0.5.1
websocket-client         1.5.1
wheel                    0.37.0
widgetsnbextension       4.0.7
xmltodict                0.13.0
yarl                     1.9.2
zipp                     3.15.0