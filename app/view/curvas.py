from builtins import str
# -*- coding: utf-8 -*-
import os
import sip
from copy import deepcopy

from qgis.core import QgsProject, QgsFields, QgsField, QgsPoint

from ..view.ui.ch import CurvasCompositorDialog, EMPTY_DATA
from ..model.utils import msgLog, PointTool

from ..model.helper.qgsgeometry import *


sip.setapi('QString', 2)

from qgis.PyQt import QtGui, uic, Qt, QtWidgets

import qgis

import shutil
from ..model.config import extractZIP, Config, compactZIP
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QAbstractItemView, QDesktopWidget

from qgis._core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeature

from qgis._core import QgsRectangle
from qgis._core import QgsVectorFileWriter
from qgis._core import QgsVectorLayer
from qgis._core import Qgis

from qgis.utils import *

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt import  QtWidgets

from ..model.helper.calculos import *
from ..model.curvas import Curvas as CurvasModel

FORMCURVA_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../view/ui/Topo_dialog_curva.ui'))

ID_ESTACA = 0
ESTACA = 1
DESCRICAO = 2
PROGRESSIVA = 3
NORTH = 4
ESTE = 5
COTA = 6
AZIMUTE = 7




class Curvas(QtWidgets.QDialog, FORMCURVA_CLASS):
    def __init__(self,view, iface, id_filename, curvas, vertices, tipoClasseProjeto):
        super(Curvas, self).__init__(None)
        self.view=view
        self.iface = iface
        self.model = CurvasModel(id_filename)
        self.estacas = self.model.list_estacas()
        self.estacas_id = [row[0] for row in self.estacas]

        self.curvas = curvas
        self.vertices=vertices

        self.tipo = tipoClasseProjeto[0]
        self.classe = tipoClasseProjeto[1]
        self.id_filename = id_filename
        self.tipo_curva = 0
        self.estacaInicial = self.estacas[0] if self.estacas else 0
        self.estacaFinal = self.estacas[0] if self.estacas else 0
        self.setupUi(self)


        self.Dialog: QtWidgets.QDialog
        self.btnAjuda: QtWidgets.QPushButton
        self.btnApagar: QtWidgets.QPushButton
        self.btnCalcular: QtWidgets.QPushButton
        self.btnCancela: QtWidgets.QPushButton
        self.btnClose: QtWidgets.QPushButton
        self.btnEditar: QtWidgets.QPushButton
        self.btnInsere: QtWidgets.QPushButton
        self.btnNew: QtWidgets.QPushButton
        self.btnRelatorio: QtWidgets.QPushButton
        self.comboCurva: QtWidgets.QComboBox
        self.comboElemento: QtWidgets.QComboBox
        self.comboEstacaFinal: QtWidgets.QComboBox
        self.comboEstacaInicial: QtWidgets.QComboBox
        self.gDadosCurva: QtWidgets.QGroupBox
        self.groupBox: QtWidgets.QGroupBox
        self.groupBox_2: QtWidgets.QGroupBox
        self.label: QtWidgets.QLabel
        self.label_10: QtWidgets.QLabel
        self.label_11: QtWidgets.QLabel
        self.label_12: QtWidgets.QLabel
        self.label_13: QtWidgets.QLabel
        self.label_14: QtWidgets.QLabel
        self.label_15: QtWidgets.QLabel
        self.label_16: QtWidgets.QLabel
        self.label_17: QtWidgets.QLabel
        self.label_18: QtWidgets.QLabel
        self.label_19: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_20: QtWidgets.QLabel
        self.label_21: QtWidgets.QLabel
        self.label_22: QtWidgets.QLabel
        self.label_23: QtWidgets.QLabel
        self.label_24: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.label_5: QtWidgets.QLabel
        self.label_6: QtWidgets.QLabel
        self.label_7: QtWidgets.QLabel
        self.label_8: QtWidgets.QLabel
        self.label_9: QtWidgets.QLabel
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.txtD: QtWidgets.QLineEdit
        self.txtDelta: QtWidgets.QLineEdit
        self.txtDist: QtWidgets.QLineEdit
        self.txtEMAX: QtWidgets.QLineEdit
        self.txtEPC: QtWidgets.QLineEdit
        self.txtEPI: QtWidgets.QLineEdit
        self.txtEPT: QtWidgets.QLineEdit
        self.txtEsteFinal: QtWidgets.QLineEdit
        self.txtEsteInicial: QtWidgets.QLineEdit
        self.txtFMAX: QtWidgets.QLineEdit
        self.txtG20: QtWidgets.QLineEdit
        self.txtI: QtWidgets.QLineEdit
        self.txtNomeFinal: QtWidgets.QLineEdit
        self.txtNomeInicial: QtWidgets.QLineEdit
        self.txtNorthFinal: QtWidgets.QLineEdit
        self.txtNorthInicial: QtWidgets.QLineEdit
        self.txtRMIN: QtWidgets.QLineEdit
        self.txtRUtilizado: QtWidgets.QLineEdit
        self.txtT: QtWidgets.QLineEdit
        self.txtVelocidade: QtWidgets.QLineEdit
        self.deflexao: QtWidgets.QLineEdit
        
        self.txtDist.setText(str(Config.instance().DIST))

        self.buttons=[self.btnAjuda, self.btnApagar, self.btnCalcular, self.btnCancela, self.btnClose, self.btnEditar,
                               self.btnInsere, self.btnNew, self.btnRelatorio ]


        self.curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.fill_comboCurva()

        self.editando = False
        self.update()
        self.eventos()
        self.location_on_the_screen()

    def location_on_the_screen(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0#widget.width()
        y = (screen.height()-widget.height())/2
        self.move(x, y)

    def fill_comboCurva(self):
        c=0
        self.PIs=[]
        self.layer=self.view.curvaLayers[0]
        for vert in self.vertices:
            n=int(vert[0][-1])
            if n==c:
                self.comboCurva.addItem("PI"+str(c))
                self.PIs.append(vert[1])
                c+=1

        if not wasInitialized(self.layer):
            tangentFeaturesFromPointList(self.layer,self.PIs)
            refreshCanvas(self.iface, self.layer)


    def update(self):
        self.curvas = self.model.list_curvas()
        estacas = self.estacas
        self.comboEstacaInicial.addItems([self.tr(estaca[1]) for estaca in self.estacas])
        self.comboEstacaFinal.addItems([self.tr(estaca[1]) for estaca in self.estacas])
        self.comboCurva.clear()
#        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])
        self.fill_comboCurva()

    def eventos(self):
        self.comboCurva.currentIndexChanged.connect(self.mudancaCurva)
        self.comboElemento.currentIndexChanged.connect(self.mudancaTipo)
        self.comboEstacaInicial.currentIndexChanged.connect(self.mudancaEstacaInicial)
        self.comboEstacaFinal.currentIndexChanged.connect(self.mudancaEstacaFinal)
        self.btnNew.clicked.connect(self.new)
        self.btnInsere.clicked.connect(self.insert)
        self.btnApagar.clicked.connect(self.apagar)
        self.btnRelatorio.clicked.connect(self.relatorio)
        self.btnEditar.clicked.connect(self.editar)
        self.btnCalcular.clicked.connect(self.calcular)
        self.mudancaCurva(0)

    def apagar(self):
        curva = self.curva
        self.model.delete_curva(curva[0])
        self.update()
        self.comboCurva.clear()
        curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])

    def relatorio(self):
        pass

    def new(self):
        self.c=CurvasCompositorDialog(self)
        self.c.accepted.connect(self.saveCurva)
        self.c.rejected.connect(self.resetCurva)
        self.c.edited.connect(self.drawCurva)
        self.hide()
        self.c.show()
        return

#        self.habilitarControles(True)
#        if (len(self.curvas) > 0):
#            ultima = self.curvas[-1][0]
#        else:
#            ultima = -1
#        self.curvas.append(["%d" % (ultima + 1,)])
#        self.comboCurva.addItems([self.tr("%d" % (ultima + 1,))])


    def exec_(self):
        self.comboCurva: QtWidgets.QComboBox
        if self.comboCurva.count()>1:
            self.comboCurva.setCurrentIndex(1)
        if self.view.empty and not featureCount(self.layer):
            PT=PointTool(self.iface, self.pointLayerDefine)
            PT.start()
            self.setNoLayer()
        else:
            return super(Curvas, self).exec_()

    def pointLayerDefine(self, point):
        point=QgsPointXY(point)
        tangentFeaturesFromPointList(self.layer,[QgsPoint(point), QgsPoint(point.x(),point.y()+.001)])
        refreshCanvas(self.iface, self.layer)
        self.comboCurva.addItem("PI"+str(0))
        self.enableInterface()
        self.justStarted=True
        return super(Curvas, self).exec_()

    def setNoLayer(self):
        self.oldTitle=self.windowTitle()
        self.setWindowTitle(u"Escolha o ponto de partida no mapa!!!")
        for btn in self.buttons:
            btn:QtWidgets.QPushButton
            btn.setDisabled(True)

    def enableInterface(self):
        self.setWindowTitle(self.oldTitle)
        for btn in self.buttons:
            btn:QtWidgets.QPushButton
            btn.setDisabled(False)

    def drawCurva(self):
        if not hasattr(self.c, "dados"):
            self.c.dados=[]
            self.comboCurva: QtWidgets.QComboBox
            layer = QgsVectorLayer('LineString?crs=%s'%(QgsProject.instance().crs().authid()), "Curva: " + str(self.comboCurva.currentText()) , "memory")
            layer.setCrs(QgsCoordinateReferenceSystem(QgsProject.instance().crs()))
            layer.renderer().symbol().setWidth(.5)
            layer.renderer().symbol().setColor(QtGui.QColor("#0f16d0"))
            layer.triggerRepaint()
            fields = []
            fields.append(QgsField("Tipo", QVariant.String))  # C, T, E (Circular, tangente, Espiral ... startswith)
            fields.append(QgsField("Descricao", QVariant.String))
            layer.dataProvider().addAttributes(fields)
            layer.updateFields()
            QgsProject.instance().addMapLayer(layer, False)
            QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
            self.c.layer=layer


        layer=self.c.layer
        layer.dataProvider().deleteFeatures([f.id() for f in layer.getFeatures()])

        vmax=0
        k=0

        i=-1
        data=None

        if hasattr(self,"justStarted") and self.justStarted:
             for tipo, index, state in self.c.readData():
                i+=1
                if tipo=="C":
                    data=circleArc2(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="EE":
                    data=inSpiral2(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="ES":
                    data=outSpiral2(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="T":
                    data=tangent2(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"
                else:
                    continue

                if len(self.c.dados)-1<i:
                    self.c.dados.append(None)

                self.c.dados[i]=tipo, data

        else:
            for tipo, index, state in self.c.readData():
                i+=1
                if tipo=="C":
                    data=circleArc(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="EE":
                    data=inSpiral(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="ES":
                    data=outSpiral(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="T":
                    data=tangent(layer, state, index, self.layer, self.comboCurva.currentIndex())
                    k=0
                    vmax="120 km/h"
                else:
                    continue

                if len(self.c.dados)-1<i:
                    self.c.dados.append(None)

                self.c.dados[i]=tipo, data

        refreshCanvas(self.iface, layer)


        #TODO compute vmax and k

        if self.c.lastWidget and data:
            self.c.lastWidget.fill(data, k=k, vmax=vmax)


    def saveCurva(self):
        self.layer: QgsVectorLayer
        self.comboCurva : QtWidgets.QComboBox

        curvaFeats=featuresList(self.c.layer)
        if hasattr(self,"justStarted") and self.justStarted:
            features=[]
            PI=0
            hasEverCurve=False
            for i, feat in enumerate(curvaFeats):
                if str(self.c.dados[i][0]).startswith("T"):
                    feat.setAttributes([str(self.c.dados[i][0]), ""])
                    if hasEverCurve:
                        PI+=1
                        hasEverCurve=False
                else:
                    feat.setAttributes([str(self.c.dados[i][0]), "PI"])
                    hasEverCurve=True

                features.append(feat)

            self.layer.dataProvider().deleteFeatures([f.id() for f in self.layer.getFeatures()])
            self.layer.addFeatures(features)
            self.layer.updateExtents()
            self.justStarted=False

        elif len(curvaFeats)>0:
            #Delete all features of self.layer and add layer geometry in between
            features=[]
            for i,feat in enumerate(self.layer.getFeatures()):
                if i==self.comboCurva.currentIndex()-1:
                    g=splitFeatures(curvaFeats[0], feat)
                    f=QgsFeature(self.layer.fields())
                    f.setAttributes(feat.attributes())
                    f.setGeometry(g)
                    features.append(f)
                    for i,feat in enumerate(curvaFeats):
                        feat.setAttributes([str(self.c.dados[i][0]), str(self.comboCurva.currentText())])
                        features.append(feat)

                elif i == self.comboCurva.currentIndex():
                    g=splitFeatures(curvaFeats[-1],feat)
                    f=QgsFeature(self.layer.fields())
                    f.setAttributes(feat.attributes())
                    f.setGeometry(g)
                    features.append(f)

                else:
                    features.append(feat)

            self.layer.dataProvider().deleteFeatures([f.id() for f in self.layer.getFeatures()])
            self.layer.addFeatures(features)
            self.layer.updateExtents()

        QgsProject.instance().removeMapLayer(self.c.layer.id())
        refreshCanvas(self.iface, self.layer)
        self.show()

    def resetCurva(self):
        QgsProject.instance().removeMapLayer(self.c.layer.id())
        refreshCanvas(self.iface, self.layer)
        self.show()

    def editar(self):
        self.habilitarControles(True)
        self.editando = True

    def calcular(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(filter="Arquivo CSV (*.csv)")[0]
        dist = int(self.txtDist.text())
        estacas = self.model.gera_estacas(dist)
        self.model.save_CSV(filename, estacas)


    def mudancaCurva(self, pos):
        self.comboCurva : QtWidgets.QComboBox
        try:
            self.zoomToPoint(self.PIs[self.comboCurva.currentIndex()])
        except:
            pass
        self.curvas = self.model.list_curvas()

        if len(self.curvas)>pos+1: #curva já existe no db?
            self.curva = list(self.curvas[pos])
            curvas_inicial_id = self.curva[5]
            curvas_final_id = self.curva[6]
            self.mudancaEstacaInicial(self.estacas_id.index(curvas_inicial_id))
            self.mudancaEstacaFinal(self.estacas_id.index(curvas_final_id))
            self.txtVelocidade.setText(str(self.curva[2]))
            self.txtRUtilizado.setText(str(self.curva[3]))
            self.txtEMAX.setText(str(self.curva[4]))
        else:  #Curva ainda não cadastrada no db
            pass

    def zoomToPoint(self, point):
        #ZOOM
        scale = 250
        x,y=point.x(), point.y()
        rect = QgsRectangle(x - scale, y - scale, x + scale, y + scale)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()



    def mudancaTipo(self, pos):
        self.tipo_curva = pos

    def mudancaEstacaInicial(self, pos):
        self.comboEstacaInicial.setCurrentIndex(pos)
        self.estacaInicial = self.estacas[pos]
        self.txtNomeInicial.setText(self.estacaInicial[DESCRICAO])
        self.txtNorthInicial.setText(self.estacaInicial[NORTH])
        self.txtEsteInicial.setText(self.estacaInicial[ESTE])
        self.velocidadeCalculada()

    def mudancaEstacaFinal(self, pos):
        self.comboEstacaFinal.setCurrentIndex(pos)
        self.estacaFinal = self.estacas[pos]
        self.txtNomeFinal.setText(self.estacaFinal[DESCRICAO])
        self.txtNorthFinal.setText(self.estacaFinal[NORTH])
        self.txtEsteFinal.setText(self.estacaFinal[ESTE])
        self.velocidadeCalculada()

    def habilitarControles(self, signal):

        if type(signal) != type(True):
            return False

        self.comboCurva.setEnabled(not (signal))
        self.btnNew.setEnabled(not (signal))
        self.btnEditar.setEnabled(not (signal))
        self.btnApagar.setEnabled(not (signal))
        self.btnRelatorio.setEnabled(not (signal))
        self.btnInsere.setEnabled(signal)
        self.comboElemento.setEnabled(signal)
        self.comboEstacaInicial.setEnabled(signal)
        self.comboEstacaFinal.setEnabled(signal)
        self.txtVelocidade.setEnabled(signal)
        self.txtEMAX.setEnabled(signal)
        self.txtRUtilizado.setEnabled(signal)
        return True

    def velocidadeCalculada(self):
        self.curvas = self.model.list_curvas()
        if self.estacaInicial[ID_ESTACA] == self.estacaFinal[ID_ESTACA]:
            return

        if len(self.curvas) == 0:
            eptAnt = -1
        else:
            detalhes = self.model.get_curva_details(int(self.estacaInicial[ID_ESTACA]))
            eptAnt = -1 if detalhes is None else detalhes[6]

        i = calculeI(float(self.estacaInicial[PROGRESSIVA]), float(self.estacaFinal[PROGRESSIVA]),
                     float(self.estacaInicial[COTA]), float(self.estacaFinal[COTA]))
        v = velocidade(float(i), self.classe, self.tipo)
        rutilizado = float(self.txtRUtilizado.text())
        delta_val = delta(float(self.estacaInicial[AZIMUTE]), float(self.estacaFinal[AZIMUTE]))
        g20_val = g20(rutilizado)
        t_val = t(rutilizado, delta_val)
        d_val = d_curva_simples(rutilizado, delta_val)
        e_max = float(self.txtEMAX.text())
        f_max = fmax(int(v[0]))

        epi_val = epi(eptAnt, float(self.estacaFinal[PROGRESSIVA]), float(self.estacaInicial[PROGRESSIVA]), t_val)
        epc_val = epc(epi_val, t_val)
        ept_val = ept(epc_val, d_curva_simples(rutilizado, delta_val))
        self.param = {
            'g20': g20_val,
            't': t_val,
            'd': d_val,
            'epi': epi_val,
            'epc': epc_val,
            'ept': ept_val
        }
        self.txtI.setText("%f" % i)
        self.txtT.setText("%f" % t_val)
        self.txtD.setText("%f" % d_val)
        self.txtG20.setText("%f" % g20_val)
        self.txtFMAX.setText("%f" % f_max)
        self.txtRMIN.setText("%f" % rmin(int(v[0]), e_max, f_max))
        self.txtVelocidade.setText(v[0])
        self.txtDelta.setText("%f" % delta_val)
        self.txtEPI.setText("%f" % epi_val)
        self.txtEPT.setText("%f" % ept_val)
        self.txtEPC.setText("%f" % epc_val)

    def insert(self):

        self.habilitarControles(False)

        velocidade = int(self.txtVelocidade.text())
        raio_utilizado = float(self.txtRUtilizado.text())
        e_max = float(self.txtEMAX.text())
        estaca_inicial_id = int(self.estacaInicial[ID_ESTACA])
        estaca_final_id = int(self.estacaFinal[ID_ESTACA])
        model = CurvasModel(self.id_filename)
        if self.editando:
            self.editando = False
            id_curva = int(self.curva[0])
            model.edit(id_curva, int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado,
                       e_max, self.param)
        else:
            model.new(int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado, e_max,
                      self.param)
        self.update()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TopoGrafia', message)
