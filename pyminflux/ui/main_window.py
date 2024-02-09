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

import sys
from datetime import datetime
from pathlib import Path

from pyqtgraph import ViewBox
from PySide6 import QtGui, __version__ as pyside6_version
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
)

import pyminflux.resources
from pyminflux import __APP_NAME__, __version__
from pyminflux.processor import MinFluxProcessor
from pyminflux.reader import MinFluxReader, NativeMetadataReader
from pyminflux.settings import Settings
from pyminflux.state import State
from pyminflux.ui.analyzer import Analyzer
from pyminflux.ui.color_unmixer import ColorUnmixer
from pyminflux.ui.dataviewer import DataViewer
from pyminflux.ui.emittingstream import EmittingStream
from pyminflux.ui.frc_tool import FRCTool
from pyminflux.ui.options import Options
from pyminflux.ui.plotter import Plotter
from pyminflux.ui.plotter_toolbar import PlotterToolbar
from pyminflux.ui.time_inspector import TimeInspector
from pyminflux.ui.trace_length_viewer import TraceLengthViewer
from pyminflux.ui.trace_stats_viewer import TraceStatsViewer
from pyminflux.ui.ui_main_window import Ui_MainWindow
from pyminflux.ui.wizard import WizardDialog
from pyminflux.utils import check_for_updates
from pyminflux.writer import MinFluxWriter, PyMinFluxNativeWriter


class PyMinFluxMainWindow(QMainWindow, Ui_MainWindow):
    """
    Main application window.
    """

    request_sync_external_tools = Signal(None, name="request_sync_external_tools")

    def __init__(self, parent=None):
        """
        Constructor.
        """

        # Call the base constructor
        super().__init__(parent)

        # Initialize the dialog
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Main window title
        self.setWindowTitle(f"{__APP_NAME__} v{__version__}")

        # Set the window icon
        icon = QIcon(":/icons/icon.png")
        self.setWindowIcon(icon)

        # Keep a reference to the state machine
        self.state = State()

        # Keep track of the last selected path
        self.last_selected_path = ""

        # Keep a reference to the MinFluxProcessor
        self.processor = None

        # Read the application settings and update the state
        self.load_and_apply_settings()

        # Set the menu state based on the settings
        self.ui.actionConsole.setChecked(self.state.open_console_at_start)

        # Dialogs and widgets
        self.data_viewer = None
        self.analyzer = None
        self.plotter = None
        self.color_unmixer = None
        self.time_inspector = None
        self.trace_stats_viewer = None
        self.trace_length_viewer = None
        self.frc_tool = None
        self.options = Options()

        # Initialize widget and its dock
        self.wizard = WizardDialog()
        self.wizard_dock = QDockWidget("", self)
        self.wizard_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.wizard_dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.wizard_dock.setWidget(self.wizard)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.wizard_dock)

        # Initialize Plotter and DataViewer
        self.plotter = Plotter()
        self.plotter_toolbar = PlotterToolbar()
        self.data_viewer = DataViewer()

        # Create the output console
        self.txConsole = QTextEdit()
        self.txConsole.setReadOnly(True)
        self.txConsole.setMinimumHeight(100)
        self.txConsole.setMaximumHeight(500)
        self.txConsole.setLineWrapMode(QTextEdit.NoWrap)
        self.txConsole.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Add them to the splitter
        self.ui.splitter_layout.addWidget(self.plotter)
        self.ui.splitter_layout.addWidget(self.plotter_toolbar)
        self.ui.splitter_layout.addWidget(self.data_viewer)
        self.ui.splitter_layout.addWidget(self.txConsole)

        # Make sure to only show the console if requested
        self.toggle_console_visibility()

        # Set initial visibility and enabled states
        self.enable_ui_components(False)

        # Set up signals and slots
        self.setup_conn()

        # Install the custom output stream
        sys.stdout = EmittingStream()
        sys.stdout.signal_textWritten.connect(self.print_to_console)

        # Print a welcome message to the console
        print(f"Welcome to {__APP_NAME__}.")

    def load_and_apply_settings(self):
        """Read the application settings and update the State."""

        # Open settings file
        settings = Settings()

        # Read and set 'last_selected_path' option
        self.last_selected_path = Path(
            settings.instance.value("io/last_selected_path", ".")
        )

        # Read and set 'min_trace_length' option
        self.state.min_trace_length = int(
            settings.instance.value(
                "options/min_trace_length", self.state.min_trace_length
            )
        )

        # @SUPERSEDED: Read 'min_trace_length' and set as 'min_trace_length'
        # This property will be removed from the file the next time the user hits
        # the "Set as new default" in the Options dialog.
        if settings.instance.contains("options/min_trace_length"):
            self.state.min_trace_length = int(
                settings.instance.value(
                    "options/min_trace_length", self.state.min_trace_length
                )
            )

        # Current option name: "options/min_trace_length"
        if settings.instance.contains("options/min_trace_length"):
            self.state.min_trace_length = int(
                settings.instance.value(
                    "options/min_trace_length", self.state.min_trace_length
                )
            )

        # Read and set 'z_scaling_factor' option
        self.state.z_scaling_factor = float(
            settings.instance.value(
                "options/z_scaling_factor", self.state.z_scaling_factor
            )
        )

        # Read and set 'efo_bin_size_hz' option
        self.state.efo_bin_size_hz = float(
            settings.instance.value(
                "options/efo_bin_size_hz", self.state.efo_bin_size_hz
            )
        )

        # Read and set 'efo_expected_frequency' option
        self.state.efo_expected_frequency = float(
            settings.instance.value(
                "options/efo_expected_frequency", self.state.efo_expected_frequency
            )
        )

        # Read and set 'weigh_avg_localization_by_eco' option
        value = settings.instance.value(
            "options/weigh_avg_localization_by_eco",
            self.state.weigh_avg_localization_by_eco,
        )
        weigh_avg_localization_by_eco = (
            value.lower() == "true" if isinstance(value, str) else bool(value)
        )
        self.state.weigh_avg_localization_by_eco = weigh_avg_localization_by_eco

        # Read and set the plot ranges
        value = settings.instance.value("options/efo_range", self.state.efo_range)
        if value == "None" or value is None:
            self.state.efo_range = None
        elif type(value) is list:
            self.state.efo_range = (float(value[0]), float(value[1]))
        else:
            raise ValueError("Unexpected value for 'efo_range' in settings.")

        value = settings.instance.value("options/cfr_range", self.state.cfr_range)
        if value == "None" or value is None:
            self.state.cfr_range = None
        elif type(value) is list:
            self.state.cfr_range = (float(value[0]), float(value[1]))
        else:
            raise ValueError("Unexpected value for 'cfr_range' in settings.")

        value = settings.instance.value(
            "options/loc_precision_range", self.state.loc_precision_range
        )
        if value == "None" or value is None:
            self.state.loc_precision_range = None
        elif type(value) is list:
            self.state.loc_precision_range = (float(value[0]), float(value[1]))
        else:
            raise ValueError("Unexpected value for 'loc_precision_range' in settings.")

        # Read and set 'plot_export_dpi' option
        self.state.plot_export_dpi = int(
            settings.instance.value(
                "options/plot_export_dpi", self.state.plot_export_dpi
            )
        )

        # Read and set 'open_console_at_start' option
        value = settings.instance.value(
            "options/open_console_at_start",
            self.state.open_console_at_start,
        )
        open_console_at_start = (
            value.lower() == "true" if isinstance(value, str) else bool(value)
        )
        self.state.open_console_at_start = open_console_at_start

    def setup_conn(self):
        """Set up signals and slots."""

        # Menu actions
        self.ui.actionLoad.triggered.connect(self.select_and_load_or_import_data_file)
        self.ui.actionSave.triggered.connect(self.save_native_file)
        self.ui.actionExport_data.triggered.connect(self.export_filtered_data)
        self.ui.actionExport_stats.triggered.connect(self.export_filtered_stats)
        self.ui.actionOptions.triggered.connect(self.open_options_dialog)
        self.ui.actionQuit.triggered.connect(self.quit_application)
        self.ui.actionConsole.changed.connect(self.toggle_console_visibility)
        self.ui.actionData_viewer.changed.connect(self.toggle_dataviewer_visibility)
        self.ui.actionState.triggered.connect(self.print_current_state)
        self.ui.actionUnmixer.triggered.connect(self.open_color_unmixer)
        self.ui.actionTime_Inspector.triggered.connect(self.open_time_inspector)
        self.ui.actionAnalyzer.triggered.connect(self.open_analyzer)
        self.ui.actionTrace_Stats_Viewer.triggered.connect(self.open_trace_stats_viewer)
        self.ui.actionTrace_Length_Viewer.triggered.connect(
            self.open_trace_length_viewer
        )
        self.ui.actionFRC_analyzer.triggered.connect(self.open_frc_tool)
        self.ui.actionManual.triggered.connect(
            lambda _: QDesktopServices.openUrl(
                "https://github.com/bsse-scf/pyMINFLUX/wiki/pyMINFLUX-user-manual"
            )
        )
        self.ui.actionWebsite.triggered.connect(
            lambda _: QDesktopServices.openUrl("https://pyminflux.ethz.ch")
        )
        self.ui.actionCode_repository.triggered.connect(
            lambda _: QDesktopServices.openUrl("https://github.com/bsse-scf/pyMINFLUX")
        )
        self.ui.actionIssues.triggered.connect(
            lambda _: QDesktopServices.openUrl(
                "https://github.com/bsse-scf/pyMINFLUX/issues"
            )
        )
        self.ui.actionMailing_list.triggered.connect(
            lambda _: QDesktopServices.openUrl(
                "https://sympa.ethz.ch/sympa/subscribe/pyminflux"
            )
        )
        self.ui.actionWhat_s_new.triggered.connect(
            lambda _: QDesktopServices.openUrl(
                "https://github.com/bsse-scf/pyMINFLUX/blob/master/CHANGELOG.md"
            )
        )
        self.ui.actionCheck_for_updates.triggered.connect(self.check_remote_for_updates)
        self.ui.actionAbout.triggered.connect(self.about)

        # Plotter toolbar
        self.plotter_toolbar.plot_requested_parameters.connect(
            self.plot_selected_parameters
        )
        self.plotter_toolbar.plot_average_positions_state_changed.connect(
            self.full_update_ui
        )

        # Plotter
        self.plotter.locations_selected.connect(
            self.show_selected_points_by_indices_in_dataviewer
        )
        self.plotter.locations_selected_by_range.connect(
            self.show_selected_points_by_range_in_dataviewer
        )
        self.plotter.crop_region_selected.connect(self.crop_data_by_range)
        self.plotter_toolbar.color_code_locs_changed.connect(
            self.plot_selected_parameters
        )

        # Options
        self.options.weigh_avg_localization_by_eco_option_changed.connect(
            self.update_weighted_average_localization_option_and_plot
        )
        self.options.min_trace_length_option_changed.connect(
            self.update_min_trace_length
        )

        # Wizard
        self.wizard.load_data_triggered.connect(
            self.select_and_load_or_import_data_file
        )
        self.wizard.reset_filters_triggered.connect(self.reset_filters_and_broadcast)
        self.wizard.open_unmixer_triggered.connect(self.open_color_unmixer)
        self.wizard.open_time_inspector_triggered.connect(self.open_time_inspector)
        self.wizard.open_analyzer_triggered.connect(self.open_analyzer)
        self.wizard.fluorophore_id_changed.connect(
            self.update_fluorophore_id_in_processor_and_broadcast
        )
        self.wizard.request_fluorophore_ids_reset.connect(self.reset_fluorophore_ids)
        self.wizard.wizard_filters_run.connect(self.full_update_ui)
        self.wizard.save_data_triggered.connect(self.save_native_file)
        self.wizard.export_data_triggered.connect(self.export_filtered_data)
        self.wizard.load_filename_triggered.connect(
            self.select_and_load_or_import_data_file
        )

    def enable_ui_components(self, enabled: bool):
        """Enable/disable UI components."""
        self.plotter.show()  # Always show
        if enabled:
            self.plotter_toolbar.show()
            self.data_viewer.show()
            self.plotter_toolbar.show()
        else:
            self.plotter_toolbar.hide()
            self.data_viewer.hide()
            self.plotter_toolbar.hide()
        self.ui.actionSave.setEnabled(enabled)
        self.ui.actionExport_data.setEnabled(enabled)
        self.ui.actionExport_stats.setEnabled(enabled)
        self.ui.actionUnmixer.setEnabled(enabled)
        self.ui.actionTime_Inspector.setEnabled(enabled)
        self.ui.actionAnalyzer.setEnabled(enabled)
        self.ui.actionTrace_Stats_Viewer.setEnabled(enabled)
        self.ui.actionTrace_Length_Viewer.setEnabled(enabled)
        self.ui.actionFRC_analyzer.setEnabled(enabled)

    def full_update_ui(self):
        """
        Updates the UI completely (after a project load, for instance).
        :return:
        """
        self.plotter.clear()
        self.plot_selected_parameters()
        self.data_viewer.clear()
        if self.processor is not None and self.processor.filtered_dataframe is not None:
            print(f"Retrieved {len(self.processor.filtered_dataframe.index)} events.")

    def print_to_console(self, text):
        """
        Append text to the QTextEdit.
        """
        cursor = self.txConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.txConsole.setTextCursor(cursor)

    def closeEvent(self, event):
        """Application close event."""

        # Ask the user
        button = QMessageBox.question(
            self,
            f"{__APP_NAME__}",
            "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No,
        )

        if button != QMessageBox.StandardButton.Yes:
            event.ignore()
        else:
            # @TODO Shutdown threads if any are running

            if self.options is not None:
                self.options.close()
                self.options = None

            if self.analyzer is not None:
                self.analyzer.close()
                self.analyzer = None

            if self.color_unmixer is not None:
                self.color_unmixer.close()
                self.color_unmixer = None

            if self.time_inspector is not None:
                self.time_inspector.close()
                self.time_inspector = None

            if self.options is not None:
                self.options.close()
                self.options = None

            if self.trace_stats_viewer is not None:
                self.trace_stats_viewer.close()
                self.trace_stats_viewer = None

            if self.trace_length_viewer is not None:
                self.trace_length_viewer.close()
                self.trace_length_viewer = None

            if self.frc_tool is not None:
                self.frc_tool.close()
                self.frc_tool = None

            # Store the application settings
            if self.last_selected_path != "":
                settings = Settings()
                settings.instance.setValue(
                    "io/last_selected_path", str(self.last_selected_path)
                )

            # # Restore sys.stdout
            # sys.stdout = sys.__stdout__
            # sys.stdout.flush()

            # Now exit
            event.accept()

    @Slot(None, name="reset_filters_and_broadcast")
    def reset_filters_and_broadcast(self):
        """Reset all filters and broadcast changes."""

        # Reset filters and data
        self.processor.reset()
        self.state.efo_thresholds = None
        self.state.cfr_thresholds = None

        # Update main window
        self.full_update_ui()

        # Signal that the external viewers and tools should be updated
        self.request_sync_external_tools.emit()

    @Slot(None, name="quit_application")
    def quit_application(self):
        """Quit the application."""
        self.close()

    @Slot(bool, name="toggle_console_visibility")
    def toggle_console_visibility(self):
        """Toggle the visibility of the console widget."""
        if self.ui.actionConsole.isChecked():
            self.txConsole.show()
        else:
            self.txConsole.hide()

    @Slot(bool, name="toggle_dataviewer_visibility")
    def toggle_dataviewer_visibility(self):
        """Toggle the visibility of the console dock widget."""
        if self.data_viewer is not None:
            if self.ui.actionData_viewer.isChecked():
                self.data_viewer.show()
            else:
                self.data_viewer.hide()

    @Slot(None, name="save_native_file")
    def save_native_file(self):
        """Save data to native pyMINFLUX `.pmx` file."""
        if self.processor is None or len(self.processor.filtered_dataframe.index) == 0:
            return

        # Get current filename to build the suggestion output
        if self.processor.filename is None:
            out_filename = str(self.last_selected_path)
        else:
            out_filename = str(
                self.processor.filename.parent / f"{self.processor.filename.stem}.pmx"
            )

        # Ask the user to pick a name (and format)
        filename, ext = QFileDialog.getSaveFileName(
            self,
            "Save pyMINFLUX dataset",
            out_filename,
            "pyMINFLUX files (*.pmx)",
        )

        # Did the user cancel?
        if filename == "":
            return

        # Does the file name have the .pmx extension?
        if not filename.lower().endswith(".pmx"):
            filename = Path(filename)
            filename = filename.parent / f"{filename.stem}.pmx"

        # Write to disk
        writer = PyMinFluxNativeWriter(self.processor)
        result = writer.write(filename)

        # Save
        if result:
            print(f"Successfully saved {filename}.")
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not save file {Path(filename).name}!\n\nThe error was:\n{writer.message}",
            )

    @Slot(None, name="select_and_load_or_import_data_file")
    def select_and_load_or_import_data_file(self, filename: str = None):
        """
        Pick a MINFLUX `.pmx` file to load, or an Imspector `.npy' or '.mat' file to import.
        :return: void
        """

        # Do we have a filename?
        if filename is None or not filename:
            # Open a file dialog for the user to pick a .pmx, .npy or .mat file
            res = QFileDialog.getOpenFileName(
                self,
                "Load file",
                str(self.last_selected_path),
                "All Supported Files (*.pmx *.npy *.mat);;"
                "pyMINFLUX file (*.pmx);;"
                "Imspector NumPy files (*.npy);;"
                "Imspector MATLAB mat files (*.mat)",
            )
            filename = res[0]

        # Make sure that we are working with a string
        filename = str(filename)

        if filename != "" and Path(filename).is_file():

            # Pick the right reader
            if len(filename) < 5:
                print(f"Invalid file {filename}: skipping.")
                return
            ext = filename.lower()[-4:]

            # Make sure we have a supported file
            if ext not in [".pmx", ".npy", ".mat"]:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Unsupported file {filename}.",
                )
                return

            # Reload the default settings
            self.load_and_apply_settings()

            # Inform
            print("Reloaded default settings.")

            # If we have a `.pmx` file, we first scan the metadata and update
            # the State
            if ext == ".pmx":
                metadata = NativeMetadataReader.scan(filename)
                if metadata is None:
                    # Could not read the metadata. Abort loading.
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Could not load {filename}.",
                    )
                    return

                # Update the State from the read metadata
                self.state.update_from_metadata(metadata)

                # Inform
                print("Applied settings from file.")

            # Now pass the filename to the MinFluxReader
            reader = MinFluxReader(
                filename, z_scaling_factor=self.state.z_scaling_factor
            )

            # Open the file
            self.last_selected_path = Path(filename).parent

            # Show some info
            print(reader)

            # Add initialize the processor with the reader
            self.processor = MinFluxProcessor(reader, self.state.min_trace_length)

            # Make sure to set current value of use_weighted_localizations
            self.processor.use_weighted_localizations = (
                self.state.weigh_avg_localization_by_eco
            )

            # Show the filename on the main window
            self.setWindowTitle(
                f"{__APP_NAME__} v{__version__} - [{Path(filename).name}]"
            )

            # Close the Options
            if self.options is not None:
                self.options.close()
                self.options = None

            # Close the Color Unmixer
            if self.color_unmixer is not None:
                self.color_unmixer.close()
                self.color_unmixer = None

            # Close the Temporal Inspector
            if self.time_inspector is not None:
                self.time_inspector.close()
                self.time_inspector = None

            # Close the Trace Stats Viewer
            if self.trace_stats_viewer is not None:
                self.trace_stats_viewer.close()
                self.trace_stats_viewer = None

            if self.trace_length_viewer is not None:
                self.trace_length_viewer.close()
                self.trace_length_viewer = None

            # Close the FRC Tool
            if self.frc_tool is not None:
                self.frc_tool.close()
                self.frc_tool = None

            # Update the ui
            self.full_update_ui()

            # Make sure to autoupdate the axis on load
            self.plotter.enableAutoRange(enable=True)

            # Reset the fluorophore list in the wizard
            self.wizard.set_fluorophore_list(self.processor.num_fluorophores)

            # Enable selected ui components
            self.enable_ui_components(True)

            # Update the Analyzer
            if self.analyzer is not None:
                self.analyzer.set_processor(self.processor)
                self.analyzer.plot()

            # Attach the processor reference to the wizard
            self.wizard.set_processor(self.processor)

            # Enable wizard
            self.wizard.enable_controls(True)

        else:
            # If nothing is loaded (even from earlier), disable wizard
            if self.processor is None:
                self.wizard.enable_controls(False)

    @Slot(None, name="export_filtered_data")
    def export_filtered_data(self):
        """Export filtered data as CSV file."""
        if self.processor is None or len(self.processor.filtered_dataframe.index) == 0:
            return

        # Get current filename to build the suggestion output
        if self.processor.filename is None:
            out_filename = str(self.last_selected_path)
        else:
            out_filename = str(
                self.processor.filename.parent / f"{self.processor.filename.stem}.csv"
            )

        # Ask the user to pick a name (and format)
        filename, ext = QFileDialog.getSaveFileName(
            self,
            "Export filtered data",
            out_filename,
            "Comma-separated value files (*.csv)",
        )

        # Did the user cancel?
        if filename == "":
            return

        if ext == "Comma-separated value files (*.csv)":
            # Does the file name have the .csv extension?
            if not filename.lower().endswith(".csv"):
                filename = Path(filename)
                filename = filename.parent / f"{filename.stem}.csv"

            # Write to disk
            result = MinFluxWriter.write_csv(self.processor, filename)

        else:
            return

        # Save
        if result:
            print(
                f"Successfully exported {len(self.processor.filtered_dataframe.index)} localizations."
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not export filtered data to {Path(filename).name}.",
            )

    @Slot(None, name="export_filtered_stats")
    def export_filtered_stats(self):
        """Export filtered, per-trace statistics as CSV file."""
        if self.processor is None or len(self.processor.filtered_dataframe.index) == 0:
            # Inform and return
            QMessageBox.information(
                self,
                "Info",
                f"Sorry, nothing to export.",
            )
            return

        # Get current filename to build the suggestion output
        if self.processor.filename is None:
            out_filename = str(self.last_selected_path)
        else:
            out_filename = str(
                self.processor.filename.parent
                / f"{self.processor.filename.stem}_stats.csv"
            )

        # Ask the user to pick a name
        filename, ext = QFileDialog.getSaveFileName(
            self,
            "Export trace statistics",
            out_filename,
            "Comma-separated value files (*.csv)",
        )

        # Did the user cancel?
        if filename == "":
            return

        # Does the file name have the .csv extension?
        if ext != "Comma-separated value files (*.csv)":
            return

        if not filename.lower().endswith(".csv"):
            filename = Path(filename)
            filename = filename.parent / f"{filename.stem}.csv"

        # Collect stats
        stats = self.processor.filtered_dataframe_stats
        if stats is None:
            return

        # Write stats to disk
        try:
            stats.to_csv(filename, index=False)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not export trace statistics to {Path(filename).name}.\n\n{str(e)}.",
            )
            return

        print(f"Successfully exported statistics for {len(stats.index)} traces.")

    @Slot(None, name="print_current_state")
    def print_current_state(self):
        """Print current contents of the state machine (DEBUG)."""
        if self.txConsole.isHidden():
            self.txConsole.show()
            self.ui.actionConsole.setChecked(True)
        state_dict = self.state.asdict()
        print("[DEBUG] Internal state:")
        for s in state_dict:
            print(f'  ∟ "{s}": {state_dict[s]}')

    @Slot(None, name="about")
    def about(self):
        """Show simple About dialog."""
        QMessageBox.about(
            self,
            "About",
            f"{__APP_NAME__} v{__version__}\n"
            f"\n"
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
            f"PySide6 {pyside6_version}\n"
            f"\n"
            f"Copyright 2022 - {datetime.now().year}\n"
            f"Single Cell Facility\n"
            f"D-BSSE\n"
            f"ETH Zurich\n"
            f"Switzerland",
        )

    @Slot(None, name="check_remote_for_updates")
    def check_remote_for_updates(self):
        """Check for application updates."""

        # Check for updates
        code, version, error = check_for_updates()

        # Process the output
        if code == -1:
            # Something went wrong: report
            html = f"<b>Error! {error}</b><br /><br /><br />Please make sure you are connected to the internet.<br />If this error persists, please <a href='https://github.com/bsse-scf/pyMINFLUX/issues/'>report it</a>."

        elif code == 0:
            # No new version
            html = f"<b>Congratulations!</b><br /><br />You are running the latest version ({pyminflux.__version__}) of {pyminflux.__APP_NAME__}."

        elif code == 1:
            # Show a dialog with a link to the download page
            html = f"<b>There is a new version ({version}) of {pyminflux.__APP_NAME__}!</b><br /><br />You can download it from the <a href='https://github.com/bsse-scf/pyMINFLUX/releases/latest'>release page</a>."

        else:
            raise ValueError("Unexpected code!")

        # Show the dialog
        dialog = QDialog()
        dialog.setWindowTitle("Check for updates")
        dialog.setMinimumSize(400, 180)
        dialog.setFixedHeight(180)
        layout = QVBoxLayout(dialog)
        text_browser = QTextBrowser()
        text_browser.setStyleSheet("background-color: transparent;")
        text_browser.setOpenExternalLinks(True)
        text_browser.insertHtml(html)
        layout.addWidget(text_browser)
        button = QPushButton("OK")
        button.clicked.connect(dialog.close)
        layout.addWidget(button)
        dialog.exec_()

    @Slot(None, name="open_analyzer")
    def open_analyzer(self):
        """Initialize and open the analyzer."""
        if self.analyzer is None:
            self.analyzer = Analyzer(self.processor)
            self.wizard.wizard_filters_run.connect(self.analyzer.plot)
            self.request_sync_external_tools.connect(self.analyzer.plot)
            self.wizard.efo_bounds_modified.connect(self.analyzer.change_efo_bounds)
            self.wizard.cfr_bounds_modified.connect(self.analyzer.change_cfr_bounds)
            self.analyzer.data_filters_changed.connect(self.full_update_ui)
            self.analyzer.cfr_threshold_factor_changed.connect(
                self.wizard.change_cfr_threshold_factor
            )
            self.analyzer.efo_bounds_changed.connect(self.wizard.change_efo_bounds)
            self.analyzer.cfr_bounds_changed.connect(self.wizard.change_cfr_bounds)
            if self.time_inspector is not None:
                self.analyzer.data_filters_changed.connect(self.time_inspector.update)
            if self.trace_stats_viewer is not None:
                self.analyzer.data_filters_changed.connect(
                    self.trace_stats_viewer.update
                )
            if self.trace_length_viewer is not None:
                self.analyzer.data_filters_changed.connect(
                    self.trace_length_viewer.update
                )
            self.analyzer.plot()
        self.analyzer.show()
        self.analyzer.activateWindow()

    @Slot(None, name="open_time_inspector")
    def open_time_inspector(self):
        """Initialize and open the Time Inspector."""
        if self.time_inspector is None:
            self.time_inspector = TimeInspector(self.processor)
            self.time_inspector.dataset_time_filtered.connect(self.full_update_ui)
            self.wizard.wizard_filters_run.connect(self.time_inspector.update)
            self.request_sync_external_tools.connect(self.time_inspector.update)
        if self.analyzer is not None:
            self.analyzer.data_filters_changed.connect(self.time_inspector.update)
            self.time_inspector.dataset_time_filtered.connect(self.analyzer.plot)
        if self.trace_stats_viewer is not None:
            self.time_inspector.dataset_time_filtered.connect(
                self.trace_stats_viewer.update
            )
        if self.trace_length_viewer is not None:
            self.time_inspector.dataset_time_filtered.connect(
                self.trace_length_viewer.update
            )
        self.time_inspector.show()
        self.time_inspector.activateWindow()

    @Slot(None, name="open_color_unmixer")
    def open_color_unmixer(self):
        """Initialize and open the color unmixer."""
        if self.color_unmixer is None:
            self.color_unmixer = ColorUnmixer(self.processor)
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.wizard.set_fluorophore_list
            )
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.plot_selected_parameters
            )
            self.wizard.wizard_filters_run.connect(self.plot_selected_parameters)
        if self.trace_stats_viewer is not None:
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.trace_stats_viewer.update
            )
        if self.trace_length_viewer is not None:
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.trace_length_viewer.update
            )
        self.color_unmixer.show()
        self.color_unmixer.activateWindow()

    @Slot(None, name="open_options_dialog")
    def open_options_dialog(self):
        """Open the options dialog."""
        if self.options is None:
            self.options = Options()
            self.options.min_trace_length_option_changed.connect(
                self.update_min_trace_length
            )
        self.options.show()
        self.options.activateWindow()

    @Slot(None, name="update_min_trace_length")
    def update_min_trace_length(self):
        if self.processor is not None:
            self.processor.min_trace_length = self.state.min_trace_length

    @Slot(None, name="open_trace_stats_viewer")
    def open_trace_stats_viewer(self):
        """Open the trace stats viewer."""
        if self.trace_stats_viewer is None:
            self.trace_stats_viewer = TraceStatsViewer(self.processor)
            self.request_sync_external_tools.connect(self.trace_stats_viewer.update)
            self.wizard.request_fluorophore_ids_reset.connect(
                self.trace_stats_viewer.update
            )
            self.wizard.wizard_filters_run.connect(self.trace_stats_viewer.update)
            self.trace_stats_viewer.export_trace_stats_requested.connect(
                self.export_filtered_stats
            )
            self.wizard.fluorophore_id_changed.connect(self.trace_stats_viewer.update)
        if self.color_unmixer is not None:
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.trace_stats_viewer.update
            )
        if self.analyzer is not None:
            self.analyzer.data_filters_changed.connect(self.trace_stats_viewer.update)
        self.trace_stats_viewer.show()
        self.trace_stats_viewer.activateWindow()

    @Slot(None, name="open_trace_length_viewer")
    def open_trace_length_viewer(self):
        """Open the trace length viewer."""
        if self.trace_length_viewer is None:
            self.trace_length_viewer = TraceLengthViewer(self.processor)
            self.request_sync_external_tools.connect(self.trace_length_viewer.update)
            self.wizard.request_fluorophore_ids_reset.connect(
                self.trace_length_viewer.update
            )
            self.wizard.wizard_filters_run.connect(self.trace_length_viewer.update)
            self.wizard.fluorophore_id_changed.connect(self.trace_length_viewer.update)
        if self.color_unmixer is not None:
            self.color_unmixer.fluorophore_ids_assigned.connect(
                self.trace_length_viewer.update
            )
        if self.analyzer is not None:
            self.analyzer.data_filters_changed.connect(self.trace_length_viewer.update)
        self.trace_length_viewer.show()
        self.trace_length_viewer.activateWindow()

    @Slot(None, name="open_frc_tool")
    def open_frc_tool(self):
        """Open the FRC tool."""
        if self.frc_tool is None:
            self.frc_tool = FRCTool(self.processor)
        self.frc_tool.show()
        self.frc_tool.activateWindow()

    @Slot(list, name="show_selected_points_by_indices_in_dataviewer")
    def show_selected_points_by_indices_in_dataviewer(self, points):
        """Show the data for the selected points in the dataframe viewer."""

        # Extract indices of the rows corresponding to the selected points
        indices = []
        for p in points:
            indices.append(p.index())

        # Sort the indices
        indices = sorted(indices)

        # Get the filtered dataframe subset corresponding to selected indices
        df = self.processor.select_by_indices(
            indices=indices, from_weighted_locs=self.state.plot_average_localisations
        )

        # Update the dataviewer
        self.data_viewer.set_data(df)

        # Inform
        point_str = "event" if len(indices) == 1 else "events"
        print(f"Selected {len(indices)} {point_str}.")

    @Slot(tuple, tuple, name="show_selected_points_by_range_in_dataviewer")
    def show_selected_points_by_range_in_dataviewer(
        self, x_param, y_param, x_range, y_range
    ):
        """Select the data by x and y range and show in the dataframe viewer."""

        # Get the filtered dataframe subset contained in the provided x and y ranges
        df = self.processor.select_by_2d_range(
            x_param,
            y_param,
            x_range,
            y_range,
            from_weighted_locs=self.state.plot_average_localisations,
        )

        # Update the dataviewer
        self.data_viewer.set_data(df)

        # Inform
        point_str = "event" if len(df.index) == 1 else "events"
        print(f"Selected {len(df.index)} {point_str}.")

    @Slot(tuple, tuple, name="crop_data_by_range")
    def crop_data_by_range(self, x_param, y_param, x_range, y_range):
        """Filter the data by x and y range and show in the dataframe viewer."""

        # Filter the dataframe by the passed x and y ranges
        self.processor.filter_by_2d_range(x_param, y_param, x_range, y_range)

        # Update the Analyzer
        if self.analyzer is not None:
            self.analyzer.plot()

        # Update the Fluorophore Detector?
        if self.color_unmixer is not None:
            # No need to update
            pass

        # Update the Temporal Inspector?
        if self.time_inspector is not None:
            # No need to update
            pass

        # Update the ui
        self.full_update_ui()

        # Make sure to autoupdate the axis (on load only)
        self.plotter.getViewBox().enableAutoRange(axis=ViewBox.XYAxes, enable=True)

        # Signal that the external viewers and tools should be updated
        self.request_sync_external_tools.emit()

    def update_weighted_average_localization_option_and_plot(self):
        """Update the weighted average localization option in the Processor and re-plot."""
        if self.processor is not None:
            self.processor.use_weighted_localizations = (
                self.state.weigh_avg_localization_by_eco
            )
        self.plot_selected_parameters()

    def plot_selected_parameters(self):
        """Plot the localizations."""

        # Remove the previous plots
        self.plotter.remove_points()

        # If there is nothing to plot, return here
        if self.processor is None:
            return

        # If an only if the requested parameters are "x" and "y" (in any order),
        # we consider the State.plot_average_localisations property.
        if (self.state.x_param == "x" and self.state.y_param == "y") or (
            self.state.x_param == "y" and self.state.y_param == "x"
        ):
            if self.state.plot_average_localisations:
                # Get the (potentially filtered) averaged dataframe
                dataframe = self.processor.weighted_localizations
            else:
                # Get the (potentially filtered) full dataframe
                dataframe = self.processor.filtered_dataframe

        else:
            # Get the (potentially filtered) full dataframe
            dataframe = self.processor.filtered_dataframe

        # Extract values
        x = dataframe[self.state.x_param].values
        y = dataframe[self.state.y_param].values
        tid = dataframe["tid"].values
        fid = dataframe["fluo"].values

        # Always plot the (x, y) coordinates in the 2D plotter
        self.plotter.plot_parameters(
            tid=tid,
            fid=fid,
            x=x,
            y=y,
            x_param=self.state.x_param,
            y_param=self.state.y_param,
        )

    def show_processed_dataframe(self, dataframe=None):
        """
        Displays the results for current frame in the data viewer.
        """

        # Is there data to process?
        if self.processor is None:
            self.data_viewer.clear()
            return

        if dataframe is None:
            # Get the (potentially filtered) dataframe
            dataframe = self.processor.filtered_dataframe()

        # Pass the dataframe to the pdDataViewer
        self.data_viewer.set_data(dataframe)

    @Slot(int, name="update_fluorophore_id_in_processor_and_broadcast")
    def update_fluorophore_id_in_processor_and_broadcast(self, index):
        """Update the fluorophore ID in the processor and broadcast the change to all parties."""

        # Update the processor
        self.processor.current_fluorophore_id = index

        # Update all views
        self.full_update_ui()

        # Update the analyzer as well
        if self.analyzer is not None:
            self.analyzer.plot()

    def reset_fluorophore_ids(self):
        """Reset the fluorophore IDs."""

        # Reset
        self.processor.reset()

        # Update UI
        self.update_fluorophore_id_in_processor_and_broadcast(0)
