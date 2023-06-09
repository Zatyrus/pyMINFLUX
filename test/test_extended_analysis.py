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

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.interpolate import CubicSpline, interp1d
from scipy.io import loadmat

from pyminflux.correct import (
    drift_correction_time_windows_2d,
    drift_correction_time_windows_3d,
)
from pyminflux.fourier import (
    estimate_resolution_by_frc,
    get_localization_boundaries,
    img_fourier_ring_correlation,
)
from pyminflux.processor import MinFluxProcessor
from pyminflux.reader import MinFluxReader
from pyminflux.render import render_xy, render_xyz


@pytest.fixture(autouse=False)
def extract_raw_npy_data_files(tmpdir):
    """Fixture to execute asserts before and after a test is run"""

    #
    # Setup
    #

    # Make sure to extract the test data if it is not already there
    npy_file_name = Path(__file__).parent / "data" / "2D_ValidOnly.npy"
    zip_file_name = Path(__file__).parent / "data" / "2D_ValidOnly.npy.zip"
    if not npy_file_name.is_file():
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            zip_ref.extractall(Path(__file__).parent / "data")

    npy_file_name = Path(__file__).parent / "data" / "3D_ValidOnly.npy"
    zip_file_name = Path(__file__).parent / "data" / "3D_ValidOnly.npy.zip"
    if not npy_file_name.is_file():
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            zip_ref.extractall(Path(__file__).parent / "data")

    yield  # This is where the testing happens

    #
    # Teardown
    #

    # Do whatever is needed to clean up:
    # - Nothing for the moment


def test_data_boundaries(extract_raw_npy_data_files):
    """Test the analysis.get_localization_boundaries() function."""

    #
    # 2D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)
    #

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "2D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at default alpha and min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
    )

    # Test
    assert np.isclose(rx[0], 1744.43303535), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5492.12179283), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15538.14183461), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11702.99913876), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Get boundaries at alpha=0.2 and default min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.2,
    )

    # Test
    assert np.isclose(rx[0], 2290.12936281), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 4720.17628345), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15065.18736499), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -12315.87321753), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Get boundaries at alpha=0.49 and default min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.49,
    )

    # Test
    assert np.isclose(rx[0], 3276.73966011), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 3476.73966011), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -13981.9058782), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -13781.9058782), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."
    assert np.isclose(rx[1] - rx[0], 200.0), "Unexpected range for x."
    assert np.isclose(ry[1] - ry[0], 200.0), "Unexpected range for y."

    # Get boundaries at default alpha and min_range=5000
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        min_range=5000,
    )

    # Test
    assert np.isclose(rx[0], 1118.27741409), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 6118.27741409), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -16120.57048668), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11120.57048668), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."
    assert np.isclose(rx[1] - rx[0], 5000.0), "Unexpected range for x."
    assert np.isclose(ry[1] - ry[0], 5000.0), "Unexpected range for y."

    #
    # 3D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)
    #

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "3D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at default alpha and min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
    )

    # Test
    assert np.isclose(rx[0], 1610.71322264), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5439.30190298), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -10610.38121423), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -6882.35098526), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], -216.75738013), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 129.18317291), "Unexpected upper boundary for z."

    # Get boundaries at alpha=0.2 and default min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.2,
    )

    # Test
    assert np.isclose(rx[0], 2311.1744342), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 4519.76543671), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -9910.17370305), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -7415.93602781), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], -111.89731079), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 88.10268921), "Unexpected upper boundary for z."
    assert np.isclose(rz[1] - rz[0], 200.0)

    # Get boundaries at alpha=0.49 and default min_range
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.49,
    )

    # Test
    assert np.isclose(rx[0], 3357.27017594), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 3557.27017594), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -8976.91805543), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -8776.91805543), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], -107.14343652), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 92.85656348), "Unexpected upper boundary for z."
    assert np.isclose(rx[1] - rx[0], 200.0), "Unexpected range for x."
    assert np.isclose(ry[1] - ry[0], 200.0), "Unexpected range for y."
    assert np.isclose(rz[1] - rz[0], 200.0), "Unexpected range for z."

    # Get boundaries at default alpha and min_range=5000
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        min_range=5000,
    )

    # Test
    assert np.isclose(rx[0], 1025.00756281), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 6025.00756281), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -11246.36609975), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -6246.36609975), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], -2543.78710361), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 2456.21289639), "Unexpected upper boundary for z."
    assert np.isclose(rx[1] - rx[0], 5000.0), "Unexpected range for x."
    assert np.isclose(ry[1] - ry[0], 5000.0), "Unexpected range for y."
    assert np.isclose(rz[1] - rz[0], 5000.0), "Unexpected range for z."


def test_render_xy(extract_raw_npy_data_files):
    """Test the render.render_xy() function."""

    #
    # 2D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)
    #

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "2D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at alpha = 0.0 and min_range = 500: this gives all data back.
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.0,
        min_range=500,
    )

    # Test
    assert np.isclose(rx[0], 1647.61105813), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5677.04500607), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15659.23531582), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11623.81911211), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Rendering resolution (in nm)
    sx = 1.0
    sy = 1.0

    # Render the 2D image as simple histogram
    img, xi, yi, m = render_xy(
        processor.filtered_dataframe["x"].values,
        processor.filtered_dataframe["y"].values,
        sx=sx,
        sy=sy,
        rx=None,
        ry=None,
    )

    # Check the returned values
    assert np.isclose(
        img.sum(), len(processor.filtered_dataframe["x"].values)
    ), "Unexpected signal integral."
    assert np.isclose(xi.min(), 1648.111058125942), "Unexpected x grid (min value)."
    assert np.isclose(xi.max(), 5677.111058125942), "Unexpected x grid (max) value)."
    assert np.isclose(yi.min(), -15658.73531581803), "Unexpected y grid (min value)."
    assert np.isclose(yi.max(), -11623.73531581803), "Unexpected y grid (max value)."
    assert m.sum() == 12580.0, "Unexpected number of considered elements."
    assert m.sum() == len(
        processor.filtered_dataframe["x"].values
    ), "Unexpected number of considered elements."

    # Render the 2D image as a Gaussian fit
    img, xi, yi, m = render_xy(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        sx=sx,
        sy=sy,
        rx=None,
        ry=None,
        render_type="fixed_gaussian",
    )

    # Check the returned values
    assert np.isclose(img.sum(), 256291.22), "Unexpected signal integral."
    assert np.isclose(xi.min(), 1648.111058125942), "Unexpected x grid (min value)."
    assert np.isclose(xi.max(), 5677.111058125942), "Unexpected x grid (max) value)."
    assert np.isclose(yi.min(), -15658.73531581803), "Unexpected y grid (min value)."
    assert np.isclose(yi.max(), -11623.73531581803), "Unexpected y grid (max value)."
    assert m.sum() == 12566.0, "Unexpected number of considered elements."
    assert m.sum() < len(
        processor.filtered_dataframe["x"].values
    ), "Unexpected number of considered elements."


def test_render_xyz(extract_raw_npy_data_files):
    """Test the render.render_xyz() function."""

    #
    # 3D_ValidOnly.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)
    #

    # 3D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "3D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at alpha = 0.0 and min_range = 500: this gives all data back.
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.0,
        min_range=500,
    )

    # Test
    assert np.isclose(rx[0], 1508.14087089), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5471.75772354), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -10781.08977624), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -6761.66793333), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], -358.31916504), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 147.03635254), "Unexpected upper boundary for z."

    # Rendering resolution (in nm)
    sx = 5.0
    sy = 5.0
    sz = 5.0

    # Render the 3D image as simple histogram
    img, xi, yi, zi, m = render_xyz(
        processor.filtered_dataframe["x"].values,
        processor.filtered_dataframe["y"].values,
        processor.filtered_dataframe["z"].values,
        sx=sx,
        sy=sy,
        sz=sz,
        rx=None,
        ry=None,
        rz=None,
    )

    # Check the returned values
    assert np.isclose(img.sum(), 5810.0), "Unexpected signal integral."
    assert np.isclose(xi.min(), 1510.6408708914191), "Unexpected x grid (min value)."
    assert np.isclose(xi.max(), 5470.640870891419), "Unexpected x grid (max) value)."
    assert np.isclose(yi.min(), -10778.589776239387), "Unexpected y grid (min value)."
    assert np.isclose(yi.max(), -6763.589776239387), "Unexpected y grid (max value)."
    assert np.isclose(zi.min(), -355.8191650390625), "Unexpected z grid (min value)."
    assert np.isclose(zi.max(), 149.1808349609375), "Unexpected z grid (max value)."
    assert m.sum() == 5810.0, "Unexpected number of considered elements."

    #
    # Fig2_U2OS_Tom70-Dreiklang_ATP5B_AB_Minflux3D.mat -> csv
    #
    # From:
    #   * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    #   * [code]  https://zenodo.org/record/6563100

    df = pd.read_csv(
        Path(__file__).parent
        / "data"
        / "Fig2_U2OS_Tom70-Dreiklang_ATP5B_AB_Minflux3D.csv",
    )
    pos = df[["x", "y", "z"]].values

    # Rendering resolution (in nm)
    sx = 3.0
    sy = 3.0
    sz = 3.0

    # Spatial ranges
    rx = (-434.5609880335669, 367.8659119806681)
    ry = (-1419.260678440071, 1801.300331041331)
    rz = (-298.8539888427734, 90.5609084228519)

    # Render the 3D image as a Gaussian fit
    img, xi, yi, si, m = render_xyz(
        pos[:, 0],
        pos[:, 1],
        pos[:, 2],
        sx=sx,
        sy=sy,
        sz=sz,
        rx=rx,
        ry=ry,
        rz=rz,
        render_type="fixed_gaussian",
        fwhm=15.0,
    )

    # Check the returned values
    assert np.isclose(img.sum(), 1704868.5), "Unexpected signal integral."
    assert np.isclose(xi.min(), -433.0609880335669), "Unexpected x grid (min value)."
    assert np.isclose(xi.max(), 367.9390119664331), "Unexpected x grid (max) value)."
    assert np.isclose(yi.min(), -1417.760678440071), "Unexpected y grid (min value)."
    assert np.isclose(yi.max(), 1801.239321559929), "Unexpected y grid (max value)."
    assert np.isclose(zi.min(), -355.8191650390625), "Unexpected z grid (min value)."
    assert np.isclose(zi.max(), 149.1808349609375), "Unexpected z grid (max value)."
    assert m.sum() == 11308.0, "Unexpected number of considered elements."


def test_fourier_ring_correlation_all_pos(extract_raw_npy_data_files):
    """Test the analysis.img_fourier_ring_correlation() function on all positions."""

    #
    # 2D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "2D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at alpha = 0.0 and min_range = 500: this gives all data back.
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.0,
        min_range=500,
    )

    # Test
    assert np.isclose(rx[0], 1647.61105813), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5677.04500607), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15659.23531582), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11623.81911211), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Work on 2D data
    x = processor.filtered_dataframe["x"].values
    y = processor.filtered_dataframe["y"].values

    # Initialize the random number generator
    rng = np.random.default_rng(2023)

    N = 5
    expected_resolutions = np.array(
        [7.19424460e-09, 6.99300699e-09, 6.75675676e-09, 6.99300699e-09, 6.99300699e-09]
    )
    resolutions = np.zeros(N)
    for r in range(N):

        # Partition the data
        ix = rng.random(size=x.shape) < 0.5
        c_ix = np.logical_not(ix)

        # Create two images from (complementary) subsets of coordinates (x, y) using the "histogram"
        # mode and a rendering resolution of sxy = 1.0 nm.
        sxy = 1.0
        h1 = render_xy(x[ix], y[ix], sxy, sxy, rx, ry)[0]
        h2 = render_xy(x[c_ix], y[c_ix], sxy, sxy, rx, ry)[0]

        # Estimate the resolution using Fourier Ring Correlation
        estimated_resolution, fc, qi, ci = img_fourier_ring_correlation(
            h1, h2, sx=sxy, sy=sxy
        )

        # Store the estimated resolution, qis and cis
        resolutions[r] = estimated_resolution

    # Test
    assert np.allclose(
        resolutions, expected_resolutions
    ), "Calculated resolutions do not match the expected ones."


def test_fourier_ring_correlation_all_pos_mat(extract_raw_npy_data_files):
    """Test the analysis.img_fourier_ring_correlation() function on all positions (.mat file)."""

    #
    # Fig1a_Tom70-Dreiklang_Minflux.mat
    #
    # From:
    #   * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    #   * [code]  https://zenodo.org/record/6563100

    minflux = loadmat(
        str(Path(__file__).parent / "data" / "Fig1a_Tom70-Dreiklang_Minflux.mat")
    )
    minflux = minflux["minflux"]

    # x and y coordinates
    pos = minflux["pos"][0][0]
    x = pos[:, 0]
    y = pos[:, 1]

    # Ranges
    rx = (-372.5786, 318.8638)
    ry = (-1148.8, 1006.6)

    # Initialize the random number generator
    rng = np.random.default_rng(2023)

    N = 5
    expected_resolutions = np.array(
        [5.44959128e-09, 5.46448087e-09, 5.66572238e-09, 5.61797753e-09, 5.49450549e-09]
    )
    resolutions = np.zeros(N)
    for r in range(N):

        # Partition the data
        ix = rng.random(size=x.shape) < 0.5
        c_ix = np.logical_not(ix)

        # Create two images from (complementary) subsets of coordinates (x, y) using the "histogram"
        # mode and a rendering resolution of sxy = 1.0 nm.
        sxy = 1.0
        h1 = render_xy(x[ix], y[ix], sxy, sxy, rx, ry)[0]
        h2 = render_xy(x[c_ix], y[c_ix], sxy, sxy, rx, ry)[0]

        # Estimate the resolution using Fourier Ring Correlation
        estimated_resolution, fc, qi, ci = img_fourier_ring_correlation(
            h1, h2, sx=sxy, sy=sxy
        )

        # Store the estimated resolution
        resolutions[r] = estimated_resolution

    # Test
    assert np.allclose(
        resolutions, expected_resolutions
    ), "Calculated resolutions do not match the expected ones."


def test_fourier_ring_correlation_per_tid(extract_raw_npy_data_files):
    """Test the analysis.img_fourier_ring_correlation() function on average positions per TID."""

    #
    # 2D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not to filter anything)

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "2D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at alpha = 0.0 and min_range = 500: this gives all data back.
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.0,
        min_range=500,
    )

    # Test
    assert np.isclose(rx[0], 1647.61105813), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5677.04500607), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15659.23531582), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11623.81911211), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Work on averaged 2D data
    x = processor.filtered_dataframe_stats["mx"].values
    y = processor.filtered_dataframe_stats["my"].values

    # Initialize the random number generator
    rng = np.random.default_rng(2023)

    N = 5
    expected_resolutions = np.array(
        [1.32450331e-08, 1.43884892e-08, 1.40845070e-08, 1.39860140e-08, 1.36986301e-08]
    )

    resolutions = np.zeros(N)
    for r in range(N):

        # Partition the data
        ix = rng.random(size=x.shape) < 0.5
        c_ix = np.logical_not(ix)

        # Create two images from (complementary) subsets of coordinates (x, y) using the "histogram"
        # mode and a rendering resolution of sxy = 1.0 nm.
        sxy = 1.0
        h1 = render_xy(x[ix], y[ix], sxy, sxy, rx, ry)[0]
        h2 = render_xy(x[c_ix], y[c_ix], sxy, sxy, rx, ry)[0]

        # Estimate the resolution using Fourier Ring Correlation
        estimated_resolution, fc, qi, ci = img_fourier_ring_correlation(
            h1, h2, sx=sxy, sy=sxy
        )

        # Store the estimated resolution
        resolutions[r] = estimated_resolution

    # Test
    assert np.allclose(
        resolutions, expected_resolutions
    ), "Calculated resolutions do not match the expected ones."


def test_fourier_ring_correlation_per_tid_mat(extract_raw_npy_data_files):
    """Test the analysis.img_fourier_ring_correlation() function on average positions per TID (.mat file)."""

    #
    # Fig1a_Tom70-Dreiklang_Minflux.mat
    #
    # From:
    #   * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    #   * [code]  https://zenodo.org/record/6563100

    minflux = loadmat(
        str(Path(__file__).parent / "data" / "Fig1a_Tom70-Dreiklang_Minflux.mat")
    )
    minflux = minflux["minflux"]

    # Extract tid, x and y coordinates
    tid = minflux["id"][0][0].ravel()
    pos = minflux["pos"][0][0][:, :2]

    # Calculate per-TID averages
    u_tid = np.unique(tid)
    m_pos = np.zeros((len(u_tid), 2), dtype=float)
    for i, t in enumerate(u_tid):
        m_pos[i, :] = pos[tid == t, :].mean(axis=0)

    # Now extract the mean x and y localizations
    x = m_pos[:, 0]
    y = m_pos[:, 1]

    # Ranges
    rx = (-372.5786, 318.8638)
    ry = (-1148.8, 1006.6)

    # Initialize the random number generator
    rng = np.random.default_rng(2023)

    N = 5
    expected_resolutions = np.array(
        [1.17647059e-08, 1.21212121e-08, 1.14942529e-08, 1.18343195e-08, 1.16279070e-08]
    )

    resolutions = np.zeros(N)
    for r in range(N):

        # Partition the data
        ix = rng.random(size=x.shape) < 0.5
        c_ix = np.logical_not(ix)

        # Create two images from (complementary) subsets of coordinates (x, y) using the "histogram"
        # mode and a rendering resolution of sxy = 1.0 nm.
        sxy = 1.0
        h1 = render_xy(x[ix], y[ix], sxy, sxy, rx, ry)[0]
        h2 = render_xy(x[c_ix], y[c_ix], sxy, sxy, rx, ry)[0]

        # Estimate the resolution using Fourier Ring Correlation
        estimated_resolution, fc, qi, ci = img_fourier_ring_correlation(
            h1, h2, sx=sxy, sy=sxy
        )

        # Store the estimated resolution
        resolutions[r] = estimated_resolution

    # Test
    assert np.allclose(
        resolutions, expected_resolutions
    ), "Calculated resolutions do not match the expected ones."


def test_estimate_resolution(extract_raw_npy_data_files):
    """Test the estimate_resolution_frc() function on average positions per TID."""

    #
    # 2D_Only.npy
    #
    # min_num_loc_per_trace = 1 (do not filter anything)

    # 2D_ValidOnly.npy
    reader = MinFluxReader(Path(__file__).parent / "data" / "2D_ValidOnly.npy")
    processor = MinFluxProcessor(reader, min_trace_length=1)

    # Get boundaries at alpha = 0.0 and min_range = 500: this gives all data back.
    rx, ry, rz = get_localization_boundaries(
        processor.filtered_dataframe["x"],
        processor.filtered_dataframe["y"],
        processor.filtered_dataframe["z"],
        alpha=0.0,
        min_range=500,
    )

    # Test
    assert np.isclose(rx[0], 1647.61105813), "Unexpected lower boundary for x."
    assert np.isclose(rx[1], 5677.04500607), "Unexpected upper boundary for x."
    assert np.isclose(ry[0], -15659.23531582), "Unexpected lower boundary for y."
    assert np.isclose(ry[1], -11623.81911211), "Unexpected upper boundary for y."
    assert np.isclose(rz[0], 0.0), "Unexpected lower boundary for z."
    assert np.isclose(rz[1], 0.0), "Unexpected upper boundary for z."

    # Work on averaged 2D data
    x = processor.filtered_dataframe_stats["mx"].values
    y = processor.filtered_dataframe_stats["my"].values

    # Expected values
    expected_resolution = 1.3880534697293937e-08
    expected_resolutions = np.array(
        [1.32450331e-08, 1.43884892e-08, 1.40845070e-08, 1.39860140e-08, 1.36986301e-08]
    )
    expected_qi = np.arange(0.0, 565500001.0, 500000.0)
    expected_ci_start = np.array(
        [
            0.9336742761682728,
            0.9121192385227754,
            0.8905642008772781,
            0.8690091632317805,
            0.8392228000026671,
        ]
    )
    expected_ci_end = np.array(
        [
            -0.009595674622152111,
            -0.005901680204625083,
            -0.005055759319879996,
            -0.004209838435134908,
            -0.0033639175503898224,
        ]
    )
    expected_cis_start = np.array(
        [
            0.9341944036592993,
            0.9352963139467972,
            0.9355879665101374,
            0.9366334447515838,
            0.9266592519735464,
        ]
    )
    expected_cis_end = np.array(
        [
            -0.021411617722575698,
            -0.012289520386436669,
            0.013807450817036786,
            -0.00017335425368504923,
            0.0032474537937115192,
        ]
    )

    # Run the resolution estimation
    resolution, qi, ci, resolutions, cis = estimate_resolution_by_frc(
        x, y, rx=rx, ry=ry, num_reps=5, seed=2023, return_all=True
    )

    # Test
    assert np.isclose(resolution, expected_resolution), "Unexpected resolution."
    assert np.allclose(
        resolutions, expected_resolutions
    ), "Unexpected array of resolutions."
    assert np.isclose(
        expected_resolutions.mean(), expected_resolution
    ), "Unexpected resolution."
    assert np.allclose(expected_qi, qi), "Unexpected array of qis."
    assert np.allclose(expected_ci_start, ci[:5]), "Unexpected beginning of ci."
    assert np.allclose(expected_ci_end, ci[-5:]), "Unexpected end of ci."
    assert np.allclose(expected_cis_start, cis[0, :]), "Unexpected array of cis."
    assert np.allclose(expected_cis_end, cis[-1, :]), "Unexpected array of cis."


def test_estimate_drift_2d_mat(extract_raw_npy_data_files):
    """Test the drift_correction_time_windows_2d() (.mat file)."""

    #
    # Fig1a_Tom70-Dreiklang_Minflux.mat
    #
    # From:
    #   * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    #   * [code]  https://zenodo.org/record/6563100

    minflux = loadmat(
        str(Path(__file__).parent / "data" / "Fig1a_Tom70-Dreiklang_Minflux.mat")
    )
    minflux = minflux["minflux"]

    # Extract tid, x and y coordinates
    t = minflux["t"][0][0].ravel()
    tid = minflux["id"][0][0].ravel()
    pos = minflux["pos"][0][0][:, :2]
    x = pos[:, 0]
    y = pos[:, 1]

    # Spatial ranges
    rx = (-372.5786, 318.8638)
    ry = (-1148.8, 1006.6)

    # Resolution
    sxy = 2

    # Run the 2D drift correction
    dx, dy, dxt, dyt, ti, T = drift_correction_time_windows_2d(
        x, y, t, sxy=sxy, rx=rx, ry=ry, T=None, tid=tid
    )

    # Expected values
    expected_dx_first = -2.205576196850738
    expected_dx_last = -2.6063570587906
    expected_dx_mean = -0.5332977272042978
    expected_dx_std = 1.127749604233301
    expected_dy_first = 0.5048935277587024
    expected_dy_last = -6.146428606993543
    expected_dy_mean = -0.7935001517529221
    expected_dy_std = 2.1620576306028627
    expected_dxt_first = -2.2055761968507386
    expected_dxt_last = -2.5483486849735746
    expected_dxt_mean = -0.5585876746324872
    expected_dxt_std = 1.1313382783145665
    expected_dyt_first = 0.5048935277587026
    expected_dyt_last = -6.040532333517817
    expected_dyt_mean = -1.2400984188497535
    expected_dyt_std = 2.3283159607530033
    expected_ti_first = 0.0
    expected_ti_last = 3634.628873523648
    expected_ti_mean = 1817.3144367618238
    expected_ti_std = 1075.7938918849325
    expected_T = 931.95612141632

    # Test
    assert np.isclose(expected_dx_first, dx[0]), "Unexpected value for dx[0]."
    assert np.isclose(expected_dx_last, dx[-1]), "Unexpected value for dx[-1]."
    assert np.isclose(expected_dx_mean, dx.mean()), "Unexpected value for dx.mean()."
    assert np.isclose(expected_dx_std, dx.std()), "Unexpected value for dx.std()."
    assert len(dx) == len(x), "Unexpected length of vector x."
    assert np.isclose(expected_dy_first, dy[0]), "Unexpected value for dy[0]."
    assert np.isclose(expected_dy_last, dy[-1]), "Unexpected value for dy[-1]."
    assert np.isclose(expected_dy_mean, dy.mean()), "Unexpected value for dy.mean()."
    assert np.isclose(expected_dy_std, dy.std()), "Unexpected value for dy.std()."
    assert len(dy) == len(y), "Unexpected length of vector y."
    assert np.isclose(expected_dxt_first, dxt[0]), "Unexpected value for dxt[0]."
    assert np.isclose(expected_dxt_last, dxt[-1]), "Unexpected value for dxt[-1]."
    assert np.isclose(expected_dxt_mean, dxt.mean()), "Unexpected value for dxt.mean()."
    assert np.isclose(expected_dxt_std, dxt.std()), "Unexpected value for dxt.std()."
    assert len(dxt) == 40, "Unexpected length of vector dxt."
    assert np.isclose(expected_dyt_first, dyt[0]), "Unexpected value for dyt[0]."
    assert np.isclose(expected_dyt_last, dyt[-1]), "Unexpected value for dyt[-1]."
    assert np.isclose(expected_dyt_mean, dyt.mean()), "Unexpected value for dyt.mean()."
    assert np.isclose(expected_dyt_std, dyt.std()), "Unexpected value for dyt.std()."
    assert len(dyt) == 40, "Unexpected length of vector dyt."
    assert np.isclose(expected_ti_first, ti[0]), "Unexpected value for ti[0]."
    assert np.isclose(expected_ti_last, ti[-1]), "Unexpected value for ti[-1]."
    assert np.isclose(expected_ti_mean, ti.mean()), "Unexpected value for ti.mean()."
    assert np.isclose(expected_ti_std, ti.std()), "Unexpected value for ti.std()."
    assert len(ti) == 40, "Unexpected length of vector ti."
    assert np.isclose(expected_T, T), "Unexpected value for T."


def test_estimate_drift_3d_mat(extract_raw_npy_data_files):
    """Test the drift_correction_time_windows_3d() (.mat file)."""

    #
    # Fig2_U2OS_Tom70-Dreiklang_ATP5B_AB_Minflux3D.mat -> csv
    #
    # From:
    #   * [paper] Ostersehlt, L.M., Jans, D.C., Wittek, A. et al. DNA-PAINT MINFLUX nanoscopy. Nat Methods 19, 1072-1075 (2022). https://doi.org/10.1038/s41592-022-01577-1
    #   * [code]  https://zenodo.org/record/6563100

    df = pd.read_csv(
        Path(__file__).parent
        / "data"
        / "Fig2_U2OS_Tom70-Dreiklang_ATP5B_AB_Minflux3D.csv",
    )

    # Extract tid, x and y coordinates
    tid = df["tid"].values
    t = df["t"].values
    pos = df[["x", "y", "z"]].values
    x = pos[:, 0]
    y = pos[:, 1]
    z = pos[:, 2]

    # Spatial ranges
    rx = (-434.5609880335669, 367.8659119806681)
    ry = (-1419.260678440071, 1801.300331041331)
    rz = (-298.8539888427734, 90.5609084228519)

    # Resolution
    sxyz = 5

    # Run the 3D drift correction
    dx, dy, dz, dxt, dyt, dzt, ti, T = drift_correction_time_windows_3d(
        x, y, z, t, sxyz=sxyz, rx=rx, ry=ry, rz=rz, T=None, tid=tid
    )

    # Expected values
    expected_dx_first = -12.460331273589698
    expected_dx_last = 8.009857008956743
    expected_dx_mean = 0.12864066343930008
    expected_dx_std = 6.589954694613107
    expected_dy_first = -16.152128169189766
    expected_dy_last = -1.152773064395448
    expected_dy_mean = -0.37461486256391596
    expected_dy_std = 6.095210550804399
    expected_dz_first = 13.232820104945795
    expected_dz_last = -2.9932534950048657
    expected_dz_mean = 0.041667510696429745
    expected_dz_std = 4.2692515907552275
    expected_dxt_first = -12.460331273589695
    expected_dxt_last = 7.8600782229735024
    expected_dxt_mean = 0.6264401262142165
    expected_dxt_std = 6.567311471605163
    expected_dyt_first = -16.152128169189762
    expected_dyt_last = -1.0904874624989902
    expected_dyt_mean = -0.5297079182499407
    expected_dyt_std = 6.324853491059834
    expected_dzt_first = 13.232820104945795
    expected_dzt_last = -2.9226937747501482
    expected_dzt_mean = -0.1086293313859324
    expected_dzt_std = 4.197818682696678
    expected_ti_first = 0.0
    expected_ti_last = 3960
    expected_ti_mean = 1980
    expected_ti_std = 1160.344776348823
    expected_T = 600.0

    # Test
    assert np.isclose(expected_dx_first, dx[0]), "Unexpected value for dx[0]."
    assert np.isclose(expected_dx_last, dx[-1]), "Unexpected value for dx[-1]."
    assert np.isclose(expected_dx_mean, dx.mean()), "Unexpected value for dx.mean()."
    assert np.isclose(expected_dx_std, dx.std()), "Unexpected value for dx.std()."
    assert len(dx) == len(x), "Unexpected length of vector x."
    assert np.isclose(expected_dy_first, dy[0]), "Unexpected value for dy[0]."
    assert np.isclose(expected_dy_last, dy[-1]), "Unexpected value for dy[-1]."
    assert np.isclose(expected_dy_mean, dy.mean()), "Unexpected value for dy.mean()."
    assert np.isclose(expected_dy_std, dy.std()), "Unexpected value for dy.std()."
    assert len(dy) == len(y), "Unexpected length of vector y."
    assert np.isclose(expected_dz_first, dz[0]), "Unexpected value for dz[0]."
    assert np.isclose(expected_dz_last, dz[-1]), "Unexpected value for dz[-1]."
    assert np.isclose(expected_dz_mean, dz.mean()), "Unexpected value for dz.mean()."
    assert np.isclose(expected_dz_std, dz.std()), "Unexpected value for dz.std()."
    assert len(dz) == len(z), "Unexpected length of vector z."
    assert np.isclose(expected_dxt_first, dxt[0]), "Unexpected value for dxt[0]."
    assert np.isclose(expected_dxt_last, dxt[-1]), "Unexpected value for dxt[-1]."
    assert np.isclose(expected_dxt_mean, dxt.mean()), "Unexpected value for dxt.mean()."
    assert np.isclose(expected_dxt_std, dxt.std()), "Unexpected value for dxt.std()."
    assert len(dxt) == 67, "Unexpected length of vector dxt."
    assert np.isclose(expected_dyt_first, dyt[0]), "Unexpected value for dyt[0]."
    assert np.isclose(expected_dyt_last, dyt[-1]), "Unexpected value for dyt[-1]."
    assert np.isclose(expected_dyt_mean, dyt.mean()), "Unexpected value for dyt.mean()."
    assert np.isclose(expected_dyt_std, dyt.std()), "Unexpected value for dyt.std()."
    assert len(dyt) == 67, "Unexpected length of vector dyt."
    assert np.isclose(expected_dzt_first, dzt[0]), "Unexpected value for dzt[0]."
    assert np.isclose(expected_dzt_last, dzt[-1]), "Unexpected value for dzt[-1]."
    assert np.isclose(expected_dzt_mean, dzt.mean()), "Unexpected value for dzt.mean()."
    assert np.isclose(expected_dzt_std, dzt.std()), "Unexpected value for dzt.std()."
    assert len(dyt) == 67, "Unexpected length of vector dyt."
    assert np.isclose(expected_ti_first, ti[0]), "Unexpected value for ti[0]."
    assert np.isclose(expected_ti_last, ti[-1]), "Unexpected value for ti[-1]."
    assert np.isclose(expected_ti_mean, ti.mean()), "Unexpected value for ti.mean()."
    assert np.isclose(expected_ti_std, ti.std()), "Unexpected value for ti.std()."
    assert len(ti) == 67, "Unexpected length of vector ti."
    assert np.isclose(expected_T, T), "Unexpected value for T."


def test_adaptive_interpolation(extract_raw_npy_data_files):

    # Sample data
    ti = np.array([0, 1, 2, 3, 4])
    sx = np.array([0, 1, 4, 9, 16])

    # Create cubic spline interpolation function
    cubic_spline = CubicSpline(ti, sx)

    # Create linear interpolation function for extrapolation
    linear_interp = interp1d(ti, sx, kind="linear", fill_value="extrapolate")

    def combined_interp(x):
        # Use cubic spline interpolation for values within the original range
        # and linear interpolation for extrapolation
        if np.min(ti) <= x <= np.max(ti):
            return cubic_spline(x)
        else:
            return linear_interp(x)

    # Test the combined_interp function
    assert combined_interp(1.5) == 2.25, "Expected result of cubic interpolation."
    assert combined_interp(-1) == -1.0, "Expected result of linear extrapolation."


def test_coordinate_processing():
    """Test the way coordinates are processed."""

    # Coordinates
    x = np.arange(1, 100, 5).astype(np.float32)
    y = np.arange(1, 100, 5).astype(np.float32)
    z = np.arange(1, 100, 5).astype(np.float32)

    # Range to consider
    rx = (10.0, 90.0)
    ry = (10.0, 90.0)
    rz = (10.0, 90.0)

    #
    # First resolution, no kernel
    #

    # Resolution (nm)
    sx = 2.0
    sy = 2.0
    sz = 5.0

    # Get target image dimension
    nx = int(np.ceil((rx[1] - rx[0]) / sx))
    ny = int(np.ceil((ry[1] - ry[0]) / sy))
    nz = int(np.ceil((rz[1] - rz[0]) / sz))

    # Get position in pixels
    px = (x - rx[0]) / sx
    py = (y - ry[0]) / sy
    pz = (z - rz[0]) / sz

    # Convert absolute position to image indices
    ix = np.round(px).astype(int)
    iy = np.round(py).astype(int)
    iz = np.round(pz).astype(int)

    # Remove positions outside the image
    m = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (iz >= 0) & (iz < nz)
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Flip iy to have 0 at the top
    f_iy = ny - iy - 1

    # Try placing all entries in the image
    success = True
    h = np.zeros((nz, ny, nx), dtype=np.float32)
    for i in range(len(ix)):
        xi = ix[i]
        yi = f_iy[i]  # Images have y = 0 at the top
        zi = iz[i]
        try:
            h[zi, yi, xi] += 1
        except IndexError as _:
            success = False
            break

    # Expected values
    expected_success = True
    expected_x = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_y = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_z = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_nx = 40
    expected_ny = 40
    expected_nz = 16
    expected_px = np.array(
        [
            0.5,
            3.0,
            5.5,
            8.0,
            10.5,
            13.0,
            15.5,
            18.0,
            20.5,
            23.0,
            25.5,
            28.0,
            30.5,
            33.0,
            35.5,
            38.0,
        ]
    )
    expected_py = np.array(
        [
            0.5,
            3.0,
            5.5,
            8.0,
            10.5,
            13.0,
            15.5,
            18.0,
            20.5,
            23.0,
            25.5,
            28.0,
            30.5,
            33.0,
            35.5,
            38.0,
        ]
    )
    expected_pz = np.array(
        [
            0.2,
            1.2,
            2.2,
            3.2,
            4.2,
            5.2,
            6.2,
            7.2,
            8.2,
            9.2,
            10.2,
            11.2,
            12.2,
            13.2,
            14.2,
            15.2,
        ]
    )
    expected_ix = np.array([0, 3, 6, 8, 10, 13, 16, 18, 20, 23, 26, 28, 30, 33, 36, 38])
    expected_iy = np.array([0, 3, 6, 8, 10, 13, 16, 18, 20, 23, 26, 28, 30, 33, 36, 38])
    expected_iz = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    expected_f_iy = np.array(
        [[39, 36, 33, 31, 29, 26, 23, 21, 19, 16, 13, 11, 9, 6, 3, 1]]
    )
    expected_m = np.array(
        [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    ).astype(bool)

    # Test
    assert expected_success == success, "Could not write all pixels in the image."
    assert np.allclose(expected_x, x), "Unexpected array y."
    assert np.allclose(expected_y, x), "Unexpected array y."
    assert np.allclose(expected_z, x), "Unexpected array y."
    assert expected_nx == nx, "Unexpected value for nx."
    assert expected_ny == ny, "Unexpected value for ny."
    assert expected_nz == nz, "Unexpected value for nZ."
    assert np.allclose(expected_px, px), "Unexpected array px."
    assert np.allclose(expected_py, py), "Unexpected array py."
    assert np.allclose(expected_pz, pz), "Unexpected array pz."
    assert np.allclose(expected_ix, ix), "Unexpected array ix."
    assert np.allclose(expected_iy, iy), "Unexpected array iy."
    assert np.allclose(expected_iz, iz), "Unexpected array iz."
    assert np.allclose(expected_f_iy, f_iy), "Unexpected array f_iy."
    assert np.allclose(expected_m, m), "Unexpected array y."

    #
    # Second resolution, no kernel
    #

    # Resolution (nm)
    sx = 2.5
    sy = 2.5
    sz = 5.0

    # Get target image dimension
    nx = int(np.ceil((rx[1] - rx[0]) / sx))
    ny = int(np.ceil((ry[1] - ry[0]) / sy))
    nz = int(np.ceil((rz[1] - rz[0]) / sz))

    # Get position in pixels
    px = (x - rx[0]) / sx
    py = (y - ry[0]) / sy
    pz = (z - rz[0]) / sz

    # Convert absolute position to image indices
    ix = np.round(px).astype(int)
    iy = np.round(py).astype(int)
    iz = np.round(pz).astype(int)

    # Remove positions outside the image
    m = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (iz >= 0) & (iz < nz)
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Flip iy to have 0 at the top
    f_iy = ny - iy - 1

    # Try placing all entries in the image
    success = True
    h = np.zeros((nz, ny, nx), dtype=np.float32)
    for i in range(len(ix)):
        xi = ix[i]
        yi = f_iy[i]  # Images have y = 0 at the top
        zi = iz[i]
        try:
            h[zi, yi, xi] += 1
        except IndexError as _:
            success = False
            break

    # Expected values
    expected_success = True
    expected_x = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_y = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_z = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_nx = 32
    expected_ny = 32
    expected_nz = 16
    expected_px = np.array(
        [
            0.4,
            2.4,
            4.4,
            6.4,
            8.4,
            10.4,
            12.4,
            14.4,
            16.4,
            18.4,
            20.4,
            22.4,
            24.4,
            26.4,
            28.4,
            30.4,
        ]
    )
    expected_py = np.array(
        [
            0.4,
            2.4,
            4.4,
            6.4,
            8.4,
            10.4,
            12.4,
            14.4,
            16.4,
            18.4,
            20.4,
            22.4,
            24.4,
            26.4,
            28.4,
            30.4,
        ]
    )
    expected_pz = np.array(
        [
            0.2,
            1.2,
            2.2,
            3.2,
            4.2,
            5.2,
            6.2,
            7.2,
            8.2,
            9.2,
            10.2,
            11.2,
            12.2,
            13.2,
            14.2,
            15.2,
        ]
    )
    expected_ix = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30])
    expected_iy = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30])
    expected_iz = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    expected_f_iy = np.array(
        [31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11, 9, 7, 5, 3, 1]
    )
    expected_m = np.array(
        [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    ).astype(bool)

    # Test
    assert expected_success == success, "Could not write all pixels in the image."
    assert np.allclose(expected_x, x), "Unexpected array y."
    assert np.allclose(expected_y, x), "Unexpected array y."
    assert np.allclose(expected_z, x), "Unexpected array y."
    assert expected_nx == nx, "Unexpected value for nx."
    assert expected_ny == ny, "Unexpected value for ny."
    assert expected_nz == nz, "Unexpected value for nZ."
    assert np.allclose(expected_px, px), "Unexpected array px."
    assert np.allclose(expected_py, py), "Unexpected array py."
    assert np.allclose(expected_pz, pz), "Unexpected array pz."
    assert np.allclose(expected_ix, ix), "Unexpected array ix."
    assert np.allclose(expected_iy, iy), "Unexpected array iy."
    assert np.allclose(expected_iz, iz), "Unexpected array iz."
    assert np.allclose(expected_f_iy, f_iy), "Unexpected array f_iy."
    assert np.allclose(expected_m, m), "Unexpected array y."

    #
    # Third resolution with kernel
    #

    # Resolution (nm)
    sx = 2.0
    sy = 2.0
    sz = 5.0

    # Kernel half-size
    L = 3

    # Get target image dimension
    nx = int(np.ceil((rx[1] - rx[0]) / sx))
    ny = int(np.ceil((ry[1] - ry[0]) / sy))
    nz = int(np.ceil((rz[1] - rz[0]) / sz))

    # Get position in pixels
    px = (x - rx[0]) / sx
    py = (y - ry[0]) / sy
    pz = (z - rz[0]) / sz

    # Convert absolute position to image indices
    ix = np.round(px).astype(int)
    iy = np.round(py).astype(int)
    iz = np.round(pz).astype(int)

    # Remove positions outside the image
    m = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (iz >= 0) & (iz < nz)
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Now apply the kernel filter (as a subsequent step to replicate the use in pymnflux.analysis)
    m = (
        (ix >= L)
        & (ix < nx - L)
        & (iy >= L)
        & (iy < ny - L)
        & (iz >= L)
        & (iz < nz - L)
    )
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Flip iy to have 0 at the top
    f_iy = ny - iy - 1

    # Try placing all entries in the image
    success = True
    h = np.zeros((nz, ny, nx), dtype=np.float32)
    for i in range(len(ix)):
        xi = ix[i]
        yi = f_iy[i]  # Images have y = 0 at the top
        zi = iz[i]
        try:
            h[zi, yi, xi] += 1
        except IndexError as _:
            success = False
            break

    # Expected values
    expected_success = True
    expected_x = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_y = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_z = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_nx = 40
    expected_ny = 40
    expected_nz = 16
    expected_px = np.array([8.0, 10.5, 13.0, 15.5, 18.0, 20.5, 23.0, 25.5, 28.0, 30.5])
    expected_py = np.array([8.0, 10.5, 13.0, 15.5, 18.0, 20.5, 23.0, 25.5, 28.0, 30.5])
    expected_pz = np.array([3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2])
    expected_ix = np.array([8, 10, 13, 16, 18, 20, 23, 26, 28, 30])
    expected_iy = np.array([8, 10, 13, 16, 18, 20, 23, 26, 28, 30])
    expected_iz = np.array([3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    expected_f_iy = np.array([31, 29, 26, 23, 21, 19, 16, 13, 11, 9])
    expected_m = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]).astype(bool)

    # Test
    assert expected_success == success, "Could not write all pixels in the image."
    assert np.allclose(expected_x, x), "Unexpected array y."
    assert np.allclose(expected_y, x), "Unexpected array y."
    assert np.allclose(expected_z, x), "Unexpected array y."
    assert expected_nx == nx, "Unexpected value for nx."
    assert expected_ny == ny, "Unexpected value for ny."
    assert expected_nz == nz, "Unexpected value for nZ."
    assert np.allclose(expected_px, px), "Unexpected array px."
    assert np.allclose(expected_py, py), "Unexpected array py."
    assert np.allclose(expected_pz, pz), "Unexpected array pz."
    assert np.allclose(expected_ix, ix), "Unexpected array ix."
    assert np.allclose(expected_iy, iy), "Unexpected array iy."
    assert np.allclose(expected_iz, iz), "Unexpected array iz."
    assert np.allclose(expected_f_iy, f_iy), "Unexpected array f_iy."
    assert np.allclose(expected_m, m), "Unexpected array y."

    #
    # Fourth resolution with kernel
    #

    # Resolution (nm)
    sx = 2.5
    sy = 2.5
    sz = 5.0

    # Kernel half-size
    L = 3

    # Get target image dimension
    nx = int(np.ceil((rx[1] - rx[0]) / sx))
    ny = int(np.ceil((ry[1] - ry[0]) / sy))
    nz = int(np.ceil((rz[1] - rz[0]) / sz))

    # Get position in pixels
    px = (x - rx[0]) / sx
    py = (y - ry[0]) / sy
    pz = (z - rz[0]) / sz

    # Convert absolute position to image indices
    ix = np.round(px).astype(int)
    iy = np.round(py).astype(int)
    iz = np.round(pz).astype(int)

    # Remove positions outside the image
    m = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny) & (iz >= 0) & (iz < nz)
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Now apply the kernel filter (as a subsequent step to replicate the use in pymnflux.analysis)
    m = (
        (ix >= L)
        & (ix < nx - L)
        & (iy >= L)
        & (iy < ny - L)
        & (iz >= L)
        & (iz < nz - L)
    )
    px = px[m]
    py = py[m]
    pz = pz[m]
    ix = ix[m]
    iy = iy[m]
    iz = iz[m]

    # Flip iy to have 0 at the top
    f_iy = ny - iy - 1

    # Try placing all entries in the image
    success = True
    h = np.zeros((nz, ny, nx), dtype=np.float32)
    for i in range(len(ix)):
        xi = ix[i]
        yi = f_iy[i]  # Images have y = 0 at the top
        zi = iz[i]
        try:
            h[zi, yi, xi] += 1
        except IndexError as _:
            success = False
            break

    # Expected values
    expected_success = True
    expected_x = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_y = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_z = np.array(
        [1, 6, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61, 66, 71, 76, 81, 86, 91, 96]
    )
    expected_nx = 32
    expected_ny = 32
    expected_nz = 16
    expected_px = np.array([6.4, 8.4, 10.4, 12.4, 14.4, 16.4, 18.4, 20.4, 22.4, 24.4])
    expected_py = np.array([6.4, 8.4, 10.4, 12.4, 14.4, 16.4, 18.4, 20.4, 22.4, 24.4])
    expected_pz = np.array([3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2])
    expected_ix = np.array([6, 8, 10, 12, 14, 16, 18, 20, 22, 24])
    expected_iy = np.array([6, 8, 10, 12, 14, 16, 18, 20, 22, 24])
    expected_iz = np.array([3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    expected_f_iy = np.array([25, 23, 21, 19, 17, 15, 13, 11, 9, 7])
    expected_m = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]).astype(bool)

    # Test
    assert expected_success == success, "Could not write all pixels in the image."
    assert np.allclose(expected_x, x), "Unexpected array y."
    assert np.allclose(expected_y, x), "Unexpected array y."
    assert np.allclose(expected_z, x), "Unexpected array y."
    assert expected_nx == nx, "Unexpected value for nx."
    assert expected_ny == ny, "Unexpected value for ny."
    assert expected_nz == nz, "Unexpected value for nZ."
    assert np.allclose(expected_px, px), "Unexpected array px."
    assert np.allclose(expected_py, py), "Unexpected array py."
    assert np.allclose(expected_pz, pz), "Unexpected array pz."
    assert np.allclose(expected_ix, ix), "Unexpected array ix."
    assert np.allclose(expected_iy, iy), "Unexpected array iy."
    assert np.allclose(expected_iz, iz), "Unexpected array iz."
    assert np.allclose(expected_f_iy, f_iy), "Unexpected array f_iy."
    assert np.allclose(expected_m, m), "Unexpected array y."
