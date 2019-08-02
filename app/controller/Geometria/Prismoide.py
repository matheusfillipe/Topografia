from .Figure import *
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import QThread, pyqtSignal

class QPrismoid(prismoide, QThread):
    volumeFinished=pyqtSignal()
    def __init__(self, terreno=None, st=None, progressiva=None, prism=None, ati=3, cti=3):
        prismoide.__init__(self)
        QThread.__init__(self)

        if prism is None:
            self.terreno=terreno
            self.st=st
            self.progressiva=progressiva

            self.cti=cti
            self.ati=ati

            self.lastGeneratedIndex=0

            sq=square()

            for i in range(0,len(self.terreno)):
                c=sq.copy()
                f=face()
                f.fromClosedCurve(c)
                f.setPos(point(c.position.x(),c.position.y(),self.progressiva[i]))
                self.appendFace(f)
            self.start()

        elif type(prism) is prismoide:
            self.fromFaces(prism.faces)
            self.lastGeneratedIndex=len(prism.faces)-1
            self.progressiva=prism.progressiva
            self.terreno=prism.terreno
            self.st=prism.st
            self.ati=prism.ati
            self.cti=prism.ati


    def run(self):
        k=self.lastGeneratedIndex
        j=len(self.terreno)

        for i in range(k, j):
            self.generate(i)
            self.lastGeneratedIndex+=1

        self.volumeFinished.emit()


    def generate(self, i):
        cti=self.cti
        ati=self.ati
        c = self.terreno[i]
        p = self.st[i]

        terreno=curve()
        pista=curve()
        ct=curve()
        at=curve()

        ptst=[]
        ptsp=[]

        corte=p[-cti:]
        atterro=p[:ati]
        ctt=[]
        att=[]

        for pt in c:
            ptst.append(point(pt[0],pt[1]))
        for pt in p[ati-1:-(cti-1)]:
            ptsp.append(point(pt[0],pt[1]))
        for pt in corte:
            ctt.append(point(pt[0],pt[1]))
        for pt in atterro:
            att.append(point(pt[0],pt[1]))

        terreno.setPoints(ptst)
        pista.setPoints(ptsp)
        ct.setPoints(ctt)
        at.setPoints(att)

        left=curve()
        right=curve()

        #left
        tmp=curve()
        a=terreno.getY(float(pista.getFirstPoint().x()))
        b=pista.getFirstPoint().y()

        if terreno.getY(float(pista.getFirstPoint().x())) < pista.getFirstPoint().y():
            tmp=at.copy()
        else:
            tmp=ct.copy()
            tmp.mirror(line(point(0,0),point(0,10)))
            tmp=tmp.getInversed()

        r=len(tmp.getInversed().intersect(terreno))
        while r == 0 and tmp.getWidth()<60:
            tmp2=tmp.copy()
            tmp2.position=tmp2.getLastPoint()
            tmp2.setPos(tmp.getFirstPoint())
            tmp.prependCurve(tmp2)
            r=len(tmp.getInversed().intersect(terreno))

        if r>1:
            left=tmp.getInversed().trim(terreno,1)
        else:
            left=tmp.trim(terreno)

        #right
        tmp=curve()
        if terreno.getY(pista.getLastPoint().x())<pista.getLastPoint().y():
            tmp=at.copy()
            tmp.mirror(line(point(0,0),point(0,10)))
            tmp=tmp.getInversed()
        else:
            tmp=ct.copy()

        inter=tmp.getInversed().intersect(terreno)
        r=len(inter)
        while r == 0 and tmp.getWidth()<60:
            tmp2=tmp.copy()
            tmp2.setPos(tmp.getLastPoint())
            tmp.appendCurve(tmp2)
            inter=tmp.getInversed().intersect(terreno)
            r=len(inter)
        if type(inter)==list:
            inter=inter[-1]
        pts=tmp.getPoints()
        rightpts=[]
        for pt in pts:
            if pt.x()>inter.x():
                rightpts.append(inter)
                break
            rightpts.append(pt)

        right.setPoints(rightpts)

#        if self.progressiva[i] == 580.0:
#            test(plotCurve(tmp), "tmp")
#            test(plotCurve(right), "right")
#            test(plotCurve(left), "left")

        f=face()
        pista.prependCurve(left)
        pista.appendCurve(right)
        f.from2Curves(pista, terreno)

       #TODO replace custom offset 20
        self.replaceFaceKeepZ(f, i)

    def getPrismoide(self):
        prismoid=prismoide()
        prismoid.fromFaces(self.faces)
        prismoid.volume=self.volume
        prismoid.lastIndex=self.lastIndex
        prismoid.wasInitialized=True
        prismoid.st=self.st
        prismoid.terreno=self.terreno
        prismoid.progressiva=self.progressiva
        prismoid.ati=self.ati
        prismoide.cti=self.cti
        return prismoid

    def getAreasCtAt(self,i):

        f=self.getFace(i)
        sup=f.superior
        inf=f.inferior
        areaCt=0
        areaAt=0

        x=sup.intersect(inf)
        for i in range(0,len(x)-1):
            f=face()
            xp=x[i].x()
            xn=x[i+1].x()
            m=(xp+xn)/2
            ys=sup.getY(m)
            yi=inf.getY(m)
            lp=line(point(xp,0),point(xp,max(ys,yi)+100))
            ln=line(point(xn,0),point(xn,max(ys,yi)+100))
            ls=line(lp.point2,ln.point2)
            trimmer=curve()
            trimmer.setLines([lp,ls,ln])

            pista=sup.trim(trimmer)
            terreno=inf.trim(trimmer)

            f.from2Curves(pista,terreno)
            #test(plotCurve(f.curve))

            if inf.getY(m)<sup.getY(m): #Aterro
                areaAt+=abs(f.getArea())
            else: #Corte
                areaCt+=abs(f.getArea())

        return areaCt, areaAt

    #correct valeta accti (bug to corte embaixo)
    #correct saving prismoid
    #correct terreno prismoid intersec lines on each side to trim
    #Set superelevation and super width rules
    #Bruckner diagram
    #Plot all

    #Correct 20 m problem
    #Add distance vision to CV's
    #Better horizontal plotind and drawing
    #horizontal Curves plotting
    #Generate intersec table

    #TODO reduce getArea and getVolume calls by doing it on instanciacion and checking if primsmoid changed before getVolume call
    #TODO verify prismoid restoring
