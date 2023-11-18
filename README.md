# data-redux
Code base of routines and the entire reduction pipeline for UMBC Observatory equipment

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
