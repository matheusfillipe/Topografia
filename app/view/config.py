# -*- coding: utf-8 -*-
import os
from PyQt4 import Qt

from PyQt4 import QtGui, uic

import qgis

import shutil
from ..model.config import extractZIP, Config, compactZIP
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QAbstractItemView

from qgis._core import QgsCoordinateReferenceSystem,QgsCoordinateTransform
from qgis._core import QgsMapLayerRegistry
from qgis._core import QgsRectangle
from qgis._core import QgsVectorFileWriter
from qgis._core import QgsVectorLayer
from qgis._core import QGis
from qgis._gui import QgsMapCanvasLayer

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_conf.ui'))

class TopoConfig(QtGui.QDialog, FORM_CLASS):
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
        self.txtCRS.setText(str(self.iface.mapCanvas().mapRenderer().destinationCrs().description()))
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

    def changeCRS(self,crs):
        if crs == None:
            crs = 31983
        mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
        # self.iface.mapCanvas().mapRenderer().setCrs( QgsCoordinateReferenceSystem(mycrs, QgsCoordinateReferenceSystem.EpsgCrsId) )
        self.iface.mapCanvas().mapRenderer().setDestinationCrs(mycrs)  # set CRS to canvas
        self.iface.mapCanvas().setMapUnits(QGis.Meters)
        self.iface.mapCanvas().refresh()
        self.iface.mapCanvas().mapRenderer().setProjectionsEnabled(True)

    def new_file(self):
        filename = QtGui.QFileDialog.getSaveFileName()
        return filename

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName(filter="Project files (*.lzip)")
        return filename

    def error(self, msg):
        msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "AVISO",
                                   u"%s" % msg,
                                   QtGui.QMessageBox.NoButton, None)
        msgBox.addButton("OK", QtGui.QMessageBox.AcceptRole)
        # msgBox.addButton("&Continue", QtGui.QMessageBox.RejectRole)
        msgBox.exec_()

    def update(self, model,txtcrs):
        self.txtCRS.setText(U"%s" % txtcrs)
        #print model.CSV_DELIMITER
        self.txtCSV.setText(U"%s" % model.CSV_DELIMITER)
        self.comboClasse.setCurrentIndex(model.class_project+1)
        self.cmpPlanoMin.setValue(model.dataTopo[0])
        self.cmpPlanoMax.setValue(model.dataTopo[1])
        self.cmpOnduladoMin.setValue(model.dataTopo[2])
        self.cmpOnduladoMax.setValue(model.dataTopo[3])
        self.cmpMontanhosoMin.setValue(model.dataTopo[4])
        self.cmpMontanhosoMax.setValue(model.dataTopo[5])
        self.comboMap.setCurrentIndex(model.ordem_mapa.index(model.tipo_mapa) + 1)
        self.comboUnits.setCurrentIndex(model.ordem_units.index(model.UNITS))

    def carregamapa(self, tmap=3):
        openLyrs = qgis.utils.plugins['openlayers_plugin']
        # g = geosearchdialog.GeoSearchDialog(self.iface)
        '''g.SearchRoute([])
        d = GoogleMapsApi.directions.Directions()
        origin = "Boston, MA"
        dest = "2517 Main Rd, Dedham, ME 04429"
        route = d.GetDirections(origin, dest, mode="driving", waypoints=None, avoid=None, units="imperial")'''
        layerType = openLyrs._olLayerTypeRegistry.getById(tmap)
        openLyrs.addLayer(layerType)
        #QgsCoordinateReferenceSystem.createFromProj4('+proj=tmerc', u'lat_0=0', u'lon_0=126', u'k=1', u'x_0=42500000', u'y_0=0', u'ellps=krass', u'towgs84=24.47,-130.89,-81.56,-0,-0,0.13,-0.22', u'units=m', u'no_defs')
        # mycrs = QgsCoordinateReferenceSystem(31983)
        # self.iface.mapCanvas().mapRenderer().setCrs( QgsCoordinateReferenceSystem(31983, QgsCoordinateReferenceSystem.EpsgCrsId) )

        # self.iface.mapCanvas().mapRenderer().setDestinationCrs(mycrs)# set CRS to canvas
        # self.iface.mapCanvas().setMapUnits(0)
        # self.iface.mapCanvas().refresh()
        # g.CreateVectorLayerGeoSearch_Route(route)
        '''filename = QtGui.QFileDialog.getOpenFileName()
        fileInfo = QFileInfo(filename)
        path = fileInfo.filePath()
        baseName = fileInfo.baseName()

        layer = QgsRasterLayer(path, baseName)
        QgsMapLayerRegistry.instance().addMapLayer(layer)'''

    def carregacarta(self,model):
        # create Qt widget
        canvas = self.iface.mapCanvas()
        #canvas.setCanvasColor(Qt.black)

        # enable this for smooth rendering
        canvas.enableAntiAliasing(True)

        # not updated US6SP10M files from ENC_ROOT
        source_dir = QtGui.QFileDialog.getExistingDirectory(None, 'Select a folder:', '',
                                                            QtGui.QFileDialog.ShowDirsOnly)
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
                #registry.addMapLayer(vlayer)
                #extent.combineExtentWith(vlayer.extent())
                #canvas_layers.append(QgsMapCanvasLayer(vlayer))

                writer = QgsVectorFileWriter.writeAsVectorFormat(vlayer, r"%s/tmp/%s.shp"%(source_dir,files), "utf-8",
                                                                  None, "ESRI Shapefile")

                vlayer = QgsVectorLayer(r"%s/tmp/%s.shp"%(source_dir,files), files, "ogr")

                
                attr={}
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
                        string_proj += '+%s '%a
                    else:
                        string_proj += '+%s=%s '%(a, attr[a])
                crs = QgsCoordinateReferenceSystem()
                crs.createFromProj4(string_proj)
                vlayer.setCrs(crs)
                registry.addMapLayer(vlayer)
                extent.combineExtentWith(vlayer.extent())
                canvas_layers.append(QgsMapCanvasLayer(vlayer))

                
                print writer
                # set extent to the extent of our layer
                # canvas.setExtent(vlayer.extent())

                # set the map canvas layer set
                # canvas.setLayerSet([QgsMapCanvasLayer(vlayer)])

        canvas.setExtent(extent)
        canvas.setLayerSet(canvas_layers)



