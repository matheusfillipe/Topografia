from __future__ import print_function
import urllib.error
import urllib.parse
import urllib.request
import tempfile
import json
import http.client
import os
from urllib.request import urlopen
import sys
from qgis.core import QgsRectangle, QgsGeometry, QgsVectorLayer, QgsPoint, QgsFeature, QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsField, QgsFields, QgsMessageLog, QgsWkbTypes
from qgis.PyQt import QtWidgets
from qgis.gui import *
from qgis._core import QgsVectorLayer
from qgis._core import QgsPoint
from qgis._core import QgsProject
from qgis._core import QgsGeometry
from qgis._core import QgsFeature
from qgis.PyQt.QtCore import qDebug
import math
from builtins import object
from builtins import range
from builtins import str

from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QDialog, QLabel
from future import standard_library

from ..model.config import Config

standard_library.install_aliases()
# -*- coding: utf-8 -*-


class Create_vlayer(object):
    '''creation of a virtual layer'''

    def __init__(self, nom, type):
        self.type = type
        self.name = nom
        self.layer = QgsVectorLayer(self.type, self.name, "memory")
        self.pr = self.layer.dataProvider()

    def create_point(self, geometry):
        # add point to the layer
        self.seg = QgsFeature()
        self.seg.setGeometry(QgsGeometry.fromPoint(geometry))
        self.pr.addFeatures([self.seg])
        self.layer.updateExtents()

    @property
    def display_layer(self):
        # end of layer and display layer
        QgsProject.instance().addMapLayers([self.layer])


def mag(point):
    # magnitude of a vector
    return math.sqrt(point.x()**2 + point.y()**2)


def diff(point2, point1):
    # substraction betwen two vector
    return p2QgsPoint(point2.x()-point1.x(), point2.y() - point1.y())


def length(point1, point2):
    # with PyQGIS: sqrDist
    return point1.distance(point2)


def dircos(point):
    Mag = mag(point)
    cosa = 0
    cosb = 0

    if Mag != 0:
        cosa = point.x() / Mag
        cosb = point.y() / Mag

    return cosa, cosb


def getTipo(feat):
    '''
    :param feat: layer feature
    :return: str: Tipo do seguimento de geometria (T para tangente, C para curva cirvular, E para curva Espiral
    Os valores são computados a partir dos fields da layer
    '''

    try:
        s = str(feat["Tipo"])
        if s.startswith("T") or s.startswith("t"):
            r = "T"
        elif s.startswith("C") or s.startswith("c"):
            r = "C"
        elif s.startswith("E") or s.startswith("e") or s.startswith("S") or s.startswith("s"):
            r = "S"
        else:
            r = "T"
    except:
        r = "T"

    return r


def featureToPolyline(f):
    g = f.geometry()
    try:
        lista = g.asPolyline()
    except:
        lista = g.asMultiPolyline()[0]
    return lista


def qgsGeometryToPolyline(g):
    if g:
        try:
            lista = g.asPolyline()
        except:
            lista = g.asMultiPolyline()[0]
    else:
        lista = [QgsPointXY(0, 0), QgsPointXY(0, 10)]

    return lista


def pairs(lista, inicio=0):
    # list pairs iteration
    tipo = getTipo(lista)
    line = featureToPolyline(lista)

    from math import isclose
    start = line[inicio]
    for i in range(inicio+1, len(line)-1):
        if not (isclose(line[i-1].azimuth(line[i]), line[i].azimuth(line[i+1]), rel_tol=.00001) or start.distance(line[i]) < 0.01):
            yield start, line[i], tipo
            start = line[i]
    yield start, line[-1], tipo


def moveLine(layer, id, dest, src=None):
    try:
        geometry = layer.getFeature(id).geometry().asPolyline()
    except:
        geometry = layer.getFeature(id).geometry().asMultiPolyline()[0]

    if not src:
        src = geometry[0]
    dx = dest.x()-src.x()
    dy = dest.y()-src.y()
    g = layer.getFeature(id).geometry()
    g.translate(dx, dy)
    layer.dataProvider().changeGeometryValues({id: g})


def getLastPoint(layer, id):
    try:
        return layer.getFeature(id-1).geometry().asPolyline()[-1]
    except:
        return layer.getFeature(id-1).geometry().asMultiPolyline()[0][-1]


def decdeg2dms(dd):
    is_positive = dd >= 0
    dd = abs(dd)
    minutes, seconds = divmod(dd*3600, 60)
    degrees, minutes = divmod(minutes, 60)
    degrees = degrees if is_positive else -degrees
    return (degrees, minutes, seconds)


def calcI(p1, p2, prog1, prog2):
    return ((p2.z()-p1.z())/(prog2-prog1))*100


def azimuth(point1, point2):
    # interval 0-180° here
    dx = point2.x() - point1.x()
    dy = point2.y() - point1.y()
    try:
        tan = math.atan(dx/dy)*(180/math.pi)
    except:
        tan = 0.0
    if dx > 0 and dy > 0:
        return tan
    elif dx > 0 and dy < 0:
        return 180 + tan

    elif dx < 0 and dy < 0:
        return 180 + tan
    elif dx < 0 and dy > 0:
        return 360 - abs(tan)
    elif dx == 0 and dy > 0:
        return 0
    elif dx > 0 and dy == 0:
        return 90
    elif dx == 0 and dy < 0:
        return 180
    elif dx < 0 and dy == 0:
        return 270


class PointTool(QgsMapTool):
    def __init__(self, iface, callback):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.callback = callback
        self.canvas = iface.mapCanvas()
        self.rpoint = QgsRubberBand(
            iface.mapCanvas(), QgsWkbTypes.PointGeometry)

    def canvasReleaseEvent(self, e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        self.point = point
        self.canvas.unsetMapTool(self)
        self.callback(self.point)
        return None

    def start(self):
        self.canvas.setMapTool(self)


class ClickTool(QgsMapTool):
    def __init__(self, iface, callback):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.callback = callback
        self.canvas = iface.mapCanvas()
        self.rpoint = QgsRubberBand(iface.mapCanvas(), QGis.Point)
        self.rline = QgsRubberBand(iface.mapCanvas(), QGis.Line)
        premuto = False
        linea = False
        point0 = iface.mapCanvas().getCoordinateTransform().toMapCoordinates(0, 0)
        point1 = iface.mapCanvas().getCoordinateTransform().toMapCoordinates(0, 0)

    def canvasReleaseEvent(self, e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(), e.pos().y())
        self.callback(point)
        return None


# Qgis 3.10.0 has a bug where the QgsPoint doesn't accept a QgsPointXY as a constructor
def p2QgsPoint(pt, pt2=None):
    if pt2 is None:
        try:
            if type(pt) is list:
                if len(pt) == 3:
                    return QgsPoint(pt[0], pt[1], pt[2])
                else:
                    return QgsPoint(pt[0], pt[1])
            else:
                return QgsPoint(pt.x(), pt.y())
        except:
            return QgsPoint(pt)
    else:
        return QgsPoint(pt, pt2)


def pointToWGS84(point):
    t = QgsCoordinateReferenceSystem("EPSG:4326")
    f = QgsProject.instance().crs()
    transformer = QgsCoordinateTransform(f, t, QgsProject.instance())
    pt = transformer.transform(point)
    return pt


def pointTo(crs, point):
    t = QgsCoordinateReferenceSystem(crs)
    f = QgsProject.instance().crs()
    transformer = QgsCoordinateTransform(f, t, QgsProject.instance())
    pt = transformer.transform(point)
    return pt


def pointFromWGS84(point):
    p = QgsProject.instance()
    (proj4string, ok) = p.readEntry("SpatialRefSys", "ProjectCRSProj4String")
    if not ok:
        return point
    f = QgsCoordinateReferenceSystem("EPSG:4326")
    t = QgsProject.instance().crs()
    transformer = QgsCoordinateTransform(f, t, p)
    pt = transformer.transform(point)
    return pt


def addGoogleXYZTiles(iface, QSettings):
    sources = []
    sources.append(["connections-xyz", "Google Satellite", "", "", "",
                    "https://mt1.google.com/vt/lyrs=s&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D", "", "19", "0"])
    sources.append(["connections-xyz", "Google Terrain", "", "", "",
                    "https://mt1.google.com/vt/lyrs=t&x=%7Bx%7D&y=%7By%7D&z=%7Bz%7D", "", "19", "0"])

    for source in sources:
        connectionType = source[0]
        connectionName = source[1]
        QSettings().setValue("qgis/%s/%s/authcfg" %
                             (connectionType, connectionName), source[2])
        QSettings().setValue("qgis/%s/%s/password" %
                             (connectionType, connectionName), source[3])
        QSettings().setValue("qgis/%s/%s/referer" %
                             (connectionType, connectionName), source[4])
        QSettings().setValue("qgis/%s/%s/url" %
                             (connectionType, connectionName), source[5])
        QSettings().setValue("qgis/%s/%s/username" %
                             (connectionType, connectionName), source[6])
        QSettings().setValue("qgis/%s/%s/zmax" %
                             (connectionType, connectionName), source[7])
        QSettings().setValue("qgis/%s/%s/zmin" %
                             (connectionType, connectionName), source[8])
    iface.reloadConnections()


def getElevation(crs, point):
    # epsg4326 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
    # mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
    # reprojectgeographic = QgsCoordinateTransform(mycrs, epsg4326, QgsCoordinateTransformContext())
    # pt = reprojectgeographic.transform(QgsPointXY(point))
    # conn = http.client.HTTPConnection("maps.googleapis.com")
    # QgsMessageLog.instance().logMessage(
    # #    "http://maps.googleapis.com/maps/api/elevation/json?locations=" + str(pt[1]) + "," + str(
    #  #       pt[0]) + "&sensor=false", "Elevation")

    # try:
    #     conn.request("GET", "/maps/api/elevation/json?locations=" + str(pt[1]) + "," + str(pt[0]) + "&sensor=false")
    #     response = conn.getresponse()
    #     jsonresult = response.read()
    #     elevation = 0.0
    #     results = json.loads(jsonresult).get('results')
    #     # fix_print_with_import
    #     print(results)
    #     if 0 < len(results):
    #         elevation = float(round(results[0].get('elevation'),4))

    # except Exception as e:
    #     msgLog(e.message)
    #     qDebug(e.message)
    #     elevation=0.0

    # return elevation
    return 0


def layerFields():
    fields = QgsFields()
    # C, T, E (Circular, tangente, Espiral ... startswith)
    fields.append(QgsField("Tipo", QVariant.String))
    fields.append(QgsField("Descricao", QVariant.String))
    fields.append(QgsField("Raio", QVariant.Double))
    fields.append(QgsField("Angulo de Deflexao (Delta)", QVariant.Double))
    fields.append(QgsField("Tangente Externa (T)", QVariant.Double))
    fields.append(QgsField("Desenvolvimento (D)", QVariant.Double))
    return fields


def msgLog(*msg):
    QgsMessageLog.logMessage(" ".join(str(p) for p in msg), tag="GeoRoad", level=0)


def interpolList(l: list, i):
    length = len(l)
    if length % 2 != 0:
        return l[int(length/2)][i]
    else:
        return (l[int(length/2)][i]+l[int(length/2)-1][i])/2


def internet_on():
    try:
        response = urlopen('https://www.google.com/', timeout=3)
        return True
    except:
        return False


# TODO allow user to configure precision
precision = 4
longPrecision = 8


def roundFloat(f: float):
    return round(f, precision)


def roundFloatShort(f):
    return round(f, 1)


def shortFloat2String(f):
    return str(round(f, 2))


def formatValue(value):
    try:
        if int(float(value)) == float(value):  # value is a int
            return str(int(value))
        return str(roundFloat(float(value)))
    except:
        return str(value)


def roundFloat2str(f: float):
    return str(round(float(f), precision))


def longRoundFloat(f: float):
    return round(f, longPrecision)


def longRoundFloat2str(f: float):
    return str(round(f, longPrecision))


def roundUpFloat2str(f: float):
    return str(round(int(f/Config.instance().DIST+1), 0))


def prog2estacaStr(i: float):
    dist = Config.instance().DIST
    if i % dist != 0:
        return str(int(i/dist))+"+"+str(round(i % dist, 2))
    else:
        return str(int(i/dist))


def fastProg2EstacaStr(i, dist):
    if i % dist != 0:
        return str(int(i/dist))+"+"+str(round(i % Config.instance().DIST, 2))
    else:
        return str(int(i/dist))


def estaca2progFloat(s: str):
    dist = Config.instance().DIST
    if '+' in s:
        i = int(s.split("+")[0])
        f = float(s.split("+")[1])
        return i*dist+f
    else:
        return int(s)*dist


def fastEstaca2progFloat(s: str, dist):
    dist = Config.instance().DIST
    if '+' in s:
        i = int(s.split("+")[0])
        f = float(s.split("+")[1])
        return i*dist+f
    else:
        return int(s)*dist


class imgDialog(QDialog):
    def __init__(self, imagepath, title="Image", parent=None):
        super(imgDialog, self).__init__(parent)
        self.title = title
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.imagepath = imagepath
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create widget
        label = QLabel(self)
        pixmap = QPixmap(self.imagepath)
        label.setPixmap(pixmap)
        self.resize(pixmap.width(), pixmap.height())


def messageDialog(iface=None, title="Concluído", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
  #  msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Ok


def yesNoDialog(iface=None, title="Atenção", info="", message=""):
    msgBox = QtWidgets.QMessageBox(iface)
    msgBox.setIcon(QtWidgets.QMessageBox.Question)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.setInformativeText(info)
    msgBox.setStandardButtons(
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
  #  msgBox.show()
    return msgBox.exec_() == QtWidgets.QMessageBox.Yes


class RasterInterpolator():
    def __init__(self):
        self.BLOCK = None
        self.LAYER = None

    def getBlockRecAndItemFromPointInRaster(self, layer, p):
        # QgsCoordinateTransform(QgsProject.instance().crs(),layer.crs(),QgsProject.instance()).transform(p)
        pt = p
        dp = layer.dataProvider()
        finalExtent = dp.extent()

        # Calculate the row / column where the point falls
        xres = layer.rasterUnitsPerPixelX()
        yres = layer.rasterUnitsPerPixelY()

        from math import floor
        col = abs(floor((pt.x() - finalExtent.xMinimum()) / xres))
        row = abs(floor((finalExtent.yMaximum() - pt.y()) / yres))

        xMin = finalExtent.xMinimum() + col * xres
        xMax = xMin + xres
        yMax = finalExtent.yMaximum() - row * yres
        yMin = yMax - yres
        pixelExtent = QgsRectangle(xMin, yMin, xMax, yMax)
        # 1 is referring to band 1
        if not(self.LAYER is None or self.BLOCK is None) and layer == self.LAYER:
            block = self.BLOCK
        else:
            block = dp.block(1, finalExtent, layer.width(), layer.height())
            self.BLOCK = block
            self.LAYER = layer

        del dp

        if pixelExtent.contains(pt):
            return block, pixelExtent, row, col
        else:
            return False, False, False, False

    def rectCell(self, layer, row, col):
        dp = layer.dataProvider()
        finalExtent = dp.extent()

        # Calculate the row / column where the point falls
        xres = layer.rasterUnitsPerPixelX()
        yres = layer.rasterUnitsPerPixelY()

        xMin = finalExtent.xMinimum() + col * xres
        xMax = xMin + xres
        yMax = finalExtent.yMaximum() - row * yres
        yMin = yMax - yres
        del dp
        return QgsRectangle(xMin, yMin, xMax, yMax)

    def cotaFromTiff(self, layer, p, interpolate=True):
        p = QgsCoordinateTransform(QgsProject.instance().crs(
        ), layer.crs(), QgsProject.instance()).transform(p)
        if interpolate:
            b, rec, row, col = self.getBlockRecAndItemFromPointInRaster(
                layer, p)
            if not b:
                return 0

            # matrix dos 9 pixels
            matx = [[[None, None, None], [None, None, None], [None, None, None]],
                    [[None, None, None], [None, None, None], [None, None, None]]]

            from itertools import product
            for i, j in product([-1, 0, 1], [-1, 0, 1]):
                matx[0][i + 1][j + 1] = b.value(row + i, col + j)  # elevações
                # distancias
                matx[1][i + 1][j +
                               1] = self.rectCell(layer, row + i, col + j).center().distance(p)
                if row < 0 or col < 0 or row >= layer.height() or col >= layer.width():
                    return 0

            V = [matx[0][i][j]
                 for i, j in product([0, 1, 2], [0, 1, 2])]  # elevações
            L = [matx[1][i][j]
                 for i, j in product([0, 1, 2], [0, 1, 2])]  # Distancias

            # tolerância de 1 diagonal inteira
            max_dist = (layer.rasterUnitsPerPixelX() ** 2 +
                        layer.rasterUnitsPerPixelY() ** 2) ** (1 / 2)
            # pesos
            I = [(max_dist - l) / max_dist if l < max_dist else 0 for l in L]
            # média
            del matx
            del b
            del rec

            return sum(v * i for v, i in zip(V, I)) / sum(I)

        else:
            v = layer.dataProvider().sample(p, 1)
            try:
                if v[1]:
                    return v[0]
                else:
                    return 0
            except:
                return 0
    #
    #        if layer.extent().contains(p) and v[1]:
    #            return v[0]
    #        else:
    #            return 0
