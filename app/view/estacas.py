from __future__ import print_function

import sip
from builtins import range

import numpy as np
from PyQt5.QtCore import Qt
from qgis.PyQt import QtWidgets, QtGui
from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, QVariant
from qgis.PyQt.QtGui import QKeySequence
from qgis.PyQt.QtWidgets import *
import qgis._core
from qgis._core import QgsCoordinateReferenceSystem
from qgis.core import QgsRectangle, QgsGeometry, QgsVectorLayer, QgsPoint, QgsFeature
from qgis.gui import *
from qgis.utils import *
from qgis.core import QgsProject, QgsCoordinateTransform, QgsPointXY, QgsVectorFileWriter, QgsWkbTypes, QgsField, QgsFields, QgsCoordinateTransformContext

from ..model.config import Config
from ..model.utils import formatValue, msgLog, prog2estacaStr, p2QgsPoint, fastProg2EstacaStr


# -*- coding: utf-8 -*-
sip.setapi('QString',2)
sip.setapi('QVariant',2)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context.encode('utf8'), text.encode('utf8'), disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context.encode('utf8'), text.encode('utf8'), disambig)

FORMESTACA1_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_estacas1.ui'))
FORMGERATRACADO_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_gera_tracado_1.ui'))
APLICAR_TRANSVERSAL_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/applyTransDiag.ui'))
SETCTATI_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/setTransPtsIndexes.ui'))
VERTICE_EDIT_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog-cv.ui'))
SET_ESCALA_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/setEscala.ui'))
SELECT_FEATURE, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/selectFeature.ui'))
ESTACAS_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_estacas.ui'))
PROGRESS_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/progressBarDialog.ui'))
BRUCKNER_SELECT, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/bruckner_select.ui'))
VOLUME_DIALOG, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/volume.ui'))
EXPORTAR_CORTE,_ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/cortePreview.ui'))

rb = QgsRubberBand(iface.mapCanvas(), 1)
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


class CopySelectedCellsAction(QtWidgets.QAction):
    def __init__(self, iface, table_widget):
        if not isinstance(table_widget, QtWidgets.QTableWidget):
            raise ValueError(str('CopySelectedCellsAction must be initialised with a QTableWidget. A %s was given.' % type(table_widget)))
        super(CopySelectedCellsAction, self).__init__("Copy", table_widget)
        self.setShortcut('Ctrl+C')
        s=QShortcut(QKeySequence("Ctrl+C"), iface)
        s.activated.connect(self.copy_cells_to_clipboard)
        self.triggered.connect(self.copy_cells_to_clipboard)
        self.table_widget = table_widget

    def copy_cells_to_clipboard(self):
        if len(self.table_widget.selectionModel().selectedIndexes()) > 0:
            columnIndex=list(set(index.column() for index in self.table_widget.selectionModel().selectedIndexes()))
            rowIndex=list(set(index.row() for index in self.table_widget.selectionModel().selectedIndexes()))
            columnIndex.sort()
            rowIndex.sort()
            nSelectedColumns=len(columnIndex)
            nSelectedRows=len(rowIndex)
            matx=[[None for a in range(max(columnIndex[-1]-columnIndex[0]+1,nSelectedColumns))] for a in range(max(1+rowIndex[-1]-rowIndex[0],nSelectedRows))]
            start=[rowIndex[0],columnIndex[0]]

            for index in self.table_widget.selectionModel().selectedIndexes():
                i=index.row()-start[0]
                j=index.column()-start[1]
                matx[i][j]=index.data()


            import numpy as np
            final=np.array(matx).transpose()
            matx=[]
            for col in final:
                if any(x is not None for x in col):
                    matx.append(col)
            final=np.array(matx).transpose()
            clipboard=""
            for row in final:
                if not any(x is not None for x in row):
                    continue
                for column in row:
                        clipboard += str(column if column else "")+'\t'
                clipboard += '\n'

            clipboard=clipboard.replace(".", ",")
            # copy to the system clipboard
            sys_clip = QtWidgets.QApplication.clipboard()
            sys_clip.setText(clipboard)

class reversedSpinBox(QtWidgets.QSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lineEdit().setReadOnly(True)

    def stepBy(self, steps: int):
        super().stepBy(-steps)

class Dialog(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        button = QtWidgets.QPushButton('Open Dialog', self)
        button.clicked.connect(self.handleOpenDialog)
        self.resize(300, 200)
        self._dialog = None

    def handleOpenDialog(self):
        if self._dialog is None:
            self._dialog = QtWidgets.QDialog(self)
            self._dialog.resize(200, 100)
        self._dialog.show()


class GeraTracadoUI(QtWidgets.QDialog,FORMGERATRACADO_CLASS):
    def __init__(self, iface):
        super(GeraTracadoUI, self).__init__(None)
        self.iface = iface
        self.setupUi(self)

class EstacasUI(QtWidgets.QDialog,FORMESTACA1_CLASS):
    deleted=QtCore.pyqtSignal()

    def __init__(self, iface):
        super(EstacasUI, self).__init__(None)
        self.iface = iface
        self.setupUi(self)
        self.setupUi2(self)
        self.points = []
        self.crs = 1
        self.edit = False
        self.dialog = QtWidgets.QDialog(None)
        self.actual_point = None
        self.btnGerarCurvas.hide()


    def curvasDialog(self, estacas, layer):
        coordenadas=[[float(x),float(y)] for y,x in zip([e[3] for e in estacas],[e[4] for e in estacas])].copy()


        #return estaca,descricao,progressiva,norte,este,cota,azimute


    def keyPressEvent(self, a0: QtGui.QKeyEvent):
        if a0.key() == QtCore.Qt.Key_Delete:
            self.deleted.emit()
        super(EstacasUI, self).keyPressEvent(a0)


    def error(self, msg):
        msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "AVISO",
                                   u"%s" % msg,
                                   QtWidgets.QMessageBox.NoButton, None)
        msgBox.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
        msgBox.exec_()

    def openCSV(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Arquivo CSV (*.csv)")
        if filename in ["", None]: return None
        fileDB, ok = QtWidgets.QInputDialog.getText(None, "Nome do arquivo", u"Nome do arquivo a ser salvo no projeto:", text="Traçado csv")
        if not ok:
            return None
        return filename, fileDB

    def new(self,recalcular=False,layerName=None,filename=None, lastIndex=0, ask=True):
        mapCanvas = self.iface.mapCanvas()
        itens = []
        for i in range(mapCanvas.layerCount() - 1, -1, -1):
            try:
                layer = mapCanvas.layer(i)
                name = layer.name()
                itens.append(name)
            except:
                pass

        if len(itens) == 0:
            from ..model.utils import messageDialog
            messageDialog(message="Nenhuma layer visível foi encontrada no projeto, por favor adicione alguma.")
            return None

        if not filename:
            if not recalcular:
                filename=""
                names=[self.tableEstacas.item(i,1).text() for i in range(self.tableEstacas.rowCount())]
                first=True
                nomeSugerido="Traçado "+str(lastIndex)
                c=0
                while nomeSugerido in names and c<3:
                    c+=1
                    nomeSugerido+="_"
                while filename=="" or filename in names:
                    if not first:
                        from ..model.utils import messageDialog
                        messageDialog(self,title="Erro",message="Já existe um arquivo com esse nome")

                    filename, ok = QtWidgets.QInputDialog.getText(None, "Nome do arquivo", u"Nome do arquivo:", text=nomeSugerido)
                    if not ok:
                        return None

                    first=False
            else:
                filename = ''

        if layerName is not None:
            layerList = QgsProject .instance().mapLayersByName(layerName)
            layer = None
            if layerList:
                layer = layerList[-1]
        else:
            itens = []
            for i in range(mapCanvas.layerCount() - 1, -1, -1):
                try:
                    layer = mapCanvas.layer(i)
                    layerName = layer.name()
                    if type(layer) == qgis._core.QgsVectorLayer:
                        itens.append(layerName)
                except:
                    pass
            item, ok = QtWidgets.QInputDialog.getItem(None, "Camada com tracado", u"Selecione a camada com o traçado:",
                                                  reversed(itens),
                                                  0, False)
            if not(ok) or not(item):
                return None
            else:
                layerList = QgsProject .instance().mapLayersByName(item)
                layer = None
                if layerList:
                    layer = layerList[0]
        if ask:
            dist, ok = QtWidgets.QInputDialog.getDouble(None, "Distancia", u"Distancia entre estacas:", Config.instance().DIST, 1,
                                                10000, 2)
        else:
            ok=True
            dist=Config.instance().DIST
        if not ok or dist<=0:
            return None

        if ask:
            estaca, ok = QtWidgets.QInputDialog.getInt(None, "Estaca Inicial", u"Estaca Inicial:", 0, 0, 10000000, 2)
        else:
            ok=True
            estaca=0
        if not ok:
            return None
        return filename, layer, dist, estaca

    def fill_table_index(self, files):
        self.tableEstacas : QtWidgets.QTableWidget
        self.tableEstacas.setRowCount(0)
        self.tableEstacas.clearContents()
        for i,f in enumerate(files):
            self.tableEstacas.insertRow(self.tableEstacas.rowCount())
            for j,f2 in enumerate(f):
                tableItem=QtWidgets.QTableWidgetItem(u"%s" % f2)
                tableItem.setFlags(tableItem.flags() ^ Qt.ItemIsEditable)
                self.tableEstacas.setItem(i,j,tableItem)
        self.tableEstacas.cellDoubleClicked.connect(self.accept)


    def create_line(self,p1,p2,name):
        layer = QgsVectorLayer('LineString?crs=%s'%int(self.crs), name, "memory")
        mycrs = QgsCoordinateReferenceSystem(int(self.crs), 0)
        self.reprojectgeographic = QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), mycrs, QgsCoordinateTransformContext())
        pr = layer.dataProvider()
        line = QgsFeature()
        line.setGeometry(QgsGeometry.fromPolyline([p2QgsPoint(self.reprojectgeographic.transform(point=QgsPointXY(p1))), p2QgsPoint(self.reprojectgeographic.transform(point=QgsPointXY(p2)))]))
        pr.addFeatures([line])
        #layer.setCrs(QgsCoordinateReferenceSystem(int(self.crs), 0))
        layer.updateExtents()

        QgsProject.instance().addMapLayer(layer)

        return p1, p2

    def create_point(self,p1,name):
        layer = QgsVectorLayer('Point?crs=%s'%int(self.crs), name, "memory")
        mycrs = QgsCoordinateReferenceSystem(int(self.crs), 0)
        self.reprojectgeographic = QgsCoordinateTransform(self.iface.mapCanvas().mapSettings().destinationCrs(), mycrs, QgsCoordinateTransformContext())
        pr = layer.dataProvider()
        point = QgsFeature()
        point.setGeometry(QgsGeometry.fromPoint(p2QgsPoint(self.reprojectgeographic.transform(point=QgsPointXY(p1)))))
        pr.addFeatures([point])
        #layer.setCrs(QgsCoordinateReferenceSystem(int(self.crs), 0))
        layer.updateExtents()

        QgsProject.instance().addMapLayer(layer)

        return p1

    def drawShapeFileAndLoad(self, crs):
        #Creates a shapefile on the given path and triggers the digitizing menu QActions
        #For editing and saving the LineString
        #This relies on the QActions order on the menu

        fields = QgsFields()
        fields.append(QgsField("Tipo", QVariant.String))
        fields.append(QgsField("Descricao", QVariant.String))
        dialog = QtWidgets.QFileDialog()
        dialog.setWindowTitle("Caminho para criar arquivo shapefile")
        dialog.setDefaultSuffix("shp")
        path = QtWidgets.QFileDialog.getSaveFileName(filter="Shapefiles (*.shp)")[0]

        if not path:
            return None

        writer = QgsVectorFileWriter(path, 'UTF-8', fields, QgsWkbTypes.MultiLineString,
                                     QgsCoordinateReferenceSystem('EPSG:' + str(crs)), 'ESRI Shapefile')
        del writer
        self.iface.addVectorLayer(path,"","ogr")

        self.iface.digitizeToolBar().show()
        addLineAction = self.iface.digitizeToolBar().actions()[8]
        toggleEditAction = self.iface.digitizeToolBar().actions()[1]
        if not addLineAction.isChecked():
            toggleEditAction.trigger()
        addLineAction.setChecked(True)
        addLineAction.trigger()


    def get_click_coordenate(self,point, mouse):
        self.actual_point=p2QgsPoint(point)
        if self.tracado_dlg.txtNorthStart.text().strip()=='':
            self.tracado_dlg.txtNorthStart.setText("%f"%self.actual_point.y())
            self.tracado_dlg.txtEsteStart.setText("%f"%self.actual_point.x())
        elif self.tracado_dlg.txtNorthEnd.text().strip()=='':
            self.tracado_dlg.txtNorthEnd.setText("%f"%self.actual_point.y())
            self.tracado_dlg.txtEsteEnd.setText("%f"%self.actual_point.x())

    def gera_tracado_pontos(self,inicial=False,final=False,callback_inst=None,callback_method=None,crs=None):
        if (not (inicial) and not (final)):
            self.callback = eval('callback_inst.%s' % callback_method)
            self.crs = crs
            self.tracado_dlg_inicial = GeraTracadoUI(self.iface)
            self.tracado_dlg_inicial.lblName.setText("Ponto Inicial")
            self.tracado_dlg_inicial.btnCapture.clicked.connect(self.capture_point_inicial)
            self.tracado_dlg_final = GeraTracadoUI(self.iface)
            self.tracado_dlg_final.lblName.setText("Ponto Final")
            self.tracado_dlg_final.btnCapture.clicked.connect(self.capture_point_final)
        if (not (inicial) and not (final)) or not (final):
            ok = self.tracado_dlg_inicial.exec_()
            if not (ok):
                return None
            else:
                pn = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",", "."))
                pe = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",", "."))
                self.gera_tracado_ponto_inicial(p2QgsPoint(pe, pn))

        if (not (inicial) and not (final)) or not (inicial):
            ok = self.tracado_dlg_final.exec_()
            if not (ok):
                return None
            else:
                pn = float(self.tracado_dlg_final.txtNorth.text().strip().replace(",", "."))
                pe = float(self.tracado_dlg_final.txtEste.text().strip().replace(",", "."))
                self.gera_tracado_ponto_final(p2QgsPoint(pe, pn))

        if inicial and final:
            p1n = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",", "."))
            p1e = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",", "."))
            p2n = float(self.tracado_dlg_final.txtNorth.text().strip().replace(",", "."))
            p2e = float(self.tracado_dlg_final.txtEste.text().strip().replace(",", "."))
            self.iface.mapCanvas().setMapTool(None)
            self.callback(pontos=self.create_line(p2QgsPoint(p1e, p1n), p2QgsPoint(p2e, p2n), "Diretriz"), parte=1)



    def gera_tracado_ponto_inicial(self,point):
        self.tracado_dlg_inicial.txtNorth.setText("%f"%point.y())
        self.tracado_dlg_inicial.txtEste.setText("%f"%point.x())
        ok = self.tracado_dlg_inicial.exec_()
        if not(ok):
            return None
        else:
            pn = float(self.tracado_dlg_inicial.txtNorth.text().strip().replace(",","."))
            pe = float(self.tracado_dlg_inicial.txtEste.text().strip().replace(",","."))
            self.gera_tracado_ponto_final(p2QgsPoint(pe, pn))
        
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
            #self.gera_tracado_ponto_final(p2QgsPoint(pe, pn))
        
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
        # fix_print_with_import
        print(points)
        anterior = p2QgsPoint(points[0])
        fets=[]
        for p in points[1:]:
            fet = QgsFeature(layer.fields())
            fet.setGeometry(QgsGeometry.fromPolyline([anterior, p2QgsPoint(p)]))
            fets.append(fet)
            anterior = p2QgsPoint(p)
        pr.addFeatures(fets)
        self.crs = crs
        layer.setCrs(QgsCoordinateReferenceSystem(int(crs), 0))
        layer.updateExtents()

        QgsProject.instance().addMapLayer(layer)

    def gera_tracado_vertices(self,pointerEmitter):
        self.iface.mapCanvas().setMapTool(pointerEmitter)
        self.name_tracado = "TracadoNovo"
        self.dialog.resize(200, 100)
        self.dialog.setWindowTitle(u"Traçado")
        self.dialog.btnClose = QtWidgets.QPushButton("Terminar",self.dialog)
        self.dialog.show()
        return self.name_tracado

    def setupUi2(self,Form):
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        self.tableEstacas : QtWidgets.QTableWidget
        self.tableEstacas.setColumnCount(3)
        self.tableEstacas.setRowCount(0)
        self.tableEstacas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableEstacas.setHorizontalHeaderLabels((u"ID",u"Arquivo",u"Data de criação"))



        self.table=self.tableEstacas
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.stretchTable(self.table)

    def resizeEvent(self, event):
        self.stretchTable(self.table)
        super(EstacasUI, self).resizeEvent(event)  # Restores the original behaviour of the resize event

    def stretchTable(self, table):
        tableSize = table.width()
        sideHeaderWidth = table.verticalHeader().width()
        tableSize -= sideHeaderWidth
        numberOfColumns = table.columnCount()

        remainingWidth = tableSize % numberOfColumns
        for columnNum in range(table.columnCount()):
            if remainingWidth > 0:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns) + 1)
                remainingWidth -= 1
            else:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns))

    def exec_(self):
        self.tableEstacas: QtWidgets.QTableWidget
        self.stretchTable(self.table)
        self.tableEstacas.selectRow(0)
        self.checkButtons()
        return super(EstacasUI, self).exec_()

    def checkButtons(self):
        if self.tableEstacas.rowCount() == 0:
            self.btnOpen.setEnabled(False)
            self.btnOpenCv.setEnabled(False)
        else:
            self.btnOpen.setEnabled(True)
            self.btnOpenCv.setEnabled(True)


class EstacasIntersec(QtWidgets.QDialog):
    def __init__(self,iface):
        super(EstacasIntersec, self).__init__(None)
        self.iface = iface
        self.setupUi(self)

    def clear(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()

    def saveEstacasCSV(self):
        filename = QtWidgets.QFileDialog.getSaveFileName()
        return filename

    def fill_table(self, xxx_todo_changeme,f=False):
        (estaca,descricao,progressiva,cota) = xxx_todo_changeme
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        k = self.tableWidget.rowCount() - 1
        self.tableWidget.setItem(k, 0, QtWidgets.QTableWidgetItem(u"%s" % estaca))
        self.tableWidget.setItem(k, 1, QtWidgets.QTableWidgetItem(u"%s" % descricao))
        self.tableWidget.setItem(k, 2, QtWidgets.QTableWidgetItem(u"%s" % progressiva))
        self.tableWidget.setItem(k, 3, QtWidgets.QTableWidgetItem(u"%s" % cota))
        '''if not f:
            naz = decdeg2dms(azimute)
            str_az = "%s* %s\' %s\'\'" % (int(naz[0]), int(naz[1]), naz[2])
            self.tableWidget.setItem(k, 6, QtWidgets.QTableWidgetItem(str_az))
        else:'''


    def get_estacas(self):
        estacas = []
        for i in range(self.tableWidget.rowCount()):
            estaca = []
            for j in range(self.tableWidget.columnCount()):
                estaca.append(self.tableWidget.item(i,j).text())
            estacas.append(estaca)
        return estacas


    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        Form.resize(919, 510)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 750, 511))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.modelSource = self.tableWidget.model()


        self.tableWidget.setColumnCount(8)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels((u"Estaca",u"Descrição",u"Progressiva",u"Cota", u"Relevo", u"Norte",u"Este",u"Azimute"))


        self.btnGen = QtWidgets.QPushButton(Form)
        self.btnGen.setText("Tabela de Verticais")
        self.btnGen.setGeometry(QtCore.QRect(755, 16, 180, 45))
        self.btnGen.setObjectName(_fromUtf8("btnGen"))
        #self.btnGen.clicked.connect(self.generate)

        self.btnTrans = QtWidgets.QPushButton(Form)
        self.btnTrans.setText("Definir Sessão Tipo")
        self.btnTrans.setGeometry(QtCore.QRect(760, 50+16, 160, 30))
        self.btnTrans.setObjectName(_fromUtf8("btnTrans"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)

        self.btnPrint = QtWidgets.QPushButton(Form)
        self.btnPrint.setText("Imprimir")
        self.btnPrint.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btnPrint.setObjectName(_fromUtf8("btnPrint"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)

        self.btnClean = QtWidgets.QPushButton(Form)
        self.btnClean.setText("Apagar Dados")
        self.btnClean.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.btnClean.setObjectName(_fromUtf8("btnClean"))


        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)



    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Traçado Horizontal", "Traçado Vertical", None))


class EstacasCv(QtWidgets.QDialog):
    layerUpdated=pyqtSignal()

    def __init__(self,iface, parent):
        super(EstacasCv, self).__init__(None)
        self.mode="N"
        self.iface = iface
        self.parent = parent
        self.setupUi(self)
        self.location_on_the_screen()


        self.spinBox: QtWidgets.QSpinBox
        self.spinBox.hide()
        self.comboBox: QtWidgets.QComboBox
        self.comboBox.currentTextChanged.connect(self.search)
        self.comboBox.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.spinBox.valueChanged.connect(self.changeSearchResult)
        self.searchResults=[]
        self.curvaLayers=[]

    def changeSearchResult(self, i):
        if i==0 or i==len(self.searchResults)+1:
            self.spinBox.valueChanged.disconnect()
            self.spinBox.setValue(i+1 if i==0 else i-1)
            self.spinBox.valueChanged.connect(self.changeSearchResult)
            return

        if len(self.searchResults)>0:
            columnIndexes = list(set(index.column()
                                     for index in self.tableWidget.selectionModel().selectedIndexes()))
            row=self.searchResults[i-1]

            if len(columnIndexes)==0:
                self.tableWidget.setRangeSelected(
                QTableWidgetSelectionRange(row, 0, row, self.tableWidget.columnCount()-1), True)
                self.tableWidget.setCurrentCell(row,0)
            else:
                for i in columnIndexes:
                    self.tableWidget.setRangeSelected(
                        QTableWidgetSelectionRange(row, i, row, i), True)
                self.tableWidget.setCurrentCell(row, columnIndexes[0])

    def search(self, txt):
        self.searchResults=[]
        columnIndexes = list(set(index.column()
                                 for index in self.tableWidget.selectionModel().selectedIndexes()))
        def searchRange(estaca, columnIndexes):
            if len(columnIndexes)>0:
                estaca=[estaca[i] for i in columnIndexes]
            return "* ".join(estaca)

        for i, estaca in enumerate(self.get_estacas()):
            if txt.upper() in searchRange(estaca, columnIndexes).upper():
                self.searchResults.append(i)
        lres=len(self.searchResults)
        if lres>1:
            self.spinBox.show()
            self.spinBox.setMaximum(lres+1)
        else:
            self.spinBox.hide()
        self.changeSearchResult(1)
        self.spinBox.setValue(1)



    def location_on_the_screen(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0#widget.width()
        y = (screen.height()-widget.height())/2
        self.move(x, y)

    def clear(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.comboBox.clear()

    def setIntersect(self):
        if hasattr(self, "mode") and self.mode=="T":
            return
        self.clear()
        self.tableWidget.setColumnCount(8)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels((u"Estaca",u"Descrição",u"Progressiva",u"Norte",u"Este",u"Greide",u"Cota",u"Azimute"))
        try:
            self.btnGen.clicked.disconnect()
        except:
            pass
        self.tableWidget.cellClicked.connect(self.zoom)
        self.btnGen.setText("Tabela de verticais")
        self.mode="T"
        self.stretchTable()


    def setCv(self):
        if hasattr(self, "mode") and  self.mode=="CV":
            return
        self.clear()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(0)
        try:
            self.tableWidget.cellClicked.disconnect()
        except:
            pass
        self.tableWidget.setHorizontalHeaderLabels((u"Estaca",u"Descrição",u"Progressiva",u"Greide"))
        self.btnGen.setText("Tabela de Interseção")
        self.mode="CV"
        self.stretchTable()


    def saveEstacasCSV(self):
        filename = QtWidgets.QFileDialog.getSaveFileName()
        return filename


    def fill_table(self, estaca, f=False):
        try:
            self.comboBox.currentTextChanged.disconnect(self.search)
        except:
            pass
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        k = self.tableWidget.rowCount() - 1
        j = 0
        for value in list(estaca):
            cell_item = QtWidgets.QTableWidgetItem(u"%s" % formatValue(value))
            cell_item.setFlags(cell_item.flags() ^ Qt.ItemIsEditable)
            self.tableWidget.setItem(k, j, cell_item)
            j += 1

        if len(estaca[1]) != 0 and not (estaca[1] in [self.comboBox.itemText(i)
                                                      for i in range(self.comboBox.count())]):
            self.comboBox.addItem(estaca[1])
        self.comboBox.currentTextChanged.connect(self.search)

    def get_estacas(self):
        estacas = []
        for i in range(self.tableWidget.rowCount()):
            estaca = []
            for j in range(self.tableWidget.columnCount()):
                estaca.append(self.tableWidget.item(i,j).text())
            estacas.append(estaca)
        return estacas

    def getEstacas(self):
        for i in range(self.tableWidget.rowCount()):
            estaca = []
            for j in range(self.tableWidget.columnCount()):
                estaca.append(self.tableWidget.item(i,j).text())
            yield estaca


    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        Form.resize(919, 510)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setColumnStretch(0, 4)
#        self.gridLayout.setRowStretch(1,3)

        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 750, 511))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.modelSource = self.tableWidget.model()

        column=1
        row=0

        self.btnRecalcular = QtWidgets.QPushButton(Form)
        self.btnRecalcular.setText("Recalcular")
        self.btnRecalcular.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.btnRecalcular.setWhatsThis("Recalcula a tabela em vista \n A tabela vertical deve"
                                        " ser calculada antes da de interseção para que as mudanças se "
                                        "apliquem corretamente")
        self.btnRecalcular.setObjectName(_fromUtf8("btnRecalcular"))
        self.gridLayout.addWidget(self.btnRecalcular, row, column, 1, 1)
        row+=1

        self.btnPerfil = QtWidgets.QPushButton(Form)
        self.btnPerfil.setText("Gerar Perfil \nLongitudinal")
        self.btnPerfil.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.btnPerfil.setWhatsThis("Define o greide")
        self.btnPerfil.setToolTip("Define o Greide")
        self.btnPerfil.setObjectName(_fromUtf8("btnPerfil"))
        self.gridLayout.addWidget(self.btnPerfil, row, column, 1, 1)
        row+=1
        self.btnPerfil.hide()

        self.btnGen = QtWidgets.QPushButton(Form)
        self.btnGen.setText("Tabela de interseção")
        self.btnGen.setGeometry(QtCore.QRect(755, 16, 180, 45))
        self.btnGen.setObjectName(_fromUtf8("btnGen"))
        self.gridLayout.addWidget(self.btnGen, row, column, 1,1)
        self.btnGen.setToolTip("Tabela contendo os dados horizonais e verticais")
        #self.btnGen.clicked.connect(self.generate)
        row+=1

        self.btnTrans = QtWidgets.QPushButton(Form)
        self.btnTrans.setText("Definir Sessão Tipo")
        self.btnTrans.setGeometry(QtCore.QRect(760, 50+16, 160, 30))
        self.btnTrans.setObjectName(_fromUtf8("btnTrans"))
        self.btnTrans.setToolTip("Inicia interface para a edição do perfil transversal")
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)

        self.gridLayout.addWidget(self.btnTrans, row, column, 1,1)
        row+=1

        self.btnBruck = QtWidgets.QPushButton(Form)
        self.btnBruck.setText("Diagrama de Bruckner")
        self.btnBruck.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btnBruck.setObjectName(_fromUtf8("btnBruck"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)
        self.btnBruck.setToolTip("Visualizar e editar o diagrama de bruckner para um intervalo de estacas")
        self.gridLayout.addWidget(self.btnBruck, row, column, 1, 1)
        row+=1

        self.btnCsv = QtWidgets.QPushButton(Form)
        self.btnCsv.setText("Exportar Tabela CSV")
        self.btnCsv.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btnCsv.setObjectName(_fromUtf8("btnCsv"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)
        self.btnCsv.setToolTip("Exportar a tabela em visualização para um arquivo csv")
        self.gridLayout.addWidget(self.btnCsv, row, column, 1,1)
        row+=1

        self.btnPrint = QtWidgets.QPushButton(Form)
        self.btnPrint.setText("Exportar Contornos DXF")
        self.btnPrint.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btnPrint.setObjectName(_fromUtf8("btnPrint"))
        self.btnPrint.setToolTip("Extportar os contornos dos perfis transversais e verticais como um arquivo CAD dxf")
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)
        self.gridLayout.addWidget(self.btnPrint, row, column, 1,1)
        row+=1

        self.btnCorte = QtWidgets.QPushButton(Form)
        self.btnCorte.setText("Exportar Corte DXF")
        self.btnCorte.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btnCorte.setObjectName(_fromUtf8("btnCorte"))
        #self.btnEstacas.clicked.connect(self.ref_super.tracado)
        self.btnCorte.setToolTip("Exportar curvas de nível do traçado como um arquivo dxf")
        self.gridLayout.addWidget(self.btnCorte, row, column, 1,1)
        row+=1

        self.btn3D = QtWidgets.QPushButton(Form)
        self.btn3D.setText("Exportar Modelo 3D")
        self.btn3D.setGeometry(QtCore.QRect(760, 16 + 34 * 6, 160, 30))
        self.btn3D.setObjectName(_fromUtf8("btn3D"))
        toolTip = "<html><head/><body><p>Exportar um modelo tridimensional do projeto como um arquivo de malha triangular." \
                      "Se o blender <a href='https://www.blender.org/'>(https://www.blender.org/)</a> estiver instalado no sistema uma animação percorrendo " \
                      "o traçado pode ser gerada automaticamente" \
                      "</p></body></html>"

        self.btn3D.setToolTip(toolTip)
        self.btn3D.setWhatsThis(toolTip)
       #self.btnEstacas.clicked.connect(self.ref_super.tracado)
        self.gridLayout.addWidget(self.btn3D, row, column, 1,1)
        row+=1

        self.btnClean = QtWidgets.QPushButton(Form)
        self.btnClean.setText("Apagar Dados Transversais")
        self.btnClean.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.btnClean.setObjectName(_fromUtf8("btnClean"))
        self.gridLayout.addWidget(self.btnClean, row, column, 1, 1)
        self.btnClean.hide()
        row+=3

        self.labelProcurar = QtWidgets.QLabel(Form)
        self.labelProcurar.setText("Procurar: ")
        self.labelProcurar.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.labelProcurar.setObjectName(_fromUtf8("labelProcurar"))
        self.gridLayout.addWidget(self.labelProcurar, row, column, 1, 1)
        row+=1

        self.hor=QtWidgets.QHBoxLayout(Form)
        self.hor.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.hor.setObjectName(_fromUtf8("hor"))
        self.comboBox=QtWidgets.QComboBox(Form)
        self.comboBox.setEditable(True)
        self.spinBox=reversedSpinBox(Form)
        self.spinBox.setMinimum(0)
        self.hor.addWidget(self.comboBox)
        self.hor.addWidget(self.spinBox)
        self.gridLayout.addLayout(self.hor, row, column, 1, 1)
        row+=1

        self.labelComp = QtWidgets.QLabel(Form)
        self.labelComp.setText("Comprimento total: ")
        self.labelComp.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.labelComp.setObjectName(_fromUtf8("labelComp"))
        self.gridLayout.addWidget(self.labelComp, row, column, 1, 1)
        row+=1

        self.comprimento = QtWidgets.QLineEdit(Form)
        self.comprimento.setGeometry(QtCore.QRect(760, 16 + 34 * 7, 160, 30))
        self.comprimento.setObjectName(_fromUtf8("comprimento"))
        self.comprimento.setReadOnly(True)
        self.comprimento.setWhatsThis(u"Comprimento total do traçado (considerando a profundidade do greide)")
        self.gridLayout.addWidget(self.comprimento, row, column, 1, 1)

        self.gridLayout.addWidget(self.tableWidget, 0, 0, row+1, 1)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.setCv()
        self.Form=Form

        self.table : QtWidgets.QTableWidget
        self.table=self.tableWidget
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.stretchTable()
        self.setCopy()
        self.point=False

    def setCopy(self):
        if not hasattr(self, "copyAction"):
            self.copyAction=CopySelectedCellsAction(self, self.table)

    def resizeEvent(self, event):
        self.stretchTable()
        super().resizeEvent(event)  # Restores the original behaviour of the resize event

    def stretchTable(self):
        table=self.tableWidget
        tableSize = table.width()
        sideHeaderWidth = table.verticalHeader().width()
        tableSize -= sideHeaderWidth
        numberOfColumns = table.columnCount()

        remainingWidth = tableSize % numberOfColumns
        for columnNum in range(table.columnCount()):
            if remainingWidth > 0:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns) + 1)
                remainingWidth -= 1
            else:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns))

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Traçado Horizontal", "Traçado Vertical", None))



    def openLayers(self):
        self.closeLayers()
        self.parent.model.iface = self.iface
        l = self.parent.model.getSavedLayers(self.windowTitle().split(":")[0])
        if l:
            l.setName("Curvas: " + l.name())
            l.startEditing()
            self.curvaLayers.append(l)
            l.layerModified.connect(lambda: self.add_row(l))
            self.parent.iface.setActiveLayer(l)

            l.renderer().symbol().setWidth(.5)
            l.renderer().symbol().setColor(QtGui.QColor("#be0c21"))
            l.triggerRepaint()

            if len([a for a in l.getFeatures()]):
                self.parent.iface.mapCanvas().setExtent(l.extent())

    def add_row(self, l):
        self.layer = l
        self.layerUpdated.emit()

    def closeLayers(self):
        for l in self.curvaLayers:
            lyr=l
            name=lyr.name()
            try:
                l.commitChanges()
                l.endEditCommand()
                path=l.dataProvider().dataSourceUri()
                QgsProject.instance().removeMapLayer(l.id())
                self.parent.model.saveLayer(path)
                del l
            except Exception as e:
                try:
                    msgLog("Erro: "+str(e)+"  ao remover layer "+name)
                    del l
                except Exception as ee:
                    msgLog("Erro: " + str(e) +" _&_  "+ str(ee))

        self.curvaLayers=[]

    def reject(self):
        try:
            self.closeLayers()
            self.setWindowTitle(": Horizontal")
        except:
            pass

        self.removePoint()
        self.comboBox.clear()
        return super(EstacasCv, self).reject()

    def close(self):
        self.removePoint()
        self.comboBox.clear()
        return super(EstacasCv, self).close()

    def accept(self):
        try:
            self.closeLayers()
            self.setWindowTitle(": Horizontal")
        except:
            pass

        self.removePoint()
        self.comboBox.clear()
        return super(EstacasCv, self).accept()

    def removePoint(self):
        root = QgsProject.instance()
        try:
            if self.point:
                root.removeMapLayer(self.point)
        except RuntimeError as e:
                pass#Duplicado
        from ..model.helper.qgsgeometry import refreshCanvas
        refreshCanvas(self.iface)

    def zoom(self, row, column):
        root = QgsProject.instance()
        try:
            if self.point:
                root.removeMapLayer(self.point)
        except RuntimeError as e:
                pass#Duplicado

        #ZOOM
        scale = 100
        table=self.tableWidget
        e, x, y = table.item(row,0).text(), float(table.item(row,4).text()), float(table.item(row,3).text())
        point = QgsPointXY(x,y)
        rect = QgsRectangle(x - scale, y - scale, x + scale, y + scale)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()


        #ADD Point Layer
        layer = QgsVectorLayer("Point?crs=%s"%(root.crs().authid()), "Estaca: "+str(e),"memory")
        layer.setCrs(root.crs())
        prov = layer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(point))
        prov.addFeatures([feat])
        root.addMapLayer(layer, False)
        QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
        self.point=layer

    def exec_(self):
        self.point=False
        self.setCopy()
        self.stretchTable()
        name=self.parent.model.getNameFromId(self.parent.model.id_filename)
        self.setWindowTitle(name + ": Vertical")
        self.openLayers()
        return super().exec_()



class Estacas(QtWidgets.QDialog, ESTACAS_DIALOG):

    layerUpdated=pyqtSignal()

    def __init__(self,iface, parent):
        super().__init__(None)
        self.parent=parent
        self.iface = iface
        self.type="horizontal"
        self.setupUi(self)
        self.curvaLayers=[]
        self.empty=True
        self.location_on_the_screen()
        #self.btnPerfil.hide()

        self.spinBox: QtWidgets.QSpinBox
        self.horizontalLayout: QtWidgets.QHBoxLayout
        sp=reversedSpinBox()
        self.horizontalLayout.addWidget(sp)
        self.spinBox=sp
        self.spinBox.setMinimum(0)
        self.spinBox.hide()
        self.comboBox: QtWidgets.QComboBox
        self.comboBox.currentIndexChanged.connect(lambda:
            self.tableWidget.setRangeSelected(
                QTableWidgetSelectionRange(0, 0, 0, self.tableWidget.columnCount() - 1), True)
            )
        self.comboBox.currentTextChanged.connect(self.search)
        self.comboBox.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.spinBox.valueChanged.connect(self.changeSearchResult)
        self.searchResults = []
        self.btnDuplicar.hide()


    def changeSearchResult(self, i):
        if i == 0 or i == len(self.searchResults) + 1:
            self.spinBox.valueChanged.disconnect()
            self.spinBox.setValue(i + 1 if i == 0 else i - 1)
            self.spinBox.valueChanged.connect(self.changeSearchResult)
            return

        if len(self.searchResults) > 0:
            columnIndexes = list(set(index.column()
                                     for index in self.tableWidget.selectionModel().selectedIndexes()))
            row = self.searchResults[i - 1]

            if len(columnIndexes) == 0:
                self.tableWidget.setRangeSelected(
                    QTableWidgetSelectionRange(row, 0, row, self.tableWidget.columnCount() - 1), True)
                self.tableWidget.setCurrentCell(row, 0)
            else:
                for i in columnIndexes:
                    self.tableWidget.setRangeSelected(
                        QTableWidgetSelectionRange(row, i, row, i), True)
                self.tableWidget.setCurrentCell(row, columnIndexes[0])

    def search(self, txt):
        self.searchResults = []
        columnIndexes = list(set(index.column()
                                 for index in self.tableWidget.selectionModel().selectedIndexes()))

        def searchRange(estaca, columnIndexes):
            if len(columnIndexes) > 0:
                estaca = [estaca[i] for i in columnIndexes]
            return "* ".join(estaca)

        for i, estaca in enumerate(self.get_estacas()):
            if txt.upper() in searchRange(estaca, columnIndexes).upper():
                self.searchResults.append(i)
        lres = len(self.searchResults)
        if lres > 1:
            self.spinBox.show()
            self.spinBox.setMaximum(lres + 1)
        else:
            self.spinBox.hide()
        self.changeSearchResult(1)
        self.spinBox.setValue(1)


    def location_on_the_screen(self):
        screen = QDesktopWidget().screenGeometry()
        widget = self.geometry()
        x = 0#widget.width()
        y = (screen.height()-widget.height())/2
        self.move(x, y)

    def clear(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.comboBox.clear()

    def saveEstacasCSV(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(caption="Save Worksheet",filter="Arquivo CSV (*.csv)")
        return filename


    def fill_table(self, estaca,f=False):
        self.comboBox.currentTextChanged.disconnect(self.search)
        self.tableWidget.insertRow(self.tableWidget.rowCount())
        k = self.tableWidget.rowCount() - 1
        j=0
        for value in list(estaca):
            cell_item = QtWidgets.QTableWidgetItem(u"%s" % formatValue(value))
            cell_item.setFlags(cell_item.flags() ^ Qt.ItemIsEditable)
            self.tableWidget.setItem(k,j,cell_item)
            j+=1

        if len(estaca[1])!=0 and not (estaca[1] in [self.comboBox.itemText(i)
                                                    for i in range(self.comboBox.count())]):
            self.comboBox.addItem(estaca[1])
        self.comboBox.currentTextChanged.connect(self.search)

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
            fet.setGeometry(QgsGeometry.fromPoint(p2QgsPoint(e, n)))
            fet.setAttributes([es, d, n, e, c, a])
            fets.append(fet)
        pr.addFeatures(fets)
        vl.commitChanges()
        QgsProject .instance().addMapLayer(vl)

    def openTIFF(self):
        mapCanvas = self.iface.mapCanvas()
        itens = []
        for i in range(mapCanvas.layerCount() - 1, -1, -1):
            try:
                layer = mapCanvas.layer(i)
                layerName = layer.name()
                if type(layer)==qgis._core.QgsRasterLayer and not layer.name() in ['Google Terrain','Google Satellite']:
                    itens.append(layerName)
            except:
                pass
        item, ok = QtWidgets.QInputDialog.getItem(None, "Camada com tracado", u"Selecione o raster com as elevações:",
                                              itens,
                                              0, False)
        if not(ok) or not(item):
            return None
        else:
            layerList = QgsProject .instance().mapLayersByName(item)
            layer = None
            if layerList:
                layer = layerList[0]

        filename = layer.source()
        #filename = QtWidgets.QFileDialog.getOpenFileName(filter="Image files (*.tiff *.tif)")

        return filename
        
    def openDXF(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Autocad files (*.dxf)")
        return filename
        
    def setupUi(self, Form):
        super(Estacas, self).setupUi(Form)
        Form.setObjectName(_fromUtf8(u"Traçado Horizontal"))
        self.modelSource = self.tableWidget.model()
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels((u"Estaca",u"Descrição",u"Progressiva",u"Norte",u"Este",u"Cota",u"Azimute"))
        self.tableWidget.cellClicked.connect(self.zoom)

        self.table : QtWidgets.QTableWidget
        self.table=self.tableWidget
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.stretchTable()


    def resizeEvent(self, event):
        self.stretchTable()
        super().resizeEvent(event)  # Restores the original behaviour of the resize event

    def stretchTable(self):
        table=self.table
        tableSize = table.width()
        sideHeaderWidth = table.verticalHeader().width()
        tableSize -= sideHeaderWidth
        numberOfColumns = table.columnCount()

        remainingWidth = tableSize % numberOfColumns
        for columnNum in range(table.columnCount()):
            if remainingWidth > 0:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns) + 1)
                remainingWidth -= 1
            else:
                table.setColumnWidth(columnNum, int(tableSize / numberOfColumns))

    def event(self, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.WindowStateChange and self.windowState() & QtCore.Qt.WindowMinimized and hasattr(self, "chview"):
            view=self.chview
#                view.show()
            view.setWindowState(view.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            view.activateWindow()
        return super(Estacas, self).event(event)

    def exec_(self):
        self.point=False
        self.setCopy()
        self.stretchTable()
        self.openLayers()
        return super().exec_()

    def accept(self):
        try:
            self.closeLayers()
            self.setWindowTitle(": Horizontal")
        except:
            pass
        return super().accept()

    def reject(self):
        try:
            self.closeLayers()
            self.setWindowTitle(": Horizontal")
        except:
            pass
        return super().reject()

    def openLayers(self):
        self.closeLayers()

        self.parent.model.iface=self.iface
        l=self.parent.model.getSavedLayers(self.windowTitle().split(":")[0])
        if l:
            l.setName("Curvas: "+l.name())
            l.startEditing()
            self.curvaLayers.append(l)
            l.layerModified.connect(lambda: self.add_row(l))
            self.parent.iface.setActiveLayer(l)

            l.renderer().symbol().setWidth(.5)
            l.renderer().symbol().setColor(QtGui.QColor("#be0c21"))
            l.triggerRepaint()

            if len([a for a in l.getFeatures()]):
              self.parent.iface.mapCanvas().setExtent(l.extent())


    def add_row(self,l):
        self.layer=l
        self.layerUpdated.emit()


    def closeLayers(self):
        for l in self.curvaLayers:
            try:
                lyr=l
                name=lyr.name()
            except:
                break
            try:
                l.commitChanges()
                l.endEditCommand()
                path=l.dataProvider().dataSourceUri()
                QgsProject.instance().removeMapLayer(l.id())
                self.parent.model.saveLayer(path)
                del l
            except Exception as e:
                try:
                    msgLog("Erro: "+str(e)+"  ao remover layer "+name)
                    del l
                except Exception as ee:
                    msgLog("Erro: " + str(e) +" _&_  "+ str(ee))

        self.curvaLayers=[]

    def setCopy(self):
        if not hasattr(self, "copyAction"):
            self.copyAction=CopySelectedCellsAction(self, self.table)


    def clearLayers(self):
        try:
            if hasattr(self,"point") and self.point:
                QgsProject.instance().removeMapLayer(self.point)
                self.iface.mapCanvas().refresh()

        except:
            pass

    def zoom(self, row, column):
        root = QgsProject.instance()
        try:
            if self.point:
                root.removeMapLayer(self.point)
        except RuntimeError as e:
                pass#Duplicado

        #ZOOM
        scale = 100
        table=self.tableWidget
        e, x, y = table.item(row,0).text(), float(table.item(row,4).text()), float(table.item(row,3).text())
        point = QgsPointXY(x,y)
        rect = QgsRectangle(x - scale, y - scale, x + scale, y + scale)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()


        #ADD Point Layer
        layer = QgsVectorLayer("Point?crs=%s"%(root.crs().authid()), "Estaca: "+str(e),"memory")
        layer.setCrs(root.crs())
        prov = layer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPointXY(point))
        prov.addFeatures([feat])
        root.addMapLayer(layer, False)
        QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
        self.point=layer



class closeDialog(QtWidgets.QDialog):
    save = QtCore.pyqtSignal()
    dischart = QtCore.pyqtSignal()
    cancel = QtCore.pyqtSignal()

    def __init__(self, *args, **kwds):
        super(closeDialog, self).__init__(*args, **kwds)
        self.wasCanceled=False
        self.setupUI()

    def setupUI(self):

        self.setWindowTitle("Fechar")
        label = QtWidgets.QLabel(u"Deseja salvar suas alterações?")
        btnSave=QtWidgets.QPushButton(self)       
        btnSave.setText("Sim")
        btnSave.setToolTip("Salvar o perfil vertical desenhado")
        btnSave.clicked.connect(self.__exitSave)


        btnNot=QtWidgets.QPushButton(self)       
        btnNot.setText(u"Não")
        btnNot.setToolTip(u"Descartar alterações")
        btnNot.clicked.connect(self.__exitNotSave)


        btnCancel=QtWidgets.QPushButton(self)       
        btnCancel.setText("Cancelar")
        btnCancel.setToolTip("Voltar para Janela de desenho")
        btnCancel.clicked.connect(self.__exitCancel)


        Vlayout=QtWidgets.QVBoxLayout()
        HLayout=QtWidgets.QHBoxLayout()

        Vlayout.addWidget(label)
        HLayout.addWidget(btnSave)
        HLayout.addWidget(btnNot)
        HLayout.addWidget(btnCancel)
        Vlayout.addLayout(HLayout)

        self.setLayout(Vlayout)



    def __exitSave(self):
        self.save.emit()
        self.close()
    def __exitNotSave(self):
        self.dischart.emit()
        self.close()
    def __exitCancel(self):
        self.cancel.emit()
        self.close()

 


class rampaDialog(QtWidgets.QDialog):
    def __init__(self, roi, segment, pos, index=1):
        super(rampaDialog, self).__init__(None)
        self.setWindowTitle(u"Modificar Rampa")
        self.roi=roi
        self.segment=segment
        self.pos=pos
        self.index=index
        self.setupUI()


    def setupUI(self):
        r=[]
        for handle in self.roi.getHandles():
            r.append(handle)
        
        self.firstHandle=r[0]
        self.lastHandle=r[len(r)-1]
 
        H1layout=QtWidgets.QHBoxLayout()
        H2layout=QtWidgets.QHBoxLayout()
        H3layout=QtWidgets.QHBoxLayout()
        Vlayout=QtWidgets.QVBoxLayout(self)

        label=QtWidgets.QLabel("Modificar Rampa")

        Incl=QtWidgets.QDoubleSpinBox()
        Incl.setMaximum(99.99)
        Incl.setMinimum(-99.99)
        Incl.setSingleStep(.05)
        compr=QtWidgets.QDoubleSpinBox()
        compr.setMaximum(1000000000.0)
        compr.setMinimum(0.0)
        cota=QtWidgets.QDoubleSpinBox()
        cota.setMinimum(0.0)
        cota.setMaximum(10000.0)
        cota2 = QtWidgets.QDoubleSpinBox()
        cota2.setMinimum(0.0)
        cota2.setMaximum(10000.0)
        abscissa=QtWidgets.QDoubleSpinBox()
        abscissa.setMaximum(1000000000.0)
        abscissa.setMinimum(0.0)

        InclLbl=QtWidgets.QLabel(u"Inclinação: ")
        posInclLbl=QtWidgets.QLabel(u"%")
        comprLbl=QtWidgets.QLabel(u"Distância inclinada: ")
        poscomprLbl=QtWidgets.QLabel(u"m")
        cotaLbl=QtWidgets.QLabel(u"Cotas: V"+str(self.index-2)+"")
        cotaLbl2=QtWidgets.QLabel(u"V"+str(self.index-1))
        poscotaLbl=QtWidgets.QLabel(u"m")
        abscissalbl=QtWidgets.QLabel(u"Distância Horizontal: ")
        posabscissaLbl=QtWidgets.QLabel(u"m")

        
        h1 = self.segment.handles[0]['item']
        h2 = self.segment.handles[1]['item']

        self.h1=h1
        self.h2=h2

        self.initialPos=[h1.pos(),h2.pos()]

        b1 = QtWidgets.QPushButton("ok",self)
        b1.clicked.connect(self.finishDialog)
        b2 = QtWidgets.QPushButton("cancelar", self)
        b2.clicked.connect(lambda: self.cleanClose())

        H1layout.addWidget(cotaLbl)
        H1layout.addWidget(cota2)
        H1layout.addWidget(cotaLbl2)
        H1layout.addWidget(cota)
        H1layout.addWidget(poscotaLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H1layout.addWidget(comprLbl)
        H1layout.addWidget(compr)
        H1layout.addWidget(poscomprLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(InclLbl)
        H2layout.addWidget(Incl)
        H2layout.addWidget(posInclLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(abscissalbl)
        H2layout.addWidget(abscissa)
        H2layout.addWidget(posabscissaLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        Vlayout.addWidget(label)
        Vlayout.addLayout(H1layout)
        Vlayout.addLayout(H2layout)
        H3layout.addItem(QtWidgets.QSpacerItem(80,20,QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
        H3layout.addWidget(b1)
        H3layout.addWidget(b2)
        Vlayout.addLayout(H3layout)

        self.InclText=Incl       
        self.Incl=100*(h2.pos().y()-h1.pos().y())/(h2.pos().x()-h1.pos().x())
        self.comprText=compr
        self.compr=np.sqrt((h2.pos().y()-h1.pos().y())**2+(h2.pos().x()-h1.pos().x())**2)
        self.cotaText=cota
        self.cotaText2=cota2
        self.cota=h2.pos().y()
        self.cotaa=h1.pos().y()
        self.abscissaText=abscissa
        self.abscissa=h2.pos().x()-h1.pos().x()
        cota2.setValue(round(h1.pos().y(), 2))
        #cota2.setDisabled(True)
        cota2.setWhatsThis("Cota do ponto anterior ao seguimento")
        cota.setWhatsThis("Cota do ponto adjacente ao seguimento")

        Incl.setValue(round(self.Incl,2))
        compr.setValue(round(self.compr,2))
        cota.setValue(round(self.cota,2))
        abscissa.setValue(round(self.abscissa,2))

        compr.valueChanged.connect(self.updateCompr)
        cota.valueChanged.connect(self.updateCota)
        cota2.valueChanged.connect(self.updateCota)
        abscissa.valueChanged.connect(self.updateAbscissa)
        Incl.valueChanged.connect(self.updateIncl)

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.isBeingModified=False 


    def updateCompr(self):
        try:
            if not self.isBeingModified:
                c=self.compr
                self.compr=float(self.comprText.value())
                dc=self.compr-c
                Incl = float(np.arctan(self.InclText.value() / 100))
                self.cota=self.cota+np.sin(np.deg2rad(self.Incl))*dc
                self.abscissa = np.cos((Incl)) * self.compr
                self.update()
                self.redefineUI(1)

        except ValueError:
            pass

     
        
    def updateCota(self):
        try:
            if not self.isBeingModified:  
                self.cota=float(self.cotaText.value())
                self.cotaa=float(self.cotaText2.value())
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(2)
        except ValueError:
            pass


    def updateAbscissa(self):
        try:
            if not self.isBeingModified:
                self.abscissa=float(self.abscissaText.value())
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(3)
        except ValueError:
            pass


    def updateIncl(self):
        try:
            if not self.isBeingModified:
               self.Incl=float(np.arctan(self.InclText.value()/100))
               self.cota=np.sin((self.Incl))*self.compr+self.h1.pos().y()
               #self.abscissa=np.cos((self.Incl))*self.compr
               self.update()
               self.compr = np.sqrt((self.h2.pos().y() - self.h1.pos().y()) ** 2 + (self.h2.pos().x() - self.h1.pos().x()) ** 2)
               self.redefineUI(4)
        except ValueError:
            pass

       
    def update(self): 

        self.h2.setPos(self.abscissa+self.h1.pos().x(), self.cota)
        self.h1.setPos(self.h1.pos().x(), self.cotaa)

        if self.firstHandle == self.h2:
            self.firstHandle.setPos(self.initialPos[1].x(),self.cota)   
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()-self.h1.pos().x()
            self.cotaText.setValue(float(self.cota))
            self.abscissaText.setValue(float(self.abscissa))

        if self.lastHandle == self.h2:
            self.lastHandle.setPos(self.initialPos[1].x(),self.cota)
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()-self.h1.pos().x()
            self.cotaText.setValue(float(self.cota))
            self.abscissaText.setValue(float(self.abscissa))

    
    def redefineUI(self, elm):
        self.isBeingModified=True

        if elm==1:       
            self.cotaText.setValue(float(round(self.cota,2)))
            self.abscissaText.setValue(float(round(self.abscissa,2)))
            self.InclText.setValue(float(round(self.Incl,2)))
        elif elm==2:
            self.comprText.setValue(float(round(self.compr,2)))
            self.abscissaText.setValue(float(round(self.abscissa,2)))
            self.InclText.setValue(float(round(self.Incl,2)))
        elif elm==3:           
            self.comprText.setValue(float(round(self.compr,2)))
            self.cotaText.setValue(float(round(self.cota,2)))
            self.InclText.setValue(float(round(self.Incl,2)))
        elif elm==4:           
            self.comprText.setValue(float(round(self.compr,2)))
            self.cotaText.setValue(float(round(self.cota,2)))
            self.abscissaText.setValue(float(round(self.abscissa,2)))
           

        self.isBeingModified=False


    def finishDialog(self):
        self.close()
    
    def cleanClose(self):
        self.h2.setPos(self.initialPos[1].x(),self.initialPos[1].y())
        self.h1.setPos(self.initialPos[0].x(),self.initialPos[0].y())
        self.close()

class ssRampaDialog(rampaDialog):
    def __init__(self, roi, segment, pos, cota):
        self.ycenter=cota
        self.isBeingModified = True
        super().__init__(roi, segment, pos)
        self.setWindowTitle("Modificar Elemento")


    def setupUI(self):
        r = []
        for handle in self.roi.getHandles():
            r.append(handle)

        self.firstHandle = r[0]
        self.lastHandle = r[len(r) - 1]

        H1layout = QtWidgets.QHBoxLayout()
        H2layout = QtWidgets.QHBoxLayout()
        H3layout = QtWidgets.QHBoxLayout()
        Vlayout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("Modificar Rampa")

        Incl=QtWidgets.QDoubleSpinBox()
        Incl.setMaximum(99.99)
        Incl.setMinimum(-99.99)
        Incl.setSingleStep(.05)
        compr=QtWidgets.QDoubleSpinBox()
        compr.setMaximum(1000000000.0)
        compr.setMinimum(0.0)
        compr.setSingleStep(.1)
        cota=QtWidgets.QDoubleSpinBox()
        cota.setMinimum(-10000.0)
        cota.setMaximum(10000.0)
        cota.setSingleStep(.1)
        cota2 = QtWidgets.QDoubleSpinBox()
        cota2.setMinimum(-10000.0)
        cota2.setMaximum(10000.0)
        cota2.setSingleStep(.1)
        abscissa=QtWidgets.QDoubleSpinBox()
        abscissa.setMaximum(100000.0)
        abscissa.setMinimum(-10000.0)
        abscissa.setSingleStep(.1)

        InclLbl = QtWidgets.QLabel(u"Inclinação: ")
        posInclLbl = QtWidgets.QLabel(u"%")
        comprLbl = QtWidgets.QLabel(u"Comprimento: ")
        poscomprLbl = QtWidgets.QLabel(u"m")
        cotaLbl = QtWidgets.QLabel(u"Cota:      ")
        poscotaLbl = QtWidgets.QLabel(u"m")
        abscissalbl = QtWidgets.QLabel(u"Distância até o eixo")
        posabscissaLbl = QtWidgets.QLabel(u"m")

        h1 = self.segment.handles[0]['item']
        h2 = self.segment.handles[1]['item']

        self.h1 = h1
        self.h2 = h2

        self.initialPos = [h1.pos(), h2.pos()]

        b1 = QtWidgets.QPushButton("ok", self)
        b1.clicked.connect(self.finishDialog)
        b2 = QtWidgets.QPushButton("cancelar", self)
        b2.clicked.connect(lambda: self.cleanClose())

        H1layout.addWidget(cotaLbl)
        H1layout.addWidget(cota2)
        H1layout.addWidget(cota)
        H1layout.addWidget(poscotaLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H1layout.addWidget(comprLbl)
        H1layout.addWidget(compr)
        H1layout.addWidget(poscomprLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(InclLbl)
        H2layout.addWidget(Incl)
        H2layout.addWidget(posInclLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(abscissalbl)
        H2layout.addWidget(abscissa)
        H2layout.addWidget(posabscissaLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        Vlayout.addWidget(label)
        Vlayout.addLayout(H1layout)
        Vlayout.addLayout(H2layout)
        H3layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
        H3layout.addWidget(b1)
        H3layout.addWidget(b2)
        Vlayout.addLayout(H3layout)

        self.InclText = Incl
        self.Incl = 100 * (h2.pos().y() - h1.pos().y()) / (h2.pos().x() - h1.pos().x())
        self.comprText = compr
        self.compr = np.sqrt((h2.pos().y() - h1.pos().y()) ** 2 + (h2.pos().x() - h1.pos().x()) ** 2)
        self.cotaText = cota
        self.cota = h2.pos().y()
        self.cotaa = h1.pos().y()
        self.abscissaText = abscissa
        self.abscissa = h2.pos().x()
        cota2.setWhatsThis("Cota do ponto anterior ao seguimento")
        cota.setWhatsThis("Cota do ponto adjacente ao seguimento")
        self.cotaText2 = cota2

        cota.setValue(float(round(self.cota-self.ycenter, 2)))
        abscissa.setValue(float(round(self.abscissa, 2)))
        cota2.setValue(round(self.cotaa-self.ycenter,2))

        compr.valueChanged.connect(self.updateCompr)
        cota.valueChanged.connect(self.updateCota)
        abscissa.valueChanged.connect(self.updateAbscissa)
        Incl.valueChanged.connect(self.updateIncl)
        cota2.valueChanged.connect(self.updateCota)

        Incl.setValue(float(round(self.Incl, 2)))
        compr.setValue(float(round(self.compr, 2)))
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.isBeingModified = False

    def updateCompr(self):
        try:
            if not self.isBeingModified:
                self.Incl = float(np.arctan(self.InclText.value() / 100))
                c=self.compr
                self.compr=float(self.comprText.value())
                dc=self.compr-c
                self.cota=self.cota+np.sin(np.deg2rad(self.Incl))*dc
                self.abscissa=self.abscissa+np.cos(np.deg2rad(self.Incl))*dc
                self.update()
                self.redefineUI(1)

        except ValueError:
            pass


    def updateIncl(self):
        try:
            if not self.isBeingModified:
               self.Incl=float(np.arctan(self.InclText.value()/100))
               self.cota=np.sin((self.Incl))*self.compr+self.h1.pos().y()
               self.abscissa=np.cos((self.Incl))*self.compr+self.h1.pos().x()
               self.update()
               self.redefineUI(4)
        except ValueError:
            pass


    def updateAbscissa(self):
        try:
            if not self.isBeingModified:
                self.abscissa=float(self.abscissaText.value())
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(3)
        except ValueError:
            pass

    def updateCota(self):
        try:
            if not self.isBeingModified:
                self.cota=float(self.cotaText.value())+self.ycenter
                self.cotaa=float(self.cotaText2.value())+self.ycenter
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(2)
        except ValueError:
            pass

    def redefineUI(self, elm):
        self.isBeingModified = True

        if elm == 1:
            self.cotaText.setValue(float(round(self.cota-self.ycenter, 2)))
            self.abscissaText.setValue(float(round(self.abscissa, 2)))
            self.InclText.setValue(float(round(self.Incl, 2)))
        elif elm == 2:
            self.comprText.setValue(float(round(self.compr, 2)))
            self.abscissaText.setValue(float(round(self.abscissa, 2)))
            self.InclText.setValue(float(round(self.Incl, 2)))
        elif elm == 3:
            self.comprText.setValue(float(round(self.compr, 2)))
            self.cotaText.setValue(float(round(self.cota-self.ycenter, 2)))
            self.InclText.setValue(float(round(self.Incl, 2)))
        elif elm == 4:
            self.comprText.setValue(float(round(self.compr, 2)))
            self.cotaText.setValue(float(round(self.cota-self.ycenter, 2)))
            self.abscissaText.setValue(float(round(self.abscissa, 2)))
        self.isBeingModified=False


    def update(self):

        self.h2.setPos(self.abscissa, self.cota)
        self.h1.setPos(self.h1.pos().x(), self.cotaa)

        if self.firstHandle == self.h2:
            self.firstHandle.setPos(self.initialPos[1].x(),self.cota)
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()
            self.cotaText.setValue(float(self.cota)-self.ycenter)
            self.abscissaText.setValue(float(self.abscissa))

        if self.lastHandle == self.h2:
            self.lastHandle.setPos(self.initialPos[1].x(),self.cota)
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()
            self.cotaText.setValue(float(self.cota)-self.ycenter)
            self.abscissaText.setValue(float(self.abscissa))



class brucknerRampaDialog(rampaDialog):
    def __init__(self, roi, segment, pos):
        super(brucknerRampaDialog, self).__init__(roi, segment, pos)
        self.setWindowTitle("Modificar Elemento")

    def setupUI(self):
        r = []
        for handle in self.roi.getHandles():
            r.append(handle)

        self.firstHandle = r[0]
        self.lastHandle = r[len(r) - 1]

        H1layout = QtWidgets.QHBoxLayout()
        H2layout = QtWidgets.QHBoxLayout()
        H3layout = QtWidgets.QHBoxLayout()
        Vlayout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel("Modificar Rampa")

        Incl=QtWidgets.QDoubleSpinBox()
        Incl.setMaximum(100.0)
        Incl.setMinimum(-100.0)
        compr=QtWidgets.QDoubleSpinBox()
        compr.setMaximum(1000000000.0)
        compr.setMinimum(0.0)
        cota=QtWidgets.QDoubleSpinBox()
        cota.setMinimum(0.0)
        cota.setMaximum(100000000.0)
        abscissa=QtWidgets.QDoubleSpinBox()
        abscissa.setMaximum(1000000000.0)
        abscissa.setMinimum(0.0)
        Incl.setSingleStep(.01)

        InclLbl = QtWidgets.QLabel(u"Inclinação: ")
        posInclLbl = QtWidgets.QLabel(u"%")
        comprLbl = QtWidgets.QLabel(u"Comprimento: ")
        poscomprLbl = QtWidgets.QLabel(u"m")
        cotaLbl = QtWidgets.QLabel(u"Cota:      ")
        poscotaLbl = QtWidgets.QLabel(u"m")
        abscissalbl = QtWidgets.QLabel(u"Distância até o eixo")
        posabscissaLbl = QtWidgets.QLabel(u"m")

        h1 = self.segment.handles[0]['item']
        h2 = self.segment.handles[1]['item']

        self.h1 = h1
        self.h2 = h2

        self.initialPos = [h1.pos(), h2.pos()]

        b1 = QtWidgets.QPushButton("ok", self)
        b1.clicked.connect(self.finishDialog)
        b2 = QtWidgets.QPushButton("cancelar", self)
        b2.clicked.connect(lambda: self.cleanClose())

        H1layout.addWidget(InclLbl)
        H1layout.addWidget(Incl)
        H1layout.addWidget(posInclLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H1layout.addWidget(comprLbl)
        H1layout.addWidget(compr)
        H1layout.addWidget(poscomprLbl)
        H1layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(cotaLbl)
        H2layout.addWidget(cota)
        H2layout.addWidget(poscotaLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        H2layout.addWidget(abscissalbl)
        H2layout.addWidget(abscissa)
        H2layout.addWidget(posabscissaLbl)
        H2layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))

        Vlayout.addWidget(label)
        Vlayout.addLayout(H1layout)
        Vlayout.addLayout(H2layout)
        H3layout.addItem(QtWidgets.QSpacerItem(80, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
        H3layout.addWidget(b1)
        H3layout.addWidget(b2)
        Vlayout.addLayout(H3layout)

        self.InclText = Incl
        self.Incl = 100 * (h2.pos().y() - h1.pos().y()) / (h2.pos().x() - h1.pos().x())
        self.comprText = compr
        self.compr = (h2.pos().x() - h1.pos().x())
        self.cotaText = cota
        self.cota = h2.pos().y()/1000000
        self.abscissaText = abscissa
        self.abscissa = h2.pos().x()

        Incl.setValue(float(round(self.Incl, 2)))
        compr.setValue(float(round(self.compr, 2)))
        cota.setValue(float(round(self.cota, 2)))
        abscissa.setValue(float(round(self.abscissa, 2)))

        compr.valueChanged.connect(self.updateCompr)
        #cota.valueChanged.connect(self.updateCota)
        abscissa.valueChanged.connect(self.updateAbscissa)
        Incl.valueChanged.connect(self.updateIncl)

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.isBeingModified = False

        Incl.setDisabled(True)
        posabscissaLbl.setText(" Estacas")
        poscomprLbl.setText(" Estacas")
        cotaLbl.setText(" Eixo")
        poscotaLbl.setText(u' 10⁶ m³')
        InclLbl.setDisabled(True)
        posInclLbl.setDisabled(True)

        self.cotasb=cota

    def updateCompr(self):
        try:
            if not self.isBeingModified:
                c = self.compr
                self.compr = round(float(self.comprText.value()), 2)
                dc = self.compr - c
                self.cota = round(self.cota + np.sin(np.deg2rad(self.Incl)) * dc, 2)
                self.abscissa = round(self.abscissa + np.cos(np.deg2rad(self.Incl)) * dc, 2)
                self.update()
                self.redefineUI(1)

        except ValueError:
            pass

    def update(self):
        self.h2.setPos(self.abscissa, self.h2.pos().y())
        if self.firstHandle == self.h2:
            self.firstHandle.setPos(self.initialPos[1].x(),self.cota)   
            self.Incl=round(100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())   , 2)
            self.compr=round(np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)   , 2)
            self.cota=round(self.h2.pos().y(), 2)
            self.abscissa=round(self.h2.pos().x(), 2)
            self.cotaText.setValue(float(self.cota))
            self.abscissaText.setValue(float(self.abscissa))

        if self.lastHandle == self.h2:
            self.lastHandle.setPos(self.initialPos[1].x(),self.cota)
            self.Incl=round(100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x()), 2)
            self.compr=round(np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)   , 2)
            self.cota=round(self.h2.pos().y(), 2)
            self.abscissa=round(self.h2.pos().x(), 2)
            self.cotaText.setValue(float(self.cota))
            self.abscissaText.setValue(float(self.abscissa))


class cvEdit(QtWidgets.QDialog, VERTICE_EDIT_DIALOG):
    def __init__(self, iface):
        super(cvEdit, self).__init__(None)
        self.iface = iface
        self.setupUi(self)

       # self.setFixedSize(self.size())

    def removeCv(self):
        self.groupBox_2.setFlat(True)
        self.groupBox_2.setStyleSheet("border:1;")

        self.pushButton.hide()
        self.widget1.hide()
        self.widget2.hide()
        self.widget3.hide()
        self.widget4.hide()
        self.groupBox_2.setTitle('')


class ApplyTransDialog(QtWidgets.QDialog, APLICAR_TRANSVERSAL_DIALOG):
    firstCb: QtWidgets.QComboBox
    secondCb: QtWidgets.QComboBox

    def __init__(self, iface, prog):
        super(ApplyTransDialog, self).__init__(None)
        self.iface=iface
        self.setupUi(self)
        self.progressiva=prog
        self.progressivas=[]
        self.dist=Config.instance().DIST
        self.firstCb.currentIndexChanged.connect(self.setSecondCb)
        self.secondCb.currentIndexChanged.connect(self.setIndexes)
        self.setupUi2()

    def setupUi2(self):
        d=self.dist
        self.firstCb.addItems(list(map(lambda i: fastProg2EstacaStr(i, d), self.progressiva)))
        self.setSecondCb()

    def setSecondCb(self):
        d=self.dist
        self.secondCb.clear()
        self.secondCb.addItems(list(map(lambda i: fastProg2EstacaStr(i, d), self.progressiva[self.firstCb.currentIndex():])))
        self.setIndexes()

    def setIndexes(self):
        self.progressivas=[self.firstCb.currentIndex(),self.secondCb.currentIndex()]


class SetCtAtiDialog(QtWidgets.QDialog, SETCTATI_DIALOG):
    firstCb: QtWidgets.QComboBox
    secondCb: QtWidgets.QComboBox

    def __init__(self, iface, prog):
        super(SetCtAtiDialog, self).__init__(None)
        self.iface=iface
        self.setupUi(self)
        self.roiIndexes=[]
        self.firstOptions=[]
        self.secondOptions=[]
        for i, _ in enumerate(prog):
            self.roiIndexes.append(i)
            self.firstOptions.append(i+1)

        self.indices=None
        self.setupUi2()
        self.firstCb.currentIndexChanged.connect(self.setIndexes)
        self.secondCb.currentIndexChanged.connect(self.setIndexes)

    def setupUi2(self):
        self.firstCb.addItems(list(map(str, self.firstOptions)))
        self.secondCb.addItems(list(map(str, self.firstOptions)))

    def setIndexes(self):
        self.cti=self.firstCb.currentIndex()
        self.ati=self.secondCb.currentIndex()


#TODO convert to real scale
class setEscalaDialog(QtWidgets.QDialog, SET_ESCALA_DIALOG):
    def __init__(self, iface):
        super(setEscalaDialog, self).__init__(None)
        self.iface=iface
        self.x: QtWidgets.QSpinBox
        self.y: QtWidgets.QSpinBox
        self.setupUi(self)
        self.vb=self.iface.vb
        self.x.setValue(1.0)
        self.y.setValue(1.0)
        self.x.valueChanged.connect(self.changed)
        self.y.valueChanged.connect(self.changed)
        self.zoomBtn.clicked.connect(self.zoom)

    def getX(self):
        return float(self.x.value())

    def getY(self):
        return float(self.y.value())

    def zoom(self):
        self.vb.autoRange()

    def changed(self):
        self.zoom()
        self.vb.scaleBy((self.getX(), self.getY()))


class SelectFeatureDialog(QtWidgets.QDialog, SELECT_FEATURE):
    def __init__(self, iface, layer):
        super().__init__(None)
        self.iface=iface
        self.layer=layer
        self.setupUi(self)
        self.Dialog: QtWidgets.QDialog
        self.buttonBox: QtWidgets.QDialogButtonBox
        self.checkBox: QtWidgets.QCheckBox
        self.groupBox: QtWidgets.QGroupBox
        self.tableWidget: QtWidgets.QTableWidget
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result=-1 #loop over all

        for feat in layer.getFeatures():
            if self.tableWidget.columnCount()>9:
                break
            if feat.hasGeometry():
                row = []
                for f in feat.fields():
                    row.append(str(f.name()) + ": " + str(feat[f.name()]))
                row.append("Comprimento: "+str(feat.geometry().length()))
                self.tableWidget.insertRow(self.tableWidget.rowCount())
                k = self.tableWidget.rowCount() - 1
                j=0
                for r in row:
                    if j>=self.tableWidget.columnCount():
                        self.tableWidget.insertColumn(self.tableWidget.columnCount())
                    item=QtWidgets.QTableWidgetItem(u"%s" % r)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    self.tableWidget.setItem(k, j, item)
                    j+=1

        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.cellDoubleClicked.connect(self.accept)
        self.tableWidget.selectRow(self.tableWidget.rowCount()-1)
        self.tableWidget.setCurrentIndex(self.tableWidget.model().index(self.tableWidget.rowCount()-1,self.tableWidget.columnCount()-1))

        if self.tableWidget.rowCount()==0:
            self.checkBox.setChecked(True)
            self.checkBox.setDisabled(True)
            self.accept()
        else:
            self.result=self.tableWidget.rowCount()-1 #feature index
            self.tableWidget.itemSelectionChanged.connect(self.updateResult)
            self.checkBox.stateChanged.connect(self.check)

        self.checkBox.setChecked(True)
        self.checkBox.setFocus()

    def updateResult(self):
        self.result=self.tableWidget.currentRow()
        g : QgsRectangle
        f=0
        for x in self.layer.getFeatures():
            if f==self.result:
                g = self.layer.getFeature(self.result).geometry().boundingBox()
                break
            f+=1
        iface.mapCanvas().setExtent(QgsRectangle(g.xMinimum()-50,g.yMinimum()-50,g.xMaximum()+50,g.yMaximum()+50))
        iface.mapCanvas().refresh()

    def check(self, i):
        if i==0:
            self.tableWidget.setDisabled(False)
            self.updateResult()
        else:
            self.result=-1
            self.tableWidget.setDisabled(True)

from qgis.PyQt.QtWidgets import QProgressBar


class ProgressDialog():#QtWidgets.QProgressDialog):  #, PROGRESS_DIALOG):

    def __init__(self, iface, msg=None, noProgressBar=False):

        self.iface=iface
        self.text=None
        self.floor=0
        self.stepValue=1
        self.ceiling=100
        self.value=0

 #       self.setupUi(self)
#
#        self.Dialog: QtWidgets.QDialog
#        self.label: QtWidgets.QLabel
#        self.progressBar: QtWidgets.QProgressBar
#
#        if not msg is None:
#            self.label.setText(str(msg))
#        self.progressBar.setValue(0)
##        self.setWindowFlags((self.windowFlags() | Qt.CustomizeWindowHint) & ~Qt.WindowCloseButtonHint)
#
#        if noProgressBar:
#            self.progressBar.hide()
#        self.stepValue=1
 #       super(ProgressDialog, self).__init__(iface)
 #       self.setLabelText(msg)
 #       self.setWindowTitle("Aguarde")


    def show(self):
   #     r=super().forceShow()
   #     self.setWindowModality(Qt.WindowModal)
   #     self.setValue(0)
   #     return r
            if self.text==None:
                self.text="Carregando"

            self.progressMessageBar = iface.messageBar().createMessage(self.text)
            self.progressBar = QProgressBar()
            self.progressBar.setMaximum(100)
            self.progressBar.setValue(0)
            self.progressBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.progressMessageBar.layout().addWidget(self.progressBar)
            self.iface.messageBar().pushWidget(self.progressMessageBar, Qgis.Info)


#    def forceShow(self):
#        return super(ProgressDialog, self).forceShow()

#    def keyPressEvent(self, a0: QtGui.QKeyEvent):
#        if a0.key() != Qt.Key_Escape:
#            super().keyPressEvent(a0)
#        else:
#            self.showMinimized()
#
    def setValue(self, f:float):
        self.progressBar: QtWidgets.QProgressBar
        self.progressBar.setValue(f)
        self.floor=f

    def setLoop(self, ceiling, totalSteps, floor=None):
        """
        :param ceiling: Onde quero chegar (Startinf point) in range 0-100
        :param totalSteps: Número de passos (Number of loop steps)  0-100
        :param floor: Onde vou partir (Starting value) 0-100
        :return:
        """
        if floor is None:
            self.floor=self.progressBar.value()
        else:
            self.floor=floor
            self.progressBar.setValue(floor)
        self.ceiling=ceiling
        self.totalSteps=totalSteps
        self.stepValue=(self.ceiling-self.floor)/totalSteps

    def increment(self):
        """
        Dá um passo. Útil para ser usada em loop
        :return:
        """
        self.progressBar: QtWidgets.QProgressBar
        self.progressBar.show()
        self.value+=self.stepValue
        self.setValue(int(min(self.value, self.ceiling)))
      #  msgLog("Progress bar"+str(self.progressBar.value()))

    def close(self):
         self.progressBar.setValue(0)
         self.__init__(self.iface)
     #   return super().close()
         self.iface.messageBar().clearWidgets()

    def setText(self, s):
        self.text=s
        self.textSet=True
        try:
            if hasattr(self, "progressBar") and self.progressBar.isVisible():
                self.close()
                self.show()
        except:  #C++ runtine error because progressBar was deleted
            pass



class EstacaRangeSelect(QtWidgets.QDialog, BRUCKNER_SELECT):

    def __init__(self, iface, estacas, bruck=[]):
        super().__init__(iface)
        self.iface=iface
        self.setupUi(self)

        self.Dialog : QtWidgets.QDialog
        self.final_2 : QtWidgets.QComboBox
        self.inicial : QtWidgets.QComboBox
        self.label : QtWidgets.QLabel
        self.label_2 : QtWidgets.QLabel
        self.listWidget : QtWidgets.QListWidget
        self.btnApagar : QtWidgets.QPushButton

        estacas=[str(e) for e in estacas]
        self.inicial.addItems(estacas)
        self.inicial.setCurrentIndex(0)
        self.final_2.addItems(estacas)
        self.final_2.setCurrentIndex(1)
        self.inicial.currentIndexChanged.connect(self.change1)
        self.final_2.currentIndexChanged.connect(self.change2)
        self.inicial.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.final_2.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.ei=float(self.inicial.currentText())
        self.ef=float(self.final_2.currentText())
        self.listWidget.itemClicked.connect(self.itemClick)
        self.bruck=bruck
        self.fill_list(self.bruck)
        self.btnApagar.clicked.connect(self.apagar)

    def apagar(self):
        self.listWidget : QtWidgets.QListWidget
        for s in self.listWidget.selectedItems():
            self.listWidget.removeItemWidget(s)
            del self.bruck[s.text()]
            msgLog("Erasing "+str(s.text()))
        self.fill_list(self.bruck)

    def itemClick(self, item):
        ests=item.text().split("-")
        index = self.inicial.findText(ests[0])
        self.inicial.setCurrentIndex(index)
        index = self.final_2.findText(ests[1])
        self.final_2.setCurrentIndex(index)
        msgLog("Setting range "+str(ests))

    def change1(self):
        self.inicial : QtWidgets.QComboBox
        self.final_2 : QtWidgets.QComboBox
        if self.inicial.currentIndex() >= self.final_2.currentIndex():
            self.final_2.setCurrentIndex(self.inicial.currentIndex()+1)


    def change2(self):
        self.inicial : QtWidgets.QComboBox
        self.final_2 : QtWidgets.QComboBox
        if self.final_2.currentIndex() <= self.inicial.currentIndex():
            self.final_2.setCurrentIndex(self.inicial.currentIndex()+1)

    def fill_list(self, data):
        self.listWidget : QtWidgets.QListWidget
        self.listWidget.clear()
        for key in list(data.keys()):
            if "-" in key:
                self.listWidget.addItem(str(key))


class VolumeDialog(QtWidgets.QDialog, VOLUME_DIALOG):
    def __init__(self, iface):
        super().__init__(iface)
        self.iface = iface
        self.setupUi(self)

    def set(self, corte, aterro):
        from ..model.utils import roundFloat2str
        self.corte: QtWidgets.QLineEdit
        self.aterro: QtWidgets.QLineEdit
        self.corte.setText(roundFloat2str(corte))
        self.aterro.setText(roundFloat2str(aterro))
        self.soma.setText(roundFloat2str(corte+aterro))



class CorteExport(QtWidgets.QDialog, EXPORTAR_CORTE):
    def __init__(self, iface, maxprog):
        super().__init__(iface)
        self.iface = iface
        self.setupUi(self)
        self.ExportarCorte: QtWidgets.QDialog
        self.btnPreview: QtWidgets.QPushButton
        self.btnSave: QtWidgets.QPushButton
        self.buttonBox: QtWidgets.QDialogButtonBox
        self.checkBox: QtWidgets.QCheckBox
        self.comboBox: QtWidgets.QComboBox
        self.espSb: QtWidgets.QDoubleSpinBox
        self.finalSb: QtWidgets.QSpinBox
        self.inicialSb: QtWidgets.QSpinBox
        self.intSp: QtWidgets.QDoubleSpinBox
        self.label: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.label_5: QtWidgets.QLabel
        self.label_6: QtWidgets.QLabel
        self.label_7: QtWidgets.QLabel
        self.label_8: QtWidgets.QLabel
        self.line: QtWidgets.Line
        self.line_2: QtWidgets.Line
        self.line_3: QtWidgets.Line
        self.planoDb: QtWidgets.QDoubleSpinBox
        self.typeLbl: QtWidgets.QLabel

        self.inicialSb.setMaximum(maxprog)
        self.finalSb.setMaximum(maxprog)
        self.inicialSb.valueChanged.connect(self.finalSb.setMinimum)
        self.intSp.valueChanged.connect(self.espSb.setMinimum)
        self.espSb.valueChanged.connect(self.offsetSb.setMaximum)
        self.btnPreview.setFocus()

        self.comboBox.currentIndexChanged.connect(self.updateUi)

        self.types=["H", "V", "T"]

    def getType(self):
        return self.types[self.comboBox.currentIndex()]
    
    def isEstaca(self):
        return self.checkBox.isChecked()

    def updateUi(self):
        if self.getType()=="T":
             self.inicialSb.setEnabled(True)
             self.finalSb.setEnabled(True)
             self.espSb.setMaximum(Config.instance().DIST)
        elif self.getType()=="V":
            self.inicialSb.setEnabled(False)
            self.finalSb.setEnabled(False)
            self.espSb.setMaximum(10000)
        else: #H
            self.inicialSb.setEnabled(False)
            self.finalSb.setEnabled(False)
            self.espSb.setMaximum(10000)
