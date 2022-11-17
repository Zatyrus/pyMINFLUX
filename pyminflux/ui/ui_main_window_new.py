# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window_new.ui'
##
## Created by: Qt User Interface Compiler version 6.4.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QDockWidget, QGridLayout, QHBoxLayout,
    QMainWindow, QMenu, QMenuBar, QSizePolicy,
    QStatusBar, QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1276, 957)
        MainWindow.setMinimumSize(QSize(1000, 800))
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionConsole = QAction(MainWindow)
        self.actionConsole.setObjectName(u"actionConsole")
        self.actionConsole.setCheckable(True)
        self.actionConsole.setChecked(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.all_data_layout = QHBoxLayout()
        self.all_data_layout.setObjectName(u"all_data_layout")
        self.dataframe_layout = QGridLayout()
        self.dataframe_layout.setObjectName(u"dataframe_layout")
        self.dataframe_layout.setHorizontalSpacing(0)

        self.all_data_layout.addLayout(self.dataframe_layout)


        self.gridLayout.addLayout(self.all_data_layout, 0, 0, 1, 1)

        self.plotting_layout = QGridLayout()
        self.plotting_layout.setObjectName(u"plotting_layout")
        self.plotting_layout.setHorizontalSpacing(0)

        self.gridLayout.addLayout(self.plotting_layout, 0, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1276, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dwBottom = QDockWidget(MainWindow)
        self.dwBottom.setObjectName(u"dwBottom")
        self.dwBottom.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.dockWidgetContents.setMinimumSize(QSize(0, 200))
        self.txConsole = QTextEdit(self.dockWidgetContents)
        self.txConsole.setObjectName(u"txConsole")
        self.txConsole.setGeometry(QRect(10, 10, 16777215, 200))
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txConsole.sizePolicy().hasHeightForWidth())
        self.txConsole.setSizePolicy(sizePolicy)
        self.txConsole.setMaximumSize(QSize(16777215, 200))
        self.txConsole.setReadOnly(True)
        self.dwBottom.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.dwBottom)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuView.addAction(self.actionConsole)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"&Load data", None))
#if QT_CONFIG(tooltip)
        self.actionLoad.setToolTip(QCoreApplication.translate("MainWindow", u"Load MinFlux binary NumPy data", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionLoad.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+L", None))
#endif // QT_CONFIG(shortcut)
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"&Quit", None))
#if QT_CONFIG(tooltip)
        self.actionQuit.setToolTip(QCoreApplication.translate("MainWindow", u"Quit application", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionQuit.setShortcut("")
#endif // QT_CONFIG(shortcut)
        self.actionConsole.setText(QCoreApplication.translate("MainWindow", u"Console", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
    # retranslateUi

