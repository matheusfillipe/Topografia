from qgis.core import *
from qgis.gui import *
from qgis.utils import *

from PyQt4.QtCore import *
import math

class PointTool(QgsMapTool):

    def __init__(self, canvas):

        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas

    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        global rb ,premuto ,point0
        if not premuto:
            premuto=True
            rb=QgsRubberBand(iface.mapCanvas(),QGis.Point )
            rb.setColor ( Qt.red )
            point0 = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
            rb.addPoint(point0)

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        global premuto,point0,point1,linea,rl
        if premuto:
            if not linea:
                rl.setColor ( Qt.red )
                poin1 = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
                rl.addPoint(point0)
                rl.addPoint(point1)
                linea=True
            else:
                if linea:
                    point1 = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
                    rl.reset(QGis.Line)
                    rl.addPoint(point0)
                    rl.addPoint(point1)



    def canvasReleaseEvent(self, event):
        global premuto,linea,rb,rl,point1,point0
        angle = math.atan2(point1.x() - point0.x(), point1.y() - point0.y())
        angle = math.degrees(angle)if angle>0 else (math.degrees(angle) + 180)+180
        premuto=False
        linea=False
        actual_crs = self.canvas.mapRenderer().destinationCrs()
        crsDest = QgsCoordinateReferenceSystem(4326)  # WGS 84 / UTM zone 33N
        xform = QgsCoordinateTransform(actual_crs, crsDest)
        pt1 = xform.transform(point0)
        dbName = os.getenv("HOME")+'/.qgis2/python/plugins/StreetView/page'
        f1 = open(dbName, 'r')
        f2 = open(dbName+'.html', 'w')
        for line in f1:
            line=line.replace('yyyy', str(pt1.x()))
            line=line.replace('xxxx', str(pt1.y()))
            line=line.replace('aaaa', str(int(angle)))
            f2.write(line)
        f1.close()
        f2.close()
        webbrowser.open_new(dbName+'.html')
        #rl.reset()
        #rb.reset()
    def activate(self):
        pass

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True