#  Copyright (c) 2022 - 2023 D-BSSE, ETH Zurich.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#   limitations under the License.
from typing import Optional

import numpy as np
from numpy.fft import ifftshift
from scipy import signal
from scipy.fft import fft2
from scipy.signal import savgol_filter

from pyminflux.render import render_xy


def img_fourier_grid(dims, dtype=float):
    """This grid has center of mass at (0, 0): if used to perform convolution via fft2, it will not produce any shift!

    Reimplemented (with modifications) from:

    * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    * [code]  https://zenodo.org/record/6563100

    Parameters
    ----------

    dims: tuple
        Size in each dimension.
        For 1D, dims = [nx]
        For 2D, dims = [nx, ny]
        For 3D, dims = [nx, ny, nz]

    dtype: np.dtype (Optional, default float = np.float64)
        Data type of the grid.

    Returns
    -------

    x: np.ndarray
        Linear grid of coordinates if ndims == 1.
        2D mesh grid of coordinates if ndims == 2.
        3D mesh grid of coordinates if ndims == 3.

    y: np.ndarray
        2D mesh grid of coordinates if ndims == 2.
        3D mesh grid of coordinates if ndims == 3.

    z: np.ndarray
        3D mesh grid of coordinates if ndims == 3.
    """

    number_dimensions = len(dims)

    if number_dimensions == 1:
        gx = np.arange(1, dims[0] + 1).astype(dtype)
        xi = ifftshift(gx)
        xi = xi - xi[0]
        return xi

    elif number_dimensions == 2:
        gx = np.arange(1, dims[0] + 1).astype(dtype)
        gy = np.arange(1, dims[1] + 1).astype(dtype)
        xi, yi = np.meshgrid(gx, gy, indexing="ij")
        xi = ifftshift(xi)
        xi = xi - xi[0, 0]
        yi = ifftshift(yi)
        yi = yi - yi[0, 0]
        return xi, yi

    elif number_dimensions == 3:
        gx = np.arange(1, dims[0] + 1).astype(dtype)
        gy = np.arange(1, dims[1] + 1).astype(dtype)
        gz = np.arange(1, dims[2] + 1).astype(dtype)
        xi, yi, zi = np.meshgrid(gx, gy, gz, indexing="ij")
        xi = ifftshift(xi)
        xi = xi - xi[0, 0, 0]
        yi = ifftshift(yi)
        yi = yi - yi[0, 0, 0]
        zi = ifftshift(zi)
        zi = zi - zi[0, 0, 0]
        return xi, yi, zi

    else:
        raise ValueError("Unsupported dimensionality!")


def img_fourier_ring_correlation(
    image1,
    image2,
    sx: float = 1.0,
    sy: float = 1.0,
    kernel: Optional[np.ndarray] = None,
    frc_bin_size: int = 11,
):
    """Perform Fourier ring correlation analysis on two images and returns the estimated resolution in m.

    Reimplemented (with modifications) from:

    * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    * [code]  https://zenodo.org/record/6563100

    Parameters
    ----------

    image1: np.ndarray
        First image, possibly generated by `pyminflux.render.render_xy()`.

    image2: np.ndarray
        Second image, possibly generated by `pyminflux.render.render_xy()`.

    sx: float (Default = 1.0 nm)
        Resolution in x direction (in nm) of the rendered image to be used for calculating FRC.

    sy: float (Default = 1.0 nm)
        Resolution in x direction (in nm) of the rendered image to be used for calculating FRC.

    kernel: np.ndarray (Optional)
        2D kernel for low-pass filtering the FRC. If omitted, a 31x31 Gaussian kernel with sigma = 1.0 will be used.

    frc_bin_size: int (Default = 11)
        Step size used to bin the frequencies of the Fourier Ring Correlation.

    Returns
    -------

    estimated_resolution: float
        Estimated image resolution in m.

    fc: np.ndarray
        Fourier Ring Correlation of `image1` and `image2`.

    qi: np.ndarray
        Array of frequencies.

    ci: np.ndarray
        Array of Fourier Ring Correlations (corresponding to the frequencies in qi)
    """

    def bin_data(qi, data):
        """Perform binning operation."""
        real = np.bincount(qi, weights=data.flatten().real)
        imag = np.bincount(qi, weights=data.flatten().imag)
        return real + 1j * imag

    if kernel is None:
        kernel = np.outer(signal.gaussian(31, std=1), signal.gaussian(31, std=1))

    # Physical size of the image (in meters!)
    physical_image_size = (image1.shape[0] * sy * 1e-9, image1.shape[1] * sx * 1e-9)

    # Calculate Fourier transforms
    f1 = fft2(image1)
    f2 = fft2(image2)

    # Calculate derived quantities for correlation
    a = f1 * np.conj(f2)
    b = f1 * np.conj(f1)
    c = f2 * np.conj(f2)

    # 2D image representation (first smooth, then real/absolute value)
    a_sm = signal.fftconvolve(ifftshift(a), kernel, mode="same")
    b_sm = signal.fftconvolve(ifftshift(b), kernel, mode="same")
    c_sm = signal.fftconvolve(ifftshift(c), kernel, mode="same")
    fc = a_sm / np.sqrt(b_sm * c_sm)
    fc = np.real(fc)

    # Calculate frequency space grid
    qx, qy = img_fourier_grid(image1.shape)
    qx = qx / physical_image_size[0]
    qy = qy / physical_image_size[1]
    q = np.sqrt(qx**2 + qy**2)

    # Calculate bin a, b, c in dependence of q and frc_bin_size
    dq_x = q[0][1] - q[0][0]
    dq_y = q[0][1] - q[0][0]
    B = np.min((dq_x, dq_y)) / frc_bin_size  # bin size (in pixel in fourier space)
    qi = np.round(q / B).astype(int)
    idx = qi.flatten()
    qi = np.arange(0, np.max(qi) + 1) * B
    aj = bin_data(idx, a)
    bj = bin_data(idx, b)
    cj = bin_data(idx, c)
    ci = np.real(aj / np.sqrt(bj * cj))
    idx = qi < np.max(qi) * 0.8  # cut a bit
    qi = qi[idx]
    ci = ci[idx]

    # Additional smoothing
    ci = savgol_filter(ci, 7, 1)

    # Determine image resolution (in m)
    q_critical = qi[np.where(ci < 1 / 7)[0][0]] if np.any(ci < 1 / 7) else qi[-1]
    estimated_resolution = 1 / q_critical

    return estimated_resolution, fc, qi, ci


def estimate_resolution_by_frc(
    x: np.ndarray,
    y: np.ndarray,
    num_reps: int = 5,
    sx: float = 1.0,
    sy: float = 1.0,
    rx: Optional[tuple] = None,
    ry: Optional[tuple] = None,
    render_type: str = "histogram",
    fwhm: Optional[float] = None,
    frc_bin_size: int = 11,
    seed: Optional[int] = None,
    return_all: bool = False,
):
    """Estimates signal resolution by averaging the results of Fourier Ring Correlation the required number of times.

    Parameters
    ----------

    x: np.ndarray
        Array of localization x coordinates.

    y: np.ndarray
        Array of localization y coordinates.

    num_reps: int (Default = 5)
        Number of time Fourier Ring Correlation analysis is run. The returned result will be  the average of the runs.

    sx: float (Default = 1.0)
        Resolution of the render in the x direction.

    sy: float (Default = 1.0)
        Resolution of the render in the y direction.

    rx: tuple (Optional)
        (min, max) boundaries for the x coordinates. If omitted, it will default to (x.min(), x.max()).

    ry: float (Optional)
        (min, max) boundaries for the y coordinates. If omitted, it will default to (y.min(), y.max()).

    render_type: str (Default = "histogram")
        Type of render to be generated. It must be one of:
            "histogram": simple 2D histogram of localization falling into each bin of size (sx, sy).
            "fixed_gaussian": sub-pixel resolution Gaussian fit. The Gaussian full-width half maximum is required
            (see below).

    fwhm: float (Optional)
        Requested full-width half maximum (FWHM) of the Gaussian kernel. If omitted, it is set to be
        3 * np.sqrt(np.power(sx, 2) + np.power(sy, 2)).

    frc_bin_size: int (Default = 11)
        Step size used to bin the frequencies of the Fourier Ring Correlation.

    seed: Optional[int]
        Seed for the random number generator if comparable runs are needed.

    return_all: bool (Default = False)
        Set to True to return all measurements along with their averages.

    Returns
    -------

    resolution: float
        Estimated resolution in nm (average over `num_reps`).

    qi: np.ndarray
        Array of frequencies.

    ci: np.ndarray
        Array of Fourier Ring Correlations (corresponding to the frequencies in qi)

    resolutions: np.ndarray (num_reps, )
        Each of the estimated `n_reps` resolutions. Only returned if `return_all` is True.

    cis: np.ndarray (:, n_reps)
        Array of Fourier Ring Correlations (corresponding to the frequencies in qi) for each of the `n_reps` runs.
        Only returned if `return_all` is True.
    """

    if seed is not None:
        # Initialize the random number generator
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    # Make sure we are working with NumPy arrays
    x = np.array(x)
    y = np.array(y)

    # Make sure to have the same ranges rx and ry bot both images
    if rx is None or ry is None:
        rx = (x.min(), x.max())
        ry = (y.min(), y.max())

    resolutions = np.zeros(num_reps)
    cis = None
    qi = None
    for r in range(num_reps):
        # Partition the data
        ix = rng.random(size=x.shape) < 0.5
        c_ix = np.logical_not(ix)

        # Create two images from (complementary) subsets of coordinates (x, y)
        h1 = render_xy(
            x[ix], y[ix], sx=sx, sy=sy, rx=rx, ry=ry, render_type=render_type, fwhm=fwhm
        )[0]
        h2 = render_xy(
            x[c_ix],
            y[c_ix],
            sx=sx,
            sy=sy,
            rx=rx,
            ry=ry,
            render_type=render_type,
            fwhm=fwhm,
        )[0]

        # Estimate the resolution using Fourier Ring Correlation
        estimated_resolution, fc, qi, ci = img_fourier_ring_correlation(
            h1, h2, sx=sx, sy=sy, frc_bin_size=frc_bin_size
        )

        # Store the estimated resolution, qis and cis
        resolutions[r] = estimated_resolution
        if cis is None:
            cis = np.zeros((len(ci), num_reps), dtype=float)
        cis[:, r] = ci

    # Now calculate average values
    resolution = np.mean(resolutions)
    ci = np.mean(cis, axis=1)

    # Return
    if return_all:
        return resolution, qi, ci, resolutions, cis
    else:
        return resolution, qi, ci


def get_localization_boundaries(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    alpha: float = 0.01,
    min_range: float = 200.0,
):
    """Return x, y, and z localization boundaries for analysis.

    Reimplemented (with modifications) from:

    * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    * [code]  https://zenodo.org/record/6563100


    Parameters
    ----------

    x: np.ndarray
        Array of localization x coordinates.

    y: np.ndarray
        Array of localization y coordinates.

    z: np.ndarray
        Array of localization z coordinates.

    alpha: float (default = 0.01)
        Quantile to remove outliers. Must be 0.0 <= alpha <= 0.5.

    min_range: float (default = 200.0)
        Absolute minimum range in nm.

    Returns
    -------

    rx: tuple
        (min, max) boundaries for the x coordinates.

    ry: float
        (min, max) boundaries for the y coordinates.

    rz: float
        (min, max) boundaries for the z coordinates.
    """

    if alpha < 0 or alpha >= 0.5:
        raise ValueError("alpha must be 0 < alpha < 0.5.")

    # Make sure we are working with NumPy arrays
    x = np.array(x)
    y = np.array(y)
    z = np.array(z)

    # Get boundaries at the given alpha level
    rx = np.quantile(x, (alpha, 1 - alpha))
    ry = np.quantile(y, (alpha, 1 - alpha))
    rz = np.quantile(z, (alpha, 1 - alpha))

    # Minimal boundaries in case of drift correction
    d_rx = float(np.diff(rx)[0])
    if d_rx < min_range:
        rx = rx + (min_range - d_rx) / 2 * np.array([-1, 1])

    d_ry = float(np.diff(ry)[0])
    if d_ry < min_range:
        ry = ry + (min_range - d_ry) / 2 * np.array([-1, 1])

    d_rz = float(np.diff(rz)[0])
    if min_range > d_rz > 1e-6:  # Only in the 3D case
        rz = rz + (min_range - d_rz) / 2 * np.array([-1, 1])

    return rx, ry, rz
