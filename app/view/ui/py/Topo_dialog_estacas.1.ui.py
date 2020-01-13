# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_estacas.1.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(945, 513)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.tableWidget = QtWidgets.QTableWidget(Dialog)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 2, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setObjectName("pushButton")
        self.buttonGroup = QtWidgets.QButtonGroup(Dialog)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.pushButton)
        self.verticalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setObjectName("pushButton_2")
        self.buttonGroup.addButton(self.pushButton_2)
        self.verticalLayout.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(Dialog)
        self.pushButton_3.setObjectName("pushButton_3")
        self.buttonGroup.addButton(self.pushButton_3)
        self.verticalLayout.addWidget(self.pushButton_3)
        self.pushButton_4 = QtWidgets.QPushButton(Dialog)
        self.pushButton_4.setObjectName("pushButton_4")
        self.buttonGroup.addButton(self.pushButton_4)
        self.verticalLayout.addWidget(self.pushButton_4)
        self.pushButton_6 = QtWidgets.QPushButton(Dialog)
        self.pushButton_6.setObjectName("pushButton_6")
        self.buttonGroup.addButton(self.pushButton_6)
        self.verticalLayout.addWidget(self.pushButton_6)
        self.pushButton_5 = QtWidgets.QPushButton(Dialog)
        self.pushButton_5.setEnabled(True)
        self.pushButton_5.setObjectName("pushButton_5")
        self.buttonGroup.addButton(self.pushButton_5)
        self.verticalLayout.addWidget(self.pushButton_5)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)
        self.btnCota = QtWidgets.QPushButton(Dialog)
        self.btnCota.setEnabled(True)
        self.btnCota.setObjectName("btnCota")
        self.gridLayout.addWidget(self.btnCota, 1, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.pushButton.setText(_translate("Dialog", "Abrir Arquivo"))
        self.pushButton_2.setText(_translate("Dialog", "Recalcular Estacas"))
        self.pushButton_3.setText(_translate("Dialog", "Plotar"))
        self.pushButton_4.setText(_translate("Dialog", "Perfil de trecho"))
        self.pushButton_6.setText(_translate("Dialog", "Salvar em CSV"))
        self.pushButton_5.setText(_translate("Dialog", "Salvar"))
        self.btnCota.setText(_translate("Dialog", "Obter Cotas\n"
"via Google"))


