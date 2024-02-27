#  Copyright (c) 2022 - 2024 D-BSSE, ETH Zurich.
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

from pathlib import Path
from pickle import UnpicklingError
from typing import Union

import h5py
import numpy as np
import pandas as pd

from pyminflux.reader import NativeArrayReader
from pyminflux.reader.util import (
    migrate_npy_array,
    convert_from_mat,
    find_last_valid_iteration,
)


class MinFluxReader:
    __docs__ = "Reader of MINFLUX data in `.pmx`, `.npy` or `.mat` formats."

    __slots__ = [
        "_filename",
        "_valid",
        "_unit_scaling_factor",
        "_data_array",
        "_data_df",
        "_data_full_df",
        "_valid_entries",
        "_is_3d",
        "_is_aggregated",
        "_is_tracking",
        "_reps",
        "_efo_index",
        "_cfr_index",
        "_eco_index",
        "_dcr_index",
        "_loc_index",
        "_tid_index",
        "_tim_index",
        "_vld_index",
        "_z_scaling_factor",
    ]

    def __init__(
        self,
        filename: Union[Path, str],
        valid: bool = True,
        z_scaling_factor: float = 1.0,
        is_tracking: bool = False,
    ):
        """Constructor.

        Parameters
        ----------

        filename: Union[Path, str]
            Full path to the `.pmx`, `.npy` or `.mat` file to read

        valid: bool (optional, default = True)
            Whether to load only valid localizations.

        z_scaling_factor: float (optional, default = 1.0)
            Refractive index mismatch correction factor to apply to the z coordinates.

        is_tracking: bool (optional, default = False)
            Whether the dataset comes from a tracking experiment; otherwise, it is considered as a
            localization experiment.
        """

        # Store the filename
        self._filename: Path = Path(filename)
        if not self._filename.is_file():
            raise IOError(f"The file {self._filename} does not seem to exist.")

        # Store the valid flag
        self._valid: bool = valid

        # The localizations are stored in meters in the Imspector files and by
        # design also in the `.pmx` format. Here, we scale them to be in nm
        self._unit_scaling_factor: float = 1e9

        # Store the z correction factor
        self._z_scaling_factor: float = z_scaling_factor

        # Initialize the data
        self._data_array = None
        self._data_df = None
        self._data_full_df = None
        self._valid_entries = None

        # Whether the acquisition is 2D or 3D
        self._is_3d: bool = False

        # Whether the acquisition is a tracking dataset
        self._is_tracking: bool = is_tracking

        # Whether the file contains aggregate measurements
        self._is_aggregated: bool = False

        # Indices dependent on 2D or 3D acquisition and whether the
        # data comes from a localization or a tracking experiment.
        self._reps: int = -1
        self._efo_index: int = -1
        self._cfr_index: int = -1
        self._dcr_index: int = -1
        self._eco_index: int = -1
        self._loc_index: int = -1

        # Constant indices
        self._tid_index: int = 0
        self._tim_index: int = 0
        self._vld_index: int = 0

        # Load the file
        self._load()

    @property
    def z_scaling_factor(self) -> float:
        """Returns the scaling factor for the z coordinates."""
        return self._z_scaling_factor

    @property
    def is_3d(self) -> bool:
        """Returns True is the acquisition is 3D, False otherwise."""
        return self._is_3d

    @property
    def is_aggregated(self) -> bool:
        """Returns True is the acquisition is aggregated, False otherwise."""
        return self._is_aggregated

    @property
    def is_tracking(self) -> bool:
        """Returns True for a tracking acquisition, False otherwise."""
        return self._is_tracking

    @property
    def num_valid_entries(self) -> int:
        """Number of valid entries."""
        if self._data_array is None:
            return 0
        return self._valid_entries.sum()

    @property
    def num_invalid_entries(self) -> int:
        """Number of valid entries."""
        if self._data_array is None:
            return 0
        return np.logical_not(self._valid_entries).sum()

    @property
    def valid_raw_data(self) -> Union[None, np.ndarray]:
        """Return the raw data."""
        if self._data_array is None:
            return None
        return self._data_array[self._valid_entries].copy()

    @property
    def processed_dataframe(self) -> Union[None, pd.DataFrame]:
        """Return the raw data as dataframe (some properties only)."""
        if self._data_df is not None:
            return self._data_df

        self._data_df = self._process()
        return self._data_df

    @property
    def raw_data_dataframe(self) -> Union[None, pd.DataFrame]:
        """Return the raw data as dataframe (some properties only)."""
        if self._data_full_df is not None:
            return self._data_full_df
        self._data_full_df = self._raw_data_to_full_dataframe()
        return self._data_full_df

    @property
    def filename(self) -> Union[Path, None]:
        """Return the filename if set."""
        if self._filename is None:
            return None
        return Path(self._filename)

    @classmethod
    def processed_properties(cls) -> list:
        """Returns the properties read from the file that correspond to the processed dataframe column names."""
        return [
            "tid",
            "tim",
            "x",
            "y",
            "z",
            "efo",
            "cfr",
            "eco",
            "dcr",
            "dwell",
            "fluo",
        ]

    @classmethod
    def raw_properties(cls) -> list:
        """Returns the properties read from the file and dynamic that correspond to the raw dataframe column names."""
        return ["tid", "aid", "vld", "tim", "x", "y", "z", "efo", "cfr", "eco", "dcr"]

    def _load(self) -> bool:
        """Load the file."""

        if not self._filename.is_file():
            print(f"File {self._filename} does not exist.")
            return False

        # Call the specialized _load_*() function
        if self._filename.name.lower().endswith(".npy"):
            try:
                data_array = np.load(str(self._filename))
                if "fluo" in data_array.dtype.names:
                    self._data_array = data_array
                else:
                    self._data_array = migrate_npy_array(data_array)
            except (
                OSError,
                UnpicklingError,
                ValueError,
                EOFError,
                FileNotFoundError,
            ) as e:
                print(f"Could not open {self._filename}: {e}")
                return False

        elif self._filename.name.lower().endswith(".mat"):
            try:
                self._data_array = convert_from_mat(self._filename)
            except Exception as e:
                print(f"Could not open {self._filename}: {e}")
                return False

        elif self._filename.name.lower().endswith(".pmx"):
            try:
                self._data_array = NativeArrayReader().read(self._filename)
                if self._data_array is None:
                    print(f"Could not open {self._filename}.")
                    return False
            except Exception as e:
                print(f"Could not open {self._filename}: {e}")
                return False

        else:
            print(f"Unexpected file {self._filename}.")
            return False

        # Store a logical array with the valid entries
        self._valid_entries = self._data_array["vld"]

        # Cache whether the data is 2D or 3D and whether is aggregated
        # The cases are different for localization vs. tracking experiments
        # num_locs = self._data_array["itr"].shape[1]
        self._is_3d = (
            float(np.nanmean(self._data_array["itr"][:, -1]["loc"][:, -1])) != 0.0
        )

        # Set all relevant indices
        self._set_all_indices()

        # Return success
        return True

    def _read_from_pmx(self) -> Union[np.ndarray, None]:
        """Load the PMX file."""

        # Open the file and read the data
        with h5py.File(self._filename, "r") as f:
            # Read the file_version attribute
            file_version = f.attrs["file_version"]

            if file_version != "1.0":
                return False

            # We only read the raw NumPy array
            data_array = f["raw/npy"][:]

        return data_array

    def _process(self) -> Union[None, pd.DataFrame]:
        """Returns processed dataframe for valid (or invalid) entries.

        Returns
        -------

        df: pd.DataFrame
            Processed data as DataFrame.
        """

        # Do we have a data array to work on?
        if self._data_array is None:
            return None

        if self._valid:
            indices = self._valid_entries
        else:
            indices = np.logical_not(self._valid_entries)

        # Extract the valid iterations
        itr = self._data_array["itr"][indices]

        # Extract the valid identifiers
        tid = self._data_array["tid"][indices]

        # Extract the valid time points
        tim = self._data_array["tim"][indices]

        # Extract the fluorophore IDs
        fluo = self._data_array["fluo"][indices]
        if np.all(fluo) == 0:
            fluo = np.ones(fluo.shape, dtype=fluo.dtype)

        # The following extraction pattern will change whether the
        # acquisition is normal or aggregated
        if self.is_aggregated:
            # Extract the locations
            loc = itr["loc"].squeeze() * self._unit_scaling_factor
            loc[:, 2] = loc[:, 2] * self._z_scaling_factor

            # Extract EFO
            efo = itr["efo"]

            # Extract CFR
            cfr = itr["cfr"]

            # Extract ECO
            eco = itr["eco"]

            # Extract DCR
            dcr = itr["dcr"]

            # Dwell
            dwell = np.around(eco / (efo / 1000.0), decimals=0)

        else:
            # Extract the locations
            loc = itr[:, self._loc_index]["loc"] * self._unit_scaling_factor
            loc[:, 2] = loc[:, 2] * self._z_scaling_factor

            # Extract EFO
            efo = itr[:, self._efo_index]["efo"]

            # Extract CFR
            cfr = itr[:, self._cfr_index]["cfr"]

            # Extract ECO
            eco = itr[:, self._eco_index]["eco"]

            # Extract DCR
            dcr = itr[:, self._dcr_index]["dcr"]

            # Calculate dwell
            dwell = np.around(eco / (efo / 1000.0), decimals=0)

        # Create a Pandas dataframe for the results
        df = pd.DataFrame(
            index=pd.RangeIndex(start=0, stop=len(tid)),
            columns=MinFluxReader.processed_properties(),
        )

        # Store the extracted valid hits into the dataframe
        df["tid"] = tid
        df["x"] = loc[:, 0]
        df["y"] = loc[:, 1]
        df["z"] = loc[:, 2]
        df["tim"] = tim
        df["efo"] = efo
        df["cfr"] = cfr
        df["eco"] = eco
        df["dcr"] = dcr
        df["dwell"] = dwell
        df["fluo"] = fluo

        return df

    def _raw_data_to_full_dataframe(self) -> Union[None, pd.DataFrame]:
        """Return raw data arranged into a dataframe."""
        if self._data_array is None:
            return None

        # Intialize output dataframe
        df = pd.DataFrame(columns=MinFluxReader.raw_properties())

        # Allocate space for the columns
        n_rows = len(self._data_array) * self._reps

        # Get all unique TIDs and their counts
        _, tid_counts = np.unique(self._data_array["tid"], return_counts=True)

        # Get all tids (repeated over the repetitions)
        tid = np.repeat(self._data_array["tid"], self._reps)

        # Create virtual IDs to mark the measurements of repeated tids
        # @TODO Optimize this!
        aid = np.zeros((n_rows, 1), dtype=np.int32)
        index = 0
        for c in np.nditer(tid_counts):
            tmp = np.repeat(np.arange(c), self._reps)
            n = len(tmp)
            aid[index : index + n, 0] = tmp
            index += n

        # Get all valid flags (repeated over the repetitions)
        vld = np.repeat(self._data_array["vld"], self._reps)

        # Get all timepoints (repeated over the repetitions)
        tim = np.repeat(self._data_array["tim"], self._reps)

        # Get all localizations (reshaped to drop the first dimension)
        loc = (
            self._data_array["itr"]["loc"].reshape((n_rows, 3))
            * self._unit_scaling_factor
        )
        loc[:, 2] = loc[:, 2] * self._z_scaling_factor

        # Get all efos (reshaped to drop the first dimension)
        efo = self._data_array["itr"]["efo"].reshape((n_rows, 1))

        # Get all cfrs (reshaped to drop the first dimension)
        cfr = self._data_array["itr"]["cfr"].reshape((n_rows, 1))

        # Get all ecos (reshaped to drop the first dimension)
        eco = self._data_array["itr"]["eco"].reshape((n_rows, 1))

        # Get all dcrs (reshaped to drop the first dimension)
        dcr = self._data_array["itr"]["dcr"].reshape((n_rows, 1))

        # Build the dataframe
        df["tid"] = tid.astype(np.int32)
        df["aid"] = aid.astype(np.int32)
        df["vld"] = vld
        df["tim"] = tim
        df["x"] = loc[:, 0]
        df["y"] = loc[:, 1]
        df["z"] = loc[:, 2]
        df["efo"] = efo
        df["cfr"] = cfr
        df["eco"] = eco
        df["dcr"] = dcr

        return df

    def _set_all_indices(self):
        """Set indices of properties to be read."""
        if self._data_array is None:
            return False

        # Number of iterations
        self._reps = self._data_array["itr"].shape[1]

        # Is this an aggregated acquisition?
        if self._reps == 1:
            self._is_aggregated = True
        else:
            self._is_aggregated = False

        # Query the data to find the last valid iteration
        # for all measurements
        last_valid = find_last_valid_iteration(self._data_array)

        # Set the extracted indices
        self._efo_index = last_valid["efo_index"]
        self._cfr_index = last_valid["cfr_index"]
        self._dcr_index = last_valid["dcr_index"]
        self._eco_index = last_valid["eco_index"]
        self._loc_index = last_valid["loc_index"]

        # Inform the user (temporary debug info)
        print(f"Selected iterations: efo: {self._efo_index}, cfr: {self._cfr_index}, dcr: {self._dcr_index}, eco: {self._eco_index}, loc: {self._loc_index}")

        # if self.is_aggregated:
        #     self._efo_index = -1  # Not used
        #     self._cfr_index = -1  # Not used
        #     self._dcr_index = -1  # Not used
        #     self._eco_index = -1  # Not used
        #     self._loc_index = -1  # Not used
        # else:
        #     if self._is_tracking:
        #         # Tracking experiment
        #         if self.is_3d:
        #             self._efo_index = 4
        #             self._cfr_index = 4
        #             self._dcr_index = 4
        #             self._eco_index = 4
        #             self._loc_index = 4
        #         else:
        #             self._efo_index = 3
        #             self._cfr_index = 3
        #             self._dcr_index = 3
        #             self._eco_index = 3
        #             self._loc_index = 3
        #     else:
        #         # Localization experiment
        #         if self.is_3d:
        #             self._efo_index = 9
        #             self._cfr_index = 6
        #             self._dcr_index = 9
        #             self._eco_index = 9
        #             self._loc_index = 9
        #         else:
        #             self._efo_index = 4
        #             self._cfr_index = 4
        #             self._dcr_index = 4
        #             self._eco_index = 4
        #             self._loc_index = 4

    def __repr__(self) -> str:
        """String representation of the object."""
        if self._data_array is None:
            return "No file loaded."

        str_valid = (
            "all valid"
            if len(self._data_array) == self.num_valid_entries
            else f"{self.num_valid_entries} valid and {self.num_invalid_entries} non valid"
        )

        str_acq = "3D" if self.is_3d else "2D"
        aggr_str = "aggregated" if self.is_aggregated else "normal"

        return (
            f"File: {self._filename.name}: "
            f"{str_acq} {aggr_str} acquisition with {len(self._data_array)} entries ({str_valid})."
        )

    def __str__(self) -> str:
        """Human-friendly representation of the object."""
        return self.__repr__()
