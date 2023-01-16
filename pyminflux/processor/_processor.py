from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.mixture import BayesianGaussianMixture, GaussianMixture

from pyminflux.analysis._analysis import select_by_bgmm_fitting
from pyminflux.reader import MinFluxReader
from pyminflux.state import State


class MinFluxProcessor:
    """Processor of MINFLUX data."""

    __slots__ = [
        "__minfluxreader",
        "state",
        "__filtered_dataframe",
        "__filtered_stats_dataframe",
        "__stats_to_be_recomputed",
    ]

    def __init__(self, minfluxreader: MinFluxReader):
        """Constructor.

        Parameters
        ----------

        minfluxreader: pyminflux.reader.MinFluxReader
            MinFluxReader object.
        """

        # Store a reference to the MinFluxReader
        self.__minfluxreader = minfluxreader

        # Keep a reference to the state machine
        self.state = State()

        # Cache the filtered dataframes
        self.__filtered_dataframe = None
        self.__filtered_stats_dataframe = None

        # Keep track whether the statistics need to be recomputed
        self.__stats_to_be_recomputed = False

        # Apply the global filters
        self._apply_global_filters()

    @property
    def is_3d(self) -> bool:
        """Return True if the acquisition is 3D.

        Returns
        -------

        is_3d: bool
            True if the acquisition is 3D, False otherwise.
        """
        return self.__minfluxreader.is_3d

    @property
    def num_values(self) -> int:
        """Return the number of values in the (filtered) dataframe.

        Returns
        -------

        n: int
            Number of values in the dataframe after all filters have been applied.
        """
        if self.__filtered_dataframe is not None:
            return len(self.__filtered_dataframe.index)

        if self.__minfluxreader.processed_dataframe is not None:
            return len(self.__minfluxreader.processed_dataframe.index)

        return 0

    @property
    def filtered_dataframe(self) -> Union[None, pd.DataFrame]:
        """Return dataframe with all filters applied.

        Returns
        -------

        filtered_dataframe: Union[None, pd.DataFrame]
            A Pandas dataframe or None if no file was loaded.
        """
        return self.__filtered_dataframe

    @property
    def filtered_dataframe_stats(self) -> Union[None, pd.DataFrame]:
        """Return dataframe stats with all filters applied.

        Returns
        -------

        filtered_dataframe_stats: Union[None, pd.DataFrame]
            A Pandas dataframe with all data statistics or None if no file was loaded.
        """
        if self.__stats_to_be_recomputed:
            self._calculate_statistics()
        return self.__filtered_stats_dataframe

    @classmethod
    def processed_properties(self):
        """Return the processed dataframe columns."""
        return MinFluxReader.processed_properties()

    def reset(self):
        """Drops all dynamic filters and resets the data to the processed data frame with global filters."""
        self.__filtered_dataframe = None
        self._apply_global_filters()

    def get_filtered_dataframe_subset_by_indices(
        self, indices
    ) -> Union[None, pd.DataFrame]:
        """Return view on a subset of the filtered dataset defined by the passed indices.

        The underlying dataframe is not modified.

        Returns
        -------

        subset: Union[None, pd.DataFrame]
            A view on a subset of the dataframe defined by the passed indices, or None if no file was loaded.
        """
        if self.__filtered_dataframe is None:
            return None
        return self.__filtered_dataframe.iloc[indices]

    def get_filtered_dataframe_subset_by_xy_range(
        self, x_range, y_range
    ) -> Union[None, pd.DataFrame]:
        """Return a view on a subset of the filtered dataset defined by the passed x and y ranges.

        The underlying dataframe is not modified.

        Returns
        -------

        subset: Union[None, pd.DataFrame]
            A view on a subset of the dataframe defined by the passed x and y ranges, or None if no file was loaded.
        """

        # Make sure that the ranges are increasing
        x_min = x_range[0]
        x_max = x_range[1]
        if x_max < x_min:
            x_max, x_min = x_min, x_max

        y_min = y_range[0]
        y_max = y_range[1]
        if y_max < y_min:
            y_max, y_min = y_min, y_max

        return self.__filtered_dataframe.loc[
            (self.__filtered_dataframe["x"] >= x_min)
            & (self.__filtered_dataframe["x"] < x_max)
            & (self.__filtered_dataframe["y"] >= y_min)
            & (self.__filtered_dataframe["y"] < y_max)
        ]

    def _apply_global_filters(self):
        """Apply filters that are defined in the global application configuration."""

        # Start from the filtered dataframe if it already exists,
        # otherwise from the processed_dataframe
        if self.__filtered_dataframe is not None:
            df = self.__filtered_dataframe.copy()
        else:
            df = self.__minfluxreader.processed_dataframe.copy()

        # Remove all rows where the count of TIDs is lower than self._min_trace_num
        counts = df["tid"].value_counts(normalize=False)
        df = df.loc[
            df["tid"].isin(counts[counts >= self.state.min_num_loc_per_trace].index), :
        ]

        # Update the filtered dataframe
        self.__filtered_dataframe = df

        # Make sure to flag the statistics to be recomputed
        self.__stats_to_be_recomputed = True

    def apply_range_filter(
        self,
        prop: str,
        min_threshold: Union[int, float],
        max_threshold: Union[int, float],
    ):
        """Apply min and max thresholding to the given property.

        Parameters
        ----------

        prop: str
            Name of the property (dataframe column) to filter.

        min_threshold: Union[int, float]
            Minimum value for prop to retain the row.

        max_threshold: Union[int, float]
            Maximum value for prop to retain the row.
        """

        # Make sure we have valid thresholds
        if min_threshold is None or max_threshold is None:
            return

        # Make sure to always apply the global filters
        self._apply_global_filters()

        # Now we are guaranteed to have a filtered dataframe to work with
        df = self.__filtered_dataframe.copy()

        # Apply filter
        df = df[(df[prop] > min_threshold) & (df[prop] < max_threshold)]

        # Cache the result
        self.__filtered_dataframe = df

        # Make sure to flag the statistics to be recomputed
        self.__stats_to_be_recomputed = True

    def _calculate_statistics(self):
        """Calculate per-trace statistics."""

        # Make sure we have processed dataframe to work on
        if self.__filtered_dataframe is None:
            return

        # Only recompute statistics if needed
        if not self.__stats_to_be_recomputed:
            return

        # Calculate some statistics per TID on the processed dataframe
        df_grouped = self.__filtered_dataframe.groupby("tid")

        tid = df_grouped["tid"].first().values
        n = df_grouped["tid"].count().values
        mx = df_grouped["x"].mean().values
        my = df_grouped["y"].mean().values
        mz = df_grouped["z"].mean().values
        sx = df_grouped["x"].std().values
        sy = df_grouped["y"].std().values
        sz = df_grouped["z"].std().values

        # Prepare a dataframe with the statistics
        df_tid = pd.DataFrame(columns=["tid", "n", "mx", "my", "mz", "sx", "sy", "sz"])

        df_tid["tid"] = tid
        df_tid["n"] = n
        df_tid["mx"] = mx
        df_tid["my"] = my
        df_tid["mz"] = mz
        df_tid["sx"] = sx
        df_tid["sy"] = sy
        df_tid["sz"] = sz

        # sx, sy sz columns will contain np.nan is n == 1: we replace with 0.0
        # @TODO: should this be changed?
        df_tid[["sx", "sy", "sz"]] = df_tid[["sx", "sy", "sz"]].fillna(value=0.0)

        # Store the results
        self.__filtered_stats_dataframe = df_tid

        # Flag the statistics to be computed
        self.__stats_to_be_recomputed = False
