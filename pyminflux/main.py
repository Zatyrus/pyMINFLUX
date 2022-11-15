import sys

from PySide6.QtWidgets import QApplication

from ui.appeventfilter import AppEventFilter
from ui.tracermainwindow import TracerMainWindow

if __name__ == '__main__':

    app = QApplication(sys.argv)
    if sys.platform.startswith("linux"):
        app.setStyle("fusion")
    main = TracerMainWindow()
    main.show()

    # Attach the event filter
    appEventFilter = AppEventFilter()
    app.installEventFilter(appEventFilter)

    # Add some connections
    appEventFilter.signal_zoom_in.connect(main.scene.zoom_in)
    appEventFilter.signal_zoom_out.connect(main.scene.zoom_out)
    appEventFilter.signal_delete_selection.connect(main.delete_selection)

    sys.exit(app.exec())
