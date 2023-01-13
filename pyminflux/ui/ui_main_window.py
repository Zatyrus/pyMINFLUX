# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTime,
    QUrl,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGridLayout,
    QMainWindow,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1276, 957)
        MainWindow.setMinimumSize(QSize(1000, 800))
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName("actionLoad")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionConsole = QAction(MainWindow)
        self.actionConsole.setObjectName("actionConsole")
        self.actionConsole.setCheckable(True)
        self.actionConsole.setChecked(True)
        self.actionData_viewer = QAction(MainWindow)
        self.actionData_viewer.setObjectName("actionData_viewer")
        self.actionData_viewer.setCheckable(True)
        self.actionData_viewer.setChecked(True)
        self.actionSave_plot = QAction(MainWindow)
        self.actionSave_plot.setObjectName("actionSave_plot")
        self.actionCamera_parameters = QAction(MainWindow)
        self.actionCamera_parameters.setObjectName("actionCamera_parameters")
        self.action3D_Plotter = QAction(MainWindow)
        self.action3D_Plotter.setObjectName("action3D_Plotter")
        self.action3D_Plotter.setCheckable(False)
        self.actionAnalyzer = QAction(MainWindow)
        self.actionAnalyzer.setObjectName("actionAnalyzer")
        self.actionAnalyzer.setEnabled(False)
        self.actionState = QAction(MainWindow)
        self.actionState.setObjectName("actionState")
        self.actionOptions = QAction(MainWindow)
        self.actionOptions.setObjectName("actionOptions")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter_layout = QSplitter(self.centralwidget)
        self.splitter_layout.setObjectName("splitter_layout")
        self.splitter_layout.setMaximumSize(QSize(16777215, 16777215))
        self.splitter_layout.setOrientation(Qt.Vertical)

        self.gridLayout.addWidget(self.splitter_layout, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 1276, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dwBottom = QDockWidget(MainWindow)
        self.dwBottom.setObjectName("dwBottom")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dwBottom.sizePolicy().hasHeightForWidth())
        self.dwBottom.setSizePolicy(sizePolicy)
        self.dwBottom.setMaximumSize(QSize(524287, 100))
        self.dwBottom.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.dockWidgetContents.setMinimumSize(QSize(0, 200))
        self.txConsole = QTextEdit(self.dockWidgetContents)
        self.txConsole.setObjectName("txConsole")
        self.txConsole.setGeometry(QRect(10, 10, 16777215, 175))
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.txConsole.sizePolicy().hasHeightForWidth())
        self.txConsole.setSizePolicy(sizePolicy1)
        self.txConsole.setMaximumSize(QSize(16777215, 16777215))
        self.txConsole.setReadOnly(True)
        self.dwBottom.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.dwBottom)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOptions)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuView.addAction(self.actionData_viewer)
        self.menuView.addAction(self.actionConsole)
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionAnalyzer)
        self.menuView.addAction(self.action3D_Plotter)
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionState)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "MainWindow", None)
        )
        self.actionLoad.setText(
            QCoreApplication.translate("MainWindow", "&Load data", None)
        )
        # if QT_CONFIG(tooltip)
        self.actionLoad.setToolTip(
            QCoreApplication.translate(
                "MainWindow", "Load MinFlux binary NumPy data", None
            )
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(shortcut)
        self.actionLoad.setShortcut(
            QCoreApplication.translate("MainWindow", "Ctrl+L", None)
        )
        # endif // QT_CONFIG(shortcut)
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", "Quit", None))
        # if QT_CONFIG(tooltip)
        self.actionQuit.setToolTip(
            QCoreApplication.translate("MainWindow", "Quit application", None)
        )
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(shortcut)
        self.actionQuit.setShortcut("")
        # endif // QT_CONFIG(shortcut)
        self.actionConsole.setText(
            QCoreApplication.translate("MainWindow", "Console", None)
        )
        self.actionData_viewer.setText(
            QCoreApplication.translate("MainWindow", "Data viewer", None)
        )
        self.actionSave_plot.setText(
            QCoreApplication.translate("MainWindow", "Save plot", None)
        )
        self.actionCamera_parameters.setText(
            QCoreApplication.translate("MainWindow", "Camera parameters", None)
        )
        self.action3D_Plotter.setText(
            QCoreApplication.translate("MainWindow", "3D Plotter", None)
        )
        self.actionAnalyzer.setText(
            QCoreApplication.translate("MainWindow", "Analyzer", None)
        )
        self.actionState.setText(
            QCoreApplication.translate("MainWindow", "[DEBUG] Show state", None)
        )
        self.actionOptions.setText(
            QCoreApplication.translate("MainWindow", "Options", None)
        )
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))

    # retranslateUi
