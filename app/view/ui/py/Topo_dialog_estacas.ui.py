# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_estacas.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(965, 575)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btnEstacas = QtWidgets.QPushButton(Dialog)
        self.btnEstacas.setObjectName("btnEstacas")
        self.buttonGroup = QtWidgets.QButtonGroup(Dialog)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.btnEstacas)
        self.verticalLayout.addWidget(self.btnEstacas)
        self.btnDuplicar = QtWidgets.QPushButton(Dialog)
        self.btnDuplicar.setObjectName("btnDuplicar")
        self.verticalLayout.addWidget(self.btnDuplicar)
        self.btnLayer = QtWidgets.QPushButton(Dialog)
        self.btnLayer.setObjectName("btnLayer")
        self.buttonGroup.addButton(self.btnLayer)
        self.verticalLayout.addWidget(self.btnLayer)
        self.btnCurva = QtWidgets.QPushButton(Dialog)
        self.btnCurva.setObjectName("btnCurva")
        self.verticalLayout.addWidget(self.btnCurva)
        self.btnPerfil = QtWidgets.QPushButton(Dialog)
        self.btnPerfil.setObjectName("btnPerfil")
        self.buttonGroup.addButton(self.btnPerfil)
        self.verticalLayout.addWidget(self.btnPerfil)
        self.btnSave = QtWidgets.QPushButton(Dialog)
        self.btnSave.setEnabled(True)
        self.btnSave.setObjectName("btnSave")
        self.buttonGroup.addButton(self.btnSave)
        self.verticalLayout.addWidget(self.btnSave)
        self.btnSaveCSV = QtWidgets.QPushButton(Dialog)
        self.btnSaveCSV.setObjectName("btnSaveCSV")
        self.buttonGroup.addButton(self.btnSaveCSV)
        self.verticalLayout.addWidget(self.btnSaveCSV)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)
        self.tableWidget = QtWidgets.QTableWidget(Dialog)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 5, 1)
        self.btnCotaTIFF = QtWidgets.QPushButton(Dialog)
        self.btnCotaTIFF.setObjectName("btnCotaTIFF")
        self.gridLayout.addWidget(self.btnCotaTIFF, 1, 1, 1, 1)
        self.btnCotaPC = QtWidgets.QPushButton(Dialog)
        self.btnCotaPC.setObjectName("btnCotaPC")
        self.gridLayout.addWidget(self.btnCotaPC, 2, 1, 1, 1)
        self.btnCota = QtWidgets.QPushButton(Dialog)
        self.btnCota.setObjectName("btnCota")
        self.gridLayout.addWidget(self.btnCota, 3, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Traçado Horizontal"))
        self.btnEstacas.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Recalcula as estacas com base em uma layer</p></body></html>"))
        self.btnEstacas.setText(_translate("Dialog", "Recalcular Estacas"))
        self.btnDuplicar.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Duplica os dados horizontai com, curvas da estaca e perfil vertical com curvas.</p></body></html>"))
        self.btnDuplicar.setText(_translate("Dialog", "Duplicar"))
        self.btnLayer.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Gera uma layer com o traçado. Essa layer não conterá informações de curvas.</p></body></html>"))
        self.btnLayer.setText(_translate("Dialog", "Plotar"))
        self.btnCurva.setToolTip(_translate("Dialog", "<html><head/><body><p>Calcular Curvas Horizontais</p></body></html>"))
        self.btnCurva.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Cria e gerencia as curvas do traçado horizontal.</p></body></html>"))
        self.btnCurva.setText(_translate("Dialog", "Curvas"))
        self.btnPerfil.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Define o greide.</p></body></html>"))
        self.btnPerfil.setText(_translate("Dialog", "Perfil de trecho"))
        self.btnSave.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Salva a tabela horizontal e as edições manuais feitas nela</p></body></html>"))
        self.btnSave.setText(_translate("Dialog", "Salvar"))
        self.btnSaveCSV.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Exporta a tabela em uma planilha.</p></body></html>"))
        self.btnSaveCSV.setText(_translate("Dialog", "Salvar em CSV"))
        self.btnCotaTIFF.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Extrair cotas de um arquivo raster de imagem tiff</p></body></html>"))
        self.btnCotaTIFF.setText(_translate("Dialog", "Obter Cotas\n"
"via GeoTIFF"))
        self.btnCotaPC.setText(_translate("Dialog", "Obter Cotas\n"
"via DXF"))
        self.btnCota.setText(_translate("Dialog", "Obter Cotas \n"
"via Google"))


