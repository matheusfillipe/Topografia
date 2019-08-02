# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_gera_tracado_1.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GeraTracadoDialog(object):
    def setupUi(self, GeraTracadoDialog):
        GeraTracadoDialog.setObjectName("GeraTracadoDialog")
        GeraTracadoDialog.resize(395, 100)
        GeraTracadoDialog.setMaximumSize(QtCore.QSize(425, 287))
        GeraTracadoDialog.setSizeGripEnabled(False)
        GeraTracadoDialog.setModal(False)
        self.gridLayout = QtWidgets.QGridLayout(GeraTracadoDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(0, 0, 0, 6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lblName = QtWidgets.QLabel(GeraTracadoDialog)
        self.lblName.setObjectName("lblName")
        self.horizontalLayout.addWidget(self.lblName)
        self.txtNorth = QtWidgets.QLineEdit(GeraTracadoDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtNorth.sizePolicy().hasHeightForWidth())
        self.txtNorth.setSizePolicy(sizePolicy)
        self.txtNorth.setObjectName("txtNorth")
        self.horizontalLayout.addWidget(self.txtNorth)
        self.txtEste = QtWidgets.QLineEdit(GeraTracadoDialog)
        self.txtEste.setObjectName("txtEste")
        self.horizontalLayout.addWidget(self.txtEste)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnCancela = QtWidgets.QPushButton(GeraTracadoDialog)
        self.btnCancela.setObjectName("btnCancela")
        self.horizontalLayout_2.addWidget(self.btnCancela)
        self.btnCapture = QtWidgets.QPushButton(GeraTracadoDialog)
        self.btnCapture.setObjectName("btnCapture")
        self.horizontalLayout_2.addWidget(self.btnCapture)
        self.btnOK = QtWidgets.QPushButton(GeraTracadoDialog)
        self.btnOK.setObjectName("btnOK")
        self.horizontalLayout_2.addWidget(self.btnOK)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(GeraTracadoDialog)
        self.btnCapture.clicked.connect(GeraTracadoDialog.reject)
        self.btnOK.clicked.connect(GeraTracadoDialog.accept)
        self.btnCancela.clicked.connect(GeraTracadoDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(GeraTracadoDialog)

    def retranslateUi(self, GeraTracadoDialog):
        _translate = QtCore.QCoreApplication.translate
        GeraTracadoDialog.setWindowTitle(_translate("GeraTracadoDialog", "Gera Traçado"))
        self.lblName.setText(_translate("GeraTracadoDialog", "Ponto Inicial  "))
        self.txtNorth.setPlaceholderText(_translate("GeraTracadoDialog", "North"))
        self.txtEste.setPlaceholderText(_translate("GeraTracadoDialog", "Este"))
        self.btnCancela.setText(_translate("GeraTracadoDialog", "Cancela"))
        self.btnCapture.setText(_translate("GeraTracadoDialog", "Capturar"))
        self.btnOK.setText(_translate("GeraTracadoDialog", "OK"))


