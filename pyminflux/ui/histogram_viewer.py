from typing import Optional, Tuple

import numpy as np
import pyqtgraph as pg
from pyqtgraph import ROI, Point
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QColor, QDoubleValidator, QFont
from PySide6.QtWidgets import QDialog

from ..analysis import get_robust_threshold, ideal_hist_bins
from ..reader import MinFluxReader
from ..state import State
from .ui_histogram_viewer import Ui_HistogramViewer


class HistogramViewer(QDialog, Ui_HistogramViewer):

    # Signal that the data viewers should be updated
    data_filters_changed = Signal(name="data_filters_changed")

    def __init__(self, minfluxreader: MinFluxReader, parent=None):
        """Constructor."""

        # Call the base class
        super().__init__(parent=parent)

        # Initialize the dialog
        self.ui = Ui_HistogramViewer()
        self.ui.setupUi(self)

        # Store the reference to the reader
        self.minfluxreader = minfluxreader

        # Keep references to the plots
        self.efo_plot = None
        self.cfr_plot = None
        self.sx_plot = None
        self.sy_plot = None
        self.sz_plot = None
        self.cfr_efo_plot = None
        self.efo_region = None
        self.cfr_region = None
        self.efo_cfr_roi = None

        # Keep a reference to the singleton State class
        self.state = State()

        # Set defaults
        self.ui.checkLowerThreshold.setChecked(self.state.enable_lower_threshold)
        self.ui.checkUpperThreshold.setChecked(self.state.enable_upper_threshold)
        self.ui.leThreshFactor.setText(str(self.state.filter_thresh_factor))
        self.ui.leThreshFactor.setValidator(
            QDoubleValidator(bottom=0.0, top=5.0, decimals=2)
        )

        # Update fields (before we connect signals and slots)
        self.ui.cbEnableEFOFiltering.setChecked(self.state.enable_filter_efo)
        self.ui.cbEnableCFRFiltering.setChecked(self.state.enable_filter_cfr)

        # Set signal-slot connections
        self.setup_conn()

    def setup_conn(self):
        """Set up signal-slot connections."""
        self.ui.pbAutoThreshold.clicked.connect(self.run_auto_threshold)
        self.ui.cbEnableEFOFiltering.stateChanged.connect(
            self.persist_efo_filtering_state
        )
        self.ui.cbEnableCFRFiltering.stateChanged.connect(
            self.persist_cfr_filtering_state
        )
        self.ui.pbUpdateViewers.clicked.connect(self.broadcast_viewers_update)
        self.ui.checkLowerThreshold.stateChanged.connect(self.persist_lower_threshold)
        self.ui.checkUpperThreshold.stateChanged.connect(self.persist_upper_threshold)
        self.ui.leThreshFactor.textChanged.connect(self.persist_thresh_factor)

    @Slot(name="run_auto_threshold")
    def run_auto_threshold(self):
        """Run auto-threshold on EFO and CFR values and update the plots."""

        # Is there something to calculate?
        if (
            not self.state.enable_lower_threshold
            and not self.state.enable_upper_threshold
        ):
            print("Both lower and upper thresholds are disabled.")
            return

        # Initialize values
        if self.state.efo_thresholds is None:
            min_efo = self.minfluxreader.processed_dataframe["efo"].values.min()
            max_efo = self.minfluxreader.processed_dataframe["efo"].values.max()
        else:
            min_efo = self.state.efo_thresholds[0]
            max_efo = self.state.efo_thresholds[1]
        if self.state.cfr_thresholds is None:
            min_cfr = self.minfluxreader.processed_dataframe["cfr"].values.min()
            max_cfr = self.minfluxreader.processed_dataframe["cfr"].values.max()
        else:
            min_cfr = self.state.cfr_thresholds[0]
            max_cfr = self.state.cfr_thresholds[1]

        # Calculate thresholds for EFO
        upper_thresh_efo, lower_thresh_efo = self.calculate_thresholds(
            self.minfluxreader.processed_dataframe["efo"].values,
            thresh_factor=self.state.filter_thresh_factor,
        )
        if self.state.enable_lower_threshold:
            min_efo = lower_thresh_efo
        if self.state.enable_upper_threshold:
            max_efo = upper_thresh_efo
        self.state.efo_thresholds = (min_efo, max_efo)

        # Calculate thresholds for CFR
        upper_thresh_cfr, lower_thresh_cfr = self.calculate_thresholds(
            self.minfluxreader.processed_dataframe["cfr"].values,
            thresh_factor=self.state.filter_thresh_factor,
        )
        if self.state.enable_lower_threshold:
            min_cfr = lower_thresh_cfr
        if self.state.enable_upper_threshold:
            max_cfr = upper_thresh_cfr
        self.state.cfr_thresholds = (min_cfr, max_cfr)

        # Update plot
        self.efo_region.setRegion(self.state.efo_thresholds)
        self.cfr_region.setRegion(self.state.cfr_thresholds)

    @Slot(int, name="persist_efo_filtering_state")
    def persist_efo_filtering_state(self, state):
        self.state.enable_filter_efo = state != 0

    @Slot(int, name="persist_lower_threshold")
    def persist_lower_threshold(self, state):
        self.state.enable_lower_threshold = state != 0

    @Slot(int, name="persist_upper_threshold")
    def persist_upper_threshold(self, state):
        self.state.enable_upper_threshold = state != 0

    @Slot(str, name="persist_thresh_factor")
    def persist_thresh_factor(self, text):
        try:
            thresh_factor = float(text)
        except Exception as _:
            return
        self.state.filter_thresh_factor = thresh_factor

    @Slot(int, name="persist_cfr_filtering_state")
    def persist_cfr_filtering_state(self, state):
        self.state.enable_filter_cfr = state != 0

    @Slot(name="broadcast_viewers_update")
    def broadcast_viewers_update(self):
        """Inform the rest of the application that the data viewers should be updated."""
        # Signal that the viewers should be updated
        self.data_filters_changed.emit()

    def plot(self):
        """Plot histograms."""

        # Make sure there is data to plot
        if self.minfluxreader is None:
            return

        if self.minfluxreader.processed_dataframe is None:
            return

        #
        # Get "efo" and "cfr" measurements, and "sx", "sy" and "sz" localization jitter
        #

        # "efo"
        n_efo, efo_bin_edges, efo_bin_centers, efo_bin_width = self._prepare_histogram(
            self.minfluxreader.processed_dataframe["efo"].values
        )
        if self.state.efo_thresholds is None:
            self.state.efo_thresholds = (efo_bin_edges[0], efo_bin_edges[-1])

        self.efo_plot, self.efo_region = self._create_histogram_plot(
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
            self.minfluxreader.processed_dataframe["cfr"].values
        )
        if self.state.cfr_thresholds is None:
            self.state.cfr_thresholds = (cfr_bin_edges[0], cfr_bin_edges[-1])

        self.cfr_plot, self.cfr_region = self._create_histogram_plot(
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

        # cfr vs. efo
        self.cfr_efo_plot = self._create_scatter_plot(
            x=self.minfluxreader.processed_dataframe["efo"],
            y=self.minfluxreader.processed_dataframe["cfr"],
            title="CFR vs. EFO",
            x_label="EFO",
            y_label="CFR",
            brush=pg.mkBrush(QColor(62, 175, 118, 128)),
            roi_color="k",  # QColor(1, 65, 130, 128),
            thresholds_efo=self.state.efo_thresholds,
            thresholds_cfr=self.state.cfr_thresholds,
        )
        self.ui.parameters_layout.addWidget(self.cfr_efo_plot)
        self.cfr_efo_plot.show()

        # sx
        n_sx, sx_bin_edges, sx_bin_centers, sx_bin_width = self._prepare_histogram(
            self.minfluxreader.processed_dataframe_stats["sx"].values
        )
        self.sx_plot, _ = self._create_histogram_plot(
            n_sx,
            sx_bin_edges,
            sx_bin_centers,
            sx_bin_width,
            title="σx",
            brush="k",
            support_thresholding=False,
        )
        self._add_median_line(
            self.sx_plot, self.minfluxreader.processed_dataframe_stats["sx"].values
        )
        self.ui.localizations_layout.addWidget(self.sx_plot)
        self.sx_plot.show()

        # sy
        n_sy, sy_bin_edges, sy_bin_centers, sy_bin_width = self._prepare_histogram(
            self.minfluxreader.processed_dataframe_stats["sy"].values
        )
        self.sy_plot, _ = self._create_histogram_plot(
            n_sy,
            sy_bin_edges,
            sy_bin_centers,
            sy_bin_width,
            title="σy",
            brush="k",
            support_thresholding=False,
        )
        self._add_median_line(
            self.sy_plot, self.minfluxreader.processed_dataframe_stats["sy"].values
        )
        self.ui.localizations_layout.addWidget(self.sy_plot)
        self.sy_plot.show()

        # sz
        if self.minfluxreader.is_3d:
            n_sz, sz_bin_edges, sz_bin_centers, sz_bin_width = self._prepare_histogram(
                self.minfluxreader.processed_dataframe_stats["sz"].values
            )
            self.sz_plot, _ = self._create_histogram_plot(
                n_sz,
                sz_bin_edges,
                sz_bin_centers,
                sz_bin_width,
                title="σz",
                brush="k",
                support_thresholding=False,
            )
            self._add_median_line(
                self.sz_plot, self.minfluxreader.processed_dataframe_stats["sz"].values
            )
            self.ui.localizations_layout.addWidget(self.sz_plot)
            self.sz_plot.show()

    @staticmethod
    def _prepare_histogram(values):
        """Prepare data to plot."""
        bin_edges, bin_centers, bin_width = ideal_hist_bins(values, scott=False)
        n, _ = np.histogram(values, bins=bin_edges, density=False)
        n = n / n.sum()
        return n, bin_edges, bin_centers, bin_width

    def _create_histogram_plot(
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
        """Create a histogram plot and return it to be added to the layout."""

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
        plot.setMouseEnabled(x=True, y=False)
        padding = 1.0 * (bin_edges[1] - bin_edges[0])
        plot.setXRange(
            bin_edges[0] - padding, bin_edges[-1] + padding, padding=0.0
        )  # setXRange()'s padding misbehaves
        plot.setYRange(0.0, n.max())
        plot.addItem(chart)

        region = None
        if support_thresholding:

            # Create a linear region for setting filtering thresholds
            region = pg.LinearRegionItem(
                values=[thresholds[0], thresholds[1]],
                pen={"color": "k", "width": 3},
            )

            # Mark region with data label for callbacks
            region.data_label = title.lower().replace(" ", "_")

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

        # Make sure the viewbox remembers its own y range
        viewbox = plot.getPlotItem().getViewBox()
        viewbox.y_min = 0.0
        viewbox.y_max = n.max()
        viewbox.sigXRangeChanged.connect(self.fix_viewbox_y_range)

        return plot, region

    def _create_scatter_plot(
        self,
        x: np.ndarray,
        y: np.ndarray,
        *,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        brush: str = "b",
        roi_color: str = "r",
        thresholds_efo: tuple = None,
        thresholds_cfr: tuple = None,
    ):
        """Create a scatter plot and return it to be added to the layout."""
        plot = pg.PlotWidget(parent=self, background="w", title=title)
        plot.setLabel("bottom", text=x_label)
        plot.setLabel("left", text=y_label)
        plot.setMouseEnabled(x=True, y=True)

        # Fix plot ratio
        efo_val = np.mean(self.minfluxreader.processed_dataframe["efo"].values)
        cfr_val = np.mean(self.minfluxreader.processed_dataframe["cfr"].values)
        try:
            ratio = cfr_val / efo_val
        except:
            ratio = 1.0
        plot.getPlotItem().getViewBox().setAspectLocked(lock=True, ratio=ratio)

        scatter = pg.ScatterPlotItem(
            size=3,
            pen=None,
            brush=brush,
            hoverable=False,
        )
        # scatter.sigClicked.connect(self.clicked)
        scatter.setData(x=x, y=y)
        plot.addItem(scatter)
        plot.showAxis("bottom")
        plot.showAxis("left")

        # Add ROI with thresholds
        if thresholds_efo is not None and thresholds_cfr is not None:
            self.efo_cfr_roi = ROI(
                pos=Point(thresholds_efo[0], thresholds_cfr[0]),
                size=Point(
                    thresholds_efo[1] - thresholds_efo[0],
                    thresholds_cfr[1] - thresholds_cfr[0],
                ),
                parent=scatter,
                pen={"color": roi_color, "width": 3},
                hoverPen={"color": roi_color, "width": 5},
                movable=False,
                rotatable=False,
                resizable=False,
                removable=False,
            )
            #self.efo_cfr_roi.sigRegionChanged.connect(self.roi_changed)
            #self.efo_cfr_roi.sigRegionChangeFinished.connect(self.roi_changed_finished)

        # Customize the context menu
        self.customize_context_menu(plot)

        return plot

    def _add_median_line(self, plot, values):
        """Add median line to plot (with median +/- mad as label)."""
        _, _, med, mad = get_robust_threshold(values, 0.0)
        line = pg.InfiniteLine(
            pos=med,
            movable=False,
            angle=90,
            pen={"color": (200, 50, 50), "width": 3},
            label=f"median={med:.4e} ± {mad:.4e}",
            labelOpts={
                "position": 0.95,
                "color": (200, 50, 50),
                "fill": (200, 50, 50, 10),
                "movable": True,
            },
        )
        plot.addItem(line)

    def calculate_thresholds(self, values, thresh_factor):
        """Prepare filter line."""

        # Calculate robust threshold
        upper_threshold, lower_threshold, _, _ = get_robust_threshold(
            values, factor=thresh_factor
        )

        # Return it
        return upper_threshold, lower_threshold

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
        """Called when the line region on one of the histogram plots is changing."""
        pass

    def region_pos_changed_finished(self, item):
        """Called when the line region on one of the histogram plots has changed."""
        if item.data_label == "efo":
            self.state.efo_thresholds = item.getRegion()
            self.update_efo_cfr_roi()
        elif item.data_label == "cfr":
            self.state.cfr_thresholds = item.getRegion()
            self.update_efo_cfr_roi()
        else:
            raise ValueError(f"Unexpected data label {item.data_label}.")

    # def roi_changed(self, item):
    #     """Called when the line region on one of the histogram plots has changed."""
    #     pass
    #
    # def roi_changed_finished(self, item):
    #     """Called when the ROI in the scatter plot has changed."""
    #     print("roi_changed_finished: called")
    #     pos = self.efo_cfr_roi.pos()
    #     size = self.efo_cfr_roi.size()
    #     self.state.efo_thresholds = (pos[0], pos[0] + size[0])
    #     self.state.cfr_thresholds = (pos[1], pos[1] + size[1])
    #
    #     # Update plot
    #     self.efo_region.setRegion(self.state.efo_thresholds)
    #     self.cfr_region.setRegion(self.state.cfr_thresholds)

    @staticmethod
    def _change_region_label_font(region_label):
        """Change the region label font style."""
        text_item = region_label.textItem
        text_item.setDefaultTextColor(QColor("black"))
        font = text_item.font()
        font.setWeight(QFont.Bold)
        font.setPointSize(20)

    def fix_viewbox_y_range(self, viewbox, x_range_limits):
        """Reset the y axis range whenever the x range changes."""
        viewbox.setYRange(viewbox.y_min, viewbox.y_max)
        viewbox.setAutoVisible(y=True)

    def update_efo_cfr_roi(self):
        """Update the efo_cfr roi with to match current threshold values."""
        if self.state.efo_thresholds is None or self.state.cfr_thresholds is None:
            return
        if self.efo_cfr_roi is None:
            return
        self.efo_cfr_roi.setPos(
            Point(self.state.efo_thresholds[0], self.state.cfr_thresholds[0])
        )
        self.efo_cfr_roi.setSize(
            Point(
                self.state.efo_thresholds[1] - self.state.efo_thresholds[0],
                self.state.cfr_thresholds[1] - self.state.cfr_thresholds[0],
            )
        )
