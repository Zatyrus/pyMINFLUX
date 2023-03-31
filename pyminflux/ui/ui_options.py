# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
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
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)


class Ui_Options(object):
    def setupUi(self, Options):
        if not Options.objectName():
            Options.setObjectName("Options")
        Options.resize(489, 261)
        self.gridLayout = QGridLayout(Options)
        self.gridLayout.setObjectName("gridLayout")
        self.hlMinNumTraces = QHBoxLayout()
        self.hlMinNumTraces.setObjectName("hlMinNumTraces")
        self.lbMinTIDNum = QLabel(Options)
        self.lbMinTIDNum.setObjectName("lbMinTIDNum")

        self.hlMinNumTraces.addWidget(self.lbMinTIDNum)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.hlMinNumTraces.addItem(self.horizontalSpacer)

        self.leMinTIDNum = QLineEdit(Options)
        self.leMinTIDNum.setObjectName("leMinTIDNum")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leMinTIDNum.sizePolicy().hasHeightForWidth())
        self.leMinTIDNum.setSizePolicy(sizePolicy)

        self.hlMinNumTraces.addWidget(self.leMinTIDNum)

        self.gridLayout.addLayout(self.hlMinNumTraces, 0, 0, 1, 1)

        self.cbColorLocsByTID = QCheckBox(Options)
        self.cbColorLocsByTID.setObjectName("cbColorLocsByTID")

        self.gridLayout.addWidget(self.cbColorLocsByTID, 6, 0, 1, 1)

        self.lbInfoImmediate = QLabel(Options)
        self.lbInfoImmediate.setObjectName("lbInfoImmediate")
        font = QFont()
        font.setItalic(True)
        self.lbInfoImmediate.setFont(font)

        self.gridLayout.addWidget(self.lbInfoImmediate, 5, 0, 1, 1)

        self.lbInfo = QLabel(Options)
        self.lbInfo.setObjectName("lbInfo")
        self.lbInfo.setFont(font)

        self.gridLayout.addWidget(self.lbInfo, 3, 0, 1, 1)

        self.line = QFrame(Options)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout.addWidget(self.line, 4, 0, 1, 1)

        self.hlEFOBinSize = QHBoxLayout()
        self.hlEFOBinSize.setObjectName("hlEFOBinSize")
        self.lbEFOBinSize = QLabel(Options)
        self.lbEFOBinSize.setObjectName("lbEFOBinSize")

        self.hlEFOBinSize.addWidget(self.lbEFOBinSize)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.hlEFOBinSize.addItem(self.horizontalSpacer_2)

        self.leEFOBinSize = QLineEdit(Options)
        self.leEFOBinSize.setObjectName("leEFOBinSize")
        sizePolicy.setHeightForWidth(self.leEFOBinSize.sizePolicy().hasHeightForWidth())
        self.leEFOBinSize.setSizePolicy(sizePolicy)

        self.hlEFOBinSize.addWidget(self.leEFOBinSize)

        self.gridLayout.addLayout(self.hlEFOBinSize, 1, 0, 1, 1)

        self.cbWeightAvgLocByECO = QCheckBox(Options)
        self.cbWeightAvgLocByECO.setObjectName("cbWeightAvgLocByECO")

        self.gridLayout.addWidget(self.cbWeightAvgLocByECO, 7, 0, 1, 1)

        self.pbSetDefault = QPushButton(Options)
        self.pbSetDefault.setObjectName("pbSetDefault")

        self.gridLayout.addWidget(self.pbSetDefault, 9, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )

        self.gridLayout.addItem(self.verticalSpacer, 8, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lbEFOExpectedCutoffFrequency = QLabel(Options)
        self.lbEFOExpectedCutoffFrequency.setObjectName("lbEFOExpectedCutoffFrequency")

        self.horizontalLayout.addWidget(self.lbEFOExpectedCutoffFrequency)

        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.leEFOExpectedCutoffFrequency = QLineEdit(Options)
        self.leEFOExpectedCutoffFrequency.setObjectName("leEFOExpectedCutoffFrequency")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(
            self.leEFOExpectedCutoffFrequency.sizePolicy().hasHeightForWidth()
        )
        self.leEFOExpectedCutoffFrequency.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.leEFOExpectedCutoffFrequency)

        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.retranslateUi(Options)

        QMetaObject.connectSlotsByName(Options)

    # setupUi

    def retranslateUi(self, Options):
        Options.setWindowTitle(QCoreApplication.translate("Options", "Options", None))
        self.lbMinTIDNum.setText(
            QCoreApplication.translate(
                "Options", "Minimum number of trace localizations", None
            )
        )
        self.cbColorLocsByTID.setText(
            QCoreApplication.translate(
                "Options", "Color-code localizations by TID in main plotter", None
            )
        )
        self.lbInfoImmediate.setText(
            QCoreApplication.translate(
                "Options",
                "Changes below will be applied immediately to all open views.",
                None,
            )
        )
        self.lbInfo.setText(
            QCoreApplication.translate(
                "Options",
                "Changes above will be applied when loading new data or when filtering in the Analyzer.",
                None,
            )
        )
        self.lbEFOBinSize.setText(
            QCoreApplication.translate(
                "Options", "EFO bin size (Hz): set to 0 for automatic estimation", None
            )
        )
        self.cbWeightAvgLocByECO.setText(
            QCoreApplication.translate(
                "Options",
                "Use relative ECO count for weighted average localization calculation",
                None,
            )
        )
        self.pbSetDefault.setText(
            QCoreApplication.translate("Options", "Set as new default", None)
        )
        self.lbEFOExpectedCutoffFrequency.setText(
            QCoreApplication.translate(
                "Options", "EFO expected cutoff frequency (Hz)", None
            )
        )

    # retranslateUi
