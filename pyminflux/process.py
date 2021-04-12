import numpy as np
import pandas as pd
from pathlib import Path
from typing import Union


def get_colors_for_unique_ids(ids: Union[pd.Series, np.ndarray]) -> np.ndarray:
    """Return an Nx3 matrix of RGB colors in the range 0.0 ... 1.0 for all unique ids in `ids`

    @param ids: Union[pd.Series, np.ndarray]
        Series or array of ids, that may contain reperitions.

    @return np.ndarray
        Nx3 matrix of RGB colors in the range 0.0 ... 1.0.
    """

    # Get the list of unique IDs
    u_ids = np.unique(ids)

    # Allocate the matrix of colors
    colors = np.zeros((len(ids), 3), dtype=np.float64)

    for id in u_ids:
        i = np.where(ids == id)
        colors[i, 0] = np.random.rand(1)
        colors[i, 1] = np.random.rand(1)
        colors[i, 2] = np.random.rand(1)

    return colors


def process_minflux_file(filename: Union[Path, str], verbose: bool = False) -> Union[pd.DataFrame, None]:
    """Load the MINFLUX .npy file and extract the valid hits.

    @param filename: Union[Path, str]
        Full path of the .npy file to process.

    @param verbose: bool (Optional, default: False)
        Set to True to display verbose information. Otherwise, the function is silent.

    @return Union[pd.DataFrame, None]
        Pandas dataframe with id, x, y, z coordinates, and timepoint of all valid hits; or None if the file could not be processed.
    """

    if verbose:
        print(f"Reading file: {filename}")

    # Load the .npy file
    try:
        npy_array = np.load(filename)
    except:
        return None

    # Number of entries to process
    n_entries = len(npy_array)

    # Get the valid entries
    valid = npy_array["vld"]

    # Count the valid entries
    n_valid = np.sum(valid)

    if verbose:
        print(f"Found {n_valid} valid hits from a total of {n_entries} entries.")

    # Extract the valid time points
    tim = npy_array["tim"][valid]

    # Extract the locations for the valid iterations
    itr = npy_array["itr"][valid]
    loc = itr[:, itr.shape[1] - 1]["loc"]

    # Extract the valid identifiers
    tid = npy_array["tid"][valid]

    # Create a Pandas dataframe for the results
    hits_df = pd.DataFrame(
        index=pd.RangeIndex(start=0, stop=n_valid),
        columns=["tid", "x", "y", "z", "tim"]
    )

    # Store the extracted valid hits into the dataframe
    hits_df["tid"] = tid
    hits_df["x"] = loc[:, 0] * 1e9
    hits_df["y"] = loc[:, 1] * 1e9
    hits_df["z"] = loc[:, 2] * 1e9
    hits_df["tim"] = tim

    if verbose:
        print(f"Number of unique IDs: {len(np.unique(tid))}")

    return hits_df
