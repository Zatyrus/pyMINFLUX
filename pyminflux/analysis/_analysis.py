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
#

import math
from typing import Optional

import numpy as np
from scipy import ndimage, signal, stats
from scipy.fftpack import fft2, ifftshift
from scipy.ndimage import median_filter
from scipy.signal import find_peaks, savgol_filter


def hist_bins(values: np.ndarray, bin_size: float) -> tuple:
    """Return the bins to be used for the passed values and bin size.

    Parameters
    ----------

    values: np.ndarray
        One-dimensional array of values for which to determine the ideal histogram bins.

    bin_size: float
        Bin size to use.

    Returns
    -------

    bin_edges: np.ndarray
        Array of bin edges (to use with np.histogram()).

    bin_centers: np.ndarray
        Array of bin centers.

    bin_width:
        Bin width.
    """

    if len(values) == 0:
        raise ValueError("No data.")

    # Find an appropriate min value that keeps the bins nicely centered
    min_value = bin_size * int(np.min(values) / bin_size)

    # Max value
    max_value = np.max(values)

    # Pathological case where bin_width is 0.0
    if bin_size <= 0.0:
        raise ValueError("`bin_size` must be a positive number!")

    # Calculate number of bins
    num_bins = math.floor((max_value - min_value) / bin_size) + 1

    # Center the first bin around the min value
    half_width = bin_size / 2
    bin_edges = np.arange(
        min_value - half_width, min_value + num_bins * bin_size, bin_size
    )
    bin_centers = (bin_edges[0:-1] + bin_edges[1:]) / 2

    return bin_edges, bin_centers, bin_size


def ideal_hist_bins(values: np.ndarray, scott: bool = False):
    """Calculate the ideal histogram bins using the Freedman-Diaconis rule.

    See: https://en.wikipedia.org/wiki/Freedman%E2%80%93Diaconis_rule

    Parameters
    ----------

    values: np.ndarray
        One-dimensional array of values for which to determine the ideal histogram bins.

    scott: bool
        Whether to use Scott's normal reference rule (if the data is normally distributed).

    Returns
    -------

    bin_edges: np.ndarray
        Array of bin edges (to use with np.histogram()).

    bin_centers: np.ndarray
        Array of bin centers.

    bin_size:
        Bin width.
    """

    if len(values) == 0:
        raise ValueError("No data.")

    # Pathological case, all values are the same
    if np.all(np.diff(values) == 0):
        bin_edges = (values[0] - 5e-7, values[0] + 5e-7)
        bin_centers = (values[0],)
        bin_size = 1e-6
        return bin_edges, bin_centers, bin_size

    # Calculate bin width
    factor = 2.0
    if scott:
        factor = 2.59
    iqr = stats.iqr(values, rng=(25, 75), scale=1.0, nan_policy="omit")
    num_values = np.sum(np.logical_not(np.isnan(values)))
    crn = np.power(num_values, 1 / 3)
    bin_size = (factor * iqr) / crn

    # Get min and max values
    min_value = np.min(values)
    max_value = np.max(values)

    # Pathological case where bin_size is 0.0
    if bin_size == 0.0:
        bin_size = 0.5 * (min_value + max_value)

    # Calculate number of bins
    num_bins = math.floor((max_value - min_value) / bin_size) + 1

    # Center the first bin around the min value
    half_width = bin_size / 2
    bin_edges = np.arange(
        min_value - half_width, min_value + num_bins * bin_size, bin_size
    )
    bin_centers = (bin_edges[0:-1] + bin_edges[1:]) / 2
    if len(bin_edges) >= 2:
        bin_size = bin_edges[1] - bin_edges[0]

    return bin_edges, bin_centers, bin_size


def get_robust_threshold(values: np.ndarray, factor: float = 2.0):
    """Calculate a robust threshold for the array of values.

    The threshold is defines as median + thresh * median absolute deviation.

    The median absolute deviation is divided by 0.67449 to bring it in the
    same scale as the (non-robust) standard deviation.

    Parameters
    ----------

    values: np.ndarray
        Array of values. It may contain NaNs.

    factor: float
        Factor by which to multiply the median absolute deviation.

    Returns
    -------

    upper_threshold: float
        Upper threshold.

    lower_threshold: float
        Lower threshold.

    med: float
        Median of the array of values.

    mad: float
        Scaled median absolute deviation of the array of values.
    """

    # Remove NaNs
    work_values = values.copy()
    work_values = work_values[np.logical_not(np.isnan(work_values))]
    if len(work_values) == 0:
        return None, None, None, None

    # Calculate robust statistics and threshold
    med = np.median(work_values)
    mad = stats.median_abs_deviation(work_values, scale=0.67449)
    step = factor * mad
    upper_threshold = med + step
    lower_threshold = med - step

    return upper_threshold, lower_threshold, med, mad


def prepare_histogram(
    values: np.ndarray,
    normalize: bool = True,
    auto_bins: bool = True,
    scott: bool = False,
    bin_size: float = 0.0,
):
    """Return histogram counts and bins for given values with provided or automatically calculated bin number.

    Parameters
    ----------

    values: np.ndarray
        Array of values. It may contain NaNs.

    normalize: bool
        Whether to normalize the histogram to a probability mass function (PMF). The integral of the PMF is 1.0.

    auto_bins: bool
        Whether to automatically calculate the bin size from the data.

    scott: bool
        Whether to use Scott's normal reference rule (the data should be normally distributed). This is used only
        if `auto_bins` is True.

    bin_size: float
        Bin size to use if `auto_bins` is False. It will be ignored if `auto_bins` is True.

    Returns
    -------

    n: np.ndarray
        Histogram counts (optionally normalized to sum to 1.0).

    bin_edges: np.ndarray
        Array of bin edges (to use with np.histogram()).

    bin_centers: np.ndarray
        Array of bin centers.

    bin_width:
        Bin width.

    """
    if auto_bins:
        bin_edges, bin_centers, bin_width = ideal_hist_bins(values, scott=scott)
    else:
        if bin_size == 0.0:
            raise Exception(
                f"Please provide a valid value for `bin_size` if `auto_bins` is False."
            )
        bin_edges, bin_centers, bin_width = hist_bins(values, bin_size=bin_size)

    n, _ = np.histogram(values, bins=bin_edges, density=False)
    if normalize:
        n = n / n.sum()
    return n, bin_edges, bin_centers, bin_width


def find_first_peak_bounds(
    counts: np.ndarray,
    bins: np.ndarray,
    min_rel_prominence: float = 0.01,
    med_filter_support: int = 5,
):
    """Finds the first peak in the histogram and return the lower and upper bounds.

    Parameters
    ----------

    counts: np.ndarray
        Array of histogram counts.

    bins: np.ndarray
        Array of histogram bins.

    min_rel_prominence: float
        Minimum relative prominences (relative to range of filtered counts) for peaks to be considered valid.

    med_filter_support: int
        Support for the median filter to suppress some spurious noisy peaks in the counts.

    Returns
    -------

    lower_bound: float
        Lower bound of the first peak.

    upper_bound: float
        Upper bound of the first peak.
    """

    # Filter the signal
    x = median_filter(counts, footprint=np.ones(med_filter_support))

    # Absolute minimum prominence
    min_prominence = min_rel_prominence * (x.max() - x.min())

    # Find maxima
    peaks, properties = find_peaks(x, prominence=(min_prominence, None))

    # Find minima
    x_inv = x.max() - x
    peaks_inv, properties_inv = find_peaks(x_inv, prominence=(min_prominence, None))

    # If we did not find any local maxima, we return failure
    if len(peaks) == 0:
        return None, None

    # First peak position
    first_peak = peaks[0]

    # If we do not have any local minima, we return the beginning and end of the bins range
    if len(peaks_inv) == 0:
        return bins[0], bins[-1]

    # Do we have a minimum on the left of the first peak?
    candidates_left = peaks_inv[peaks_inv < first_peak]
    if len(candidates_left) == 0:
        lower_bound = bins[0]
    else:
        lower_bound = bins[candidates_left[-1]]

    # Do we have a minimum on the right of the first peak?
    candidates_right = peaks_inv[peaks_inv > first_peak]
    if len(candidates_right) == 0:
        upper_bound = bins[-1]
    else:
        upper_bound = bins[candidates_right[0]]

    return lower_bound, upper_bound


def find_cutoff_near_value(
    counts: np.ndarray,
    bins: np.ndarray,
    expected_value: float,
):
    """Finds the first peak in the histogram and return the lower and upper bounds.

    Parameters
    ----------

    counts: np.ndarray
        Array of histogram counts.

    bins: np.ndarray
        Array of histogram bins.

    expected_value: float
        The cutoff is expected to be close to the expected value.

    Returns
    -------

    cutoff: float
        Estiated cutoff frequency.
    """

    # Absolute minimum prominence
    min_prominence = 0.05 * (counts.max() - counts.min())

    # Find minima
    counts_inv = counts.max() - counts
    peaks_inv, properties_inv = find_peaks(
        counts_inv, prominence=(min_prominence, None)
    )

    # Which is the local minimum closest to the expected value
    cutoff_pos = peaks_inv[np.argmin(np.abs(bins[peaks_inv] - expected_value))]

    # Extract the corresponding frequency
    cutoff = bins[cutoff_pos]

    # Return the obtained cutoff frequency
    return cutoff


def calculate_density_map(
    x: np.ndarray,
    y: np.ndarray,
    x_bin_edges: Optional[np.ndarray] = None,
    y_bin_edges: Optional[np.ndarray] = None,
    auto_bins: bool = True,
    scott: bool = False,
    bin_size: Optional[float] = None,
) -> np.ndarray:
    """Create density map for 2D data.

    Parameters
    ----------

    x: np.ndarray
        1D array of X values.

    y: np.ndarray
        1D array of Y values.

    x_bin_edges: np.ndarray
        1D array of bin edge values for the X array. If omitted, it will be calculated automatically
        (see `pyminflux.analysis.prepare_histogram`.)

    y_bin_edges: np.ndarray
        1D array of bin edge values for the X array. If omitted, it will be calculated automatically
        (see `pyminflux.analysis.prepare_histogram`.)

    auto_bins: bool
        Whether to automatically calculate the bin size from the data. Only used if either `x_bin_edges`
        or `y_bin_edges` are None.

    scott: bool
        Whether to use Scott's normal reference rule (the data should be normally distributed).
        This is only used if either `x_bin_edges` or `y_bin_edges` are None and `auto_bins` is True.

    bin_size: float
        Bin size to use if either `x_bin_edges` or `y_bin_edges` are None and `auto_bins` is False.
        It will be ignored if `auto_bins` is True.

    Returns
    -------

    density: np.ndarray
        2D density maps.
    """

    # Calculate bin edges if needed
    if x_bin_edges is None:
        _, x_bin_edges, _, _ = prepare_histogram(
            x, auto_bins=auto_bins, scott=scott, bin_size=bin_size
        )

    if y_bin_edges is None:
        _, y_bin_edges, _, _ = prepare_histogram(
            y, auto_bins=auto_bins, scott=scott, bin_size=bin_size
        )

    # Create density map
    xx, yy = np.meshgrid(x_bin_edges, y_bin_edges)
    positions = np.vstack([xx.ravel(), yy.ravel()])
    values = np.vstack([x, y])
    kernel = stats.gaussian_kde(values)
    density = np.reshape(kernel(positions).T, xx.shape)

    # Return density map
    return density


def calculate_2d_histogram(
    x: np.ndarray,
    y: np.ndarray,
    x_bin_edges: Optional[np.ndarray] = None,
    y_bin_edges: Optional[np.ndarray] = None,
    x_auto_bins: bool = True,
    y_auto_bins: bool = True,
    scott: bool = False,
    x_bin_size: float = 0.0,
    y_bin_size: float = 0.0,
) -> np.ndarray:
    """Create density map for 2D data.

    Parameters
    ----------

    x: np.ndarray
        1D array of X values.

    y: np.ndarray
        1D array of Y values.

    x_bin_edges: np.ndarray
        1D array of bin edge values for the X array. If omitted, it will be calculated automatically
        (see `pyminflux.analysis.prepare_histogram`.)

    y_bin_edges: np.ndarray
        1D array of bin edge values for the X array. If omitted, it will be calculated automatically
        (see `pyminflux.analysis.prepare_histogram`.)

    x_auto_bins: bool
        Whether to automatically calculate the bin size for `x` from the data. Only used if `x_bin_edges`
        is None.

    y_auto_bins: bool
        Whether to automatically calculate the bin size for `y` from the data. Only used if `y_bin_edges`
        is None.

    scott: bool
        Whether to use Scott's normal reference rule (the data should be normally distributed).
        This is only used if either `x_bin_edges` or `y_bin_edges` are None and `auto_bins` is True.

    x_bin_size: float
        Bin size to use for `x` if `x_bin_edges` is None and `x_auto_bins` is False.
        It will be ignored if `x_auto_bins` is True.

    y_bin_size: float
        Bin size to use for `y` if `y_bin_edges` is None and `y_auto_bins` is False.
        It will be ignored if `y_auto_bins` is True.

    Returns
    -------

    density: np.ndarray
        2D density maps.
    """

    # Calculate bin edges if needed
    if x_bin_edges is None:
        _, x_bin_edges, _, _ = prepare_histogram(
            x, auto_bins=x_auto_bins, scott=scott, bin_size=x_bin_size
        )

    if y_bin_edges is None:
        _, y_bin_edges, _, _ = prepare_histogram(
            y, auto_bins=y_auto_bins, scott=scott, bin_size=y_bin_size
        )

    # Create 2D histogram
    histogram = np.histogram2d(y, x, bins=(y_bin_edges, x_bin_edges))

    # Return histogram
    return histogram[0]


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


def render_xy(
    x,
    y,
    sx: float = 1.0,
    sy: float = 1.0,
    rx: Optional[tuple] = None,
    ry: Optional[tuple] = None,
    render_type: Optional[str] = "histogram",
    fwhm: Optional[float] = None,
):
    """Renders the localizations as a 2D image with given resolution.

    Reimplemented (with modifications) from:

    * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    * [code]  https://zenodo.org/record/6563100

    Parameters
    ----------

    x: np.ndarray
        Array of localization x coordinates.

    y: np.ndarray
        Array of localization y coordinates.

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

    Returns
    -------

    h: rendered image (as float32 2D NumPy array)
    xi: array of x coordinates of the output x, y grid
    yi: array of x coordinates of the output x, y grid
    m: logical array with the positions that were considered. The False entries were rejected because they were
       outside the rx, ry ranges (with the additional constraint of the edge effect of the Gaussian support for
    the "fixed_gaussian" render type.
    """

    if render_type is None:
        render_type = "histogram"

    render_type = render_type.lower()
    if render_type not in ["histogram", "fixed_gaussian"]:
        raise ValueError("plot_type must be one of 'histogram' or 'fixed_gaussian'.'")

    if render_type == "fixed_gaussian" and fwhm is None:
        sxy = np.sqrt(np.power(sx, 2) + np.power(sy, 2))
        fwhm = 3 * sxy

    # Make sure we are working with NumPy arrays
    x = np.array(x)
    y = np.array(y)

    # Make sure rx and ry are defined
    if rx is None:
        rx = (x.min(), x.max())
    if ry is None:
        ry = (y.min(), y.max())

    # Get dimensions and allocate output array
    Nx = int(np.ceil((rx[1] - rx[0]) / sx))
    Ny = int(np.ceil((ry[1] - ry[0]) / sy))
    h = np.zeros((Ny, Nx), dtype=np.float32)

    # Get position in pixels
    px = (x - rx[0]) / sx
    py = (y - ry[0]) / sy

    # Convert absolute position to image indices
    ix = np.round(px).astype(int)
    iy = np.round(py).astype(int)

    # Remove positions outside the image
    m = (ix >= 0) & (ix < Nx) & (iy >= 0) & (iy < Ny)
    px = px[m]
    py = py[m]
    ix = ix[m]
    iy = iy[m]

    # Plot requested image type
    if render_type == "histogram":
        # Fill in histogram
        for i in range(len(ix)):
            xi = ix[i]
            yi = Ny - iy[i] - 1  # Images have y = 0 at the top
            try:
                h[yi, xi] += 1
            except IndexError as e:
                print(
                    f"Tried to access (y={yi}, x={xi}) in image of size (Ny={Ny}, Nx={Nx})."
                )

    elif render_type == "fixed_gaussian":
        # Gaussian with subpixel accuracy
        wx = fwhm / sx
        wy = fwhm / sy
        L = int(np.ceil(2 * max(wx, wy)))

        # Small grid
        g = np.arange(-L, L + 1)
        xk, yk = np.meshgrid(g, g)

        # Remove close to borders
        m = (ix >= L + 1) & (ix < Nx - L - 1) & (iy > L + 1) & (iy < Ny - L - 1)
        px = px[m]
        py = py[m]
        ix = ix[m]
        iy = iy[m]

        for i in range(len(ix)):
            xi = ix[i]
            yi = iy[i]
            dx = px[i] - xi
            dy = py[i] - yi
            gx = xi + g
            gy = yi + g

            # Calculate the Gaussian kernel using the requested FWHM.
            k = np.exp(
                -4 * np.log(2) * ((xk - dx) ** 2 / wx**2 + (yk - dy) ** 2 / wy**2)
            )

            # Add it to the image
            my, mx = np.meshgrid(
                gy, gx, indexing="ij"
            )  # We need to create meshgrid to add the k matrix
            my = Ny - my - 1  # Images have y = 0 at the top
            try:
                h[my, mx] = h[my, mx] + k
            except IndexError as e:
                print(
                    f"Tried to access (y={yi}, x={xi}) in image of size (Ny={Ny}, Nx={Nx})."
                )

    else:
        raise ValueError("Unknown type")

    # Define output xy grid
    xi = rx[0] + (np.arange(Nx)) * sx + sx / 2
    yi = ry[0] + (np.arange(Ny)) * sy + sy / 2

    return h, xi, yi, m


def img_fourier_grid(dims, type_name="float64"):
    """
    This grid has center of mass at (0, 0): if used to perform convolution via fft2, it will not produce any shift!
    """

    number_dimensions = len(dims)

    if number_dimensions == 1:
        gx = np.arange(1, dims[0] + 1).astype(type_name)
        xi = np.fft.ifftshift(gx)
        xi = xi - xi[0]
        return xi

    elif number_dimensions == 2:
        gx = np.arange(1, dims[0] + 1).astype(type_name)
        gy = np.arange(1, dims[1] + 1).astype(type_name)
        xi, yi = np.meshgrid(gx, gy, indexing="ij")
        xi = np.fft.ifftshift(xi)
        xi = xi - xi[0, 0]
        yi = np.fft.ifftshift(yi)
        yi = yi - yi[0, 0]
        return xi, yi

    elif number_dimensions == 3:
        gx = np.arange(1, dims[0] + 1).astype(type_name)
        gy = np.arange(1, dims[1] + 1).astype(type_name)
        gz = np.arange(1, dims[2] + 1).astype(type_name)
        xi, yi, zi = np.meshgrid(gx, gy, gz, indexing="ij")
        xi = np.fft.ifftshift(xi)
        xi = xi - xi[0, 0, 0]
        yi = np.fft.ifftshift(yi)
        yi = yi - yi[0, 0, 0]
        zi = np.fft.ifftshift(zi)
        zi = zi - zi[0, 0, 0]
        return xi, yi, zi

    else:
        raise ValueError("Unsupported dimensionality!")


def img_fourier_ring_correlation(
    image1, image2, sx: float = 1.0, sy: float = 1.0, frc_smoothing_kernel=None
):
    """Perform Fourier ring correlation analysis on two images.

        Reimplemented (with modifications) from:

    * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    * [code]  https://zenodo.org/record/6563100

    Parameters
    ----------

    image1: np.ndarray
        First image, possibly generated by `pyminflux.analysis.render_xy()`.

    image2: np.ndarray
        Second image, possibly generated by `pyminflux.analysis.render_xy()`.

    physical_image_size: tuple (sy, sz)
        Physical size of the image.

    sx: float (Default = 1.0 nm)
        Resolution in nm of the rendered image in the x direction.

    sy: float (Default = 1.0 nm)
        Resolution in nm of the rendered image in the y direction.

    render_type: np.ndarray (Optional)
        2D kernel for low-pass filtering the FRC. If omitted, a 31x31 Gaussian kernel with sigma = 1.0 will be used.

    Returns
    -------

    estimated_resolution: estimated image resolution in nm.
    fc: @TODO Add description
    qi: @TODO Add description
    ci: @TODO Add description
    """

    if frc_smoothing_kernel is None:
        frc_smoothing_kernel = np.outer(
            signal.gaussian(31, std=1), signal.gaussian(31, std=1)
        )

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
    a_sm = signal.fftconvolve(ifftshift(a), frc_smoothing_kernel, mode="same")
    b_sm = signal.fftconvolve(ifftshift(b), frc_smoothing_kernel, mode="same")
    c_sm = signal.fftconvolve(ifftshift(c), frc_smoothing_kernel, mode="same")
    fc = a_sm / np.sqrt(b_sm * c_sm)
    fc = np.real(fc)

    # Calculate frequency space grid
    qx, qy = img_fourier_grid(image1.shape)
    qx = qx / physical_image_size[0]
    qy = qy / physical_image_size[1]
    q = np.sqrt(qx**2 + qy**2)

    # Calculate bin a, b, c in dependence of q
    B = 5e5  # bin size (in pixel in fourier space)  # @TODO must be adapted to physical stack size (this is in m)!!
    qi = np.round(q / B).astype(int)
    idx = qi.flatten()  # + 1
    qi = np.arange(0, np.max(qi) + 1) * B
    aj_real = np.bincount(idx, weights=a.flatten().real)
    aj_imag = np.bincount(idx, weights=a.flatten().imag)
    aj = aj_real + 1j * aj_imag
    bj_real = np.bincount(idx, weights=b.flatten().real)
    bj_imag = np.bincount(idx, weights=b.flatten().imag)
    bj = bj_real + 1j * bj_imag
    cj_real = np.bincount(idx, weights=c.flatten().real)
    cj_imag = np.bincount(idx, weights=c.flatten().imag)
    cj = cj_real + 1j * cj_imag
    ci = np.real(aj / np.sqrt(bj * cj))
    idx = qi < np.max(qi) * 0.8  # cut a bit
    qi = qi[idx]
    ci = ci[idx]

    # Additional smoothing
    ci = savgol_filter(ci, 7, 1)

    # @TODO Make this an option:
    # ci = ndimage.convolve(ci, np.array([1, 1, 1]) / 3, mode='nearest')

    # Determine image resolution
    q_critical = qi[np.where(ci < 1 / 7)[0][0]] if np.any(ci < 1 / 7) else qi[-1]
    estimated_resolution = 1 / q_critical

    return estimated_resolution, fc, qi, ci
