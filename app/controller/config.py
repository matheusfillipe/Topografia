# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from ..model.config import Config as ModelConfig
from ..view.config import TopoConfig


class Config:
    def __init__(self,iface):
        """
            ----view------
            criacao da tela config
        """
        self.conf = TopoConfig(iface)
        #defino o modelo de dados
        self.model = ModelConfig()
        self.events()
        self.crs = self.model.crs
        self.ordem_mapa = self.model.ordem_mapa

        self.update()

    def events(self):
        self.conf.txtCRS.textChanged.connect(self.listCRS)
        # self.txtCRS.textChanged(self.listCRS)
        self.conf.tableCRS.itemClicked.connect(self.itemClick)
        self.conf.comboClasse.currentIndexChanged.connect(self.mudancaClasseProjeto)
        self.conf.comboMap.currentIndexChanged.connect(self.mudancaMapa)
        self.conf.comboUnits.currentIndexChanged.connect(self.mudancaUnits)

    def changeCRS(self):
        self.conf.changeCRS(self.model.crs)

    def listCRS(self, txt=''):
        crs = self.model.listCRS(txt)
        self.conf.tableCRS.clearContents()
        k = 0
        for x in crs:
            self.conf.tableCRS.insertRow(self.conf.tableCRS.rowCount())
            self.conf.tableCRS.setItem(k, 0, QtGui.QTableWidgetItem(str(x[1])))
            self.conf.tableCRS.setItem(k, 1, QtGui.QTableWidgetItem(str(x[0])))
            k += 1

    def itemClick(self, item):
        crs = int(self.conf.tableCRS.item(item.row(), 0).text())
        self.model.itemClick(crs)

    def mudancaClasseProjeto(self, pos):
        self.model.mudancaClasseProjeto(pos)

    def mudancaMapa(self, pos):
        pos -= 1
        if pos < 0:
            self.model.tipo_mapa = self.ordem_mapa[0]
        else:
            self.model.tipo_mapa = self.ordem_mapa[pos]

    def mudancaUnits(self, pos):
        
        self.model.UNITS = self.model.ordem_units[pos]

    def newfile(self):
        filename = u"%s" % self.conf.new_file()
        if filename in ["",None]:
            return
        self.model.newfile(filename)

    def openfile(self):
        filename = u"%s" % self.conf.open_file()
        if filename in ["",None] or not(filename.endswith('lzip')):
            self.conf.error('SELECIONE UM ARQUIVO lzip PARA SER ABERTO')
            return
        self.model.openfile(filename)
        self.update()
        self.carregamapa()

    def savefile(self):
        self.model.filename = u"%s" % self.model.filename
        try:
            self.model.savefile()
            self.update()
        except:
            self.newfile()
            if self.model.filename not in [None, '']:
                self.savefile()
            else:
                return None
        return self.model.filename

    def carregamapa(self):
        self.changeCRS()
        self.conf.carregamapa(self.model.tipo_mapa)

    def carregacarta(self):
        self.conf.carregacarta(self.model)

    def update(self):
        self.changeCRS()
        txt = self.model.listCRSID()
        self.conf.update(self.model, txt)

    def run(self):
        self.conf.show()
        crs = self.crs
        result = self.conf.exec_()
        if result:
            self.changeCRS()

            self.dataTopo = [
                self.conf.cmpPlanoMin.value(),
                self.conf.cmpPlanoMax.value(),
                self.conf.cmpOnduladoMin.value(),
                self.conf.cmpOnduladoMax.value(),
                self.conf.cmpMontanhosoMin.value(),
                self.conf.cmpMontanhosoMax.value()
            ]
            self.model.dataTopo = self.dataTopo
            self.model.CSV_DELIMITER = self.conf.txtCSV.text()
            print self.model.CSV_DELIMITER
            print self.model.UNITS
            self.crs = self.model.crs
            self.update()
        else:
            self.model.crs = crs
