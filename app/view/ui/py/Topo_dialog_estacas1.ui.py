# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_estacas1.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ProjetoEstradas(object):
    def setupUi(self, ProjetoEstradas):
        ProjetoEstradas.setObjectName("ProjetoEstradas")
        ProjetoEstradas.resize(894, 508)
        self.gridLayout = QtWidgets.QGridLayout(ProjetoEstradas)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(ProjetoEstradas)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tableEstacas = QtWidgets.QTableWidget(self.groupBox)
        self.tableEstacas.setObjectName("tableEstacas")
        self.tableEstacas.setColumnCount(0)
        self.tableEstacas.setRowCount(0)
        self.horizontalLayout.addWidget(self.tableEstacas)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btnOpen = QtWidgets.QPushButton(self.groupBox)
        self.btnOpen.setObjectName("btnOpen")
        self.verticalLayout.addWidget(self.btnOpen)
        self.btnOpenCv = QtWidgets.QPushButton(self.groupBox)
        self.btnOpenCv.setObjectName("btnOpenCv")
        self.verticalLayout.addWidget(self.btnOpenCv)
        self.btnOpenCSV = QtWidgets.QPushButton(self.groupBox)
        self.btnOpenCSV.setObjectName("btnOpenCSV")
        self.verticalLayout.addWidget(self.btnOpenCSV)
        self.btnNovo = QtWidgets.QPushButton(self.groupBox)
        self.btnNovo.setObjectName("btnNovo")
        self.verticalLayout.addWidget(self.btnNovo)
        self.btnGerarTracado = QtWidgets.QPushButton(self.groupBox)
        self.btnGerarTracado.setObjectName("btnGerarTracado")
        self.buttonGroup_2 = QtWidgets.QButtonGroup(ProjetoEstradas)
        self.buttonGroup_2.setObjectName("buttonGroup_2")
        self.buttonGroup_2.addButton(self.btnGerarTracado)
        self.verticalLayout.addWidget(self.btnGerarTracado)
        self.btnApagar = QtWidgets.QPushButton(self.groupBox)
        self.btnApagar.setObjectName("btnApagar")
        self.buttonGroup_2.addButton(self.btnApagar)
        self.verticalLayout.addWidget(self.btnApagar)
        self.btnCancela = QtWidgets.QPushButton(self.groupBox)
        self.btnCancela.setObjectName("btnCancela")
        self.verticalLayout.addWidget(self.btnCancela)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.retranslateUi(ProjetoEstradas)
        self.btnCancela.clicked.connect(ProjetoEstradas.reject)
        self.btnOpen.clicked.connect(ProjetoEstradas.accept)
        self.btnNovo.clicked.connect(ProjetoEstradas.accept)
        self.btnOpenCSV.clicked.connect(ProjetoEstradas.accept)
        self.btnGerarTracado.clicked.connect(ProjetoEstradas.reject)
        self.btnOpenCv.clicked.connect(ProjetoEstradas.accept)
        QtCore.QMetaObject.connectSlotsByName(ProjetoEstradas)

    def retranslateUi(self, ProjetoEstradas):
        _translate = QtCore.QCoreApplication.translate
        ProjetoEstradas.setWindowTitle(_translate("ProjetoEstradas", "Projeto de Estradas"))
        self.groupBox.setTitle(_translate("ProjetoEstradas", "Arquivos de estacas salvos no projeto"))
        self.btnOpen.setText(_translate("ProjetoEstradas", "Abrir"))
        self.btnOpenCv.setText(_translate("ProjetoEstradas", "Abrir Verticais"))
        self.btnOpenCSV.setText(_translate("ProjetoEstradas", "Abrir Arquivo CSV"))
        self.btnNovo.setText(_translate("ProjetoEstradas", "Novo arquivo de estacas"))
        self.btnGerarTracado.setText(_translate("ProjetoEstradas", "Gerar Traçado"))
        self.btnApagar.setText(_translate("ProjetoEstradas", "Apagar Arquivo"))
        self.btnCancela.setText(_translate("ProjetoEstradas", "Cancelar"))


