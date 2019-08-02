# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TOPO_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TopoDialogBase(object):
    def setupUi(self, TopoDialogBase):
        TopoDialogBase.setObjectName("TopoDialogBase")
        TopoDialogBase.setWindowModality(QtCore.Qt.WindowModal)
        TopoDialogBase.resize(352, 277)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(TopoDialogBase.sizePolicy().hasHeightForWidth())
        TopoDialogBase.setSizePolicy(sizePolicy)
        TopoDialogBase.setAutoFillBackground(False)
        TopoDialogBase.setSizeGripEnabled(False)
        self.gridLayout = QtWidgets.QGridLayout(TopoDialogBase)
        self.gridLayout.setObjectName("gridLayout")
        self.openFolder = QtWidgets.QPushButton(TopoDialogBase)
        self.openFolder.setObjectName("openFolder")
        self.gridLayout.addWidget(self.openFolder, 0, 0, 1, 1)
        self.openMap = QtWidgets.QPushButton(TopoDialogBase)
        self.openMap.setObjectName("openMap")
        self.gridLayout.addWidget(self.openMap, 1, 0, 1, 1)
        self.crsCombo = QtWidgets.QComboBox(TopoDialogBase)
        self.crsCombo.setAcceptDrops(False)
        self.crsCombo.setEditable(False)
        self.crsCombo.setObjectName("crsCombo")
        self.crsCombo.addItem("")
        self.gridLayout.addWidget(self.crsCombo, 2, 0, 1, 1)
        self.button_box = QtWidgets.QDialogButtonBox(TopoDialogBase)
        self.button_box.setEnabled(True)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.gridLayout.addWidget(self.button_box, 3, 0, 1, 1)
        self.actionOpenFolderAction = QtWidgets.QAction(TopoDialogBase)
        self.actionOpenFolderAction.setObjectName("actionOpenFolderAction")

        self.retranslateUi(TopoDialogBase)
        self.button_box.accepted.connect(TopoDialogBase.accept)
        self.button_box.rejected.connect(TopoDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(TopoDialogBase)

    def retranslateUi(self, TopoDialogBase):
        _translate = QtCore.QCoreApplication.translate
        TopoDialogBase.setWindowTitle(_translate("TopoDialogBase", "Topo"))
        self.openFolder.setText(_translate("TopoDialogBase", "Abrir Cartas"))
        self.openMap.setText(_translate("TopoDialogBase", "Abrir Mapa"))
        self.crsCombo.setItemText(0, _translate("TopoDialogBase", "Selecione qual sistemas de coordenadas"))
        self.actionOpenFolderAction.setText(_translate("TopoDialogBase", "openFolderAction"))


