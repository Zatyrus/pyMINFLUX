import sys
from pathlib import Path

from PySide6 import QtGui
from PySide6.QtCore import QSettings, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from pyminflux import __version__
from pyminflux.processor import MinFluxProcessor
from pyminflux.reader import MinFluxReader

__APP_NAME__ = "pyMinFlux"

import pyminflux.resources
from pyminflux.state import State
from pyminflux.ui.analyzer import Analyzer
from pyminflux.ui.dataviewer import DataViewer
from pyminflux.ui.emittingstream import EmittingStream
from pyminflux.ui.options import Options
from pyminflux.ui.plotter import Plotter
from pyminflux.ui.plotter_3d import Plotter3D
from pyminflux.ui.ui_main_window import Ui_MainWindow


class PyMinFluxMainWindow(QMainWindow, Ui_MainWindow):
    """
    Main application window.
    """

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

        # Dialogs and widgets
        self.data_viewer = None
        self.analyzer = None
        self.plotter = None
        self.plotter3D = None
        self.options = None

        # Read the application settings
        app_settings = QSettings("ch.ethz.bsse.scf", "pyminflux")
        self.last_selected_path = app_settings.value("io/last_selected_path", ".")
        self.state.min_num_loc_per_trace = int(
            app_settings.value("options/min_num_loc_per_trace", 1)
        )

        # Initialize in-window widgets
        self.setup_data_viewer()
        self.setup_data_plotter()
        self.options = Options()

        # Set up signals and slots
        self.setup_conn()

        # Keep a reference to the MinFluxProcessor
        self.minfluxprocessor = None

        # Install the custom output stream
        sys.stdout = EmittingStream()
        sys.stdout.signal_textWritten.connect(self.print_to_console)

        # Print a welcome message to the console
        print(f"Welcome to {__APP_NAME__}.")

    def setup_conn(self):
        """Set up signals and slots."""

        # Menu actions
        self.ui.actionLoad.triggered.connect(self.select_and_open_numpy_file)
        self.ui.actionOptions.triggered.connect(self.open_options_dialog)
        self.ui.actionQuit.triggered.connect(self.quit_application)
        self.ui.actionConsole.changed.connect(self.toggle_dock_console_visibility)
        self.ui.actionData_viewer.changed.connect(self.toggle_dataviewer_visibility)
        self.ui.action3D_Plotter.triggered.connect(self.open_3d_plotter)
        self.ui.actionAnalyzer.triggered.connect(self.open_analyzer)
        self.ui.actionState.triggered.connect(self.print_current_state)

        # Other connections
        self.plotter.locations_selected.connect(self.highlight_selected_locations)

    def enable_ui_components_on_loaded_data(self):
        """Enable UI components."""
        self.ui.actionAnalyzer.setEnabled(True)

    def disable_ui_components_on_closed_data(self):
        """Disable UI components."""
        self.ui.actionAnalyzer.setEnabled(False)

    def full_update_ui(self):
        """
        Updates the UI completely (after a project load, for instance).
        :return:
        """
        self.plotter.clear()
        dataframe = self.minfluxprocessor.filtered_dataframe
        self.plot_localizations(dataframe)
        self.show_processed_dataframe(dataframe)
        print(f"Retrieved {len(dataframe.index)} events.")

    def update_plots(self):
        """
        Update the UI after a change.
        :return:
        """
        self.plotter.clear()
        self.plot_localizations()

    def print_to_console(self, text):
        """
        Append text to the QTextEdit.
        """
        cursor = self.ui.txConsole.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.ui.txConsole.setTextCursor(cursor)

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

            # Close the external dialogs
            if self.plotter3D is not None:
                self.plotter3D.close()
                self.plotter3D = None

            if self.analyzer is not None:
                self.analyzer.close()
                self.analyzer = None

            if self.options is not None:
                self.options.close()
                self.options = None

            # Store the application settings
            if self.last_selected_path != "":
                app_settings = QSettings("ch.ethz.bsse.scf", "pyminflux")
                app_settings.setValue(
                    "io/last_selected_path", str(self.last_selected_path)
                )

            # Restore sys.stdout
            sys.stdout = sys.__stdout__
            sys.stdout.flush()

            # Now exit
            event.accept()

    def setup_data_viewer(self):
        """
        Set up the data viewer.
        """

        # Initialize widget if needed
        if self.data_viewer is None:
            self.data_viewer = DataViewer()

        # Add to the UI
        self.ui.splitter_layout.addWidget(self.data_viewer)

        # Show the widget
        self.data_viewer.show()

    def setup_data_plotter(self):
        """Setup 2D in-window plotter."""

        # 2D plotter
        self.plotter = Plotter()

        # Add to the UI
        self.ui.splitter_layout.addWidget(self.plotter)

        # Show the widget
        self.data_viewer.show()

    @Slot(None, name="quit_application")
    def quit_application(self):
        """Quit the application."""
        self.close()

    @Slot(bool, name="toggle_dock_console_visibility")
    def toggle_dock_console_visibility(self):
        """Toggle the visibility of the console dock widget."""
        if self.ui.actionConsole.isChecked():
            self.ui.dwBottom.show()
        else:
            self.ui.dwBottom.hide()

    @Slot(bool, name="toggle_dataviewer_visibility")
    def toggle_dataviewer_visibility(self):
        """Toggle the visibility of the console dock widget."""
        if self.data_viewer is not None:
            if self.ui.actionData_viewer.isChecked():
                self.data_viewer.show()
            else:
                self.data_viewer.hide()

    @Slot(None, name="select_and_open_numpy_file")
    def select_and_open_numpy_file(self):
        """
        Pick NumPy MINFLUX data file to open.
        :return: void
        """

        # Open a file dialog for the user to pick an .npy file
        res = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            str(self.last_selected_path),
            "NumPy binary file (*.npy);;All files (*.*)",
        )
        filename = res[0]
        if filename != "":

            # Reset the state machine
            self.state.reset()

            # Open the file
            self.last_selected_path = Path(filename).parent
            minfluxreader = MinFluxReader(filename)

            # Show some info
            print(minfluxreader)

            # Add initialize the processor with the reader
            self.minfluxprocessor = MinFluxProcessor(minfluxreader)

            # Show the filename on the main window
            self.setWindowTitle(
                f"{__APP_NAME__} v{__version__} - [{Path(filename).name}]"
            )

            # Close the Analyzer
            if self.analyzer is not None:
                self.analyzer.close()
                self.analyzer = None

            # Close the 3D plotter
            if self.plotter3D is not None:
                self.plotter3D.close()
                self.plotter3D = None

            # Update the ui
            self.full_update_ui()

            # Enable selected ui components
            self.enable_ui_components_on_loaded_data()

    @Slot(None, name="print_current_state")
    def print_current_state(self):
        """Print current contents of the state machine (DEBUG)."""
        print(f"{self.state.asdict()}")

    @Slot(None, name="self.open_analyzer")
    def open_analyzer(self):
        """Initialize and open the analyzer."""
        if self.analyzer is None:
            self.analyzer = Analyzer(self.minfluxprocessor)
            self.analyzer.data_filters_changed.connect(self.full_update_ui)
            self.analyzer.plot()
        self.analyzer.show()
        self.analyzer.activateWindow()

    @Slot(None, name="open_options_dialog")
    def open_options_dialog(self):
        """Open the options dialog."""
        if self.options is None:
            self.options = Options()
        self.options.show()
        self.options.activateWindow()

    @Slot(list, name="highlight_selected_locations")
    def highlight_selected_locations(self, points):
        """Highlight selected locations in the dataframe viewer and scroll to the first one."""

        # Extract indices of the rows corresponding to the selected points
        indices = []
        for n, p in enumerate(points):
            indices.append(p.index())
            if n > 100:
                print(f"Too many points ({len(points)}), only selecting the first 100.")
                break

        # Update the dataviewer
        self.data_viewer.select_and_scroll_to_rows(indices)

    def plot_localizations(self, dataframe=None):
        """Plot the localizations."""

        if self.minfluxprocessor is None:
            self.plotter.remove_points()
            return

        # Remove the previous plots
        self.plotter.remove_points()

        if dataframe is None:
            # Get the (potentially filtered) dataframe
            dataframe = self.minfluxprocessor.filtered_dataframe

        # Always plot the (x, y) coordinates in the 2D plotter
        self.plotter.plot_localizations(
            x=dataframe["x"],
            y=dataframe["y"],
        )

        # If the dataset is 3D, also plot the coordinates in the 3D plotter.
        if self.minfluxprocessor.is_3d:
            self.plot_localizations_3d(dataframe[["x", "y", "z"]].values)

    def plot_localizations_3d(self, coords=None):
        """If the acquisition is 3D and the Show Plotter menu is checked, show the 3D plotter.

        If coords is None, filters may be applied.
        """

        # Only plot if the View 3D Plotter is open
        if self.plotter3D is None:
            return

        if coords is None:
            dataframe = self.minfluxprocessor.filtered_dataframe
            if dataframe is None:
                return
            coords = dataframe[["x", "y", "z"]].values

        # Plot new data (old data will be dropped)
        self.plotter3D.plot(coords)

        # Show the plotter
        self.plotter3D.show()

    @Slot(None, name="open_3d_plotter")
    def open_3d_plotter(self):
        """Open 3D plotter."""

        """Initialize and open the analyzer."""
        if self.plotter3D is None:
            self.plotter3D = Plotter3D()
            if (
                self.minfluxprocessor is not None
                and self.minfluxprocessor.num_values > 0
            ):
                self.plot_localizations_3d(
                    self.minfluxprocessor.filtered_dataframe[["x", "y", "z"]].values
                )
        self.plotter3D.show()
        self.plotter3D.activateWindow()

    def show_processed_dataframe(self, dataframe=None):
        """
        Displays the results for current frame in the data viewer.
        """

        # Is there data to process?
        if self.minfluxprocessor is None:
            self.data_viewer.clear()
            return

        if dataframe is None:
            # Get the (potentially filtered) dataframe
            dataframe = self.minfluxprocessor.filtered_dataframe()

        # Pass the dataframe to the pdDataViewer
        self.data_viewer.set_data(dataframe)

        # Optimize the table view columns
        self.data_viewer.optimize()
