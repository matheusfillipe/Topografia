from __future__ import print_function
from builtins import str
# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic, QtWidgets

import qgis

from ..model.config import Config
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QAbstractItemView
from ..model.utils import addGoogleXYZTiles

from qgis._core import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_conf.ui'))


class TopoConfig(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        # muda configuração padrão para aparecer prompt ao inves de pegar do projeto.
        settings = QSettings()
        settings.setValue("/Projections/defaultBehaviour", "prompt")
        super(TopoConfig, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.setupUi(self)
        self.setup()

    def setup(self):
        self.setWindowTitle(u"Configurações")
        self.txtCRS.setText(str(self.iface.mapCanvas().mapSettings().destinationCrs().description()))
        self.txtCSV.setText(';')
        self.tableCRS.setColumnCount(2)
        self.tableCRS.setColumnWidth(1, 254)
        self.tableCRS.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.conf.tableCRS.setRowCount(300)
        self.tableCRS.setHorizontalHeaderLabels((u"ID", u"CRS"))
        self.tableCRS = self.tableCRS
        self.comboClasse = self.comboClasse
        self.comboMap = self.comboMap
        self.cmpPlanoMin = self.planoMin
        self.cmpPlanoMax = self.planoMax
        self.cmpOnduladoMin = self.onduladoMin
        self.cmpOnduladoMax = self.onduladoMax
        self.cmpMontanhosoMin = self.montanhosoMin
        self.cmpMontanhosoMax = self.montanhosoMax
        self.comboUnits = self.comboUnits


    def changeCRS(self, crs):
        if crs == None:
            crs = 31983
        mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
        # self.iface.mapCanvas().mapRenderer().setCrs( QgsCoordinateReferenceSystem(mycrs, QgsCoordinateReferenceSystem.EpsgCrsId) )
        self.iface.mapCanvas().mapSettings().setDestinationCrs(mycrs)  # set CRS to canvas
        # self.iface.mapCanvas().setMapUnits(QGis.Meters)
        self.iface.mapCanvas().refresh()

    # self.iface.mapCanvas().mapSettings().setProjectionsEnabled(True)

    def new_file(self):
        filename = QtWidgets.QFileDialog.getSaveFileName()
        return filename

    def open_file(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(filter="Project files (*.lzip)")
        return filename

    def error(self, msg):
        msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "AVISO",
                                       u"%s" % msg,
                                       QtWidgets.QMessageBox.NoButton, None)
        msgBox.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
        # msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
        msgBox.exec_()

    def update(self, model, txtcrs):
        self.txtCRS.setText(U"%s" % txtcrs)
        # print model.CSV_DELIMITER
        self.txtCSV.setText(U"%s" % model.CSV_DELIMITER)
        self.comboClasse.setCurrentIndex(model.class_project + 1)
        self.cmpPlanoMin.setValue(model.dataTopo[0])
        self.cmpPlanoMax.setValue(model.dataTopo[1])
        self.cmpOnduladoMin.setValue(model.dataTopo[2])
        self.cmpOnduladoMax.setValue(model.dataTopo[3])
        self.cmpMontanhosoMin.setValue(model.dataTopo[4])
        self.cmpMontanhosoMax.setValue(model.dataTopo[5])
        self.comboMap.setCurrentIndex(model.ordem_mapa.index(model.tipo_mapa) + 1)
        self.comboUnits.setCurrentIndex(model.ordem_units.index(model.UNITS))

    def carregamapa(self, tmap=3):
        from ..model.utils import msgLog

        root = QgsProject.instance().layerTreeRoot()
        urlWithParams = 'type=xyz&url=http://mt1.google.com/vt/lyrs%3Ds%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
        rlayer = QgsRasterLayer(urlWithParams, 'Google Satellite', 'wms')
        if rlayer.isValid():
            QgsProject.instance().addMapLayer(rlayer, False)
            root.addLayer(rlayer)
        else:
            msgLog('Failed to load Satellite layer')


        urlWithParams = 'type=xyz&url=http://mt1.google.com/vt/lyrs%3Dt%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0'
        rlayer = QgsRasterLayer(urlWithParams, 'Google Terrain', 'wms')
        if rlayer.isValid():
            QgsProject.instance().addMapLayer(rlayer, False)
            root.addLayer(rlayer)
        else:
            msgLog('Failed to load Terrain layer')



    def carregacarta(self, model):
        # create Qt widget
        canvas = self.iface.mapCanvas()
        # canvas.setCanvasColor(Qt.black)

        # enable this for smooth rendering
        canvas.enableAntiAliasing(True)

        # not updated US6SP10M files from ENC_ROOT
        source_dir = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select a folder:', '',
                                                                QtWidgets.QFileDialog.ShowDirsOnly)
        if source_dir in [None, '']: return
        # source_dir = "/home/lucas/python_work/TopoGraph"
        canvas_layers = []
        extent = QgsRectangle()
        extent.setMinimal()

        # load vector layers
        registry = QgsMapLayerRegistry.instance()

        try:
            os.mkdir(r"%s/tmp" % (source_dir))
        except:
            pass

        for files in os.listdir(source_dir):

            # load only the shapefiles
            if files.endswith(".dxf") or files.endswith(".shp") or files.endswith(".dgn"):
                vlayer = QgsVectorLayer(source_dir + "/" + files, files, "ogr")

                # add layer to the registry
                # registry.addMapLayer(vlayer)
                # extent.combineExtentWith(vlayer.extent())
                # canvas_layers.append(QgsMapCanvasLayer(vlayer))

                vlayer = QgsVectorLayer(r"%s/tmp/%s.shp" % (source_dir, files), files, "ogr")

                attr = {}
                vlayerUser = vlayer.crs().toProj4()
                for elem in vlayerUser.strip().split('+'):
                    key_value = elem.strip().split('=')
                    if len(key_value) > 1:
                        attr[key_value[0]] = key_value[1]
                    else:
                        attr[key_value[0]] = None
                attr['units'] = Config.UNITS
                string_proj = ''
                for a in attr:
                    if a == '':
                        continue
                    if attr[a] is None:
                        string_proj += '+%s ' % a
                    else:
                        string_proj += '+%s=%s ' % (a, attr[a])
                crs = QgsCoordinateReferenceSystem()
                crs.createFromProj4(string_proj)
                vlayer.setCrs(crs)
                registry.addMapLayer(vlayer)
                extent.combineExtentWith(vlayer.extent())
                canvas_layers.append(QgsMapLayer(vlayer))

                self.format = QgsVectorFileWriter.writeAsVectorFormat(vlayer, r"%s/tmp/%s.shp" % (source_dir, files),
                                                                      "utf-8", None, "ESRI Shapefile")
                print(self.format)
                # set extent to the extent of our layer
                # canvas.setExtent(vlayer.extent())

                # set the map canvas layer set
                # canvas.setLayerSet([QgsMapCanvasLayer(vlayer)])

        canvas.setExtent(extent)
        canvas.setLayerSet(canvas_layers)
