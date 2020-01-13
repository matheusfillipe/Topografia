# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'compor_curvas.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(613, 626)
        Dialog.setMinimumSize(QtCore.QSize(580, 0))
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.btnAdd = QtWidgets.QPushButton(Dialog)
        self.btnAdd.setObjectName("btnAdd")
        self.gridLayout.addWidget(self.btnAdd, 0, 1, 1, 1)
        self.comboBox = QtWidgets.QComboBox(Dialog)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 1, 0, 1, 3)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 2, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Composição das Curvas"))
        self.btnAdd.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Inserir tipo de curva definida a esquerda</p><p><br/></p></body></html>"))
        self.btnAdd.setText(_translate("Dialog", "Adicionar"))
        self.comboBox.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Tipo de curva:</p><p>Circular: Curva com Raio Constante</p><p>Espiral: Clotóide ou Espiral de Cornu</p></body></html>"))
        self.comboBox.setItemText(0, _translate("Dialog", "Circular"))
        self.comboBox.setItemText(1, _translate("Dialog", "Circular com Transição Simétrica"))
        self.comboBox.setItemText(2, _translate("Dialog", "Tangente"))
        self.comboBox.setItemText(3, _translate("Dialog", "Espiral de Entrada"))
        self.comboBox.setItemText(4, _translate("Dialog", "Espiral de Saída"))


