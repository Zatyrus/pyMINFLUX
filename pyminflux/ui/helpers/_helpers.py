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
from pathlib import Path
from typing import Union

import pyqtgraph as pg
from pyqtgraph import AxisItem, ViewBox
from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication, QFileDialog

from pyminflux.analysis import get_robust_threshold
from pyminflux.state import State


def export_plot_interactive(item, parent=None):
    """Save the content of the current scene to a PNG image."""
    if isinstance(item, ViewBox):
        view_box = item
    elif isinstance(item, AxisItem):
        view_box = item.getViewBox()
    elif isinstance(item, pg.PlotItem):
        view_box = item.getViewBox()
    else:
        return

    # Ask the user to pick a file name
    filename, ext = QFileDialog.getSaveFileName(
        parent,
        "Export filtered data",
        ".",
        "PNG images (*.png)",
    )

    # Did the user cancel?
    if filename == "":
        return

    # Make sure to add the extension
    if not filename.lower().endswith(".png"):
        filename += ".png"

    # Get the dpi from the State
    state = State()

    # Save the scene to file
    export_to_image(view_box, filename, dpi=state.plot_export_dpi)


def export_to_image(item: pg.ViewBox, out_file_name: Union[Path, str], dpi: int = 600):
    """Export current QGraphicsScene to file."""

    # Get the scene from the viewBox
    if isinstance(item, pg.ViewBox):
        plot_item = item.parentItem()
        plot_widget = plot_item.getViewWidget()
    elif isinstance(item, pg.PlotWidget):
        plot_widget = item
    else:
        return

    # Get primary screen resolution
    app = QApplication.instance()
    screen = app.primaryScreen()
    logical_dpi = screen.logicalDotsPerInch()

    # Final image size at given dpi
    dpi_scaling = dpi / logical_dpi
    img_size = plot_widget.size() * dpi_scaling

    # Create the image and painter
    image = QImage(img_size, QImage.Format_ARGB32)
    painter = QPainter()

    # Begin the QPainter operation
    painter.begin(image)

    # Set the viewport and window of the QPainter
    painter.setViewport(QRect(0, 0, img_size.width(), img_size.height()))

    # Paint the scene onto the image
    plot_widget.render(painter)

    # End the QPainter operation
    painter.end()

    # Save the image to a file
    image.save(out_file_name)

    # Inform
    print(f"Plot exported to {out_file_name}.")


def add_median_line(plot, values, label_pos=0.95, unit="nm"):
    """Add median line to plot (with median +/- mad as label)."""
    _, _, med, mad = get_robust_threshold(values, 0.0)
    unit_str = f" {unit}" if unit != "" else ""
    line = pg.InfiniteLine(
        pos=med,
        movable=False,
        angle=90,
        pen={"color": (200, 50, 50), "width": 3},
        label=f"median={med:.2f} ± {mad:.2f}{unit_str}",
        labelOpts={
            "position": label_pos,
            "color": (200, 50, 50),
            "fill": (200, 50, 50, 10),
            "movable": True,
        },
    )
    plot.addItem(line)
