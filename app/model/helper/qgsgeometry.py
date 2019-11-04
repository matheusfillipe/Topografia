from copy import deepcopy

from ..utils import *
import numpy as np
from osgeo import gdal
from qgis.core import QgsRectangle, QgsGeometry, QgsVectorLayer, QgsPoint, QgsFeature, QgsPointXY, QgsCircularString

polyline=qgsGeometryToPolyline

def wasInitialized(layer : QgsVectorLayer):
    return sum([1 for f in layer.getFeatures()]) > 0

def refreshCanvas(ifac, layer:QgsVectorLayer = None):
    if layer and ifac.mapCanvas().isCachingEnabled():
        layer.triggerRepaint()
    ifac.mapCanvas().refresh()

def tangentFeaturesFromPointList(layer: QgsVectorLayer, list:list):
    if len(list)>=2:
            anterior=list[0]
            for p in list[1:]:
                feat = QgsFeature(layer.fields())
                feat.setAttribute('Tipo', 'T')
                feat.setGeometry(QgsGeometry.fromPolyline([anterior,p]))
                layer.dataProvider().addFeatures([feat])
                layer.updateExtents()
                anterior=p
            

def perp( a ) :
    b = np.empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return 
def seg_intersect(a1,a2, b1,b2) :
    a1=np.array([a1.x(), a1.y()])
    a2=np.array([a2.x(), a2.y()])
    b1=np.array([b1.x(), b1.y()])
    b2=np.array([b2.x(), b2.y()])
    da = a2-a1
    db = b2-b1
    dp = a1-b1
    dap = perp(da)
    denom = np.dot( dap, db)
    num = np.dot( dap, dp )
    pi=(num / denom.astype(float))*db + b1
    return p2QgsPoint(pi[0], pi[1])


def getTangentesGeometry(layer, i, j=0):
    layer: QgsVectorLayer
    G=[f.geometry() for f in layer.getFeatures()]
    if j==0:
        if i >len(G)-1:
            G=[G[-1], None]
        elif i==0:
            G=[None, G[0]]
        else:
            G=[G[i-1],G[i]]
    else:
        l1:QgsGeometry
        l2:QgsGeometry
        l1=G[i]
        l2=G[j]
        g1=qgsGeometryToPolyline(l1)
        g2=qgsGeometryToPolyline(l2)
        pi=p2QgsPoint(seg_intersect(g1[0],g1[-1],g2[0],g2[-1]))
        G=[QgsGeometry.fromPolyline([p2QgsPoint(g1[0]),pi]), QgsGeometry.fromPolyline([pi,p2QgsPoint(g2[-1])])]

    return G

def deflection(layer2, i):
    line1, line2=getTangentesGeometry(layer2,i)
    a1, a2 = [azimuth(qgsGeometryToPolyline(l)[0], qgsGeometryToPolyline(l)[-1]) for l in [line1, line2]]
    a=a2-a1
    if abs(a)>180.0:
        a=a/abs(a)*abs(180-a)
    return a

def azi(p1,p2=None):
    if not p2:
        return azimuth(p1[-2], (p1[-1]))
    return azimuth(p1, p2)

def featureCount(layer):
    return sum([1 for f in layer.getFeatures()])

def featuresList(layer):
    return [f for f in layer.getFeatures()]

def cleanLayer(layer, i=0):
    F=[]

    if i==0:
        F=[f.id() for f in layer.getFeatures]
    else:
        F=[f.id() for f in featuresList(layer)[-i:]]
    layer.dataProvider().deleteFeatures(F)

def geolengh(geom):
    s=0
    L=qgsGeometryToPolyline(geom)[1:]
    p0=L[0]
    for pt in L:
        s+=p0.distance(pt)
        p0=pt

def contains(rect, geom):
    for pt in qgsGeometryToPolyline(geom):
        if not rect.contains(pt):
            return False
    return True

def splitFeatures(f1, f2):
    '''

    :param f1: feature que define o corte
    :param f2: trimmed feature
    :return:geometry
    '''
    g1 = QgsGeometry(f1.geometry())
    g2 = QgsGeometry(f2.geometry())
    gg = g2.splitGeometry(qgsGeometryToPolyline(g1), False)
    gg=gg[1][0]
    return g2 if contains(g1.boundingBox(), gg) else gg

def splitGeometry(g1, g2):
    '''

    :param g1: defining line and rectangle
    :param g2:line to split
    :return: geometry
    '''

    gg = g2.splitGeometry(qgsGeometryToPolyline(g1), False)[1][0]
    return g2 if contains(g1.boundingBox(), gg) else gg


def createGeometry(geom):
    return QgsGeometry.fromWkt(geom.asWkt())


def unifyGeometry(g1, g2):
    PL = polyline(g1) + polyline(g2)
    pant = PL[0]
    L = [pant]
    for p in PL[1:]:
        if not (p.x() == pant.x() and p.y() == pant.y()):
            L.append(p)
        pant = p

    return QgsGeometry.fromPolylineXY(L)

def clotX(theta):
    return 1-theta**2/10+theta**4/216

def clotY(theta):
    return theta/3-theta**3/42

def lastAzimuth(geo):
    pol=qgsGeometryToPolyline(geo)
    return azimuth(pol[-2],pol[-1])

def xrange(n):
     for i in range(int(n)):
         yield i
     yield n

def polyCircle(layer, data, index, layer2, i):
    pass

def polyTransCircle(layer, data, index, layer2, i, ic):

    LsMax=data["R"]*abs(data["D"])*np.pi/180
    LsMin=0

    fcount=featureCount(layer)
    if fcount>0:
        l1, l2=getTangentesGeometry(layer2, ic, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
        data["Disable"].append("C")

    else:
        l1, l2=getTangentesGeometry(layer2, ic, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
        if l1 is None:
            l1=QgsGeometry(l2)
            dd=diff(qgsGeometryToPolyline(l2)[0], qgsGeometryToPolyline(l2)[-1])
            l2.translate(dd.x(), dd.y())
        elif l2 is None:
            l2=QgsGeometry(l1)
            dd=diff(qgsGeometryToPolyline(l1)[-1], qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())

    startAngle=azi(qgsGeometryToPolyline(l1))
    angle=90-(data["D"]+startAngle)
    angle=angle if angle>0 else 360+angle
    angle=angle if angle<360 else angle-360
    p1=p2QgsPoint(PI)
    p2=p2QgsPoint(data["L"]*np.cos(np.deg2rad(angle))+p1.x(), data["L"]*np.sin(np.deg2rad(angle))+p1.y())
    line=QgsGeometry.fromPolyline([p1,p2])

    a1=azi(polyline(l1))
    a2=azi(polyline(l2))
    msgLog("a1: "+str(a1)+"   "+"a2: "+str(a2))


    data["C"] = True
    corda = 2 * data["R"] * np.sin(np.deg2rad(abs(data["D"]) / 2))


    p1 = p2QgsPoint(l1.interpolate(l1.length() - data["T"]).asPoint())
    p2 = p2QgsPoint(l2.interpolate(data["T"]).asPoint())
    PI = p2QgsPoint(PI)

    p1=p2QgsPoint(p1)
    p2=p2QgsPoint(p2)

    feat1 = QgsFeature(layerFields())
    feat2 = QgsFeature(layerFields())
    feat3 = QgsFeature(layerFields())
    feat1.setAttributes(['E',"",data["R"],data["D"],data["T"],data["L"]])
    feat2.setAttributes(['C',"",data["R"],data["D"],data["T"],data["L"]])
    feat3.setAttributes(['E',"",data["R"],data["D"],data["T"],data["L"]])

  #  if ((a2 - a1 >= 0 and (a1 <= 90 or a1 >= 270)) or (a2 - a1 <= 0 and (a1 >= 90 or a1 <= 270))) and not (
   #         (abs(a1 - a2) > 180 or (a1 < 90 and a2 > 90) or (a1 < 90, a2 < 90)) and not (a2 - a1) < 0):

    pointsT1 = [p2QgsPoint(clotX(L ** 2 / (2 * data["R"] * data["L"])) * L, clotY(L ** 2 / (2 * data["R"] * data["L"])) * L)
        for L in xrange(data["L"])]
    pointsT2 = list(reversed([p2QgsPoint(clotX(L ** 2 / (2 * data["R"] * data["L"])) * L, 1000 - clotY(L ** 2 / (2 * data["R"] * data["L"])) * L)
                              for L in xrange(data["L"])]))

    IpointsT1 = [p2QgsPoint(clotX(L ** 2 / (2 * data["R"] * data["L"])) * L, 1000 - clotY(L ** 2 / (2 * data["R"] * data["L"])) * L)
                for L in xrange(data["L"])]
    IpointsT2 = list(reversed([p2QgsPoint(clotX(L ** 2 / (2 * data["R"] * data["L"])) * L, clotY(L ** 2 / (2 * data["R"] * data["L"])) * L)
         for L in xrange(data["L"])]))

    g1=QgsGeometry.fromPolyline(pointsT1)
    dd = diff(p1, pointsT1[0])
    g1.translate(dd.x(), dd.y())
    g1.rotate(polyline(l1)[0].azimuth(polyline(l1)[-1])-90,polyline(g1)[0])
    g2=QgsGeometry.fromPolyline(pointsT2)
    dd = diff(p2, pointsT2[-1])
    g2.translate(dd.x(), dd.y())
    g2.rotate(polyline(l2)[0].azimuth(polyline(l2)[-1])+90,polyline(g2)[-1])

    Ig1 = QgsGeometry.fromPolyline(IpointsT1)
    dd = diff(p1, IpointsT1[0])
    Ig1.translate(dd.x(), dd.y())
    Ig1.rotate(polyline(l1)[0].azimuth(polyline(l1)[-1]) - 90, polyline(Ig1)[0])
    Ig2 = QgsGeometry.fromPolyline(IpointsT2)
    dd = diff(p2, IpointsT2[-1])
    Ig2.translate(dd.x(), dd.y())
    Ig2.rotate(polyline(l2)[0].azimuth(polyline(l2)[-1]) + 90, polyline(Ig2)[-1])

    g1, g2 = [g1, g2] if polyline(g1)[-1].distance(polyline(g2)[0]) \
                         <= polyline(Ig1)[-1].distance(polyline(Ig2)[0]) else [Ig1, Ig2]

    feat1.setGeometry(g1)
    feat3.setGeometry(g2)

    p = p2QgsPoint((p1.x() + p2.x()) / 2, (p2.y() + p1.y()) / 2)
    p1=p2QgsPoint(polyline(g1)[-1])
    p2=p2QgsPoint(polyline(g2)[0])
    tmp_line=QgsGeometry.fromPolyline([p2QgsPoint(PI),p])
    theta=data["L"]/(2*data["R"])
    ys=clotY(theta)*data["L"]
    p=ys-data["R"]*(1-np.cos(theta))
    E = abs((data["R"]+p)/np.cos(np.deg2rad((data["D"]+2*np.rad2deg(theta))/2))-data["R"])
    msgLog("E="+str(E))
    p=p2QgsPoint(tmp_line.interpolate(E).asPoint())
    circularRing = QgsCircularString()
    circularRing.setPoints([
        p1,
        p,
        p2
        ]
    )
    feat2.setGeometry(circularRing)
    layer.dataProvider().addFeatures([feat1, feat2, feat3])

    return data

def circleArc(layer, data, index, layer2, i, ic):
    fcount=featureCount(layer)
    if fcount>0:
        l1, l2=getTangentesGeometry(layer2, ic, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
    else:
        l1, l2=getTangentesGeometry(layer2, ic, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
        if l1 is None:
            l1=QgsGeometry(l2)
            dd=diff(qgsGeometryToPolyline(l2)[0], qgsGeometryToPolyline(l2)[-1])
            l2.translate(dd.x(), dd.y())
        elif l2 is None:
            l2=QgsGeometry(l1)
            dd=diff(qgsGeometryToPolyline(l1)[-1], qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())

    pl=qgsGeometryToPolyline(l1)
    startAngle=azi(pl)
    angle=90-(data["D"]+startAngle)
    angle=angle if angle>0 else 360+angle
    angle=angle if angle<360 else angle-360
    angleInternal=180-d
    p1=p2QgsPoint(PI)
    corda=2*data["R"]*np.sin(np.deg2rad(angleInternal/2))
    p2=p2QgsPoint(corda*np.cos(np.deg2rad(angle))+p1.x(), corda*np.sin(np.deg2rad(angle))+p1.y())

    T=None
    E=None
    p=None
    arc=None



    if index=="R":
         if data["C"]:
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            data["T"]=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)
         else:
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            dd=diff(l2.interpolate(T).asPoint(), qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], QgsPointXY(qgsGeometryToPolyline(l2)[0]))
            l2.extendLine(0, 500000)
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(qgsGeometryToPolyline(l2)[0])

    elif index=="L":
         if data["C"]:
            if data["L"] > np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d):
                data["D"]=d/abs(d)*abs(abs(d)*data["L"]/(np.deg2rad(abs(d))*data["R"]))
            if data["L"]>np.deg2rad(abs(d))*data["R"]:
                data["R"]=data["L"]/(np.deg2rad(abs(d)))
                corda=2*data["R"]*np.sin(np.deg2rad(abs(d)/2))
                data["T"]=abs(corda/(2*np.tan(np.deg2rad((abs(d))/2))))
                p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
                p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
                PI=p2QgsPoint(PI)
         else:
            data["R"]=data["L"]/(np.deg2rad(abs(data["D"])))
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad(abs(data["D"])/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            dd=diff(l2.interpolate(T).asPoint(), qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], QgsPointXY(qgsGeometryToPolyline(l2)[0]))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(qgsGeometryToPolyline(l2)[0])


    elif index=="T":
        if data["C"]:
            corda=data["T"]*abs(2*np.tan(np.deg2rad((d)/2)))
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            data["R"]=corda/(2*np.sin(np.deg2rad(angleInternal/2)))
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)
            T=data["T"]
        else:
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            dd=diff(l2.interpolate(T).asPoint(), qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], QgsPointXY(qgsGeometryToPolyline(l2)[0]))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(qgsGeometryToPolyline(l2)[0])


    elif index=="D":
        if data["C"]:
            T=data["T"]
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)
            E=abs(T*np.tan(np.deg2rad(d/4)))
            l2=QgsGeometry(l1)
            dd=diff(PI, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(abs((abs(d)-180)/d*data["D"]+180-abs(d))*d/abs(d)+d, qgsGeometryToPolyline(l2)[0])
            p=p2QgsPoint((p1.x()+p2.x())/2, (p2.y()+p1.y())/2)
            tmp_line=QgsGeometry.fromPolyline([p2QgsPoint(PI),p])
            p=p2QgsPoint(tmp_line.interpolate(E).asPoint())
            arc=QgsCircularString()
            arc.setPoints([p1, p, p2])
            l3=QgsGeometry(l2)
            dd=diff(qgsGeometryToPolyline(l3)[-1], qgsGeometryToPolyline(l3)[0])
            l3.translate(dd.x(), dd.y())
            l3.rotate(-90*d/abs(d), qgsGeometryToPolyline(l3)[0])
            l2=unifyGeometry(l2,l3)
            arc=QgsCircularString()
            arc.setPoints([p1,p,p2])
            arc=splitGeometry(l2, createGeometry(arc))

        else:
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            PI=p2QgsPoint(l2.interpolate(T).asPoint())
            dd=diff(PI, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], qgsGeometryToPolyline(l2)[0])
            p2=p2QgsPoint(l2.interpolate(T).asPoint())

    elif index=="C":
        if data["C"]:
            data["D"]=d
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            data["T"]=abs(corda/(2*np.tan(np.deg2rad((d)/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)
        else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)

    elif index=="S":
            data["C"]=True
           # data["D"]=d
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            #data["T"]=abs(corda/(2*np.tan(np.deg2rad((d)/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)

    if (data["T"]>l1.length() or data["T"]>l2.length()) and data["C"]:
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            data["T"]=abs(corda/(2*np.tan(np.deg2rad((d)/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(PI)

    T = data["T"] if T is None else T
    E = abs(T*np.tan(np.deg2rad(data["D"]/4))) if E is None else E

    p=p2QgsPoint((p1.x()+p2.x())/2, (p2.y()+p1.y())/2)
    #msgLog("p: " + str(p.x()) +"," +str(p.y()))
    #msgLog("PI: " + str(PI.x()) +"," +str(PI.y()))
    tmp_line=QgsGeometry.fromPolyline([p2QgsPoint(PI),p])
    p=p2QgsPoint(tmp_line.interpolate(E).asPoint())

    feat = QgsFeature(layerFields())
    feat.setAttributes(['C',"",data["R"],data["D"],data["T"],data["L"]])
    # Create a QgsCircularStringV2
    circularRing = QgsCircularString()
    # Set first point, intermediate point for curvature and end point
    circularRing.setPoints([
        p1,
        p,
        p2]
    )
#    data["R"]=QgsGeometryUtils.circleCenterRadius(p1,p,p2)[0]
    circularRing=arc if arc else circularRing
    feat.setGeometry(circularRing)
    f2=QgsFeature(layer.fields())
    f2.setGeometry(l2)
    layer.dataProvider().addFeatures([feat])

    return data




def inSpiral(layer, data, index, layer2, i):
    line1, line2=getTangentesGeometry(layer2,i)
    angle=deflection(layer2,i)
    PI=qgsGeometryToPolyline(line1)[-1]
    if data["T"]>data["L"]:
        data["T"]=data["L"]

    if index=="R":
        pass
    elif index=="L":
        pass
    elif index=="T":
        pass
    elif index=="D":
        pass
    elif index=="C":
        pass
    elif index=="S":
        pass

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'S')
#    feat.setGeometry(QgsGeometry.)
    layer.dataProvider().addFeatures([feat])
    return data


def outSpiral(layer, data, index, layer2, i):
    line1, line2=getTangentesGeometry(layer2,i)
    angle=deflection(layer2,i)
    PI=qgsGeometryToPolyline(line1)[-1]
    if data["T"]>data["L"]:
        data["T"]=data["L"]

    if index=="R":
        pass
    elif index=="L":
        pass
    elif index=="T":
        pass
    elif index=="D":
        pass
    elif index=="C":
        pass
    elif index=="S":
        pass

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'S')
#    feat.setGeometry(QgsGeometry.)
    layer.dataProvider().addFeatures([feat])
    return data


def tangent(layer, data, index, layer2, i):
    fcount=featureCount(layer)
    if fcount>0:
        fant=[f for f in layer.getFeatures()][fcount-1]
        l1=fant.geometry()
        l2=QgsGeometry(l1)
        dd=diff(qgsGeometryToPolyline(fant.geometry())[-1],qgsGeometryToPolyline(fant.geometry())[0])
        l2.translate(dd.x(),dd.y())
        PI=qgsGeometryToPolyline(fant.geometry())[-1]
        d=0
        data["Disable"].append("C")

    else:
        l1, l2=getTangentesGeometry(layer2, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
        if l1 is None:
            l1=QgsGeometry(l2)
            dd=diff(qgsGeometryToPolyline(l2)[0], qgsGeometryToPolyline(l2)[-1])
            l2.translate(dd.x(), dd.y())
        elif l2 is None:
            l2=QgsGeometry(l1)
            dd=diff(qgsGeometryToPolyline(l1)[-1], qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())

    startAngle=azi(qgsGeometryToPolyline(l1))
    angle=90-(data["D"]+startAngle)
    angle=angle if angle>0 else 360+angle
    angle=angle if angle<360 else angle-360
    p1=p2QgsPoint(PI)
    p2=p2QgsPoint(data["L"]*np.cos(np.deg2rad(angle))+p1.x(), data["L"]*np.sin(np.deg2rad(angle))+p1.y())
    line=QgsGeometry.fromPolyline([p1,p2])

    if data["T"]>l1.length():
        data["T"]=l1.length

    if index=="R":
        pass

    elif index=="L":
         if data["C"]:
            Lmax=np.sqrt(l1.length()**2+l2.length()**2-2*l1.length()*l2.length()*np.cos(np.deg2rad(360-d)))
            if data["L"]>Lmax:
                data["L"]=Lmax
            data["T"]=abs(data["L"]/(2*np.tan(np.deg2rad((d)/2))))
            data["D"]=d-90
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
         else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="T":
        if data["C"]:
            data["L"]=abs(data["T"]*2*np.tan(np.deg2rad((d)/2)))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
        else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="D":
        if data["C"]:
            data["D"]=0
            data["T"]=0
            data["C"]=False
            p2=qgsGeometryToPolyline(line)[-1]
        else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="C":
        if data["C"]:
            Lmax=np.sqrt(l1.length()**2+l2.length()**2-2*l1.length()*l2.length()*np.cos(np.deg2rad(360-d)))
            if data["L"]>Lmax:
                data["L"]=Lmax
            data["T"]=abs(data["L"]/(2*np.tan(np.deg2rad((d)/2))))
            data["D"]=d-90
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
        else:
            data["D"]=d
            if data["L"]<data["T"]:
                data["L"]=data["T"]
            data["T"]=0
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["L"]-data["T"]).asPoint())

    elif index=="S":
            data["D"]=0
            data["T"]=0
            p2=qgsGeometryToPolyline(line)[-1]

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'T')
    feat.setGeometry(QgsGeometry.fromPolyline([p2QgsPoint(p1),p2QgsPoint(p2)]))
    layer.dataProvider().addFeatures([feat])

    data["Disable"].append("R")

    return data



def circleArc2(layer, data, index, layer2, i):
    fcount=featureCount(layer)
    if fcount>0:
        fant=[f for f in layer.getFeatures()][fcount-1]
        l1=fant.geometry()
        l2=QgsGeometry(l1)
        dd=diff(qgsGeometryToPolyline(fant.geometry())[-1], qgsGeometryToPolyline(fant.geometry())[0])
        l2.translate(dd.x(),dd.y())
        PI=qgsGeometryToPolyline(fant.geometry())[-1]
        d=float(data["D"]) if not index=="S" else 90.0
        l2.rotate(d, QgsPointXY(PI))

    else:
        data["Disable"].append("C")
        data["Disable"].append("D")
        data["Disable"].append("R")
        data["Disable"].append("L")
        data["Disable"].append("T")
        return data

    data["Disable"].append("C")
    startAngle=azi(qgsGeometryToPolyline(l1))
    angle=90-(data["D"]+startAngle)
    angle=angle if angle>0 else 360+angle
    angle=angle if angle<360 else angle-360
    angleInternal=180-abs(d)
    p1=p2QgsPoint(PI)
    corda=2*data["R"]*np.sin(np.deg2rad(angleInternal/2))
    p2=p2QgsPoint(corda*np.cos(np.deg2rad(angle))+p1.x(), corda*np.sin(np.deg2rad(angle))+p1.y())

    T=None
    E=None
    p=None
    arc=None

    if index=="R":
            pass
    elif index=="L":
            data["R"]=data["L"]/(np.deg2rad(abs(data["D"])))
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad(abs(data["D"])/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            dd=diff(l2.interpolate(T).asPoint(), qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], QgsPointXY(qgsGeometryToPolyline(l2)[0]))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(qgsGeometryToPolyline(l2)[0])


    elif index=="T":
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            dd=diff(l2.interpolate(T).asPoint(), qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], QgsPointXY(qgsGeometryToPolyline(l2)[0]))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
            PI=p2QgsPoint(qgsGeometryToPolyline(l2)[0])


    elif index=="D":
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            T=abs(corda/(2*np.tan(np.deg2rad((abs(data["D"]))/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            l2=QgsGeometry(l1)
            dd=diff(p1, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            PI=p2QgsPoint(l2.interpolate(T).asPoint())
            dd=diff(PI, qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())
            l2.rotate(data["D"], qgsGeometryToPolyline(l2)[0])
            p2=p2QgsPoint(l2.interpolate(T).asPoint())

    elif index=="C":
        pass
    elif index=="S":
            data["C"]=True
            data["D"]=90
            data["L"]=np.deg2rad(abs(data["D"]))*data["R"]
            data["T"]=0

    if (data["T"]>l1.length() or data["T"]>l2.length()) and data["C"]:
            data["L"]=np.deg2rad(abs(d))*data["R"]*abs(data["D"]/d)
            corda=2*data["R"]*np.sin(np.deg2rad(abs(data["D"])/2))
            data["T"]=abs(corda/(2*np.tan(np.deg2rad((d)/2))))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            PI=p2QgsPoint(PI)
            corda=2*data["R"]*np.sin(np.deg2rad(angleInternal/2))
            p2=p2QgsPoint(corda*np.cos(np.deg2rad(angle))+p1.x(), corda*np.sin(np.deg2rad(angle))+p1.y())

    T = float(data["T"]) if T is None else T
    E = abs(T*np.tan(np.deg2rad(data["D"]/4))) if E is None else E

    p=p2QgsPoint((p1.x()+p2.x())/2, (p2.y()+p1.y())/2)
    tmp_line=QgsGeometry.fromPolyline([p2QgsPoint(PI),p])
    p=p2QgsPoint(tmp_line.interpolate(E).asPoint())

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'C')
    # Create a QgsCircularStringV2
    circularRing = QgsCircularString()
    # Set first point, intermediate point for curvature and end point
    circularRing.setPoints([
        p1,
        p,
        p2]
    )
#    data["R"]=QgsGeometryUtils.circleCenterRadius(p1,p,p2)[0]
    circularRing=arc if arc else circularRing
    feat.setGeometry(circularRing)
    f2=QgsFeature(layer.fields())
    f2.setGeometry(l2)
    layer.dataProvider().addFeatures([feat])

    data["Disable"].append("C")
    return data




def inSpiral2(layer, data, index, layer2, i):
    line1, line2=getTangentesGeometry(layer2,i)
    angle=deflection(layer2,i)
    PI=qgsGeometryToPolyline(line1)[-1]
    if data["T"]>data["L"]:
        data["T"]=data["L"]

    if index=="R":
        pass
    elif index=="L":
        pass
    elif index=="T":
        pass
    elif index=="D":
        pass
    elif index=="C":
        pass
    elif index=="S":
        pass

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'S')
#    feat.setGeometry(QgsGeometry.)
    layer.dataProvider().addFeatures([feat])
    return data


def outSpiral2(layer, data, index, layer2, i):
    line1, line2=getTangentesGeometry(layer2,i)
    angle=deflection(layer2,i)
    PI=qgsGeometryToPolyline(line1)[-1]
    if data["T"]>data["L"]:
        data["T"]=data["L"]

    if index=="R":
        pass
    elif index=="L":
        pass
    elif index=="T":
        pass
    elif index=="D":
        pass
    elif index=="C":
        pass
    elif index=="S":
        pass

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'S')
#    feat.setGeometry(QgsGeometry.)
    layer.dataProvider().addFeatures([feat])
    return data


def tangent2(layer, data, index, layer2, i):
    fcount=featureCount(layer)
    if fcount>0:
        fant=[f for f in layer.getFeatures()][fcount-1]
        length=fant.geometry().length()
        lpt=qgsGeometryToPolyline(fant.geometry())[-1]
        angle=90-lastAzimuth(fant.geometry())
        lpt=p2QgsPoint(lpt.x()-length*np.cos(np.deg2rad(angle)), lpt.y()-length*np.sin(np.deg2rad(angle)))

        l1=QgsGeometry.fromPolyline([p2QgsPoint(lpt), p2QgsPoint(qgsGeometryToPolyline(fant.geometry())[-1])])
        l2=QgsGeometry(l1)
        dd=diff(qgsGeometryToPolyline(fant.geometry())[-1],qgsGeometryToPolyline(fant.geometry())[0])
        l2.translate(dd.x(),dd.y())
        PI=qgsGeometryToPolyline(fant.geometry())[-1]
        d=0
        data["Disable"].append("C")

    else:
        l1, l2=getTangentesGeometry(layer2, i)
        d=deflection(layer2, i)
        PI=qgsGeometryToPolyline(l1)[-1]
        if l1 is None:
            l1=QgsGeometry(l2)
            dd=diff(qgsGeometryToPolyline(l2)[0], qgsGeometryToPolyline(l2)[-1])
            l2.translate(dd.x(), dd.y())
        elif l2 is None:
            l2=QgsGeometry(l1)
            dd=diff(qgsGeometryToPolyline(l1)[-1], qgsGeometryToPolyline(l2)[0])
            l2.translate(dd.x(), dd.y())

    startAngle=azi(qgsGeometryToPolyline(l1))
    angle=90-(data["D"]+startAngle)
    angle=angle if angle>0 else 360+angle
    angle=angle if angle<360 else angle-360
    p1=p2QgsPoint(PI)
    p2=p2QgsPoint(data["L"]*np.cos(np.deg2rad(angle))+p1.x(), data["L"]*np.sin(np.deg2rad(angle))+p1.y())
    line=QgsGeometry.fromPolyline([p1,p2])

    if data["T"]>l1.length():
        data["T"]=l1.length

    if index=="R":
        pass

    elif index=="L":
         if data["C"]:
            Lmax=np.sqrt(l1.length()**2+l2.length()**2-2*l1.length()*l2.length()*np.cos(np.deg2rad(360-d)))
            if data["L"]>Lmax:
                data["L"]=Lmax
            data["T"]=abs(data["L"]/(2*np.tan(np.deg2rad((d)/2))))
            data["D"]=d-90
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
         else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="T":
        if data["C"]:
            data["L"]=abs(data["T"]*2*np.tan(np.deg2rad((d)/2)))
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
        else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="D":
        if data["C"]:
            data["D"]=0
            data["T"]=0
            data["C"]=False
            p2=qgsGeometryToPolyline(line)[-1]
        else:
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            dd=diff(p1,PI)
            line.translate(dd.x(), dd.y())
            p2=qgsGeometryToPolyline(line)[-1]

    elif index=="C":
        if data["C"]:
            Lmax=np.sqrt(l1.length()**2+l2.length()**2-2*l1.length()*l2.length()*np.cos(np.deg2rad(360-d)))
            if data["L"]>Lmax:
                data["L"]=Lmax
            data["T"]=abs(data["L"]/(2*np.tan(np.deg2rad((d)/2))))
            data["D"]=d-90
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["T"]).asPoint())
        else:
            data["D"]=d
            if data["L"]<data["T"]:
                data["L"]=data["T"]
            data["T"]=0
            p1=p2QgsPoint(l1.interpolate(l1.length()-data["T"]).asPoint())
            p2=p2QgsPoint(l2.interpolate(data["L"]-data["T"]).asPoint())

    elif index=="S":
            data["D"]=0
            data["T"]=0
            p2=qgsGeometryToPolyline(line)[-1]

    feat = QgsFeature(layer.fields())
    feat.setAttribute('Tipo', 'T')
    feat.setGeometry(QgsGeometry.fromPolyline([p2QgsPoint(p1),p2QgsPoint(p2)]))
    layer.dataProvider().addFeatures([feat])

    data["Disable"].append("R")
    data["Disable"].append("C")

    return data




