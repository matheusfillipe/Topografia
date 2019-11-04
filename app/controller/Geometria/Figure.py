from typing import *
import os
import pickle
import sys

import numpy as np
import copy

def Infinity():
    return float("inf")

class figure():
    def __init__(self):
        self.index=0
        self.position=point(0,0,0)
        self.precision=4
        self.referencePoit=point(0,0,0)
        self.update()

    def setPrecision(self, p):
        self.precision=p

    def setIndex(self, i):
        self.index=i
        self.update()

    def setPos(self, pt):
        self.position=pt
        self.update()

    def getPos(self):
        return self.position

    def move(self, pt):
        self.setPos(pt)
        self.update()

    def save(self, filename):
        pickle.dump(self, open(filename, "wb"))

    def copy(self):
        return copy.copy(self)

    def restore(self, filename):
        try:
            value=pickle.load(open(filename, "rb"))
        except FileNotFoundError:
            return False
        self.copyFrom(value)
        return True

    def update(self):
        self._x=self.position[0]
        self._y=self.position[1]
        self._z=self.position[2]


    def x(self):
        return self.position.x()

    def y(self):
        return self.position.y()

    def z(self):
        return self.position.z()


    def __add__(self, other):
        return point(self._x + other.x(), self._y + other.y(), self._z + other.z())

    def __sub__(self, other):
        return  point(self._x - other.x(), self._y - other.y(), self._z - other.z())

    def __eq__(self, other):
        return self._x == other.x() and self._y == other.y() and self._z == other.z()

    def __gt__(self, other):
        return self.position.distanceTo(self.position.reference) > other.distanceTo(self.position.reference)

    def __ge__(self, other):
        return self.position.distanceTo(self.position.reference) >= other.distanceTo(self.position.reference)

    def __lt__(self, other):
        return self.position.distanceTo(self.position.reference) < other.distanceTo(self.position.reference)

    def __le__(self, other):
        return self.position.distanceTo(self.position.reference) <= other.distanceTo(self.position.reference)

    def __str__(self):
        return str("x: " + str(self._x) + ", y: " + str(self._y) + ", z: " + str(self._z))

    def __ne__(self, other):
         return self._x != other.x() or self._y != other.y() or self._z != other.z()

    def __getitem__(self, item):
        return self.position.toList()[item]

    def __contains__(self, point):
        pass

    def copyFrom(self, value):
        if isinstance(value, figure):
            self.__dict__ = copy.deepcopy(value.__dict__)
        else:
            self.data = value




class point():
    def __init__(self, x, y, z=0):
        self._x=float(x)
        self._y=float(y)
        self._z=float(z)
        self.index=0
        self.precision=5

        if self._x==0 and self._y==0 and self._z==0:
            self.reference=self

        else:
            self.reference=point(0,0,0)

    def setIndex(self, i):
        self.index=i

    def setX(self, z):
        self._x=z

    def x(self):
        return self._x

    def setY(self, z):
        self._y=z

    def y(self):
        return self._y

    def setZ(self, z):
        self._z=z

    def z(self):
        return self._z

    def toList(self):
        return [self._x, self._y, self._z]

    def setFromList(self, l):
        self._z=l[2]
        self._y=l[1]
        self._x=l[0]

    def deltaX(self, p):
        if type(p)==point:
            return self.x() - p.x()
        elif type(p)==float or type(p) == int:
            return self.x() - p
        return 0

    def deltaY(self, p):
        if type(p) == point:
            return self.y() - p.y()
        elif type(p) == float or type(p)==int:
            return self.y() - p
        return 0

    def deltaZ(self, p):
        if type(p)==point:
            return self.z() - p.z()
        elif type(p)==float or type(p)==int:
            return self.z() - p
        return 0

    def distanceTo(self, point2):
        return np.sqrt(self.deltaX(point2)**2+self.deltaY(point2)**2+self.deltaZ(point2)**2)

    def __add__(self, other):
        return point(self._x + other.x(), self._y + other.y(), self._z + other.z())

    def __sub__(self, other):
        return  point(self._x - other.x(), self._y - other.y(), self._z - other.z())

    def __mul__(self, other):
        tp=type(other)
        if type(other)==int or type(other)==float or tp==np.float or tp==np.float16 or tp==np.float32 or tp==np.float64 or tp==np.float80:
            return point(self._x*other, self._y*other, self._z*other)
        return False

    def __divmod__(self, other):
        if type(other)==int:
            return point(self._x*1/other, self._y*1/other, self._z*1/other)
        return False

    def __eq__(self, other):
        return round(self._x - other.x(), self.precision) == 0 and round(self._y - other.y(), self.precision)==0 and round(self._z - other.z(), self.precision)==0

    def __gt__(self, other):
        return self.distanceTo(self.reference) > other.distanceTo(self.reference)

    def __ge__(self, other):
        return self.distanceTo(self.reference) >= other.distanceTo(self.reference)

    def __lt__(self, other):
        return self.distanceTo(self.reference) < other.distanceTo(self.reference)

    def __le__(self, other):
        return self.distanceTo(self.reference) <= other.distanceTo(self.reference)

    def __str__(self):
        return str("x: " + str(self._x) + ", y: " + str(self._y) + ", z: " + str(self._z))

    def __ne__(self, other):
         return round(self._x - other.x(), self.precision)!=0 or round(self._y - other.y(), self.precision)!=0 or round(self._z - other.z(), self.precision)!=0

    def __getitem__(self, item):
        return self.toList()[item]

    def __contains__(self, lineOrCurve):
        if type(lineOrCurve)==line:

            return line in self

        elif type(lineOrCurve)==curve:
            for l in lineOrCurve.lines:
                if self in l:
                    return True

        else:
            raise ValueError



    def add(self, x, y, z=0):
        self._x += x
        self._y += y
        self._z += z
        return self

    def subtract(self, x, y, z=0):
        self.add(-x,-y,-z)


    def displaceXY(self, tan, lenghX):
        if not Infinity()==tan:
            self.add(lenghX, tan*lenghX)

    def displace(self, tanXY, tanZY, lengh):
        pass

    def tan(self, point1):
        try:
           return (self.y() - point1.y()) / (self.x() - point1.x())
        except ZeroDivisionError:
            return Infinity()

    def interpolXY(self, point1, x):
        tan=self.tan(point1)
        pt=copy.copy(self)
        pt.displaceXY(tan, x - self.x())
        return pt.y()

    def invertXY(self):
        x=self._x
        self._x=self._y
        self._y=x

    def move(self, pt):
        self.setPos(pt)

    def setPos(self, pt):
        self._x=pt.x()
        self._y=pt.y()
        self._z=pt.z()

    def copy(self):
        return point(self._x, self._y)

    def copyFrom(self, value):
        if isinstance(value, point):
            self.__dict__ = copy.deepcopy(value.__dict__)
        else:
            self.data = value

class pt(point):

    def __init__(self, x, y, z=0):
        super(pt,self).__init__(x, y, z)


class line(figure): #ax+b
    def __init__(self, p1, p2, index=0):
        super(line,self).__init__()
        self.point1=point(p1.x(), p1.y(), p1.z())
        self.point2=point(p2.x(), p2.y(), p2.z())
        self.position=self.point1
        self.point1.index=0
        self.point2.index=1

    def getB(self):
        return (self.point1.y()-self.point1.x()*self.getTan())

    def getTan(self):
        return self.point1.tan(self.point2)

    def getY(self, x):
        return self.point1.interpolXY(self.point2, x)

    def getX(self, y):
        self.point1.invertXY()
        r=self.getY(y)
        self.point1.invertXY()
        return r

    def getFirstPoint(self):
        return self.point1

    def getLastPoint(self):
        return self.point2

    def __eq__(self, other):
        return self.point1 == other.point1 and self.point2 == other.point2

    def __contains__(self, item):

        if type(item) == curve:
            for l in item.lines:
                if self == l:
                    return True
            return False

        elif type(item) == point:

            y1=self.getY(item.x())
            y2=item.y()

            if round(y1 - y2, self.precision) == 0:
                x1=self.point1.x()
                x2=self.point2.x()
                return (min(x1,x2) <= item.x() and item.x() <= max(x1,x2))
            else:
                return False
        else:
            raise ValueError

    def __str__(self):
        return "("+str(self.point1.x())+","+str(self.point1.y())+"), " + "("+str(self.point2.x())+","+str(self.point2.y())+") ;  "

    def isPositiveX(self):
        return self.point1.x() <= self.point2.x()

    def trim(self, pt):
        newLine=self.copy()
        if type(pt)==line:
            pt=self.intersect(pt)
        if type(pt)==point:
            if pt in newLine:
                newLine = line(newLine.point1, pt)
                return newLine
            else:
                return newLine
        else:
            return False

    def intersect(self, line2):
        if self.isIntersecting(line2):
            if line2.point1 in self and line2.point2 in self:
                return copy.copy(line2)
            elif line2.point1 in self:
                return copy.copy(line2.point1)
            elif line2.point2 in self:
                return copy.copy(line2.point2)
            elif self.point1 in line2 and self.point2 in line2:
                return copy.copy(self)
            elif self.point1 in line2:
                return copy.copy(self.point1)
            elif self.point2 in line2:
                return copy.copy(self.point2)
            elif self.point2.x() == self.point1.x():
                self.point2+=point(0.00000001, 0)
                return self.intersect(line2)
            elif line2.point2.x() == line2.point1.x():
                line2.point2+=point(0.00000001, 0)
                return self.intersect(line2)
            elif self.getTan() - line2.getTan() != 0:
                x = (line2.getB()-self.getB())/(self.getTan()-line2.getTan())
                pt=point(x, (self.getY(x)+line2.getY(x))/2)
                if (pt in line2) and (pt in self):
                    return pt
                else:
                    return True
        else:
            return False



    def infiniteLineIntersec(self, line2):
        if self.getTan() - line2.getTan() != 0:
            x = (line2.getB()-self.getB())/(self.getTan()-line2.getTan())
            pt=point(x, (self.getY(x)+line2.getY(x))/2)
            return pt
        elif self.point2.x() == self.point1.x():
            self.point2+=point(0.00000001, 0)
            return self.infiniteLineIntersec(line2)
        elif line2.point2.x() == line2.point1.x():
            line2.point2+=point(0.00000001, 0)
            return self.infiniteLineIntersec(line2)
        else:
            return False

    def getInversed(self):
        r = self.copy()
        r.point2 = self.point1
        r.point1 = self.point2
        return r

    def getLengh(self):
        return self.point1.distanceTo(self.point2)

    def getHeight(self):
        return (self.point2-self.point1).y()

    def getWidth(self):
        return (self.point2-self.point1).x()

    def getMiddlePoint(self):
        return (self.point2+self.point1)*0.5

    def setPos(self, pt):
        d=pt-self.position
        self.point1+=d
        self.point2+=d
        self.position=pt
        self.update()

    def rotate(self, angle, axes:point):

        if axes == self.point1:
            pos=self.position.copy()
            self.setPos(self.referencePoit)
            angle = angle*np.pi/180
            pt = self.point2
            x = pt.x()*np.cos(angle)-pt.y()*np.sin(angle)
            y = pt.x()*np.sin(angle)+pt.y()*np.cos(angle)
            self.point2=point(x,y)
            self.setPos(pos)
            return

        elif axes == self.point2:
            pos=self.position.copy()
            self.setPos(self.referencePoit)
            angle = angle*np.pi/180
            pt = self.point1
            x = pt.x()+pt.x()*np.cos(angle)-pt.y()*np.sin(angle)
            y = pt.y()+pt.x()*np.sin(angle)+pt.y()*np.cos(angle)
            self.point1=point(x,y)
            self.setPos(pos)
            return

        else:
            l1=line(axes,self.point1)
            l1.rotate(angle,axes)

            l2=line(axes,self.point2)
            l2.rotate(angle,axes)

            self.point1=l1.point2
            self.point2=l2.point2
        self.update()

    def copy(self):
        return line(self.point1.copy(), self.point2.copy())

    def scale(self, s, reference = None):
        if reference is None:
            reference=self.getMiddlePoint()

        if reference == self.point1:
            self.point2*=s

        elif reference == self.point2:
            self.point1*=s

        else:
            self.point1*=s
            self.point2*=s

        self.update()


    def isIntersecting(self, l):
        p1=self.point1
        p2=self.point2
        q1=l.point1
        q2=l.point2
        return True or (((q1.x()-p1.x())*(p2.y()-p1.y()) - (q1.y()-p1.y())*(p2.x()-p1.x())) * ((q2.x()-p1.x())*(p2.y()-p1.y()) - (q2.y()-p1.y())*(p2.x()-p1.x())) < 0) and (((p1.x()-q1.x())*(q2.y()-q1.y()) - (p1.y()-q1.y())*(q2.x()-q1.x())) * ((p2.x()-q1.x())*(q2.y()-q1.y()) - (p2.y()-q1.y())*(q2.x()-q1.x())) < 0)






class curve(figure):
    def __init__(self):
        self.lines=[]
        self.index=0
        self.wasInitialized=False
        super(curve,self).__init__()


    def clear(self):
        self.lines=[]
        self.wasInitialized=False

    def setPoints(self, points):
        self.clear()
        self.position=(points[0])

        for i in range(0, len(points)-1):
            self.lines.append(line(points[i], points[1+i], i))

        self.wasInitialized=True
        self.update()
        return self

    def setLines(self, lines):
        self.clear()
        self.position = (lines[0].position)
        i=0
        for l in lines:
            L=copy.copy(l)
            L.index=i
            self.lines.append(L)
            i+=1
        self.wasInitialized=True
        self.update()
        return self

    def setEq(self, string):
        self.update()

    def prependCurve(self, c):
        tmpc=c.copy()
        lines=tmpc.lines
        lines.reverse()

        if lines[-1].point2!=self.getFirstPoint():
            self.prependPoint(lines[0].point2)
        for l in lines:
            self.prependPoint(l.point1)

    def appendCurve(self,c):
        lines=c.copy()
        lines=lines.lines

        if lines[-1].point1!=self.getLastPoint():
            self.appendPoint(lines[0].point1)
        for l in lines:
            self.appendPoint(l.point2)

    def getY(self, x):
        if not self.isClosed():
            for l in self.lines:
                if (l.point2.x() >= x and l.point1.x() <= x and l.point2.x() > l.point1.x()) or (l.point2.x() <= x and l.point1.x() >= x and l.point2.x() < l.point1.x()):
                    return l.point1.interpolXY(l.point2, x)
            return False

    def getX(self, y):
        pass

    def getNumberOfLines(self):
        return len(self.lines)

    def getFirstLine(self):
        return self.lines[0]

    def getLastLine(self):
        return self.lines[self.getNumberOfLines()-1]

    def getFirstPoint(self):
        return self.lines[0].getFirstPoint()

    def getLastPoint(self):
        return self.getLastLine().getLastPoint()

    def appendPoint(self, pt):
        l=line(self.getLastPoint(), pt)
        self.lines.append(l)
        self.update()

    def intersect(self, curve2):

        r=[]
        for l in self.lines:
            for c in curve2.lines:
                ax=[l.point1.x(), l.point2.x()]
                bx=[c.point1.x(), c.point2.x()]
                cy=[l.point1.y(), l.point2.y()]
                dy=[c.point1.y(), c.point2.y()]

                if min(max(ax,bx))<=max(min(ax,bx)) and min(max(cy,dy))<=max(min(cy,dy)):
                   if l==c:
                        r.append(l.point2)
                   else:
                       pt=l.intersect(c)
                       if type(pt)==point:
                           r.append(pt)
            R=[]

        for pt in r:
            if not pt in R:
                R.append(pt)

        return R


    def removeLine(self, l):
        if l in self:
            self.lines.remove(l)
        self.update()

    def __contains__(self, item):

        if type(item) == point:
            for l in self.lines:
                if item in l:
                    return True
                return False

        elif type(item) == line:
            for l in self.lines:
                if l == item:
                    return True
            return False
        else:
            return False

    def __str__(self):
        s=""
        for l in self.lines:
            s+=str(l)
        return s


    def trim(self, c, n=-1):
        lines=[]

        r=self.intersect(c)

        if type(r)==point:
            s=False
            for l in self.lines:
                if r in l:
                    s=True
                    if n==-1:
                        lines.append(line(l.point1,r))
                    else:
                        lines.append(line(r,l.point2))
                    continue
                if s:
                    lines.append(l)

        elif len(r)==1 or n==1:
            r=r[0]
            s=False
            for l in self.lines:
                if r in l:
                    s=True
                    if n==1:
                        lines.append(line(l.point1,r))
                        s=False
                    else:
                        lines.append(line(r,l.point2))
                    continue
                if s:
                    lines.append(l)

        elif type(r) == list and len(r) >= 2:
            if n==-1:
                r=[r[0],r[-1]]
            elif n>1:
                r=r[:n]

            s = False
            for l in self.lines:
                if r[0] in l:
                    s = True
                    if r[1] in l:
                        lines.append(line(r[0],r[1]))
                        break
                    lines.append(line(r[0],l.point2))
                    continue

                if r[1] in l:
                    lines.append(line(l.point1,r[1]))
                    break

                if s:
                    lines.append(l)
        else:
            return self.copy()

        return curve().setLines(lines)


    def indexOfLine(self, l):
        for L in self.lines:
            if L==l:
                return self.lines.index(L)
        raise ValueError

    def update(self):
        i=0
        for l in self.lines:
            l.setIndex(i)
            i+=1
        if self.wasInitialized:
            self.position=self.lines[0].point1
        super(curve, self).update()

    def getInversed(self):
        lines=[]
        for l in self.lines:
            lines.append(l.getInversed())
        r=curve()
        lines.reverse()
        r.setLines(lines)
        return r

    def isContinuous(self):
        for i, _ in enumerate(self.lines[:-1]):
            if self.lines[i].point2 != self.lines[i+1].point1:
                return False
        return True

    def isClosed(self):
        return self.isContinuous() and self.getLastPoint() == self.lines[0].point1

    def getPoints(self):
        r = []
        l2 = 0

        for i, _ in enumerate(self.lines[:-1]):
            l1 = self.lines[i]
            l2 = self.lines[i+1]

            r.append(l1.point1.copy())

            if l1.point2 != l2.point1:
                r.append(l1.point2.copy())

        if type(l2) == line:
            r.append(l2.point1.copy())
            r.append(l2.point2.copy())

        if len(self.lines)==1:
            r.append(self.lines[0].point1)
            r.append(self.lines[0].point2)

        return r


    def prependPoint(self, pt):
        lines=[]
        lines.append(line(pt, self.lines[0].point1))
        for l in self.lines:
            lines.append(l)
        self.setLines(lines)

    def setPos(self, pt):
        d=pt-self.position
        for i,_ in enumerate(self.lines):
            self.lines[i].setPos(d+self.lines[i].position)

        self.position=pt
        self.update()

    def rotate(self, angle, axes):

        if axes==self.position:
            points=[]
            for pt in self.getPoints():
                l=line(axes,pt)
                l.rotate(angle,axes)
                points.append(l.point2)

            self.setPoints(points)
            self.position=self.lines[0].point1
            self.update()

        else:
            self.prependPoint(axes)
            self.rotate(angle,axes)
            self.removeLine(self.getFirstLine())

    def getGeoCenter(self):
        y=0
        x=0
        for pt in self.getPoints():
            y+=pt.y()
            x+=pt.x()
        x=x/(self.getNumberOfLines()+1)
        y=y/(self.getNumberOfLines()+1)

        return point(x, y)

    def scale(self, s, reference=None):
        if reference is None:
            reference=self.getGeoCenter()

        points=[]
        for pt in self.getPoints():
            l=line(reference,pt)
            l.scale(s,l.point1)
            points.append(l.point2)

        self.setPoints(points)
        self.position=self.lines[0].point1
        self.update()



    def mirror(self, l:line):
        if l.getTan() == 0 or l.point2.x()==l.point1.x():
            l.point2+=point(0.00001,0.00001)

        points=[]
        perp=l.copy()
        perp.rotate(90,perp.point1)

        for pt in self.getPoints():
            p=perp.copy()
            p.setPos(pt)
            r=p.infiniteLineIntersec(l)

            if type(r)==point:

                points.append(pt+(r-pt)*2)

        self.setPoints(points)
        self.update()
        return perp



    def copy(self):
        c=curve()
        c.setPoints(self.getPoints())
        return c

    def getHeight(self):
        h=0
        H=[]
        for l in self.lines:
            h+=l.getHeight()
            H.append(abs(h))
        return max(H)

    def getWidth(self):
        h=0
        H=[]
        for l in self.lines:
            h+=l.getWidth()
            H.append(abs(h))
        return max(H)

    def cut(self, xn):
        newCurve1=curve()
        newCurve2=curve()
        lines1=[]
        lines2=[]
        cutted=False
        for l in self.lines:
            if not cutted:
                if xn in l:
                    lines1.append(line(l.point1, xn))
                    lines2.append(line(xn, l.point2))
                    cutted=True
                else:
                    lines1.append(l)
            else:
                lines2.append(l)

        if len(lines1)>0:
            newCurve1.setLines(lines1)
        if len(lines2)>0:
            newCurve2.setLines(lines2)
        return newCurve1, newCurve2



class face(figure):

    def __init__(self):
        self.position=pt(0,0)
        self.superior = curve()
        self.inferior = curve()
        self.area  = 0
        self.index = 0
        self.curve = curve()


    def from2Curves(self, superior, inferior):

        self.superior = superior.trim(inferior)
        self.inferior = inferior.trim(superior)

        self.position = superior.position
        lines=[]
        for l in self.superior.getInversed().lines:
            lines.append(l)
        for l in self.inferior.lines:
            lines.append(l)
        self.curve.setLines(lines)
        self.update()

        return self

    def fromClosedCurve(self, c:curve):

        if not c.isClosed():
            c.appendPoint(c.getFirstPoint())

        self.curve = c
        self.update()
        return self


    def update(self):

        super(face, self).update()

        if not self.curve.wasInitialized:
            self.curve=curve()
            self.setPos(self.superior.getFirstPoint())
            lines=[]
            for l in self.inferior.lines:
                lines.append(l)
            for l in self.superior.getInversed().lines:
                lines.append(l)
            self.setPos(lines[0].point1)

            self.curve.setLines(lines)






    def getArea(self):
        s=0
        if self.curve.isClosed():
            points=self.curve.getPoints()
            act=0
            aat=0

            for i,_ in enumerate(points[:-1]):
                s+=points[i].x()*points[i+1].y()
            s+=points[-1].x()*points[0].y()

            for i,_ in enumerate(points[:-1]):
               s-=points[i].y()*points[i+1].x()
            s-=points[-1].y()*points[0].x()

            s=(s)/2

        self.area=s
        return s

    def getAreas(self):
        sup=self.superior
        inf=self.inferior
        areaCt=0
        areaAt=0
        x=sup.intersect(inf)


        for i in range(0, len(x)-1):
            mf=face()
            xp=x[i].x()
            xn=x[i+1].x()
            m=(xp+xn)/2
            pista, sup=sup.cut(x[i+1])
            terreno, inf=inf.cut(x[i+1])
            mf.from2Curves(pista,terreno)
          #  test(plotCurve(mf.curve))

            if self.inferior.getY(m)<self.superior.getY(m): #Aterro
                areaAt+=abs(mf.getArea())
            else: #Corte
                areaCt+=abs(mf.getArea())

        areaCt=-areaCt

     #   if round(areaAt-areaCt,2)!=self.getArea():
     #       if abs(areaAt) > abs(areaCt):
     #           areaCt=self.getArea()-areaAt
     #       else:
     #           areaAt=self.getArea()-areaCt

        return areaCt, areaAt


    def copy(self):
        f=face()
        f.fromClosedCurve(self.curve.copy())
        return f



class prismoide(figure):

    def __init__(self):
        self.volume=0
        self.faces=[]
        self.lastIndex=-1
        self.wasInitialized=False
        super(prismoide, self).__init__()

    def getCurve(self, i) -> curve:
        return self.faces[i].curve

    def fromFaces(self, faces, s=None):
        if s is None:
            self.faces=faces
        else:
            z=0
            for fc in faces:
                fc.setPos(point(fc.position.x(), fc.position.y(), z))
                self.faces.append(fc)

                z+=s
        self.wasInitialized=True
        self.update()
        return self

    def addFace(self,f:face,offset=20):
        if self.lastIndex==-1:
            z=0
        else:
            z=self.getLastFace().position.z()+offset
        f=f.copy()
        f.setPos(point(f.position.x(),f.position.y(),z))
        self.faces.append(f)
        self.update()

    def appendFace(self,f):
        f.setPos(point(f.position.x(),f.position.y(),f.position.z()))
        self.faces.append(f)
        self.update()


    def getFace(self, i:int) -> face:
        return self.faces[i]

    def replaceFaceKeepZ(self,f:face,i):
        tmpf=self.getFace(i)
        self.faces[i]=f
        self.faces[i].setPos(point(f.position.x(),f.position.y(),tmpf.z()))

    def replaceFace(self,f:face,i):
        self.faces[i]=f
        self.faces[i].setPos(point(f.position.x(),f.position.y(),f.position.z()))


    def getLastFace(self) -> face:
        return self.faces[-1]

    def getFirstFace(self) -> face:
        return self.faces[0]


    def update(self):
        super(prismoide, self).update()
        self.lastIndex=len(self.faces)-1


    def getVolume(self, i1=0, i2=None):

        if i2 is None:
            i2=len(self.faces)

        self.volume=0
        for i, face in enumerate(self.faces[i1:i2-1]):
            #semisoma
            nextFace=self.faces[i+1]
            self.volume+=(face.getArea()+nextFace.getArea())*abs(face.position.z()-nextFace.position.z())/2
        return self.volume

    def getVolumes(self, i1=0, i2=None):
        if i2 is None:
            i2 = len(self.faces)
        vat = vct = 0
        for i, face in enumerate(self.faces[i1:i2-1]):
            #semisoma
            nextFace = self.faces[i+1]
            nct, nat = nextFace.getAreas()
            ct, at = face.getAreas()
            vct += (ct + nct) * abs(face.position.z() - nextFace.position.z()) / 2
            vat += (at + nat) * abs(face.position.z() - nextFace.position.z()) / 2

        return vct, vat


class square(curve):

    def __init__(self,side=1):
        super(square, self).__init__()
        self.setPoints([pt(-0.5,0.5),pt(.5,.5),pt(.5,-.5),pt(-.5,-.5)])
        self.scale(side)


def plotLine(l:line, color="w"):

    x=[]
    y=[]

    x.append(l.point1.x())
    x.append(l.point2.x())
    y.append(l.point1.y())
    y.append(l.point2.y())
    return x, y

def plotCurve(c:curve, color="w"):

    x=[]
    y=[]

    for pt in c.getPoints():
        x.append(pt.x())
        y.append(pt.y())
    return x, y

def plotPrismoid(pris:prismoide):
    pass

#TESTS:
def test(a, title="Test"):
    from .... import PyQtGraph as pg
    plotWidget=pg.plot(title=title)
    X,Y=a
    cu=pg.PlotCurveItem()
    cu.setData(X,Y)
    plotWidget.addItem(cu)

    pg.mkQApp()
    pg.QAPP.exec_()



def test1():
    p1 = point(-10, -2)
    p2 = point(-5, 3)
    p3 = point(0, 10)
    p4 = point(5, 5)
    p5 = point(10, -10)
    p6 = point(15, 10)
    p7 = point(20, 7)
    p8 = point(25, 1)

    ptList=[p1,p2,p3,p4,p5,p6,p7,p8]
    ptList2=[p1+point(2,-5)]

    for pt in ptList:
        if pt.x()==10:
             ptList2.append(pt.copy().add(0,10))
        else:
            ptList2.append(pt.copy().add(0,5))

    ptList2.append(p8+point(-2,-5))

    l=line(p1,p2)
    l2=line(p2,p3)

    c=curve()
    c.setPoints(ptList)

    c2=curve()
    c2.setPoints(ptList2)

    s=line(point(-5,-5),point(5,5))
    s2=line(point(-5,5),point(6,-5))

    x=curve()
    x.setPoints([point(-1,-1),point(1,-1),point(1,1),point(-1,1),point(-1,-1)])

    f=face()
    f.from2Curves(c,c2)

    w1=c.getLastLine()
    w2=c2.getLastLine()

    c4=f.curve.copy()
    c4.rotate(90, point(0,0))

    ref=line(point(-10,0),point(10,0))

    c3=f.curve.copy()
    c3.mirror(ref)
    c3.setPos(c3.position+point(0,-1))

    plotCurve(f.curve)
    plotCurve(c3)

    l3=line(point(-10,0),point(10,0))

    plotLine(l3)

    l4=l3.copy()
    l4.rotate(90,l3.getMiddlePoint())
    l4=l4.trim(l3)
    plotLine(l4)
    print("A= " + str(f.area))



def test2():
    terreno=[pt(-6,-5),pt(-4,-4),pt(-4,-2),pt(-3,0),pt(-2,2),pt(-1,1),pt(0,3),pt(1,3),pt(2,6),pt(3,8),pt(4,9),pt(5,10),pt(6,15)]
    tc=curve()
    tc.setPoints(terreno)

    l=line(tc.getFirstPoint(), pt(tc.getFirstPoint().x(),tc.getHeight()))
    l2=l.copy()
    l2.setPos(tc.getLastPoint())

    tc.prependPoint(l.point2)
    tc.appendPoint(l2.point2)

    pista=curve()
    pista.setPoints([pt(-7,-20),pt(-3,5),pt(3,5),pt(7,20)])

    f=face()
    f.from2Curves(pista, tc)
    print("A: " + str(f.area))

    #plotCurve(tc)
    #plotCurve(pista)



    prism=prismoide()
    prism.fromFaces([f,f.copy(), f.copy()], 20)
    print("Volume 20m: " + str(prism.getVolume()))

    prism.save("test")

    prism2=prismoide()
    prism2.restore("test")

    print("Volume 20m: " + str(prism2.getVolume()))

    import pyqtgraph as pg
    plotWidget=pg.plot(title="test")

    tc2=tc.copy()
    tc2.position=tc2.getLastPoint()
    tc2.setPos(tc.getFirstPoint())
    tc.prependCurve(tc2)

    X,Y = plotCurve(tc)
    cu=pg.PlotCurveItem()
    cu.setData(X,Y)
    plotWidget.addItem(cu)

    pg.mkQApp()
    pg.QAPP.exec_()





