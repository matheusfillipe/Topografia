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


        self.btnInsere: QtWidgets.QPushButton

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

        self.buttons=[self.btnAjuda, self.btnApagar, self.btnCancela,
                               self.btnInsere, self.btnRelatorio ]

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
        self.curvaFailed=False
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

    def createLayer(self):
        self.c = CurvasCompositorDialog(self)
        self.c.accepted.connect(self.saveCurva)
        self.c.rejected.connect(self.resetCurva)
        self.c.edited.connect(self.drawCurva)

    def location_on_the_screen(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0#widget.width()
        y = (screen.height()-widget.height())/2
        self.move(x, y)

    def fill_comboCurva(self):
        c=0
        self.comboCurva.clear()
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
        self.nextIndex()



    def eventos(self):
        self.comboCurva.currentIndexChanged.connect(self.mudancaCurva)
        self.comboElemento.currentIndexChanged.connect(self.mudancaTipo)
        self.btnInsere.clicked.connect(self.insert)
        self.btnApagar.clicked.connect(self.apagar)
        self.btnRelatorio.clicked.connect(self.draw)
        self.btnCancela.clicked.connect(self.mudancaCurva)
        self.generateAll.clicked.connect(self.genAll)
        [w.valueChanged.connect(lambda: self.calcularCurva(False))
         for w in [self.txtVelocidade, self.txtRUtilizado, self.txtEMAX, self.Ls, self.txtD]]

    def genAll(self):
        self.comboCurva.setCurrentIndex(0)
        while self.next.isEnabled():
            self.insert()
            self.nextCurva()
        self.insert()

    def apagar(self):
        if self.curva_id:
            self.model.delete_curva(self.curva_id, self.dados)
            self.update()
            features=[]
            PI=0
            for i,feat in enumerate(self.layer.getFeatures()):
                if i>self.current_index and i<self.next_index:
                    continue
                f = QgsFeature(self.layer.fields())
                attr=feat.attributes()
                attr[0]=len(features)+1
                f.setAttributes(attr)
                if i==self.current_index:
                    l1=featureToPolyline(feat)
                    l2=featureToPolyline(self.layer.getFeature(self.next_index+1))
                    PI=seg_intersect(l1[0],l1[-1], l2[0],l2[-1])
                    f.setGeometry(QgsGeometry.fromPolyline([QgsPoint(featureToPolyline(feat)[0]), PI ]))
                    features.append(f)
                elif i == self.next_index:
                    PF=PI
                    f.setGeometry(QgsGeometry.fromPolyline([PF, QgsPoint(featureToPolyline(feat)[-1])]))
                    features.append(f)
                else:
                    f.setGeometry(feat.geometry())
                    features.append(f)

        self.layer.dataProvider().deleteFeatures([f.id() for f in self.layer.getFeatures()])
        self.layer.dataProvider().addFeatures(features)
        self.layer.updateExtents()

        try:
            QgsProject.instance().removeMapLayer(self.c.layer.id())
        except:
            pass
        refreshCanvas(self.iface, self.layer)
        self.show()

    def draw(self):
         # TODO Sistema dinamico de criar curvas arbritárias:
         try:
             self.c.rejected.emit()
         except:
             pass
         self.createLayer()
         self.c.edited.emit()


    def new(self):
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

        try:

            if hasattr(self,"justStarted") and self.justStarted:
                 for tipo, index, state in self.c.readData():
                    i+=1
                    if tipo=="C":
                        data=circleArc2(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="EC":
                        data = polyTransCircle(layer, state, index, self.layer, self.next_index, self.current_index)
                        k = 0
                        vmax = "120 km/h"

                    elif tipo=="EE":
                        data=inSpiral2(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="ES":
                        data=outSpiral2(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="T":
                        data=tangent2(layer, state, index, self.layer, self.next_index)
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
                        data=circleArc(layer, state, index, self.layer, self.next_index, self.current_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="EC":
                        data = polyTransCircle(layer, state, index, self.layer, self.next_index, self.current_index)
                        k = 0
                        vmax = "120 km/h"

                    elif tipo=="EE":
                        data=inSpiral(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="ES":
                        data=outSpiral(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"

                    elif tipo=="T":
                        data=tangent(layer, state, index, self.layer, self.next_index)
                        k=0
                        vmax="120 km/h"
                    else:
                        continue

                    if len(self.c.dados)-1<i:
                        self.c.dados.append(None)

                    self.c.dados[i]=tipo, data

        except Exception as e:
            messageDialog(title="Erro", message="Não foi possível definir a geometria", info="Provavelmente houve a interseção de curvas")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__)))
            self.curvaFailed=True

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
        self.draw()
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
                if i>self.current_index and i<self.next_index:
                    continue
                f = QgsFeature(self.layer.fields())
                attr=feat.attributes()
                attr[0]=len(features)+1
                f.setAttributes(attr)
                if i==self.current_index:
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


                elif i == self.next_index:
                    PF=QgsPoint(featureToPolyline(curvaFeats[-1])[-1])
                    f.setGeometry(QgsGeometry.fromPolyline([PF, QgsPoint(featureToPolyline(feat)[-1])]))
                    features.append(f)
                else:
                    f.setGeometry(feat.geometry())
                    features.append(f)

        self.layer.dataProvider().deleteFeatures([f.id() for f in self.layer.getFeatures()])
        self.layer.dataProvider().addFeatures(features)
        self.layer.updateExtents()

        try:
            QgsProject.instance().removeMapLayer(self.c.layer.id())
        except:
            pass
        refreshCanvas(self.iface, self.layer)
        self.show()


    def resetCurva(self):
        try:
            QgsProject.instance().removeMapLayer(self.c.layer.id())
        except:
            pass
        refreshCanvas(self.iface, self.layer)
        self.show()


    def clearAll(self):
        texts=["txtI", "txtDelta", "txtRMIN", "txtT", "theta", "txtG20", "lsmin",
               "lsmax", "xs", "ys"
               ]
        for txt in texts:
            getattr(self, txt).setText("")
        

    def mudancaCurva(self, pos):
        if hasattr(self, "c") and hasattr(self.c, "layer"):
            self.c.rejected.emit()

        self.calcularCurva(True)
        self.comboCurva : QtWidgets.QComboBox
        try:
            self.zoomToPoint(self.PIs[1:-1][self.comboCurva.currentIndex()])
        except:
            pass

        self.curvas = self.model.list_curvas()
        self.clearAll()

        self.curva_id, self.dados=self.model.getId(self.comboCurva.currentText(), self.dados)
        if self.curva_id:
            self.comboElemento.setCurrentIndex(self.dados['tipo'])
            self.comboCurva.setCurrentText(self.dados['curva'])
            self.txtVelocidade.setValue(self.dados['vel'])
            self.txtEMAX.setValue(self.dados['emax'])
            self.Ls.setValue(self.dados['ls'])
            self.txtRUtilizado.setValue(self.dados['R'])
            self.txtFMAX.setText(roundFloat2str(self.dados['fmax']))
            self.txtD.setValue(self.dados['D'])
            self.editando=True

            self.calcularCurva()
        else:
            self.editando=False
            self.calcularCurva(True)

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
        if pos>0:
            self.groupBox_3.show()
        else:
            self.groupBox_3.hide()

        self.calcularCurva(True)


    def mudancaEstacaInicial(self, pos):

        self.estacaInicial = self.estacas[pos]

        self.calcularCurva()

    def mudancaEstacaFinal(self, pos):
        self.calcularCurva()

    def desabilitarControles(self):
        #self.habilitarControles(False)
        pass

    def habilitarControles(self, signal):

        if type(signal) != type(True):
            return False

        self.comboCurva.setEnabled(not (signal))


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
                self.current_index = max(f, 0)
                return max(f, 0)
            if getTipo(feat2)=="T":
                n+=1
            f+=1
        self.current_index= max(f-1, 0)
        return max(f-1, 0)

    def nextIndex(self):
        i=self.currentIndex()+1
        fl = featuresList(self.layer)
        feat = fl[i]
        while getTipo(feat) != "T":
            i += 1
            feat = fl[i]
        self.next_index=i
        return i

    def calcularCurva(self, new=False):
        self.nextIndex()
       # i = calculeI(float(self.estacaInicial[PROGRESSIVA]), float(self.estacaFinal[PROGRESSIVA]),
        #             float(self.estacaInicial[COTA]), float(self.estacaFinal[COTA]))
        i=0
        v = Config.instance().velproj if new else self.txtVelocidade.value()
        #velocidade(float(i), self.classe, self.tipo)
        e_max = Config.instance().emax if new else float(self.txtEMAX.value())
        f_max = fmax(int(v)) if new else 0 if self.txtFMAX.text()=="" else float(self.txtFMAX.text())

        delta_val = delta(float(azi(featureToPolyline(featuresList(self.layer)[self.current_index]))),
                          float(azi(featureToPolyline(featuresList(self.layer)[self.next_index]))))

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
        if not hasattr(self,"c"):
            self.createLayer()
        if self.curvaFailed:
            self.curvaFailed=False
            return
        self.c.accepted.emit()
        model = CurvasModel(self.id_filename)
        if self.editando:
            self.editando = False
            id_curva = self.comboCurva.currentIndex()+1
            model.edit(self.dados)
        else:
            model.new(self.dados)
       # self.update()

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
