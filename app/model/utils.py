# -*- coding: utf-8 -*-
import math

from PyQt4.QtCore import qDebug
from qgis._core import QgsFeature
from qgis._core import QgsGeometry
from qgis._core import QgsMapLayerRegistry
from qgis._core import QgsPoint
from qgis._core import QgsVectorLayer
from qgis.core import *
from qgis.gui import *
import sys, os, httplib, json, tempfile, urllib


class Create_vlayer(object):
    '''creation of a virtual layer'''
    def __init__(self,nom,type):
        self.type=type
        self.name = nom
        self.layer = QgsVectorLayer(self.type, self.name , "memory")
        self.pr =self.layer.dataProvider()

    def create_point(self,geometry):
        # add point to the layer
        self.seg = QgsFeature()
        self.seg.setGeometry(QgsGeometry.fromPoint(geometry))
        self.pr.addFeatures([self.seg])
        self.layer.updateExtents()

    @property
    def display_layer(self):
        #end of layer and display layer
        QgsMapLayerRegistry.instance().addMapLayers([self.layer])


def mag(point):
    # magnitude of a vector
    return math.sqrt(point.x()**2 + point.y()**2)


def diff(point2, point1):
    # substraction betwen two vector
    return QgsPoint(point2.x()-point1.x(), point2.y() - point1.y())


def length(point1,point2):
    # with PyQGIS: sqrDist
    return math.sqrt(point1.sqrDist(point2))


def dircos(point):
    cosa = point.x() / mag(point)
    cosb = point.y()/ mag(point)
    return cosa,cosb


def pairs(lista,inicio=0):
    # list pairs iteration
    p = lista.geometry().asPolyline()
    for i in range(inicio+1, len(p)):
        yield p[i-1], p[i]


def decdeg2dms(dd):
    is_positive = dd >= 0
    dd = abs(dd)
    minutes,seconds = divmod(dd*3600,60)
    degrees,minutes = divmod(minutes,60)
    degrees = degrees if is_positive else -degrees
    return (degrees,minutes,seconds)


def calcI(p1,p2,prog1,prog2):
    return ((p2.z()-p1.z())/(prog2-prog1))*100


def azimuth(point1,point2):
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


class ClickTool(QgsMapTool):
    def __init__(self,iface, callback):
        QgsMapTool.__init__(self,iface.mapCanvas())
        self.iface      = iface
        self.callback   = callback
        self.canvas     = iface.mapCanvas()
        self.rpoint=QgsRubberBand(iface.mapCanvas(),QGis.Point )
        self.rline=QgsRubberBand(iface.mapCanvas(),QGis.Line )
        premuto= False
        linea=False
        point0=iface.mapCanvas().getCoordinateTransform().toMapCoordinates(0, 0)
        point1=iface.mapCanvas().getCoordinateTransform().toMapCoordinates(0, 0)



    def canvasReleaseEvent(self,e):
        point = self.canvas.getCoordinateTransform().toMapPoint(e.pos().x(),e.pos().y())
        self.callback(point)
        return None


def pointToWGS84(point):
    p = QgsProject.instance()
    (proj4string,ok) = p.readEntry("SpatialRefSys","ProjectCRSProj4String")
    if not ok:
        return point
    t=QgsCoordinateReferenceSystem()
    t.createFromEpsg(4326)
    f=QgsCoordinateReferenceSystem()
    f.createFromProj4(proj4string)
    transformer = QgsCoordinateTransform(f,t)
    pt = transformer.transform(point)
    return pt


def pointFromWGS84(point):
    p = QgsProject.instance()
    (proj4string,ok) = p.readEntry("SpatialRefSys","ProjectCRSProj4String")
    if not ok:
        return point
    f=QgsCoordinateReferenceSystem()
    f.createFromEpsg(4326)
    t=QgsCoordinateReferenceSystem()
    t.createFromProj4(proj4string)
    transformer = QgsCoordinateTransform(f,t)
    pt = transformer.transform(point)
    return pt


def getElevation(crs,point):
    epsg4326 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
    mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
    reprojectgeographic = QgsCoordinateTransform(mycrs, epsg4326)
    pt = reprojectgeographic.transform(point)
    conn = httplib.HTTPConnection("maps.googleapis.com")
    QgsMessageLog.instance().logMessage(
        "http://maps.googleapis.com/maps/api/elevation/json?locations=" + str(pt[1]) + "," + str(
            pt[0]) + "&sensor=false", "Elevation")

    try:
        conn.request("GET", "/maps/api/elevation/json?locations=" + str(pt[1]) + "," + str(pt[0]) + "&sensor=false")
        response = conn.getresponse()
        jsonresult = response.read()
        elevation = 0.0
        results = json.loads(jsonresult).get('results')
        print results
        if 0 < len(results):
            elevation = float(round(results[0].get('elevation'),4))


    except Exception as e:
        print (e.message)
        qDebug(e.message)
        elevation=0.0

    return elevation