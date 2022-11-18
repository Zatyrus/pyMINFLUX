import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QDialog

from pyminflux.analysis import ideal_hist_bins
from pyminflux.reader import MinFluxReader
from pyminflux.ui.ui_histogram_viewer import Ui_HistogramViewer


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
        self.efo_plot = self._create_plot(
            n_efo, efo_bin_edges, efo_bin_centers, efo_bin_width, "EFO", "b"
        )
        self.ui.parameters_layout.addWidget(self.efo_plot)
        self.efo_plot.show()

        # cfr
        n_cfr, cfr_bin_edges, cfr_bin_centers, cfr_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe["cfr"].values
        )
        self.cfr_plot = self._create_plot(
            n_cfr, cfr_bin_edges, cfr_bin_centers, cfr_bin_width, "CFR", "r"
        )
        self.ui.parameters_layout.addWidget(self.cfr_plot)
        self.cfr_plot.show()

        # sx
        n_sx, sx_bin_edges, sx_bin_centers, sx_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe_stats["sx"].values
        )
        self.sx_plot = self._create_plot(
            n_sx, sx_bin_edges, sx_bin_centers, sx_bin_width, "SX", "k"
        )
        self.ui.localizations_layout.addWidget(self.sx_plot)
        self.sx_plot.show()

        # sy
        n_sy, sy_bin_edges, sy_bin_centers, sy_bin_width = self._prepare_histogram(
            minfluxreader.processed_dataframe_stats["sy"].values
        )
        self.sy_plot = self._create_plot(
            n_sy, sy_bin_edges, sy_bin_centers, sy_bin_width, "SY", "k"
        )
        self.ui.localizations_layout.addWidget(self.sy_plot)
        self.sy_plot.show()

        # sz
        if minfluxreader.is_3d:
            n_sz, sz_bin_edges, sz_bin_centers, sz_bin_width = self._prepare_histogram(
                minfluxreader.processed_dataframe_stats["sz"].values
            )
            self.sz_plot = self._create_plot(
                n_sz, sz_bin_edges, sz_bin_centers, sz_bin_width, "SZ", "k"
            )
            self.ui.localizations_layout.addWidget(self.sz_plot)
            self.sz_plot.show()

    def _prepare_histogram(self, values):
        """Prepare data to plot."""
        bin_edges, bin_centers, bin_width = ideal_hist_bins(values, scott=False)
        n, _ = np.histogram(values, bins=bin_edges, density=False)
        n = n / n.sum()
        return n, bin_edges, bin_centers, bin_width

    def _create_plot(self, n, bin_edges, bin_centers, bin_width, title="", brush="b"):
        """Create a plot and return it to be added to the layout."""
        chart = pg.BarGraphItem(
            x=bin_centers, height=n, width=0.9 * bin_width, brush=brush
        )
        plot = pg.PlotWidget(parent=self, background="w", title=title)
        plot.setXRange(bin_edges[0], bin_edges[-1], 0)
        plot.setYRange(0.0, n.max())
        plot.addItem(chart)
        return plot
