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
        self.btnNovo = QtWidgets.QPushButton(self.groupBox)
        self.btnNovo.setAutoDefault(False)
        self.btnNovo.setObjectName("btnNovo")
        self.verticalLayout.addWidget(self.btnNovo)
        self.btnOpen = QtWidgets.QPushButton(self.groupBox)
        self.btnOpen.setDefault(True)
        self.btnOpen.setObjectName("btnOpen")
        self.verticalLayout.addWidget(self.btnOpen)
        self.btnOpenCv = QtWidgets.QPushButton(self.groupBox)
        self.btnOpenCv.setAutoDefault(False)
        self.btnOpenCv.setObjectName("btnOpenCv")
        self.verticalLayout.addWidget(self.btnOpenCv)
        self.btnOpenCSV = QtWidgets.QPushButton(self.groupBox)
        self.btnOpenCSV.setAutoDefault(False)
        self.btnOpenCSV.setObjectName("btnOpenCSV")
        self.verticalLayout.addWidget(self.btnOpenCSV)
        self.btnDuplicar = QtWidgets.QPushButton(self.groupBox)
        self.btnDuplicar.setAutoDefault(False)
        self.btnDuplicar.setObjectName("btnDuplicar")
        self.verticalLayout.addWidget(self.btnDuplicar)
        self.btnGerarTracado = QtWidgets.QPushButton(self.groupBox)
        self.btnGerarTracado.setAutoDefault(False)
        self.btnGerarTracado.setObjectName("btnGerarTracado")
        self.buttonGroup_2 = QtWidgets.QButtonGroup(ProjetoEstradas)
        self.buttonGroup_2.setObjectName("buttonGroup_2")
        self.buttonGroup_2.addButton(self.btnGerarTracado)
        self.verticalLayout.addWidget(self.btnGerarTracado)
        self.btnGerarCurvas = QtWidgets.QPushButton(self.groupBox)
        self.btnGerarCurvas.setAutoDefault(False)
        self.btnGerarCurvas.setObjectName("btnGerarCurvas")
        self.verticalLayout.addWidget(self.btnGerarCurvas)
        self.btnApagar = QtWidgets.QPushButton(self.groupBox)
        self.btnApagar.setAutoDefault(False)
        self.btnApagar.setObjectName("btnApagar")
        self.buttonGroup_2.addButton(self.btnApagar)
        self.verticalLayout.addWidget(self.btnApagar)
        self.btnCancela = QtWidgets.QPushButton(self.groupBox)
        self.btnCancela.setAutoDefault(False)
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
        self.btnGerarCurvas.clicked.connect(ProjetoEstradas.accept)
        QtCore.QMetaObject.connectSlotsByName(ProjetoEstradas)

    def retranslateUi(self, ProjetoEstradas):
        _translate = QtCore.QCoreApplication.translate
        ProjetoEstradas.setWindowTitle(_translate("ProjetoEstradas", "Projeto de Estradas"))
        self.groupBox.setTitle(_translate("ProjetoEstradas", "Arquivos de estacas salvos no projeto"))
        self.btnNovo.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Cria um novo arquivo a partir do traçado horizontal definido uma layer.</p></body></html>"))
        self.btnNovo.setText(_translate("ProjetoEstradas", "Novo arquivo de estacas"))
        self.btnOpen.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Traçado horizontal em tabela curvas horizontais, edição do perfil vertical e curvas verticais.</p></body></html>"))
        self.btnOpen.setText(_translate("ProjetoEstradas", "Abrir"))
        self.btnOpenCv.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Tabelas de interseção de estacas, edição do perfil transversal, cálculo de volumes de corte e aterro, diagrama de bruckner</p></body></html>"))
        self.btnOpenCv.setText(_translate("ProjetoEstradas", "Abrir Verticais"))
        self.btnOpenCSV.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Cria o traçado transversal a partir de um arquivo CSV extraído pelo plugin ou no formato do plugin.</p></body></html>"))
        self.btnOpenCSV.setText(_translate("ProjetoEstradas", "Abrir Arquivo CSV"))
        self.btnDuplicar.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Duplica o arquivo selecionado.</p><p>Dados horizontais e a configuração do perfil transversal serão copiados.<br/>A tabela de verticais e de interseção serão recalculadas.</p></body></html>"))
        self.btnDuplicar.setText(_translate("ProjetoEstradas", "Duplicar"))
        self.btnGerarTracado.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Gera um arquivo shapefile que será incluído no projeto contento as tranversais.</p></body></html>"))
        self.btnGerarTracado.setText(_translate("ProjetoEstradas", "Gerar Traçado"))
        self.btnGerarCurvas.setWhatsThis(_translate("ProjetoEstradas", "<html><head/><body><p>Gera um geopackage do projeto que pode conter curvas e tangentes. </p><p>Essa opção é útil caso você queira gerar o traçado e curvas de uma só vez.</p></body></html>"))
        self.btnGerarCurvas.setText(_translate("ProjetoEstradas", "Gerar Curvas"))
        self.btnGerarCurvas.setShortcut(_translate("ProjetoEstradas", "Alt+C"))
        self.btnApagar.setText(_translate("ProjetoEstradas", "Apagar Arquivo"))
        self.btnCancela.setText(_translate("ProjetoEstradas", "Cancelar"))


