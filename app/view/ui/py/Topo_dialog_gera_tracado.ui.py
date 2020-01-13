# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_gera_tracado.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GeraTracadoDialog(object):
    def setupUi(self, GeraTracadoDialog):
        GeraTracadoDialog.setObjectName("GeraTracadoDialog")
        GeraTracadoDialog.resize(399, 287)
        GeraTracadoDialog.setMaximumSize(QtCore.QSize(399, 287))
        GeraTracadoDialog.setSizeGripEnabled(False)
        self.gridLayout = QtWidgets.QGridLayout(GeraTracadoDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(GeraTracadoDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtNorthStart = QtWidgets.QLineEdit(GeraTracadoDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtNorthStart.sizePolicy().hasHeightForWidth())
        self.txtNorthStart.setSizePolicy(sizePolicy)
        self.txtNorthStart.setObjectName("txtNorthStart")
        self.gridLayout.addWidget(self.txtNorthStart, 0, 1, 1, 1)
        self.txtEsteStart = QtWidgets.QLineEdit(GeraTracadoDialog)
        self.txtEsteStart.setObjectName("txtEsteStart")
        self.gridLayout.addWidget(self.txtEsteStart, 0, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(GeraTracadoDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.txtNorthEnd = QtWidgets.QLineEdit(GeraTracadoDialog)
        self.txtNorthEnd.setObjectName("txtNorthEnd")
        self.gridLayout.addWidget(self.txtNorthEnd, 1, 1, 1, 1)
        self.txtEsteEnd = QtWidgets.QLineEdit(GeraTracadoDialog)
        self.txtEsteEnd.setObjectName("txtEsteEnd")
        self.gridLayout.addWidget(self.txtEsteEnd, 1, 2, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(GeraTracadoDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 3)

        self.retranslateUi(GeraTracadoDialog)
        self.buttonBox.accepted.connect(GeraTracadoDialog.accept)
        self.buttonBox.rejected.connect(GeraTracadoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(GeraTracadoDialog)

    def retranslateUi(self, GeraTracadoDialog):
        _translate = QtCore.QCoreApplication.translate
        GeraTracadoDialog.setWindowTitle(_translate("GeraTracadoDialog", "Gera Traçado"))
        self.label.setText(_translate("GeraTracadoDialog", "Ponto Inicial"))
        self.txtNorthStart.setPlaceholderText(_translate("GeraTracadoDialog", "North"))
        self.txtEsteStart.setPlaceholderText(_translate("GeraTracadoDialog", "Este"))
        self.label_3.setText(_translate("GeraTracadoDialog", "Ponto Final"))
        self.txtNorthEnd.setPlaceholderText(_translate("GeraTracadoDialog", "North"))
        self.txtEsteEnd.setPlaceholderText(_translate("GeraTracadoDialog", "Este"))


