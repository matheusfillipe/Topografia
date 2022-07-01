from __future__ import print_function
from builtins import str
from builtins import object
# -*- coding: utf-8 -*-

from qgis.PyQt import QtGui, QtWidgets

from ..model.utils import msgLog
from ..model.config import Config as ModelConfig
from ..view.config import TopoConfig
from ..model.estacas import Estacas
from ..controller import perfil


class Config(object):
    def __init__(self, iface):
        """
            ----view------
            criacao da tela config
        """
        self.conf = TopoConfig(iface)
        # defino o modelo de dados
        self.model = ModelConfig()
        self.events()
        self.crs = self.model.crs
        self.ordem_mapa = self.model.ordem_mapa

        self.update()

    def events(self):
        self.conf.txtCRS.textChanged.connect(self.listCRS)
        # self.txtCRS.textChanged(self.listCRS)
        self.conf.tableCRS.itemClicked.connect(self.itemClick)
        self.conf.comboClasse.currentIndexChanged.connect(
            self.mudancaClasseProjeto)
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
            self.conf.tableCRS.setItem(
                k, 0, QtWidgets.QTableWidgetItem(str(x[1])))
            self.conf.tableCRS.setItem(
                k, 1, QtWidgets.QTableWidgetItem(str(x[0])))
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
        filename = u"{0}".format(self.conf.new_file()[0])
        if filename in ["", None]:
            return
        if filename.endswith(".zip"):
            ModelConfig.instance().store("FILE_PATH", filename)
        else:
            ModelConfig.instance().store("FILE_PATH", filename+".zip")
        self.model.newfile(filename)

    def openfile(self, filename=None):
        if filename is None:
            filename = u"{0}".format(self.conf.open_file()[0])
            if filename in ["", None] or not(filename.endswith('zip')):
                self.conf.error(
                    'SELECIONE UM ARQUIVO zip PARA SER ABERTO\n'+filename+' invalido!')
                return

        ModelConfig.instance().store("FILE_PATH", filename)
        self.model.openfile(filename)
        self.update()
        return filename

    def savefile(self):
        self.model.filename = u"{0}".format(self.model.filename)
        fromf = self.model.filename
        try:
            filename = u"{0}".format(self.conf.new_file()[0])
            if filename in ["", None]:
                return
            if not filename.endswith(".zip"):
                filename += ".zip"
            self.model.filename = filename
            self.model.savefile(fromf=fromf)
            self.update()
        except:
            self.newfile()
            if self.model.filename not in [None, '']:
                self.savefile()
            else:
                return None
        ModelConfig.instance().store("FILE_PATH", self.model.filename)
        return self.model.filename

    def carregamapa(self):
        self.changeCRS()
        from ..model.utils import addGoogleXYZTiles
        from qgis.PyQt.QtCore import QSettings
        addGoogleXYZTiles(self.iface, QSettings)
        try:
            self.conf.carregamapa(self.model.tipo_mapa)
        except Exception as e:
            msgLog(str(e))
            return

    def carregacarta(self):
        self.conf.carregacarta(self.model)

    def update(self):
        self.changeCRS()
        txt = self.model.listCRSID()
        self.conf.update(self.model, txt)

    def runTrasversalDialog(self):
        self.trasversalDialog = perfil.Ui_sessaoTipo(self.conf)
        self.trasversalDialog.save.connect(self.savePerfil)
        self.trasversalDialog.showMaximized()
        self.trasversalDialog.exec_()

    def savePerfil(self):
        pass

    def run(self):
        self.conf.show()
        crs = self.crs
        result = self.conf.exec_()
        if result:
            self.changeCRS()

            self.dataTopo = [
                self.conf.planoMin.value(),
                self.conf.planoMax.value(),
                self.conf.onduladoMin.value(),
                self.conf.onduladoMax.value(),
                self.conf.montanhosoMin.value(),
                self.conf.montanhosoMax.value()
            ]
            self.model.dataTopo = self.dataTopo
            self.model.CSV_DELIMITER = self.conf.txtCSV.text()
            print(self.model.CSV_DELIMITER)
            print(self.model.UNITS)
            self.crs = self.model.crs
            self.update()
        else:
            self.model.crs = crs
