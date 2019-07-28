# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_perfil.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PerfilTrecho(object):
    def setupUi(self, PerfilTrecho):
        PerfilTrecho.setObjectName("PerfilTrecho")
        PerfilTrecho.resize(590, 169)
        self.gridLayout = QtWidgets.QGridLayout(PerfilTrecho)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(PerfilTrecho)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.comboEstaca1 = QtWidgets.QComboBox(PerfilTrecho)
        self.comboEstaca1.setObjectName("comboEstaca1")
        self.comboEstaca1.addItem("")
        self.gridLayout.addWidget(self.comboEstaca1, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(PerfilTrecho)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 2, 1, 1)
        self.comboEstaca2 = QtWidgets.QComboBox(PerfilTrecho)
        self.comboEstaca2.setObjectName("comboEstaca2")
        self.comboEstaca2.addItem("")
        self.gridLayout.addWidget(self.comboEstaca2, 0, 3, 1, 1)
        self.btnCalcular = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCalcular.setObjectName("btnCalcular")
        self.gridLayout.addWidget(self.btnCalcular, 1, 1, 1, 2)
        self.lblTipo = QtWidgets.QLabel(PerfilTrecho)
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName("lblTipo")
        self.gridLayout.addWidget(self.lblTipo, 2, 1, 1, 3)

        self.retranslateUi(PerfilTrecho)
        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)

    def retranslateUi(self, PerfilTrecho):
        _translate = QtCore.QCoreApplication.translate
        PerfilTrecho.setWindowTitle(_translate("PerfilTrecho", "Perfil do trecho"))
        self.label.setText(_translate("PerfilTrecho", "Estaca 1"))
        self.comboEstaca1.setItemText(0, _translate("PerfilTrecho", "Selecione Estaca Inicial"))
        self.label_2.setText(_translate("PerfilTrecho", "Estaca 2"))
        self.comboEstaca2.setItemText(0, _translate("PerfilTrecho", "Selecione Estaca Final"))
        self.btnCalcular.setText(_translate("PerfilTrecho", "Calcular"))
        self.lblTipo.setText(_translate("PerfilTrecho", "Plano"))


