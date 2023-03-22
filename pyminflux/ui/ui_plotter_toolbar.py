# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plotter_toolbar.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)


class Ui_PlotterToolbar(object):
    def setupUi(self, PlotterToolbar):
        if not PlotterToolbar.objectName():
            PlotterToolbar.setObjectName("PlotterToolbar")
        PlotterToolbar.resize(791, 31)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlotterToolbar.sizePolicy().hasHeightForWidth())
        PlotterToolbar.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(PlotterToolbar)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 3, -1, 3)
        self.horizontalSpacer_2 = QSpacerItem(
            10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.pbOpenAnalyzer = QPushButton(PlotterToolbar)
        self.pbOpenAnalyzer.setObjectName("pbOpenAnalyzer")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.pbOpenAnalyzer.sizePolicy().hasHeightForWidth()
        )
        self.pbOpenAnalyzer.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pbOpenAnalyzer)

        self.horizontalSpacer = QSpacerItem(
            60, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.lbFluorophoreIndex = QLabel(PlotterToolbar)
        self.lbFluorophoreIndex.setObjectName("lbFluorophoreIndex")
        self.lbFluorophoreIndex.setEnabled(True)
        self.lbFluorophoreIndex.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )

        self.horizontalLayout.addWidget(self.lbFluorophoreIndex)

        self.cbFluorophoreIndex = QComboBox(PlotterToolbar)
        self.cbFluorophoreIndex.addItem("")
        self.cbFluorophoreIndex.setObjectName("cbFluorophoreIndex")
        sizePolicy1.setHeightForWidth(
            self.cbFluorophoreIndex.sizePolicy().hasHeightForWidth()
        )
        self.cbFluorophoreIndex.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.cbFluorophoreIndex)

        self.pbAssignFluorophores = QPushButton(PlotterToolbar)
        self.pbAssignFluorophores.setObjectName("pbAssignFluorophores")
        self.pbAssignFluorophores.setEnabled(False)
        sizePolicy1.setHeightForWidth(
            self.pbAssignFluorophores.sizePolicy().hasHeightForWidth()
        )
        self.pbAssignFluorophores.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pbAssignFluorophores)

        self.horizontalSpacer_3 = QSpacerItem(
            60, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.cbFirstParam = QComboBox(PlotterToolbar)
        self.cbFirstParam.setObjectName("cbFirstParam")
        sizePolicy1.setHeightForWidth(
            self.cbFirstParam.sizePolicy().hasHeightForWidth()
        )
        self.cbFirstParam.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.cbFirstParam)

        self.cbSecondParam = QComboBox(PlotterToolbar)
        self.cbSecondParam.setObjectName("cbSecondParam")
        sizePolicy1.setHeightForWidth(
            self.cbSecondParam.sizePolicy().hasHeightForWidth()
        )
        self.cbSecondParam.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.cbSecondParam)

        self.pbPlot = QPushButton(PlotterToolbar)
        self.pbPlot.setObjectName("pbPlot")
        sizePolicy1.setHeightForWidth(self.pbPlot.sizePolicy().hasHeightForWidth())
        self.pbPlot.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.pbPlot)

        self.horizontalSpacer_4 = QSpacerItem(
            10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_4)

        self.retranslateUi(PlotterToolbar)

        QMetaObject.connectSlotsByName(PlotterToolbar)

    # setupUi

    def retranslateUi(self, PlotterToolbar):
        PlotterToolbar.setWindowTitle(
            QCoreApplication.translate("PlotterToolbar", "Form", None)
        )
        self.pbOpenAnalyzer.setText(
            QCoreApplication.translate("PlotterToolbar", "Analyze", None)
        )
        self.lbFluorophoreIndex.setText(
            QCoreApplication.translate("PlotterToolbar", "Fluorophore", None)
        )
        self.cbFluorophoreIndex.setItemText(
            0, QCoreApplication.translate("PlotterToolbar", "1", None)
        )

        self.pbAssignFluorophores.setText(
            QCoreApplication.translate("PlotterToolbar", "Assign", None)
        )
        self.pbPlot.setText(QCoreApplication.translate("PlotterToolbar", "Plot", None))

    # retranslateUi
