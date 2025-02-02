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
import time

import numpy as np
import pyqtgraph as pg
from pyqtgraph import ROI, PlotCurveItem, PlotWidget, TextItem, ViewBox, mkPen
from PySide6 import QtCore
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QInputDialog, QMenu

from ..state import ColorCode, State
from .helpers import (
    BottomLeftAnchoredScaleBar,
    create_brushes_by,
    export_plot_interactive,
    update_brushes_by_,
)


class Plotter(PlotWidget):
    # Signals
    locations_selected = Signal(list)
    locations_selected_by_range = Signal(str, str, tuple, tuple)
    crop_region_selected = Signal(str, str, tuple, tuple)

    def __init__(self):
        super().__init__()
        self.setBackground("w")
        self.brush = pg.mkBrush(255, 255, 255, 128)
        self.pen = pg.mkPen(None)
        self.remove_points()
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.show()

        # Disable default context menu
        self.setMenuEnabled(False)

        # Set aspect ratio to 1.0 locked
        self.getPlotItem().getViewBox().setAspectLocked(lock=True, ratio=1.0)

        # Keep a reference to the singleton State class
        self.state = State()

        # Keep track of the mapping between unique identifiers or fluorophore identifiers and cached QBrushes
        self._id_to_brush = None
        self._fid_to_brush = None

        # Keep a reference to the scatter_plot/line plot objects
        self.scatter_plot = None
        self.line_plot = None

        # ROI for localizations selection
        self.ROI = None
        self.line = None
        self.line_text = None
        self._roi_start_point = None
        self._roi_is_being_drawn = False
        self._line_start_point = None
        self._line_is_being_drawn = False

        # Keep track of last plot
        self._last_x_param = None
        self._last_y_param = None

        # Keep track of the ScaleBar
        self.scale_bar = None

    def enableAutoRange(self, enable: bool):
        """Enable/disable axes autorange."""
        self.getViewBox().enableAutoRange(axis=ViewBox.XYAxes, enable=enable)

    def mousePressEvent(self, ev):
        """Override mouse press event."""

        # Is the user trying to initiate drawing an ROI?
        if (
            self.scatter_plot is not None
            and ev.button() == Qt.MouseButton.LeftButton
            and ev.modifiers() == QtCore.Qt.ShiftModifier
        ):
            # Remove previous ROI if it exists
            if self.ROI is not None:
                self.removeItem(self.ROI)
                self.ROI.deleteLater()
                self.ROI = None

            # Create ROI and keep track of position
            self._roi_is_being_drawn = True
            self._roi_start_point = (
                self.getPlotItem().getViewBox().mapSceneToView(ev.position())
            )
            self.ROI = ROI(
                pos=self._roi_start_point,
                size=(0, 0),
                resizable=False,
                rotatable=False,
                pen=(255, 0, 0),
            )
            self.ROI.setAcceptedMouseButtons(Qt.MouseButton.RightButton)
            self.addItem(self.ROI)
            self.ROI.show()

            # Make sure to react to ROI shifts
            self.ROI.sigRegionChangeFinished.connect(self.roi_moved)

            # Accept the event
            ev.accept()

        elif (
            self.scatter_plot is not None
            and ev.button() == Qt.MouseButton.LeftButton
            and ev.modifiers() == QtCore.Qt.ControlModifier
            and self.state.x_param in ("x", "y", "z")
            and self.state.y_param in ("x", "y", "z")
        ):
            # Is the user trying to initiate drawing a line?

            # Remove previous line if it exists
            if self.line is not None:
                self.removeItem(self.line)
                self.line.deleteLater()
                self.line = None

            if self.line_text is not None:
                self.removeItem(self.line_text)
                self.line_text.deleteLater()
                self.line_text = None

            # Create ROI and keep track of position
            self._line_is_being_drawn = True
            self._line_start_point = (
                self.getPlotItem().getViewBox().mapSceneToView(ev.position())
            )
            self.line = PlotCurveItem(
                x=[self._line_start_point.x(), self._line_start_point.x()],
                y=[self._line_start_point.y(), self._line_start_point.y()],
                pen=mkPen(color=(255, 0, 0), width=2),
            )
            self.addItem(self.line)
            self.line.show()

            # Accept the event
            ev.accept()

        else:

            # Is the user trying to open a context menu?
            if (
                self.scatter_plot is not None
                and ev.button() == Qt.MouseButton.RightButton
            ):
                menu = QMenu()
                if self.ROI is not None:
                    crop_data_action = QAction("Crop data")
                    crop_data_action.triggered.connect(self.crop_data_by_roi_selection)
                    menu.addAction(crop_data_action)
                    menu.addSeparator()
                set_scalebar_size_action = QAction("Set scale bar size")
                set_scalebar_size_action.triggered.connect(self.set_scalebar_size)
                menu.addAction(set_scalebar_size_action)
                export_action = QAction("Export plot")
                export_action.triggered.connect(
                    lambda checked: export_plot_interactive(self.getPlotItem())
                )
                menu.addAction(export_action)
                pos = ev.screenPos()
                menu.exec(QPoint(int(pos.x()), int(pos.y())))
                ev.accept()
            else:

                # Call the parent method
                ev.ignore()
                super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        # Is the user drawing an ROI?
        if (
            self.scatter_plot is not None
            and ev.buttons() == Qt.MouseButton.LeftButton
            and self.ROI is not None
            and self._roi_is_being_drawn
        ):
            # Resize the ROI
            current_point = (
                self.getPlotItem().getViewBox().mapSceneToView(ev.position())
            )
            self.ROI.setSize(current_point - self._roi_start_point)

            # Accept the event
            ev.accept()

        elif (
            self.scatter_plot is not None
            and ev.buttons() == Qt.MouseButton.LeftButton
            and self.line is not None
            and self._line_is_being_drawn
        ):
            # Is the user drawing a line?

            # Resize the ROI
            current_point = (
                self.getPlotItem().getViewBox().mapSceneToView(ev.position())
            )
            self.line.setData(
                x=[self._line_start_point.x(), current_point.x()],
                y=[self._line_start_point.y(), current_point.y()],
            )

            # Accept the event
            ev.accept()
        else:
            # Call the parent method
            ev.ignore()
            super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if self.scatter_plot is not None and ev.button() == Qt.MouseButton.LeftButton:
            if self._roi_is_being_drawn:
                # Extract the ranges
                x_range, y_range = self._get_ranges_from_roi()
                if x_range is None or y_range is None:
                    # Handle the case where ranges are None
                    return

                # Get current parameters
                x_param = self.state.x_param
                y_param = self.state.y_param

                # Update the DataViewer with current selection
                self.locations_selected_by_range.emit(
                    x_param, y_param, x_range, y_range
                )

                # Reset flags
                self._roi_start_point = None
                self._roi_is_being_drawn = False

                # Check if the ROI has 0 size
                if (
                    np.abs(x_range[1] - x_range[0]) < 1e-4
                    or np.abs(y_range[1] - y_range[0]) < 1e-4
                ):
                    if hasattr(self, "ROI") and self.ROI:
                        self.removeItem(self.ROI)
                        self.ROI.deleteLater()
                        self.ROI = None

                # Accept the event
                ev.accept()

            elif self._line_is_being_drawn:
                if self.line:
                    # Display the measurement
                    x_data, y_data = self.line.getData()
                    if (
                        x_data is None
                        or len(x_data) < 2
                        or y_data is None
                        or len(y_data) < 2
                    ):  # Check if data is incomplete
                        return

                    center = np.array(
                        [0.5 * (x_data[0] + x_data[1]), 0.5 * (y_data[0] + y_data[1])]
                    )
                    delta_y = y_data[1] - y_data[0]
                    delta_x = x_data[1] - x_data[0]
                    v = np.array([-1.0 * delta_y, delta_x])
                    norm = np.linalg.norm(v)

                    if norm >= 1e-4:
                        v_norm = v / norm
                        length = np.sqrt(delta_x**2 + delta_y**2)
                        pos = center + 1.0 * v_norm
                        clr = (
                            (255, 255, 0)
                            if self.state.color_code == ColorCode.NONE
                            else (255, 255, 255)
                        )
                        self.line_text = TextItem(text=f"{length:.2f} nm", color=clr)
                        self.line_text.setPos(pos[0], pos[1])
                        self.addItem(self.line_text)
                    else:
                        self.removeItem(self.line)
                        self.line.deleteLater()
                        self.line = None

                    # Reset flags
                    self._line_start_point = None
                    self._line_is_being_drawn = False

                    # Accept the event
                    ev.accept()
                else:
                    # If line is None, safely ignore the operation
                    ev.ignore()

            else:
                # Call the parent method if no conditions are met
                super().mouseReleaseEvent(ev)
        else:
            # Properly ignore the event if conditions are not met
            ev.ignore()

    def reset(self):
        # Forget last plot
        self._last_x_param = None
        self._last_y_param = None
        self.remove_points()

        # Clear color caches
        self._id_to_brush = None
        self._fid_to_brush = None

    def remove_points(self):
        self.setBackground("w")
        self.clear()

    def plot_parameters(self, x, y, x_param, y_param, tid, fid):
        """Plot localizations and other parameters in a 2D scatter_plot plot."""

        # Color-code the data points
        if self.state.color_code == ColorCode.NONE:
            brushes = self.brush
        elif self.state.color_code == ColorCode.BY_TID:
            if self._id_to_brush is None:
                brushes, self._id_to_brush = create_brushes_by(tid)
            else:
                brushes, self._id_to_brush = update_brushes_by_(tid, self._id_to_brush)
        elif self.state.color_code == ColorCode.BY_FLUO:
            if self._fid_to_brush is None:
                brushes, self._fid_to_brush = create_brushes_by(
                    fid, color_scheme="green-magenta"
                )
            else:
                brushes, self._fid_to_brush = update_brushes_by_(
                    fid, self._fid_to_brush, color_scheme="green-magenta"
                )
        else:
            raise ValueError("Unexpected request for color-coding the localizations!")

        # Create the scatter_plot plot
        self.scatter_plot = pg.ScatterPlotItem(
            x=x,
            y=y,
            data=tid,
            size=5,
            pen=None,
            brush=brushes,
            hoverable=True,
            hoverSymbol="s",
            hoverSize=5,
            hoverPen=pg.mkPen("w", width=2),
            hoverBrush=None,
        )
        self.scatter_plot.sigClicked.connect(self.clicked)
        self.addItem(self.scatter_plot)

        # For a tracking dataset, we also add the connecting line_plot (for spatial parameters only)
        if self.state.is_tracking and (
            x_param in ["x", "y", "z"] and y_param in ["x", "y", "z"]
        ):

            # Add the line_plot within TIDs
            line_indices = np.concatenate((np.diff(tid) == 0, [1])).astype(np.int32)
            self.line_plot = pg.PlotDataItem(
                x,
                y,
                connect=line_indices,
                pen=mkPen(cosmetic=True, width=0.5, color="w"),
                symbol=None,
                brush=None,
            )
            self.addItem(self.line_plot)

        self.setLabel("bottom", text=x_param)
        self.setLabel("left", text=y_param)
        self.showAxis("bottom")
        self.showAxis("left")
        self.setBackground("k")

        # Fix aspect ratio (if needed)
        if (self._last_x_param is None or self._last_x_param != x_param) or (
            self._last_y_param is None or self._last_y_param != y_param
        ):
            # Update range
            self.getViewBox().enableAutoRange(axis=ViewBox.XYAxes, enable=True)

            if x_param in ["x", "y", "z"] and y_param in ["x", "y", "z"]:
                # Set fixed aspect ratio
                aspect_ratio = 1.0

                # Add scale bar
                if self.scale_bar is None:
                    self.scale_bar = BottomLeftAnchoredScaleBar(
                        size=self.state.scale_bar_size,
                        auto_resize=False,
                        viewBox=self.getViewBox(),
                        brush="w",
                        pen=None,
                        suffix="nm",
                        offset=(50, -15),
                    )
                self.scale_bar.setEnabled(True)
                self.scale_bar.setVisible(True)

            else:
                # Calculate aspect ratio
                x_min, x_max = np.nanpercentile(x, (1, 99))
                x_scale = x_max - x_min
                y_min, y_max = np.nanpercentile(y, (1, 99))
                y_scale = y_max - y_min
                aspect_ratio = y_scale / x_scale
                if np.isnan(aspect_ratio):
                    aspect_ratio = 1.0

                if self.scale_bar is not None:
                    self.scale_bar.setEnabled(False)
                    self.scale_bar.setVisible(False)

            self.getPlotItem().getViewBox().setAspectLocked(
                lock=True, ratio=aspect_ratio
            )

        # Update last plotted parameters
        self._last_x_param = x_param
        self._last_y_param = y_param

    def crop_data_by_roi_selection(self, item):
        """Open dialog to manually set the filter ranges"""

        # Get the ROI bounds
        pos = self.ROI.pos()
        size = self.ROI.size()

        # Create the ranges
        x_range = (pos[0], pos[0] + size[0])
        y_range = (pos[1], pos[1] + size[1])

        # Get the parameter names
        x_param = self.state.x_param
        y_param = self.state.y_param

        self.crop_region_selected.emit(x_param, y_param, x_range, y_range)

        # Delete ROI after it has been used to crop
        self.removeItem(self.ROI)
        self.ROI.deleteLater()
        self.ROI = None

    def roi_moved(self):
        """Inform that the selection of localizations may have changed after the ROI was moved."""

        # If the ROI is being drawn now, do nothing
        if self._roi_is_being_drawn:
            return

        # Extract the ranges
        x_range, y_range = self._get_ranges_from_roi()

        # Get current parameters
        x_param = self.state.x_param
        y_param = self.state.y_param

        # Update the DataViewer with current selection
        if x_range is not None and y_range is not None:
            self.locations_selected_by_range.emit(x_param, y_param, x_range, y_range)

    def clicked(self, _, points):
        """Emit 'signal_selected_locations' when points are selected in the plot."""
        self.locations_selected.emit(points)

        # Remove ROI if it exists
        if self.ROI is not None:
            self.removeItem(self.ROI)
            self.ROI = None

    def _get_ranges_from_roi(self):
        """Calculate x and y ranges from ROI."""

        # Initialize x and y ranges to None
        x_range = None
        y_range = None

        # Extract x and y ranges
        if self.ROI is not None:
            x_range = (self.ROI.pos()[0], self.ROI.pos()[0] + self.ROI.size()[0])
            y_range = (self.ROI.pos()[1], self.ROI.pos()[1] + self.ROI.size()[1])

        return x_range, y_range

    def set_scalebar_size(self):
        """Ask the user to specify the size of the scalebar."""
        size, ok = QInputDialog.getInt(
            self,
            "Scale bar",
            "Set scale bar length (nm):",
            self.state.scale_bar_size,
            minValue=1,
            maxValue=10000,
        )
        if ok:
            # Set the new value
            self.state.scale_bar_size = size

            # Update the bar
            self.scale_bar.setSize(self.state.scale_bar_size)
