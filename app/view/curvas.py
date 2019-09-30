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

        self.btnCancela: QtWidgets.QPushButton

        self.btnEditar: QtWidgets.QPushButton
        self.btnInsere: QtWidgets.QPushButton
        self.btnNew: QtWidgets.QPushButton
        self.btnRelatorio: QtWidgets.QPushButton
        self.comboCurva: QtWidgets.QComboBox
        self.comboElemento: QtWidgets.QComboBox

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

        self.txtEMAX: QtWidgets.QDoubleSpinBox

        self.btnAjuda.hide()

        self.txtFMAX: QtWidgets.QTextEdit
        self.txtG20: QtWidgets.QLineEdit
        self.txtI: QtWidgets.QLineEdit



        self.txtRMIN: QtWidgets.QLineEdit
        self.txtRUtilizado: QtWidgets.QDoubleSpinBox
        self.txtT: QtWidgets.QLineEdit
        self.txtVelocidade: QtWidgets.QSpinBox
        self.deflexao: QtWidgets.QLineEdit
        

        self.whatsThisAction=QtWidgets.QWhatsThis.createAction(self)
        self.btnAjuda.clicked.connect(self.whatsThisAction.trigger)

        self.buttons=[self.btnAjuda, self.btnApagar, self.btnCancela, self.btnEditar,

                               self.btnInsere, self.btnNew, self.btnRelatorio ]
        self.dados = {
            'file': self.model.id_filename,
            'tipo': self.comboElemento.currentIndex(),
            'curva': self.comboCurva.currentText(),
            'vel': self.txtVelocidade.value(),
            'emax': self.txtEMAX.value(),
            'ls': self.Ls.value(),
            'R': self.txtRUtilizado.value(),
            'fmax': 0 if self.txtFMAX.text()=="" else float(self.txtFMAX.text()),
            'D': self.txtD.value()
        }


        self.curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.fill_comboCurva()

        self.editando = False
        self.update()
        self.eventos()
        self.location_on_the_screen()
        
        
        self.label_5.hide()
        self.label_3.hide()
        self.txtI.hide()
        self.label_11.hide()

        self.nextCurva()
        self.previousCurva()

        [w.valueChanged.connect(lambda: self.calcularCurva(False))
         for w in [self.txtVelocidade, self.txtRUtilizado, self.txtEMAX, self.Ls, self.txtD]]
        

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
        items=[]
        for c, vert in enumerate(self.vertices):
            items.append("PI"+str(c))
            self.PIs.append(vert[1])
        items=items[1:-1]
        self.comboCurva.addItems(items)
        if not wasInitialized(self.layer):
            tangentFeaturesFromPointList(self.layer,self.PIs)
            refreshCanvas(self.iface, self.layer)


    def update(self):
        self.curvas = self.model.list_curvas()
        estacas = self.estacas


        self.comboCurva.clear()
#        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])
        self.fill_comboCurva()

    def eventos(self):
        self.comboCurva.currentIndexChanged.connect(self.mudancaCurva)
        self.comboElemento.currentIndexChanged.connect(self.mudancaTipo)


        self.btnNew.clicked.connect(self.new)
        self.btnInsere.clicked.connect(self.insert)
        self.btnApagar.clicked.connect(self.apagar)
        self.btnRelatorio.clicked.connect(self.relatorio)
        self.btnEditar.clicked.connect(self.editar)
        self.mudancaCurva(0)

    def apagar(self):
        curva = self.curva
        self.model.delete_curva(curva[0])
        self.update()
        self.comboCurva.clear()
        curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])

    def relatorio(self):
    # TODO Sistema dinamico de criar curvas arbritárias:
         self.c=CurvasCompositorDialog(self)
         self.c.accepted.connect(self.saveCurva)
         self.c.rejected.connect(self.resetCurva)
         self.c.edited.connect(self.drawCurva)
         self.hide()
         self.c.show()

    def new(self):
        self.habilitarControles(True)
        if (len(self.curvas) > 0):
            ultima = self.curvas[-1][0]
        else:
            ultima = -1
        self.curvas.append(["%d" % (ultima + 1,)])
        #self.comboCurva.addItems([self.tr("%d" % (ultima + 1,))])
        self.calcularCurva(new=True)

    def exec_(self):
        self.comboCurva: QtWidgets.QComboBox
        if self.comboCurva.count()>1:
            self.comboCurva.setCurrentIndex(0)
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
            fields=layerFields()
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
                    data=circleArc2(layer, state, index, self.layer, self.nextIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="EC":
                    data = polyTransCircle(layer, state, index, self.layer, self.nextIndex(), self.currentIndex())
                    k = 0
                    vmax = "120 km/h"

                elif tipo=="EE":
                    data=inSpiral2(layer, state, index, self.layer, self.nextIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="ES":
                    data=outSpiral2(layer, state, index, self.layer, self.nextIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="T":
                    data=tangent2(layer, state, index, self.layer, self.nextIndex())
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
                    data=circleArc(layer, state, index, self.layer, self.nextIndex(), self.currentIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="EC":
                    data = polyTransCircle(layer, state, index, self.layer, self.nextIndex(), self.currentIndex())
                    k = 0
                    vmax = "120 km/h"

                elif tipo=="EE":
                    data=inSpiral(layer, state, index, self.layer, self.nextIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="ES":
                    data=outSpiral(layer, state, index, self.layer, self.nextIndex())
                    k=0
                    vmax="120 km/h"

                elif tipo=="T":
                    data=tangent(layer, state, index, self.layer, self.nextIndex())
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

    def nextCurva(self):
        self.comboCurva: QtWidgets.QComboBox
        i=self.comboCurva.currentIndex()+1
        if i>=self.comboCurva.count()-1:
            self.next.setEnabled(False)
            self.comboCurva.setCurrentIndex(self.comboCurva.count()-1)
        elif i<self.comboCurva.count()-1:
            self.comboCurva.setCurrentIndex(i)
            self.next.setEnabled(True)
            self.prev.setEnabled(True)

    def previousCurva(self):
        self.comboCurva: QtWidgets.QComboBox
        i=self.comboCurva.currentIndex()-1
        if i<=0:
            self.prev.setEnabled(False)
            self.comboCurva.setCurrentIndex(0)
        elif i>0:
            self.comboCurva.setCurrentIndex(i)
            self.prev.setEnabled(True)
            self.next.setEnabled(True)

    def saveCurva(self):
        self.layer: QgsVectorLayer
        self.comboCurva : QtWidgets.QComboBox

        curvaFeats=featuresList(self.c.layer)
        features = []
        if hasattr(self,"justStarted") and self.justStarted:
            i=0
            for f, tipo in zip(curvaFeats, self.c.dados):
                feat=QgsFeature(self.layer.fields())
                feat.setGeometry(f.geometry())
                feat.setAttributes([i,str(tipo[0]), "Traçado"])
                features.append(feat)
                i+=1
            self.justStarted=False

        elif len(curvaFeats)>0:
            fid=1
            nomes=[]
            #Delete all features of self.layer and add layer geometry in between
            for i,feat in enumerate(self.layer.getFeatures()):
                if i>self.currentIndex() and i<self.nextIndex():
                    continue
                f = QgsFeature(self.layer.fields())
                attr=feat.attributes()
                attr[0]=len(features)+1
                f.setAttributes(attr)
                if i==self.currentIndex():
                    PI=QgsPoint(featureToPolyline(curvaFeats[0])[0])
                    f.setGeometry(QgsGeometry.fromPolyline([QgsPoint(featureToPolyline(feat)[0]), PI ]))
                    features.append(f)

                    for i,cf in enumerate(curvaFeats):
                        f=QgsFeature(self.layer.fields())
                        attr = cf.attributes()
                        attr = [len(features) + 1]+attr
                        f.setAttributes(attr)
                        f.setGeometry(cf.geometry())
                        features.append(f)
                        if i==0: nomes.append(str(attr[1]))
                    nomes.append(str(attr[1]))


                elif i == self.nextIndex():
                    PF=QgsPoint(featureToPolyline(curvaFeats[-1])[-1])
                    f.setGeometry(QgsGeometry.fromPolyline([PF, QgsPoint(featureToPolyline(feat)[-1])]))
                    features.append(f)
                else:
                    f.setGeometry(feat.geometry())
                    features.append(f)

        self.layer.dataProvider().deleteFeatures([f.id() for f in self.layer.getFeatures()])
        self.layer.dataProvider().addFeatures(features)
        self.layer.updateExtents()

        QgsProject.instance().removeMapLayer(self.c.layer.id())
        refreshCanvas(self.iface, self.layer)
        self.show()
        self.txtRUtilizado.setValue(float(self.c.dados[0][1]['R']))


    def resetCurva(self):
        QgsProject.instance().removeMapLayer(self.c.layer.id())
        refreshCanvas(self.iface, self.layer)
        self.show()

    def editar(self):
        self.habilitarControles(True)
        self.editando = True

    def calcular(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(filter="Arquivo CSV (*.csv)")[0]

        estacas = self.model.gera_estacas(dist)
        self.model.save_CSV(filename, estacas)

    def clearAll(self):
        texts=["txtI", "txtDelta", "txtRMIN", "txtT", "theta", "txtG20", "lsmin",
               "lsmax", "xs", "ys"
               ]
        for txt in texts:
            getattr(self, txt).setText("")
        

    def mudancaCurva(self, pos):
        self.comboCurva : QtWidgets.QComboBox
        try:
            self.zoomToPoint(self.currentIndex())#self.PIs[1:-1][self.comboCurva.currentIndex()])
        except:
            pass

        self.curvas = self.model.list_curvas()
        self.clearAll()

#        if len(self.curvas)>pos+1: #curva já existe no db?
#            self.curva = list(self.curvas[pos])
#            curvas_inicial_id = self.curva[5]
#            curvas_final_id = self.curva[6]
#            self.mudancaEstacaInicial(self.estacas_id.index(curvas_inicial_id))
#            self.mudancaEstacaFinal(self.estacas_id.index(curvas_final_id))
#            self.txtVelocidade.setValue(int(self.curva[2]))
#            self.txtRUtilizado.setValue(float(self.curva[3]))
#            self.txtEMAX.setValue(float(self.curva[4]))
#        else:  #Curva ainda não cadastrada no db
#            pass

        id, self.dados=self.model.getId(self.comboCurva.currentText(), self.dados)
        if id:
            self.comboElemento.setCurrentIndex(self.dados['tipo'])
            self.comboCurva.setCurrentText(self.dados['curva'])
            self.txtVelocidade.setValue(self.dados['vel'])
            self.txtEMAX.setValue(self.dados['emax'])
            self.Ls.setValue(self.dados['ls'])
            self.txtRUtilizado.setValue(self.dados['R'])
            self.txtFMAX.setText(roundFloat2str(self.dados['fmax']))
            self.txtD.setValue(self.dados['D'])
            self.editando=True
            self.btnNew.setEnabled(False)
            self.btnEditar.setEnabled(True)
            self.calcularCurva()
        else:
            self.btnNew.setEnabled(True)
            self.btnEditar.setEnabled(False)
            self.editando=False

        max=self.comboCurva.count()-1
        i=self.comboCurva.currentIndex()

        if i==max:
            self.prev.setEnabled(True)
            self.next.setEnabled(False)
        elif i==0:
            self.prev.setEnabled(False)
            self.next.setEnabled(True)
        else:
            self.prev.setEnabled(True)
            self.next.setEnabled(True)


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

        self.estacaInicial = self.estacas[pos]

        self.calcularCurva()

    def mudancaEstacaFinal(self, pos):
        self.calcularCurva()

    def desabilitarControles(self):
        self.habilitarControles(False)

    def habilitarControles(self, signal):

        if type(signal) != type(True):
            return False

        self.comboCurva.setEnabled(not (signal))
        self.btnNew.setEnabled(not (signal))
        self.btnEditar.setEnabled(not (signal))
        self.btnApagar.setEnabled(not (signal))
        self.btnRelatorio.setEnabled(not (signal))
        self.btnInsere.setEnabled(signal)
        self.comboElemento.setEnabled(not signal)


        self.txtVelocidade.setEnabled(signal)
        self.txtEMAX.setEnabled(signal)
        self.txtRUtilizado.setEnabled(signal)
        self.btnRelatorio.setEnabled(signal)
        self.btnCancela.setEnabled(signal)
        self.txtFMAX.setEnabled(signal)
        self.prev.setEnabled(not signal)
        self.next.setEnabled(not signal)

        if self.comboElemento.currentIndex()>0:
            self.Ls.setEnabled(signal)
            self.txtD.setEnabled(signal)


        return True

    def currentIndex(self):
        i=self.comboCurva.currentIndex()
        f=0
        n=0
        for feat1, feat2 in zip(featuresList(self.layer), featuresList(self.layer)[1:]):
            if n == i:
                return max(f, 0)
            if getTipo(feat2)=="T":
                n+=1
            f+=1
        return max(f-1, 0)

    def nextIndex(self):
        i=self.currentIndex()+1
        fl = featuresList(self.layer)
        feat = fl[i]
        while getTipo(feat) != "T":
            i += 1
            feat = fl[i]
        return i

    def calcularCurva(self, new=False):
        self.curvas = self.model.list_curvas()
      #  if self.estacaInicial[ID_ESTACA] == self.estacaFinal[ID_ESTACA]:
      #      return

        if len(self.curvas) == 0:
            eptAnt = -1
        else:
            detalhes = self.model.get_curva_details(int(self.estacaInicial[ID_ESTACA]))
            eptAnt = -1 if detalhes is None else detalhes[6]

       # i = calculeI(float(self.estacaInicial[PROGRESSIVA]), float(self.estacaFinal[PROGRESSIVA]),
        #             float(self.estacaInicial[COTA]), float(self.estacaFinal[COTA]))
        i=0
        v = Config.instance().velproj if new else self.txtVelocidade.value()
        #velocidade(float(i), self.classe, self.tipo)
        e_max = Config.instance().emax if new else float(self.txtEMAX.value())
        f_max = fmax(int(v)) if new else 0 if self.txtFMAX.text()=="" else float(self.txtFMAX.text())

        delta_val = delta(float(azi(featureToPolyline(featuresList(self.layer)[self.currentIndex()]))),
                          float(azi(featureToPolyline(featuresList(self.layer)[self.nextIndex()]))))

        if new:
            rutilizado=rmin(int(v), e_max, f_max)
            self.txtRUtilizado.setValue(math.ceil(rutilizado/50)*50)
            self.txtVelocidade.setValue(v)
            self.txtEMAX.setValue(e_max)
            lutilizado=(max(0.036*v**3/rutilizado, 0.556*v)+rutilizado*delta_val*np.pi/180)/2
            self.Ls.setValue(lutilizado)
        else:
            lutilizado = float(self.Ls.value())
            rutilizado = float(self.txtRUtilizado.value())

        g20_val = g20(rutilizado)
        t_val = t(rutilizado, delta_val)
        d_val = d_curva_simples(rutilizado, delta_val)
        epi_val = epi(eptAnt, float(self.estacaFinal[PROGRESSIVA]), float(self.estacaInicial[PROGRESSIVA]), t_val)
        epc_val = epc(epi_val, t_val)
        ept_val = ept(epc_val, d_curva_simples(rutilizado, delta_val))

        if self.comboElemento.currentIndex() > 0:
            # d_val, theta, lsmin, lsmax, sc, cs
            lsmin=max(0.036*v**3/rutilizado, 0.556*v)
            lsmax=rutilizado*delta_val*np.pi/180
            theta=lutilizado/(2*rutilizado)
            self.theta.setText(roundFloat2str(np.rad2deg(theta)))
            self.lsmax.setText(roundFloat2str(lsmax))
            self.lsmin.setText(roundFloat2str(0.036*v**3/rutilizado))
            self.txtD.setEnabled(True)

            #d_val=self.txtD.value()
            xs=clotX(theta)*lutilizado
            ys=clotY(theta)*lutilizado
            k=xs-rutilizado*np.sin(theta)
            p=ys-rutilizado*(1-np.cos(theta))
            t_val=k+(rutilizado+p)*np.tan(np.deg2rad(delta_val)/2)
            self.txtTT.setText(roundFloat2str(t_val))
            self.txtp.setText(roundFloat2str(p))
            self.txtk.setText(roundFloat2str(k))
            self.txtPhi.setText(roundFloat2str(delta_val-2*np.rad2deg(theta)))
            self.lsminv.setText(roundFloat2str(.556*v))
            self.xs.setText(roundFloat2str(xs))
            self.ys.setText(roundFloat2str(ys))
            d_val=rutilizado*(delta_val-2*np.rad2deg(theta))*np.pi/180
            self.groupBox_3.show()

        else:
            self.theta.setText(roundFloat2str(np.rad2deg(0)))
            self.lsmax.setText(roundFloat2str(0))
            self.lsmin.setText(roundFloat2str(0))
            self.xs.setText(roundFloat2str(0))
            self.ys.setText(roundFloat2str(0))
            self.Ls.setValue(0)
            self.groupBox_3.hide()
            self.txtD.setEnabled(False)

        self.param = {
            'g20': g20_val,
            't': t_val,
            'd': d_val,
            'epi': epi_val,
            'epc': epc_val,
            'ept': ept_val
        }


        self.txtI.setText("%f" % i)
        self.txtI.setEnabled(False)
        self.txtT.setText("%f" % t_val)
        self.txtD.setValue(float(d_val))
        self.txtG20.setText("%f" % g20_val)
        self.txtFMAX.setText(roundFloat2str(f_max))
        self.txtRMIN.setText("%f" % rmin(int(v), e_max, f_max))
        self.txtVelocidade.setValue(int(v))
        self.txtDelta.setText("%f" % delta_val)

        self.dados = {
            'file': self.model.id_filename,
            'tipo': self.comboElemento.currentIndex(),
            'curva': self.comboCurva.currentText(),
            'vel': self.txtVelocidade.value(),
            'emax': self.txtEMAX.value(),
            'ls': self.Ls.value(),
            'R': self.txtRUtilizado.value(),
            'fmax': float(self.txtFMAX.text()),
            'D': self.txtD.value()
        }

    def insert(self):

        self.habilitarControles(False)
        velocidade = int(self.txtVelocidade.value())
        raio_utilizado = float(self.txtRUtilizado.value())
        e_max = float(self.txtEMAX.value())
        estaca_inicial_id = int(self.estacaInicial[ID_ESTACA])
        estaca_final_id = int(self.estacaFinal[ID_ESTACA])
        model = CurvasModel(self.id_filename)
        if self.editando:
            self.editando = False
            id_curva = int(self.curva[0])
            #TODO make it save and edit!!!
            model.edit(id_curva, int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado,
                       e_max, self.param, self.dados)
        else:
            model.new(int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado, e_max,
                      self.param, self.dados)
#        self.update()

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
