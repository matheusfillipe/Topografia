# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'estacas.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

import os
import sip
from PyQt4 import QtCore, QtGui
from PyQt4 import uic

from PyQt4.QtCore import QObject
from PyQt4.QtCore import QVariant, SIGNAL
from PyQt4.QtGui import QAbstractItemView
from PyQt4.QtGui import QDialog
from qgis._core import QgsCoordinateReferenceSystem
from qgis._core import QgsFeature
from qgis._core import QgsField
from qgis._core import QgsGeometry
from qgis._core import QgsMapLayerRegistry
from qgis._core import QgsPoint
from qgis._core import QgsRectangle
from qgis._core import QgsVectorLayer
from qgis._gui import QgsMapCanvasLayer
from qgis._gui import QgsMapToolEmitPoint
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *

from ..model.utils import decdeg2dms
import subprocess
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
sip.setapi('QString',2)
sip.setapi('QVariant',2)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

FORMESTACA1_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_estacas1.ui'))
FORMGERATRACADO_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_gera_tracado_1.ui'))

rb = QgsRubberBand(iface.mapCanvas(), QGis.Point)
premuto = False
point0 = iface.mapCanvas().getCoordinateTransform().toMapCoordinates(0, 0)


class PointTool(QgsMapTool):
    def __init__(self, canvas, ref, method):

        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.estacasUI = ref
        self.method = method
        self.callback = eval('self.estacasUI.%s'%self.method)



    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.callback(self.canvas.getCoordinateTransform().toMapCoordinates(x, y))



class Dialog(QDialog):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        button = QtGui.QPushButton('Open Dialog', self)
        button.clicked.connect(self.handleOpenDialog)
        self.resize(300, 200)
        self._dialog = None

    def handleOpenDialog(self):
        if self._dialog is None:
            self._dialog = QtGui.QDialog(self)
            self._dialog.resize(200, 100)
        self._dialog.show()


class GeraTracadoUI(QtGui.QDialog,FORMGERATRACADO_CLASS):
    def __init__(self, iface):
        super(GeraTracadoUI, self).__init__(None)
        self.iface = iface
        self.setupUi(self)


class EstacasUI(QtGui.QDialog,FORMESTACA1_CLASS):
    def __init__(self, iface):
        super(EstacasUI, self).__init__(None)
        self.iface = iface
        self.setupUi(self)
        self.setupUi2(self)
        self.points = []
        self.crs = 1
        self.edit = False
        self.dialog = QtGui.QDialog(None)
        self.actual_point = None

    def error(self, msg):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "AVISO",
                                   u"%s" % msg,
                                   QtGui.QMessageBox.NoButton, None)
        msgBox.addButton("OK", QtGui.QMessageBox.AcceptRole)
        # msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
        msgBox.exec_()

    def openCSV(self):
        filename = QtGui.QFileDialog.getOpenFileName()
        if filename in ["", None]: return None
        fileDB, ok = QtGui.QInputDialog.getText(None, "Nome do arquivo", u"Nome do arquivo a ser salvo no projeto:")
        if not ok:
            return None
        return filename, fileDB

    def new(self,recalcular=False,layerName=None):
        mapCanvas = self.iface.mapCanvas()
        itens = []
        for i in range(mapCanvas.layerCount() - 1, -1, -1):
            try:
                layer = mapCanvas.layer(i)
                layerName = layer.name()
                itens.append(layerName)
            except:
                pass
        if len(itens) == 0: return None
        if not recalcular:
            filename, ok = QtGui.QInputDialog.getText(None, "Nome do arquivo", u"Nome do arquivo:")
            if not ok:
                return None
        else:
            filename = ''

        if layerName is None:
            layerList = QgsMapLayerRegistry.instance().mapLayersByName(layerName)
            layer = None
            if layerList:
                layer = layerList[-1]
        else:
            itens = []
            for i in range(mapCanvas.layerCount() - 1, -1, -1):
                try:
                    layer = mapCanvas.layer(i)
                    layerName = layer.name()
                    itens.append(layerName)
                except:
                    pass
            item, ok = QtGui.QInputDialog.getItem(None, "Camada com tracado", u"Selecione a camada com o traçado:",
                                                  itens,
                                                  0, False)
            if not(ok) or not(item):
                return None
            else:
                layerList = QgsMapLayerRegistry.instance().mapLayersByName(item)
                layer = None
                if layerList:
                    layer = layerList[0]

        dist, ok = QtGui.QInputDialog.getDouble(None, "Distancia", u"Distancia entre estacas:", 20.0, -10000,
                                                10000, 2)
        if not ok or dist<=0:
            return None
        estaca, ok = QtGui.QInputDialog.getInteger(None, "Estaca Inicial", u"Estaca Inicial:", 0, -10000, 10000, 2)

        if not ok:
            return None
        return filename, layer, dist, estaca

    def fill_table_index(self, files):
        self.tableEstacas.setRowCount(0)
        self.tableEstacas.clearContents()
        for i,f in enumerate(files):
            self.tableEstacas.insertRow(self.tableEstacas.rowCount())
            for j,f2 in enumerate(f):
                self.tableEstacas.setItem(i,j,QtGui.QTableWidgetItem(u"%s" % f2))

    def create_line(self,p1,p2,name):
        layer = QgsVectorLayer('LineString?crs=%s'%int(self.crs), name, "memory")
        mycrs = QgsCoordinateReferenceSystem(int(self.crs), 0)
        self.reprojectgeographic = QgsCoordinateTransform(self.iface.mapCanvas().mapRenderer().destinationCrs(), mycrs)
        pr = layer.dataProvider()
        line = QgsFeature()
        line.setGeometry(QgsGeometry.fromPolyline([self.reprojectgeographic.transform(p1), self.reprojectgeographic.transform(p2)]))
        pr.addFeatures([line])
        #layer.setCrs(QgsCoordinateReferenceSystem(int(self.crs), 0))
        layer.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayer(layer)

        return p1, p2

    def create_point(self,p1,name):
        layer = QgsVectorLayer('Point?crs=%s'%int(self.crs), name, "memory")
        mycrs = QgsCoordinateReferenceSystem(int(self.crs), 0)
        self.reprojectgeographic = QgsCoordinateTransform(self.iface.mapCanvas().mapRenderer().destinationCrs(), mycrs)
        pr = layer.dataProvider()
        point = QgsFeature()
        point.setGeometry(QgsGeometry.fromPoint(self.reprojectgeographic.transform(p1)))
        pr.addFeatures([point])
        #layer.setCrs(QgsCoordinateReferenceSystem(int(self.crs), 0))
        layer.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayer(layer)

        return p1

    def get_click_coordenate(self,point, mouse):
        self.actual_point=QgsPoint(point)
        if self.tracado_dlg.txtNorthStart.text().strip()=='':
            self.tracado_dlg.txtNorthStart.setText("%f"%self.actual_point.y())
            self.tracado_dlg.txtEsteStart.setText("%f"%self.actual_point.x())
        elif self.tracado_dlg.txtNorthEnd.text().strip()=='':
            self.tracado_dlg.txtNorthEnd.setText("%f"%self.actual_point.y())
            self.tracado_dlg.txtEsteEnd.setText("%f"%self.actual_point.x())

    def gera_tracado_pontos(self,inicial=False,final=False,callback_inst=None,callback_method=None,crs=None):
        if (not(inicial) and not(final)):
            self.callback = eval('callback_inst.%s'%callback_method)
            self.crs = crs
            self.tracado_dlg_inicial = GeraTracadoUI(self.iface)
            self.tracado_dlg_inicial.lblName.setText("Ponto Inicial")
            self.tracado_dlg_inicial.btnCapture.clicked.connect(self.capture_point_inicial)
            self.tracado_dlg_final = GeraTracadoUI(self.iface)
            self.tracado_dlg_final.lblName.setText("Ponto Final")
            self.tracado_dlg_final.btnCapture.clicked.connect(self.capture_point_final)
        if (not(inicial) and not(final)) or not(final):
            ok = self.tracado_dlg_inicial.exec_()
            if not(ok):
                return None
            else:
                pn = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",","."))
                pe = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",","."))
                self.gera_tracado_ponto_inicial(QgsPoint(pe, pn)) 

        if (not(inicial) and not(final)) or not(inicial):
            ok = self.tracado_dlg_final.exec_()
            if not(ok):
                return None
            else:
                pn = float(self.tracado_dlg_final.txtNorth.text().strip().replace(",","."))
                pe = float(self.tracado_dlg_final.txtEste.text().strip().replace(",","."))
                self.gera_tracado_ponto_final(QgsPoint(pe, pn))

        if inicial and final:
            p1n = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",","."))
            p1e = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",","."))
            p2n = float(self.tracado_dlg_final.txtNorth.text().strip().replace(",", "."))
            p2e = float(self.tracado_dlg_final.txtEste.text().strip().replace(",", "."))
            self.iface.mapCanvas().setMapTool(None)
            self.callback(pontos=self.create_line(QgsPoint(p1e, p1n), QgsPoint(p2e, p2n), "Diretriz"),parte=1)

    def gera_tracado_ponto_inicial(self,point):
        self.tracado_dlg_inicial.txtNorth.setText("%f"%point.y())
        self.tracado_dlg_inicial.txtEste.setText("%f"%point.x())
        ok = self.tracado_dlg_inicial.exec_()
        if not(ok):
            return None
        else:
            pn = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",","."))
            pe = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",","."))
            self.gera_tracado_ponto_final(QgsPoint(pe, pn))
        
        #self.gera_tracado_pontos(inicial=True)
        self.gera_tracado_pontos(final=True)

    def gera_tracado_ponto_final(self,point):
        self.tracado_dlg_final.txtNorth.setText("%f"%point.y())
        self.tracado_dlg_final.txtEste.setText("%f"%point.x())
        ok = self.tracado_dlg_final.exec_()
        if not(ok):
            return None
        else:
            pn = float(self.tracado_dlg_final.txtNorth.text().strip().replace(",","."))
            pe = float(self.tracado_dlg_final.txtEste.text().strip().replace(",","."))
            #self.gera_tracado_ponto_final(QgsPoint(pe, pn))
        
        #self.gera_tracado_pontos(final=True)
        self.gera_tracado_pontos(inicial=True,final=True)
    
    def capture_point_inicial(self):
        tool = PointTool(self.iface.mapCanvas(),self,'gera_tracado_ponto_inicial')
        self.iface.mapCanvas().setMapTool(tool)

    def capture_point_final(self):
        tool = PointTool(self.iface.mapCanvas(),self,'gera_tracado_ponto_final')
        self.iface.mapCanvas().setMapTool(tool)


    def exit_dialog(self, points, crs):
        self.dialog.close()

        layer = QgsVectorLayer('LineString', self.name_tracado, "memory")
        pr = layer.dataProvider()
        print points
        anterior = QgsPoint(points[0])
        fets=[]
        for p in points[1:]:
            fet = QgsFeature(layer.pendingFields())
            fet.setGeometry(QgsGeometry.fromPolyline([anterior, QgsPoint(p)]))
            fets.append(fet)
            anterior = QgsPoint(p)
        pr.addFeatures(fets)
        self.crs = crs
        layer.setCrs(QgsCoordinateReferenceSystem(int(crs), 0))
        layer.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayer(layer)

    def gera_tracado_vertices(self,pointerEmitter):
        self.iface.mapCanvas().setMapTool(pointerEmitter)
        self.name_tracado = "TracadoNovo"
        self.dialog.resize(200, 100)
        self.dialog.setWindowTitle(u"Traçado")
        self.dialog.btnClose = QtGui.QPushButton("Terminar",self.dialog)
        self.dialog.show()
        return self.name_tracado



    def setupUi2(self,Form):
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        self.tableEstacas.setColumnCount(3)
        self.tableEstacas.setRowCount(0)
        self.tableEstacas.setColumnWidth(0, 54)
        self.tableEstacas.setColumnWidth(1, 254)
        self.tableEstacas.setColumnWidth(2, 154)
        self.tableEstacas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableEstacas.setHorizontalHeaderLabels((u"ID",u"Arquivo",u"Data criação"))




class Estacas(QtGui.QDialog):

    def __init__(self,iface):
        super(Estacas, self).__init__(None)
        self.iface = iface
        self.setupUi(self)

    def clear(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()

    def saveEstacasCSV(self):
        filename = QtGui.QFileDialog.getSaveFileName()
        return filename

    def fill_table(self,(estaca,descricao,progressiva,norte,este,cota,azimute),f=False):
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        k = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(k, 0, QtGui.QTableWidgetItem(u"%s" % estaca))
        self.tableWidget.setItem(k, 1, QtGui.QTableWidgetItem(u"%s" % descricao))
        self.tableWidget.setItem(k, 2, QtGui.QTableWidgetItem(u"%s" % progressiva))
        self.tableWidget.setItem(k, 3, QtGui.QTableWidgetItem(u"%s" % norte))
        self.tableWidget.setItem(k, 4, QtGui.QTableWidgetItem(u"%s" % este))
        self.tableWidget.setItem(k, 5, QtGui.QTableWidgetItem(u"%s" % cota))
        '''if not f:
            naz = decdeg2dms(azimute)
            str_az = "%s* %s\' %s\'\'" % (int(naz[0]), int(naz[1]), naz[2])
            self.tableWidget.setItem(k, 6, QtGui.QTableWidgetItem(str_az))
        else:'''
        self.tableWidget.setItem(k, 6, QtGui.QTableWidgetItem(u"%s" % azimute))

    def get_estacas(self):
        estacas = []
        for i in range(self.tableWidget.rowCount()):
            estaca = []
            for j in range(self.tableWidget.columnCount()):
                estaca.append(self.tableWidget.item(i,j).text())
            estacas.append(estaca)
        return estacas

    def plotar(self):
        vl = QgsVectorLayer("Point", "temporary_points", "memory")
        pr = vl.dataProvider()

        # Enter editing mode
        vl.startEditing()

        # add fields
        pr.addAttributes([QgsField("estaca", QVariant.String), QgsField("descrição", QVariant.String),
                          QgsField("north", QVariant.String), QgsField("este", QVariant.String),
                          QgsField("cota", QVariant.String), QgsField("azimite", QVariant.String)])
        fets = []

        for r in range(self.tableWidget.rowCount()):
            ident = self.tableWidget.item(r, 0).text()
            if ident in ["", None]: break
            fet = QgsFeature(vl.pendingFields())
            n = 0.0
            e = 0.0
            try:
                es = self.tableWidget.item(r, 0).text()
                d = self.tableWidget.item(r, 1).text()
                n = float(self.tableWidget.item(r, 3).text())
                e = float(self.tableWidget.item(r, 4).text())
                c = float(self.tableWidget.item(r, 5).text())
                a = self.tableWidget.item(r, 6).text()
            except:
                break
            fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(e, n)))
            fet.setAttributes([es, d, n, e, c, a])
            fets.append(fet)
        pr.addFeatures(fets)
        vl.commitChanges()
        QgsMapLayerRegistry.instance().addMapLayer(vl)

    def openTIFF(self):
        filename = QtGui.QFileDialog.getOpenFileName(filter="Image files (*.tiff *.tif)")
        return filename
        
    def openDXF(self):
        filename = QtGui.QFileDialog.getOpenFileName(filter="Autocad files (*.dxf)")
        return filename
        
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        Form.resize(919, 510)
        self.tableWidget = QtGui.QTableWidget(Form)
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 761, 511))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.modelSource = self.tableWidget.model()
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels((u"Estaca",u"Descrição",u"Progressiva",u"Norte",u"Este",u"Cota",u"Azimute"))

        self.btnRead = QtGui.QPushButton(Form)
        self.btnRead.setText("Abrir Arquivo")
        self.btnRead.setGeometry(QtCore.QRect(769, 16, 143, 27))
        self.btnRead.setObjectName(_fromUtf8("btnRead"))
        #self.btnRead.clicked.connect(self.carrega)

        self.btnEstacas = QtGui.QPushButton(Form)
        self.btnEstacas.setText("Recalcular Estacas")
        self.btnEstacas.setGeometry(QtCore.QRect(769, 50, 143, 27))
        self.btnEstacas.setObjectName(_fromUtf8("btnEstacas"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)

        self.btnLayer = QtGui.QPushButton(Form)
        self.btnLayer.setText("Plotar")
        self.btnLayer.setGeometry(QtCore.QRect(769, 84, 143, 27))
        self.btnLayer.setObjectName(_fromUtf8("btnLayer"))
        #self.btnLayer.clicked.connect(self.plot)

        self.btnPerfil = QtGui.QPushButton(Form)
        self.btnPerfil.setText("Perfil do trecho")
        self.btnPerfil.setGeometry(QtCore.QRect(769, 118, 143, 27))
        self.btnPerfil.setObjectName(_fromUtf8("btnPerfil"))
        #self.btnPerfil.clicked.connect(self.perfil)

        self.btnSaveCSV = QtGui.QPushButton(Form)
        self.btnSaveCSV.setText("Salvar em CSV")
        self.btnSaveCSV.setGeometry(QtCore.QRect(769, 152, 143, 27))
        self.btnSaveCSV.setObjectName(_fromUtf8("btnSave"))
        #self.btnSave.clicked.connect(self.save)
        self.btnSave = QtGui.QPushButton(Form)
        self.btnSave.setText("Salvar")
        self.btnSave.setGeometry(QtCore.QRect(769, 186, 143, 27))
        self.btnSave.setObjectName(_fromUtf8("btnSave"))

        self.btnCurva = QtGui.QPushButton(Form)
        self.btnCurva.setText("Curvas...")
        self.btnCurva.setGeometry(QtCore.QRect(769, 220, 143, 27))
        self.btnCurva.setObjectName(_fromUtf8("btnCurva"))
        #self.btnCurva.clicked.connect(self.perfil)

        self.btnCotaTIFF = QtGui.QPushButton(Form)
        self.btnCotaTIFF.setText("Obter Cotas\nvia GeoTIFF")
        self.btnCotaTIFF.setGeometry(QtCore.QRect(769, 300, 143, 44))
        self.btnCotaTIFF.setObjectName(_fromUtf8("btnCotaTIFF"))

        self.btnCotaPC = QtGui.QPushButton(Form)
        self.btnCotaPC.setText("Obter Cotas\nvia Pontos cotados\nDXF")
        self.btnCotaPC.setGeometry(QtCore.QRect(769, 375, 143, 50))
        self.btnCotaPC.setObjectName(_fromUtf8("btnCotaPC"))


        self.btnCota = QtGui.QPushButton(Form)
        self.btnCota.setText("Obter Cotas\nvia Google")
        self.btnCota.setGeometry(QtCore.QRect(769, 450, 143, 44))
        self.btnCota.setObjectName(_fromUtf8("btnCota"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Traçado Horizontal", "Traçado Horizontal", None))






