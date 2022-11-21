from typing import Optional, Tuple

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QFont, QPen, Qt
from PySide6.QtWidgets import QDialog

from ..analysis import get_robust_threshold, ideal_hist_bins
from ..reader import MinFluxReader
from ..state import State
from .ui_histogram_viewer import Ui_HistogramViewer


class HistogramViewer(QDialog, Ui_HistogramViewer):
    def __init__(self, parent=None):
        """Constructor."""

        # Call the base class
        super().__init__(parent=parent)

        # Initialize the dialog
        self.ui = Ui_HistogramViewer()
        self.ui.setupUi(self)

        # Keep references to the plots
        self.efo_plot = None
        self.cfr_plot = None
        self.sx_plot = None
        self.sy_plot = None
        self.sz_plot = None

        # Keep a reference to the singleton State class
        self.state = State()

        # Set signal-slot connections
        self.setup_conn()

        # Update fields
        self.ui.cbEnableFiltering.setChecked(self.state.filter)
        self.ui.cbEnableEFOFiltering.setChecked(self.state.filter_efo)
        self.ui.cbEnableCFRFiltering.setChecked(self.state.filter_cfr)
        self.ui.cbEnableEFOFiltering.setEnabled(self.state.filter)
        self.ui.cbEnableEFOFiltering.setEnabled(self.state.filter)

    def setup_conn(self):
        """Set up signal-slot connections."""
        self.ui.cbEnableFiltering.stateChanged.connect(self.persist_filtering_state)
        self.ui.cbEnableEFOFiltering.stateChanged.connect(
            self.persist_efo_filtering_state
        )
        self.ui.cbEnableCFRFiltering.stateChanged.connect(
            self.persist_cfr_filtering_state
        )

    @Slot(int, name="persist_filtering_state")
    def persist_filtering_state(self, state):
        self.state.filter = state != 0
        self.ui.cbEnableEFOFiltering.setEnabled(self.state.filter)
        self.ui.cbEnableCFRFiltering.setEnabled(self.state.filter)

    @Slot(int, name="persist_efo_filtering_state")
    def persist_efo_filtering_state(self, state):
        self.state.filter_efo = state != 0

    @Slot(int, name="persist_cfr_filtering_state")
    def persist_cfr_filtering_state(self, state):
        self.state.filter_cfr = state != 0

    def plot(self, minfluxreader: MinFluxReader):
        """Plot histograms."""

        # Make sure there is data to plot
        if minfluxreader is None:
            return

        if minfluxreader.processed_dataframe is None:
            return

        #
        # Get "efo" and "cfr" measurements, and "sx", "sy" and "sz" localization jitter
        #

        # "efo"
        n_efo, efo_bin_edges, efo_bin_centers, efo_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe["efo"].values
        )
        if self.state.efo_thresholds is None:
            thresh_efo = self.calculate_upper_threshold(
                minfluxreader.processed_dataframe["efo"].values,
                thresh_factor=self.state.filter_thresh_factor,
            )
            self.state.efo_thresholds = (efo_bin_edges[0], thresh_efo)

        self.efo_plot = self._create_plot(
            n_efo,
            efo_bin_edges,
            efo_bin_centers,
            efo_bin_width,
            title="EFO",
            brush="b",
            fmt="{value:.0f}",
            support_thresholding=True,
            thresholds=self.state.efo_thresholds,
        )
        self.ui.parameters_layout.addWidget(self.efo_plot)
        self.efo_plot.show()

        # cfr
        n_cfr, cfr_bin_edges, cfr_bin_centers, cfr_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe["cfr"].values
        )
        if self.state.cfr_thresholds is None:
            thresh_cfr = self.calculate_upper_threshold(
                minfluxreader.processed_dataframe["cfr"].values,
                thresh_factor=self.state.filter_thresh_factor,
            )
            self.state.cfr_thresholds = (cfr_bin_edges[0], thresh_cfr)

        self.cfr_plot = self._create_plot(
            n_cfr,
            cfr_bin_edges,
            cfr_bin_centers,
            cfr_bin_width,
            title="CFR",
            brush="r",
            fmt="{value:.2f}",
            support_thresholding=True,
            thresholds=self.state.cfr_thresholds,
        )
        self.ui.parameters_layout.addWidget(self.cfr_plot)
        self.cfr_plot.show()

        # sx
        n_sx, sx_bin_edges, sx_bin_centers, sx_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe_stats["sx"].values
        )
        self.sx_plot = self._create_plot(
            n_sx,
            sx_bin_edges,
            sx_bin_centers,
            sx_bin_width,
            title="SX",
            brush="k",
            support_thresholding=False,
        )
        self.ui.localizations_layout.addWidget(self.sx_plot)
        self.sx_plot.show()

        # sy
        n_sy, sy_bin_edges, sy_bin_centers, sy_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe_stats["sy"].values
        )
        self.sy_plot = self._create_plot(
            n_sy,
            sy_bin_edges,
            sy_bin_centers,
            sy_bin_width,
            title="SY",
            brush="k",
            support_thresholding=False,
        )
        self.ui.localizations_layout.addWidget(self.sy_plot)
        self.sy_plot.show()

        # sz
        if minfluxreader.is_3d:
            n_sz, sz_bin_edges, sz_bin_centers, sz_bin_width = self._prepare_histogram(
                minfluxreader.processed_dataframe_stats["sz"].values
            )
            self.sz_plot = self._create_plot(
                n_sz,
                sz_bin_edges,
                sz_bin_centers,
                sz_bin_width,
                title="SZ",
                brush="k",
                support_thresholding=False,
            )
            self.ui.localizations_layout.addWidget(self.sz_plot)
            self.sz_plot.show()

    def _prepare_histogram(self, values):
        """Prepare data to plot."""
        bin_edges, bin_centers, bin_width = ideal_hist_bins(values, scott=False)
        n, _ = np.histogram(values, bins=bin_edges, density=False)
        n = n / n.sum()
        return n, bin_edges, bin_centers, bin_width

    def _create_plot(
        self,
        n: np.ndarray,
        bin_edges: np.ndarray,
        bin_centers: np.ndarray,
        bin_width: np.ndarray,
        *,
        title: str = "",
        brush: str = "b",
        fmt: str = "{value:0.2f}",
        support_thresholding: bool = False,
        thresholds: Optional[Tuple] = None,
    ):
        """Create a plot and return it to be added to the layout."""

        # Check for consistency
        if support_thresholding and thresholds is None:
            raise ValueError(
                "If 'support_thresholding' is True, 'thresholds' must be a tuple with two values."
            )
        if thresholds is not None and len(thresholds) != 2:
            raise ValueError(
                "If 'support_thresholding' is True, 'thresholds' must be a tuple with two values."
            )

        chart = pg.BarGraphItem(
            x=bin_centers, height=n, width=0.9 * bin_width, brush=brush
        )
        plot = pg.PlotWidget(parent=self, background="w", title=title)
        padding = 1.0 * (bin_edges[1] - bin_edges[0])
        plot.setXRange(
            bin_edges[0] - padding, bin_edges[-1] + padding, padding=0.0
        )  # setXRange()'s padding misbehaves
        plot.setYRange(0.0, n.max())
        plot.addItem(chart)

        if support_thresholding:

            # Create a linear region for setting filtering thresholds
            region = pg.LinearRegionItem(
                values=[thresholds[0], thresholds[1]], pen={"color": "k", "width": 3}
            )

            # Mark region with data label for callbacks
            region.data_label = title.lower()

            # Add to plot
            plot.addItem(region)

            # Add labels with current values of lower and upper thresholds
            low_thresh_label = pg.InfLineLabel(region.lines[0], fmt, position=0.95)
            self._change_region_label_font(low_thresh_label)
            high_thresh_label = pg.InfLineLabel(region.lines[1], fmt, position=0.95)
            self._change_region_label_font(high_thresh_label)

            # Connect signals
            region.sigRegionChanged.connect(self.region_pos_changed)
            region.sigRegionChangeFinished.connect(self.region_pos_changed_finished)

        # Customize the context menu
        self.customize_context_menu(plot)

        return plot

    def calculate_upper_threshold(self, values, thresh_factor):
        """Prepare filter line."""

        # Calculate robust threshold
        threshold_valid_cfr, _, _ = get_robust_threshold(values, factor=thresh_factor)

        # Return it
        return threshold_valid_cfr

    def customize_context_menu(self, item):
        """Remove some of the default context menu actions.

        See: https://stackoverflow.com/questions/44402399/how-to-disable-the-default-context-menu-of-pyqtgraph#44420152
        """
        # Disable some actions
        viewbox = item.getPlotItem().getViewBox()
        actions = viewbox.menu.actions()
        for action in actions:
            action.setVisible(False)

        # Hide the "Plot Options" menu
        item.getPlotItem().ctrlMenu.menuAction().setVisible(False)

    def region_pos_changed(self, item):
        pass

    def region_pos_changed_finished(self, item):
        if item.data_label == "efo":
            self.state.efo_thresholds = item.getRegion()
        elif item.data_label == "cfr":
            self.state.cfr_thresholds = item.getRegion()
        else:
            raise ValueError(f"Unexpected data label {item.data_label}.")

    def _change_region_label_font(self, region_label):
        """Change the region label font style."""
        text_item = region_label.textItem
        text_item.setDefaultTextColor(QColor("black"))
        font = text_item.font()
        font.setWeight(QFont.Bold)
        font.setPointSize(20)
