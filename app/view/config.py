from __future__ import print_function

# -*- coding: utf-8 -*-
import os
from builtins import str

from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import QSettings, Qt
from qgis.PyQt.QtWidgets import QAbstractItemView
from qgis._core import *

from ..model.utils import yesNoDialog
from ..model.config import Config, extractZIP, compactZIP

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../view/ui/Topo_dialog_conf.ui'))


class TopoConfig(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        # muda configuração padrão para aparecer prompt ao inves de pegar do projeto.
        settings = QSettings()
        settings.setValue("/Projections/defaultBehaviour", "prompt")

        self.TopoDialogBase: QtWidgets.QDialog
        self.button_box: QtWidgets.QDialogButtonBox
        self.comboClasse: QtWidgets.QComboBox
        self.comboMap: QtWidgets.QComboBox
        self.comboUnits: QtWidgets.QComboBox
        self.estacas: QtWidgets.QDoubleSpinBox
        self.groupBox: QtWidgets.QGroupBox
        self.groupBox_2: QtWidgets.QGroupBox
        self.label = QtWidgets.QLabel()
        self.label_10: QtWidgets.QLabel
        self.label_11: QtWidgets.QLabel
        self.label_12: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.label_5: QtWidgets.QLabel
        self.label_6: QtWidgets.QLabel
        self.label_7: QtWidgets.QLabel
        self.label_8: QtWidgets.QLabel
        self.label_9: QtWidgets.QLabel
        self.montanhosoMax: QtWidgets.QDoubleSpinBox
        self.montanhosoMin: QtWidgets.QDoubleSpinBox
        self.onduladoMax: QtWidgets.QDoubleSpinBox
        self.onduladoMin: QtWidgets.QDoubleSpinBox
        self.planoMax: QtWidgets.QDoubleSpinBox
        self.planoMin: QtWidgets.QDoubleSpinBox
        self.tableCRS = QtWidgets.QTableWidget()
        self.transversal: QtWidgets.QDoubleSpinBox
        self.txtCRS = QtWidgets.QLineEdit()
        self.txtCSV: QtWidgets.QLineEdit
        self.offsetSpinBox: QtWidgets.QSpinBox
        self.velProj : QtWidgets.QSpinBox


        super(TopoConfig, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() & Qt.WindowContextHelpButtonHint)
        self.setup()
        
        self.unitsList=['m','Km','mm']

        self.dataAssociationWrite = {Config.data[0]: self.units,
                                Config.data[1]: self.txtCSV.text,
                                Config.data[2]: self.estacas.value,
                                Config.data[3]: self.transversal.value,
                                Config.data[4]: self.comboClasse.currentIndex,
                                Config.data[5]: self.txtCRS.text,
                                Config.data[6]: self.planoMin.value,
                                Config.data[7]: self.planoMax.value,
                                Config.data[8]: self.onduladoMin.value,
                                Config.data[9]: self.onduladoMax.value,
                                Config.data[10]: self.montanhosoMin.value,
                                Config.data[11]: self.montanhosoMax.value,
                                Config.data[12]: self.offsetSpinBox.value,
                                Config.data[14]: self.interpol.isChecked,
                                Config.data[15]: self.velProj.value,
                                Config.data[16]: self.emax.value
        }

        self.dataAssociationRead = {Config.data[0]: self.setUnits,
                                 Config.data[1]: self.txtCSV.setText,
                                 Config.data[2]: self.estacas.setValue,
                                 Config.data[3]: self.transversal.setValue,
                                 Config.data[4]: self.comboClasse.setCurrentIndex,
                                 Config.data[5]: self.txtCRS.setText,
                                 Config.data[6]: self.planoMin.setValue,
                                 Config.data[7]: self.planoMax.setValue,
                                 Config.data[8]: self.onduladoMin.setValue,
                                 Config.data[9]: self.onduladoMax.setValue,
                                 Config.data[10]: self.montanhosoMin.setValue,
                                 Config.data[11]: self.montanhosoMax.setValue,
                                 Config.data[12]: self.offsetSpinBox.setValue,
                                 Config.data[14]: self.interpol.setChecked,
                                 Config.data[15]: self.velProj.setValue,
                                 Config.data[16]: self.emax.setValue
                                }

        self.dbBuild: QtWidgets.QPushButton
        self.dbBuild.clicked.connect(self.buildDb)


    def buildDb(self):
        if yesNoDialog(iface=self, message="Tem certeza que deseja reconstruir o banco de dados?"):
            cfg=Config.instance()
            extractZIP(cfg.FILE_PATH)
            con=cfg.create_datatable(cfg.TMP_DIR_PATH + "tmp/data/data.db")
            con.close()
            compactZIP(cfg.FILE_PATH)


    def show(self):
        for d in self.dataAssociationRead:
            cfg=Config.instance()
            try:
                self.dataAssociationRead[d](getattr(cfg, d))
            except:
                pass
        return super(TopoConfig, self).show()

    def setUnits(self, s:str):
        self.comboUnits.setCurrentIndex(self.unitsList.index(s))

    def units(self):
        return self.unitsList[self.comboUnits.currentIndex()]

    def accept(self):
        for d in self.dataAssociationWrite:
            setattr(Config, d, self.dataAssociationWrite[d]())
            Config.instance().store(d, self.dataAssociationWrite[d]())
        x=Config.instance().T_OFFSET
        return super(TopoConfig, self).accept()

    def setup(self):
        self.setWindowTitle(u"Configurações")
        self.txtCRS.setText(str(self.iface.mapCanvas().mapSettings().destinationCrs().description()))
        self.txtCSV.setText(';')
        self.tableCRS.setColumnCount(2)
        self.tableCRS.setColumnWidth(1, 254)
        self.tableCRS.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.conf.tableCRS.setRowCount(300)
        self.tableCRS.setHorizontalHeaderLabels((u"ID", u"CRS"))
        self.tableCRS:QtWidgets.QTableWidget
        self.tableCRS.hide()
        self.txtCRS.hide()
        self.label.hide()
        self.comboMap.hide()

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
        self.planoMin.setValue(model.dataTopo[0])
        self.planoMax.setValue(model.dataTopo[1])
        self.onduladoMin.setValue(model.dataTopo[2])
        self.onduladoMax.setValue(model.dataTopo[3])
        self.montanhosoMin.setValue(model.dataTopo[4])
        self.montanhosoMax.setValue(model.dataTopo[5])
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
        registry = QgsMapLayer.instance()

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
