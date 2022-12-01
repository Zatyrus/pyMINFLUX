from PySide6.QtCore import QSettings, Signal, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QDialog

from pyminflux.state import State

from .ui_options import Ui_Options


class Options(QDialog, Ui_Options):

    # Signal that the options have changed
    options_changed = Signal(name="options_changed")

    def __init__(self, parent=None):
        """Constructor."""

        # Call the base class
        super().__init__(parent=parent)

        # Initialize the dialog
        self.ui = Ui_Options()
        self.ui.setupUi(self)

        # Keep a reference to the singleton State class
        self.state = State()

        # Set defaults
        self.ui.leMinTIDNum.setText(str(self.state.min_num_loc_per_trace))
        self.ui.leMinTIDNum.setValidator(QIntValidator(bottom=0))

        # Set signal-slot connections
        self.setup_conn()

    def setup_conn(self):
        """Set up signal-slot connections."""
        self.ui.leMinTIDNum.textChanged.connect(self.persist_min_num_loc_per_trace)
        self.ui.pbSetDefault.clicked.connect(self.set_as_new_default)

    @Slot(str, name="persist_thresh_factor")
    def persist_min_num_loc_per_trace(self, text):
        try:
            min_num_loc_per_trace = int(text)
        except Exception as _:
            return
        self.state.min_num_loc_per_trace = min_num_loc_per_trace

    @Slot(str, name="set_as_new_default")
    def set_as_new_default(self, text):
        """Persist current selection as new default options."""

        # Read the application settings
        app_settings = QSettings("ch.ethz.bsse.scf", "pyminflux")
        app_settings.setValue(
            "options/min_num_loc_per_trace", str(self.state.min_num_loc_per_trace)
        )
