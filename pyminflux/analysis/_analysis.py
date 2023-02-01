from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from scipy.ndimage import median_filter
from scipy.signal import find_peaks
from scipy.spatial.distance import cdist
from sklearn.mixture import BayesianGaussianMixture, GaussianMixture


def ideal_hist_bins(values, scott=False):
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

    bin_width:
        Bin width.
    """

    if len(values) == 0:
        raise ValueError("No data.")

    # Pathological case, all values are the same
    if np.all(np.diff(values) == 0):
        bin_edges = (values[0] - 5e-7, values[0] + 5e-7)
        bin_centers = (values[0],)
        bin_width = 1e-6
        return bin_edges, bin_centers, bin_width

    # Calculate bin width
    factor = 2.0
    if scott:
        factor = 2.59
    iqr = stats.iqr(values, rng=(25, 75), scale=1.0, nan_policy="omit")
    num_values = np.sum(np.logical_not(np.isnan(values)))
    crn = np.power(num_values, 1 / 3)
    bin_width = (factor * iqr) / crn

    # Get min and max values
    min_value = np.min(values)
    max_value = np.max(values)

    # Pathological case where bin_width is 0.0
    if bin_width == 0.0:
        bin_width = 0.5 * (min_value + max_value)

    # Calculate number of bins
    num_bins = int(np.round((max_value - min_value) / bin_width))

    half_width = bin_width / 2

    bin_edges = np.linspace(min_value - half_width, max_value, num_bins)
    bin_centers = (bin_edges[0:-1] + bin_edges[1:]) / 2
    if len(bin_edges) >= 2:
        bin_width = bin_edges[1] - bin_edges[0]

    return bin_edges, bin_centers, bin_width


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


def prepare_histogram(values, normalize=True, scott=False):
    """Return histogram counts and bins for given values with ideal bin number.

    Parameters
    ----------

    values: np.ndarray
        Array of values. It may contain NaNs.

    normalize: bool
        Whether to normalize the histogram to a probability mass function (PMF). The integral of the PMF is 1.0.

    scott: bool
        Whether to use Scott's normal reference rule (if the data is normally distributed).

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
    bin_edges, bin_centers, bin_width = ideal_hist_bins(values, scott=scott)
    n, _ = np.histogram(values, bins=bin_edges, density=False)
    if normalize:
        n = n / n.sum()
    return n, bin_edges, bin_centers, bin_width


def select_by_gmm_fitting(values: np.ndarray, num_test_components: int = 5):
    """Finds the first subpopulation by Gaussian Mixture Model fitting.

    Parameters
    ----------

    values: np.ndarray
        Array of values to be fit.

    num_test_components: int
        Maximum number of components to test. The model with the lowest Bayesian information criterion will be chosen
        for prediction.

    Returns
    -------

    res: Tuple
        selected: logical array with True for the values that correspond to the winning subpopulation,
        labels: predicted array of labels
        means: cluster means
    """

    # Prepare the data
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.shape[0] == 1 and values.shape[1] > 1:
        values = values.T

    # Fit 'num_components' models
    models = []
    for n in range(1, num_test_components + 1):
        models.append(
            GaussianMixture(
                n_components=n,
                init_params="k-means++",
                covariance_type="full",
                random_state=42,
            ).fit(values)
        )

    # Calculate the Bayesian information criterions for all models
    bic = [m.bic(values) for m in models]

    # Pick the GMM model with the lowest Akaike information criterion
    best_model = models[np.argmin(bic)]

    # Origin
    origin = np.min(values, axis=0).reshape(1, values.shape[1])

    # Pick the model closest to the origin
    model_index = np.argmin(cdist(origin, best_model.means_))

    # Predict with the selected model
    y_pred = best_model.predict(values)

    # Keep only the rows that are predicted to have y_pred = model_index
    selected = y_pred == model_index

    # Return the selection
    return selected, y_pred, best_model.means_


def select_by_bgmm_fitting(values: np.ndarray, num_test_components: int = 5):
    """Finds the first subpopulation by (Bayesian) Gaussian Mixture Model fitting.

    Parameters
    ----------

    values: np.ndarray
        Array of values to be fit.

    num_test_components: int
        Maximum number of components to test. The model with the lowest Bayesian information criterion will be chosen
        for prediction.

    Returns
    -------

    res: Tuple
        selected: logical array with True for the values that correspond to the winning subpopulation,
        labels: predicted array of labels
        means: cluster means
    """

    # Prepare the data
    if values.ndim == 1:
        values = values.reshape(-1, 1)
    if values.shape[0] == 1 and values.shape[1] > 1:
        values = values.T

    # Fit the Bayesian Gaussian Mixture Model
    model = BayesianGaussianMixture(
        n_components=num_test_components,
        n_init=num_test_components,
        init_params="k-means++",
        max_iter=1000,
        covariance_type="full",
        random_state=42,
    ).fit(values)

    # Predict with the selected model
    y_pred = model.predict(values)

    # Build the means vector
    labels = np.unique(y_pred)
    means = np.zeros((len(labels), values.shape[1]))
    for i, y in enumerate(labels):
        means[i, :] = values[y_pred == y, :].mean(axis=0)

    # Origin
    origin = np.min(values, axis=0).reshape(1, values.shape[1])

    # Pick the model closest to the origin
    model_index = np.argmin(cdist(origin, means))

    # Keep only the rows that are predicted to have y_pred = model_index
    selected = y_pred == model_index

    # Return the selection
    return selected, y_pred, means


def find_first_peak_bounds(
    counts: np.ndarray,
    bins: np.ndarray,
    min_rel_prominence: float = 0.01,
    med_filter_support: int = 5,
    qc: bool = False,
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

    qc: bool
        Whether to create quality control figures.

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
        if qc:
            fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=300)
            ax.plot(bins, x)
        return None, None

    # First peak position
    first_peak = peaks[0]

    # If we do not have any local minima, we return the beginning and end of the bins range
    if len(peaks_inv) == 0:
        if qc:
            fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=300)
            ax.plot(bins, x)
            ax.plot(bins[peaks], x[peaks], "x")
            ax.plot(bins, np.zeros_like(x), "--", color="gray")
            ax.vlines(
                x=bins[peaks],
                ymin=x[peaks] - properties["prominences"],
                ymax=x[peaks],
                color="C1",
            )
            ax.vlines(x=bins[0], ymin=x.min(), ymax=x.max(), color="r")
            ax.vlines(x=bins[-1], ymin=x.min(), ymax=x.max(), color="r")
            plt.show()
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

    # Plot results
    if qc:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12), dpi=300)
        ax.plot(bins, x)
        ax.plot(bins[peaks], x[peaks], "x")
        ax.plot(bins[peaks_inv], x[peaks_inv], "x")
        ax.plot(bins, np.zeros_like(x), "--", color="gray")
        ax.vlines(
            x=bins[peaks],
            ymin=x[peaks] - properties["prominences"],
            ymax=x[peaks],
            color="C1",
        )
        ax.vlines(x=lower_bound, ymin=x.min(), ymax=x.max(), color="r")
        ax.vlines(x=upper_bound, ymin=x.min(), ymax=x.max(), color="r")
        plt.show()

    return lower_bound, upper_bound


def calculate_density_map(
    x: np.ndarray,
    y: np.ndarray,
    x_bin_edges: Optional[np.ndarray] = None,
    y_bin_edges: Optional[np.ndarray] = None,
    scott: bool = False,
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

    scott: bool
        Whether to use Scott's normal reference rule (if the data is normally distributed).
        This is only used if either `x_bin_edges` or `y_bin_edges` are None.

    Returns
    -------

    density: np.ndarray
        2D density maps.
    """

    # Calculate bin edges if needed
    if x_bin_edges is None:
        _, x_bin_edges, _, _ = prepare_histogram(x, scott=scott)

    if y_bin_edges is None:
        _, y_bin_edges, _, _ = prepare_histogram(y, scott=scott)

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
    scott: bool = False,
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

    scott: bool
        Whether to use Scott's normal reference rule (if the data is normally distributed).
        This is only used if either `x_bin_edges` or `y_bin_edges` are None.

    Returns
    -------

    density: np.ndarray
        2D density maps.
    """

    # Calculate bin edges if needed
    if x_bin_edges is None:
        _, x_bin_edges, _, _ = prepare_histogram(x, scott=scott)

    if y_bin_edges is None:
        _, y_bin_edges, _, _ = prepare_histogram(y, scott=scott)

    # Create 2D histogram
    histogram = np.histogram2d(y, x, bins=(y_bin_edges, x_bin_edges))

    # Return histogram
    return histogram
