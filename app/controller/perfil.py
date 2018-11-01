from __future__ import absolute_import
from builtins import zip
from builtins import str
from builtins import range

# -*- coding: utf-8 -*-


from qgis.PyQt import QtCore, QtWidgets, QtGui
import numpy as np

from ..model.utils import *
from ... import PyQtGraph as pg
from ..view.estacas import cvEdit, closeDialog, rampaDialog, QgsMessageLog, ApplyTransDialog, SetCtAtiDialog
import functools
from copy import deepcopy


##############################################################################################################
#TODO:
#Corrigir bugs: reposicionamento dos handles quando outro é arrastado, 
#limpar curva vertical quando outra é criada por cima (handle.curve) ou quando handle é exluído
#reposicionar curvas verticais e replotar quando segmentos ou handles são movidos
#checar se as curvas são possíveis
#Features to  ADD
#Zoom button no menu de curva vertical
#Cálculo de aterro imbutido 
#ctrl+Z utility
##############################################################################################################



try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class CustomViewBox(pg.ViewBox):
      def __init__(self, *args, **kwds):
          pg.ViewBox.__init__(self, *args, **kwds)
          self.setMouseMode(self.PanMode)

      ## reimplement mid-click to zoom out
      def mouseClickEvent(self, ev):
          if ev.button() == QtCore.Qt.MidButton:
              self.autoRange()

      def mouseDragEvent(self, ev):
          if ev.button() == QtCore.Qt.LeftButton:
              ev.ignore()
          else:
              pg.ViewBox.mouseDragEvent(self, ev)


class cv():
    
    def __init__(self, i1, i2, L,handlePos, lastHandlePos):

        self.i1=i1
        self.i2=i2
        self.G=(i1-i2)/100
        self.L=L
        self.lastHandlePos=lastHandlePos
        self.handlePos=handlePos
        self.curve=pg.PlotCurveItem()       
        self.update(i1,i2,L,handlePos, lastHandlePos)

    def update(self, i1, i2, L,handlePos, lastHandlePos):
        if L!=0:
            self.i1=i1
            self.i2=i2
            self.G=(i1-i2)/100
            self.L=L

            G=self.G
            i1=self.i1/100
            L=self.L
            xpcv=handlePos.x()-L/2
            ypcv=lastHandlePos.y()+i1*(xpcv-lastHandlePos.x())

            x=[]

            for n in range(0,int(L/20)+1):
                x.append(n*20)        



            x=np.array(x)
            y=(-G/(2*L))*x*x+i1*x+ypcv

          

            x=[]
            for n in range(0,int(L/20)+1):
                x.append(n*20+xpcv)        


            self.xpcv=xpcv
            self.ypcv=ypcv
            self.xptv=xpcv+L
            self.yptv=self.getCota(self.xptv)
            self.x=x
            self.y=y
            
            self.curve.clear()


            self.curve.setData(x,y,pen=pg.mkPen('r', width=3, style=QtCore.Qt.DashLine))


        else:
            self.L=0

    
    def getCota(self, x):
        return False if x < self.xpcv or x > self.xptv else (-self.G/(2*self.L))*(x-self.xpcv)**2+self.i1*(x-self.xpcv)/100+self.ypcv



class cvEditDialog(QtWidgets.QDialog):
    

    
    def __init__(self,roi, i):
        super(cvEditDialog, self).__init__(None)
        self.setWindowTitle(u"Modificar Rampa")
        self.ui = cvEdit()
        self.ui.setupUi(self)
        self.isBeingModified=False 
        self.i=i
        self.initialHandlesPos = []
        self.i1=0
        self.i2=0
        self.G=0
        self.L=0


        self.roi=roi
        self.cota=self.getHandlePos(i).y()
        self.horizontal=self.getHandlePos(i).x()
        self.redefineUI(-10) 
        self.updateCota()
        self.ui.cota.textChanged.connect(self.updateCota)
        self.ui.horizontal.textChanged.connect(self.updateAbscissa)
        self.ui.i1.setReadOnly(True)
        self.ui.i2.setReadOnly(True)
        self.ui.G.setReadOnly(True)

        self.ui.buttonBox.accepted.connect(self.save)
        self.ui.buttonBox.rejected.connect(self.reset)

        for j in range(0,roi.countHandles()):
            self.initialHandlesPos.append(self.getHandlePos(j))

        self.handle=self.roi.handles[i]['item']

        try:
            self.ui.L.setText(str(self.handle.curve.L))
        except AttributeError:
            self.handle.curve = cv(self.i1, self.i2, 0, self.handle.pos, self.getHandlePos(i-1))
            self.ui.L.setText(str(self.handle.curve.L))

        self.initialCurve = cv(self.handle.curve.i1,self.handle.curve.i2, self.handle.curve.L, self.handle.curve.handlePos, self.handle.curve.lastHandlePos)


        self.ui.groupBox.setTitle("Vertice: " + str(i+1))

        self.ui.L.textChanged.connect(self.updateL)

        self.show()

    def save(self):
         
        pass


    def reset(self):
        j=0
        for pos in self.initialHandlesPos:
            self.roi.handles[j]["item"].setPos(pos)
            j+=1
        self.handle.curve.curve.clear();               
        self.handle.curve=self.initialCurve
        self.ui.L.setText(str(self.handle.curve.L))
      
        self.roi.plotWidget.addItem(self.handle.curve.curve)
       

    def getHandlePos(self, i):
       
        return self.roi.handles[i]['item'].pos()
       


                

    def getSegIncl(self, i, j):
        try:
            return round(100*(self.getHandlePos(j).y()-self.getHandlePos(i).y())/(self.getHandlePos(j).x()-self.getHandlePos(i).x()), 4)
        except IndexError:
            return None


 


    def updateCota(self):
        try:
            if not self.isBeingModified:  
                self.cota=float(self.ui.cota.text())
                self.update()
                self.redefineUI(3)        
               
           
        except ValueError:
            pass


    def updateAbscissa(self):
        try:
            if not self.isBeingModified:
                self.horizontal=float(self.ui.horizontal.text())
                self.update()
                self.redefineUI(4)
           
           
        except ValueError:
            pass


    def updateL(self):
        try:
            if not self.isBeingModified:  
                self.L=float(self.ui.L.text())
                self.handle.curve.update(self.i1, self.i2, self.L,self.getHandlePos(self.i), self.getHandlePos(self.i-1))
                self.roi.plotWidget.addItem(self.handle.curve.curve)

           
        except ValueError:
            pass



    def update(self): 

        self.roi.handles[self.i]["item"].setPos(self.horizontal, self.cota)
      

        
    def redefineUI(self, elm):
        self.isBeingModified=True
        i=self.i
        roi=self.roi
        

        updateList=[(self.ui.i1, self.i1), (self.ui.i2,self.i2), (self.ui.G,self.G), (self.ui.cota,self.cota), (self.ui.horizontal, self.horizontal)]

        if i>=roi.countHandles()-1 or i==0:
            self.ui.removeCv()
        else:
            self.i1=self.getSegIncl(i-1,i)
            self.i2=self.getSegIncl(i,i+1)
            self.G=self.i1-self.i2
            
        c=0
        for a,x in updateList:
            c+=1
            try:
                if c-1==elm:
                    continue
                else:
                    a.setText(str(round(x,2)))       
            except:
                continue
        self.updateL()

        self.isBeingModified=False



class CustomPolyLineROI(pg.PolyLineROI):
    wasModified=QtCore.pyqtSignal()
    modified=QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwds):
        self.wasInitialized=False
        pg.PolyLineROI.__init__(self,*args,**kwds)

    def setPlotWidget(self, plotWidget):
        self.plotWidget = plotWidget

    def HandleEditDialog(self, i):
        dialog=cvEditDialog(self, i)
        dialog.exec_()
        self.sigRegionChangeFinished.emit(self)
        self.modified.emit(self)


    def mouseClickEvent(self, ev):

        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.modified.emit(self)
            ev.accept()
            self.cancelMove()

        self.wasModified.emit()
        ev.accept()
        self.modified.emit(self)
        self.sigClicked.emit(self, ev)

    def setPoints(self, points, closed=None):
        self.wasInitialized=False   
        QgsMessageLog.logMessage("Iniciando pontos", "Topografia", level=0)
        if closed is not None:
            self.closed = closed
        
        self.clearPoints()


        for p in points:
            self.addRotateHandle(p,p)
                      
        start = -1 if self.closed else 0

        self.handles[0]['item'].sigEditRequest.connect(lambda: self.HandleEditDialog(0))

        for i in range(start, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item'])
            j=i+1
            self.handles[j]['item'].sigEditRequest.connect(functools.partial(self.HandleEditDialog, j))

        self.wasInitialized=True
        self.updateHandles()


    def updateHandles(self):

        if self.wasInitialized:
            for i in range(0, len(self.handles)-1):
    
                try:
                    self.handles[i]['item'].sigEditRequest.disconnect()
                except:
                    pass


            self.handles[0]['item'].sigEditRequest.connect(lambda: self.HandleEditDialog(0))
            start = -1 if self.closed else 0

            for i in range(start, len(self.handles)-1):
                j=i+1
                self.handles[j]['item'].sigEditRequest.connect(functools.partial(self.HandleEditDialog, j))


            self.wasInitialized=True

    def addHandle(self, info, index=None):
        h = pg.ROI.addHandle(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)        
        self.stateChanged(finish=True)
        QgsMessageLog.logMessage("Adicionando Vertice", "Topografia", level=0)
        self.wasInitialized=True
        self.updateHandles()

        return h
 


    def countHandles(self):
       return len(self.handles)


    def segmentClicked(self, segment, ev=None, pos=None): ## pos should be in this item's coordinate system
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        if ev.button() == QtCore.Qt.RightButton:
            d = rampaDialog(self, segment, pos)
            d.exec_()
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

        elif ev.button() == QtCore.Qt.LeftButton:
            h1 = segment.handles[0]['item']
            h2 = segment.handles[1]['item']
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i+1)
            segment.replaceHandle(h2, h3)
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)


    def getHandlePos(self, i):
        return self.handles[i]['item'].pos()


    def getVerticesList(self):
        l=[]
        for i in range(0,len(self.handles)):
            p=self.getHandlePos(i)
            l.append([p.x(),p.y()])

        return l

       
    def getYfromX(self,x):
        for i in range(0,self.countHandles()-2):
            h=self.handles[i]["item"].pos()
            nh=self.handles[1+i]["item"].pos()
            if h.x() <= x and nh.x() >= x:
                return (nh.y()-h.y())/(nh.x()-h.x())*(x-h.x())+h.y()
        raise ValueError



    def getSegIncl(self, i, j):
        try:
            return round(100*(self.getHandlePos(j).y()-self.getHandlePos(i).y())/(self.getHandlePos(j).x()-self.getHandlePos(i).x()), 4)
        except IndexError:
            return None





    def addCvs(self, cvList):

        if(cvList==False or len(cvList)<=2):
            
            for i in range(0, len(self.handles)-1):

                    i1=self.getSegIncl(i-1,i)
                    i2=self.getSegIncl(i,i+1)
                    L=0
                    self.handles[i]['item'].curve=cv(i1, i2, L,self.getHandlePos(i), self.getHandlePos(i-1))
                    self.plotWidget.addItem(self.handles[i]['item'].curve.curve)

            
            return
       
        
        for i in range(0, len(self.handles)-1):
            if  cvList[i][1]!="None":
                i1=self.getSegIncl(i-1,i)
                i2=self.getSegIncl(i,i+1)
                L=float(cvList[i][1])
                self.handles[i]['item'].curve=cv(i1, i2, L,self.getHandlePos(i), self.getHandlePos(i-1))
                self.plotWidget.addItem(self.handles[i]['item'].curve.curve)
            else:
 
                i1=self.getSegIncl(i-1,i)
                i2=self.getSegIncl(i,i+1)
                L=0
                self.handles[i]['item'].curve=cv(i1, i2, L,self.getHandlePos(i), self.getHandlePos(i-1))
                self.plotWidget.addItem(self.handles[i]['item'].curve.curve)
                



   
   
class Ui_Perfil(QtWidgets.QDialog):
    
    save = QtCore.pyqtSignal()

    def __init__(self, ref_estaca, tipo, classeProjeto, greide, cvList, wintitle="Perfil Longitudinal"):
        super(Ui_Perfil, self).__init__(None)
        self.initVars(ref_estaca, tipo, classeProjeto, greide, cvList, wintitle)
        self.setupUi(self)

    def initVars(self, ref_estaca, tipo, classeProjeto, greide, cvList, wintitle):

        self.everPloted=False
        self.ref_estaca = ref_estaca
        self.tipo = tipo
        self.classeProjeto = classeProjeto
        self.estaca1txt = -1
        self.estaca2txt = -1
        self.greide=greide
        self.cvList=cvList
        self.vb=CustomViewBox()
        self.perfilPlot = pg.PlotWidget(viewBox=self.vb,  enableMenu=False, title=wintitle)
        self.perfilPlot.curves=[]
        self.saved=False



    def __setAsNotSaved(self):
        self.lblTipo.setText("Modificado")
        self.saved=False


    def perfil_grafico(self):

        pontos = []
        k = 0
        while True:
            try:
                ponto = []
                e = self.ref_estaca.tableWidget.item(k,0).text()
                if e in [None,""]:
                    break
                ponto.append(float(self.ref_estaca.tableWidget.item(k,2).text()))
                ponto.append(float(self.ref_estaca.tableWidget.item(k,5).text()))
                pontos.append(ponto)
                #self.comboEstaca1.addItem(_fromUtf8(e))
            except:
                break
            k += 1
       
        x,y=list(zip(*pontos))
        x=list(x)
        y=list(y)       
                
        self.perfilPlot.plot(x=x, y=y, symbol='o')

        self.perfilPlot.setWindowTitle('Perfil Vertical')

        A = np.array([x,np.ones(len(x))])
        w = np.linalg.lstsq(A.T,y)[0]
        if self.greide:
           # i=0
            lastHandleIndex=len(self.greide)-1
            L=[]            
            for pt in self.greide:
                x=pt[0]
                cota=pt[1]
                pos=(x,cota)
                L.append(pos)
            self.roi = CustomPolyLineROI(L)


        else:
            self.roi = CustomPolyLineROI([(x[0],w[0]*x[0]+w[1]), (x[len(x)-1],w[0]*x[len(x)-1]+w[1])])

        self.roi.wasModified.connect(self.__setAsNotSaved)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.perfilPlot.addItem(self.roi)


        self.lastGreide=self.getVertices()
        self.lastCurvas=self.getCurvas()
        self.roi.setPlotWidget(self.perfilPlot)
        self.roi.addCvs(self.cvList)

        self.roi.sigRegionChangeFinished.connect(self.modifiedRoi)
        self.roi.sigRegionChanged.connect(self.modifiedRoiStarted)
        
       # self.perfilPlot.plot(y,x)

    def calcularGreide(self):
        self.roi.getMenu()
        I=[] 
        handles=self.roi.getHandles()
        for i in range(0,len(self.roi.getHandles())-1):
                g1=[]
                g2=[]
                handle=handles[i]
                nextHandle=handles[i+1]
                g1.append(handle.pos().x())
                g1.append(handle.pos().y())
                g2.append(nextHandle.pos().x())
                g2.append(nextHandle.pos().y())
                p1 =abs((g1[1] - g2[1]) / (g1[0] - g2[0])) * 100
                I.append(p1)
        A=[]
        for x in I:
            A.append(x)
        A.sort()
        p1=A[len(I)-1]
        maxIndex=I.index(p1)+1
        classeProjeto = self.classeProjeto
        if p1>=float(self.tipo[0]) and p1<float(self.tipo[1]):
            if classeProjeto<=0:
                s = "120"
            elif classeProjeto <4:
                s = "100"
            elif classeProjeto <6:
                s = "80"
            else:
                s = "60"
            self.lblTipo.setText(u"Plano %s KM/h, Rampa n° %d"%(s,maxIndex))
         #   for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
         #       for j in range(self.ref_estaca.tableWidget.columnCount()):
         #           self.ref_estaca.tableWidget.item(k, j).setBackground(QtWidgets.QColor(51,153,255))

        elif p1>=float(self.tipo[2]) and p1<float(self.tipo[3]):
            if classeProjeto<=0:
                s = "100"
            elif classeProjeto <3:
                s = "80"
            elif classeProjeto <4:
                s = "70"
            elif classeProjeto <6:
                s = "60"
            else:
                s = "40"
            self.lblTipo.setText(u"Ondulado %s KM/h, Rampa n° %d"%(s, maxIndex))
 #           for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
 #               for j in range(self.ref_estaca.tableWidget.columnCount()):
 #                   self.ref_estaca.tableWidget.item(k, j).setBackground(QtWidgets.QColor(255,253,150))
        else:
            if classeProjeto<=0:
                s = "80"
            elif classeProjeto <3:
                s = "60"
            elif classeProjeto <4:
                s = "50"
            elif classeProjeto <6:
                s = "40"
            else:
                s = "30"
            self.lblTipo.setText("Montanhoso %s KM/h, Rampa n° %d"%(s, maxIndex))
 #           for k in range(int(self.estaca1txt),int(self.estaca2txt)+1):
#                for j in range(self.ref_estaca.tableWidget.columnCount()):
#                    self.ref_estaca.tableWidget.item(k, j).setBackground(QtWidgets.QColor(255,51,51))


        for a in A:
            maxIndex=I.index(a)+1
            if a==p1:
                self.maxInclinationIndicatorLine=pg.PlotCurveItem()
                self.maxInclinationIndicatorLine.setData([self.roi.getHandlePos(maxIndex-1).x(),self.roi.getHandlePos(maxIndex).x()],[self.roi.getHandlePos(maxIndex-1).y(), self.roi.getHandlePos(maxIndex).y()], pen=pg.mkPen("r", width=4))
                self.perfilPlot.addItem(self.maxInclinationIndicatorLine)

    def modifiedRoiStarted(self):

        for h in self.roi.getHandles():
            h.curve.update(self.i1, self.i2, self.L,self.getHandlePos(self.i), self.getHandlePos(self.i-1))
            self.roi.plotWidget.addItem(h.curve.curve)


        try:
            self.maxInclinationIndicatorLine.clear()
        except:
            pass


    def modifiedRoi(self):
        self.modifiedRoiStarted()
        pass

    def estaca1(self,ind):
        self.estaca1txt = ind-1

    def estaca2(self,ind):
        self.estaca2txt = ind-1

    def setupUi(self, PerfilTrecho):

    
        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(590, 169)
  
        self.perfil_grafico()

        self.lblTipo = QtWidgets.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.calcularGreide)
        
        self.btnAutoRange=QtWidgets.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Zoom")
        self.btnAutoRange.clicked.connect(lambda: self.vb.autoRange())


        self.btnSave=QtWidgets.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Salvar")
        self.btnSave.clicked.connect(self.salvarPerfil)

        self.btnCancel=QtWidgets.QPushButton(PerfilTrecho)
        self.btnCancel.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCancel.setText("Fechar")
        self.btnCancel.clicked.connect(self.close)

        Hlayout=QtWidgets.QHBoxLayout()
        Vlayout=QtWidgets.QVBoxLayout()

        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)
        
        Hlayout.addWidget(self.btnCalcular)
        Hlayout.addWidget(self.btnAutoRange) 
        Hlayout.addWidget(self.btnSave)
        Hlayout.addWidget(self.btnCancel)
        Vlayout.addLayout(Hlayout)
        Vlayout.addWidget(self.lblTipo)
        Vlayout.addWidget(self.perfilPlot)

       
        self.setLayout(Vlayout)          


        PerfilTrecho.setWindowTitle(_translate("PerfilTrecho", "Perfil do trecho", None))
        self.calcularGreide()
        self.btnCalcular.setText("Calcular")
        


    def salvarPerfil(self):
        '''exportar greide para o banco de dados
        sinal emitido para salvar'''
    
        self.save.emit()        
        self.saved=True
        self.lastGreide=self.getVertices()
        self.lastCurvas=self.getCurvas()
        self.lblTipo.setText("Salvo!")
    
    def getCurvas(self):

        r=[]        
        for i in range(0,self.roi.countHandles()):
            x=[]
            x.append(i)
            try:
                x.append(str(self.roi.handles[i]["item"].curve.L))

            except:
                x.append(str(None))
            r.append(x)
        
        return r

    def getVertices(self):

        r=[]
        for handle in self.roi.getHandles():
           x=[]
           x.append(str(handle.pos().x())) 
           x.append(str(handle.pos().y())) 
           r.append(x)
        
        return r

    def wasSaved(self):
        if(self.lastGreide==self.getVertices() and self.lastCurvas==self.getCurvas()):
            return True
        else:
            return False
                

    def closeEvent(self, event):

        if (not self.wasSaved()):
           
            closedialog = closeDialog(self)
            closedialog.setModal(True)

            closedialog.save.connect(self.__exitSave)
            closedialog.cancel.connect(event.ignore)
            closedialog.dischart.connect(self.close)

            closedialog.exec_()
    
        else:
            event.accept()
            super(Ui_Perfil, self).closeEvent(event)

    def __exitSave(self):
        self.salvarPerfil()
        self.close()








from .Geometria import Figure, Prismoide


class Ui_sessaoTipo(Ui_Perfil):

    save = QtCore.pyqtSignal()
    plotar = QtCore.pyqtSignal(int)

    def __init__(self, iface, terreno, hor, ver=[], st=False, prism=None, estacanum=0, greide=[]):

        self.progressiva=[]
        self.terreno=[]
        self.iface=iface
        self.editMode=True


        if not st:
            msgLog("Creating new terrain")
            st=[]
            self.terreno=terreno
            ptList=[]
            for item in greide:
                ptList.append(Figure.point(item[0],item[1]))
            greide=Figure.curve()
            greide.setPoints(ptList)

            for item in hor:
                self.progressiva.append(float(item[2]))
                defaultST=[[-9.8,-5.0],[-8.3,-5.0],[-7.3,0], [0,0.14], [7,0], [7.08,-0.1],[7.12,-0.1], [7.2,0], [7.3,0], [8.3,5], [9.8,5]]
                newST=[]
                for pt in defaultST:
                   newST.append([pt[0],pt[1]+greide.getY(float(item[2]))])
                st.append(newST)

            self.st=st

        else:
            msgLog("Using existing terrain")
            self.terreno=terreno
            self.progressiva=ver
            self.st=st

        self.current=estacanum

        super(Ui_sessaoTipo, self).__init__(iface, 0, 0, st[self.current], [], "Perfil Transversal")

        if prism is None:
            try:
                self.prismoide
            except AttributeError:
                self.prismoide = Prismoide.QPrismoid(self.terreno, self.st, self.progressiva)
                self.createPrismoid(self.current)
        else:
            self.prismoide=Prismoide(prism=prism, cti=7)

        self.setFixedSize(1000, 600)
        self.roi.sigRegionChangeFinished.connect(self.updateData)

        self.updateAreaLabels()


    def createPrismoid(self, j):
        self.prismoide.generate(j)
        self.updateAreaLabels()


    def createLabels(self):
        self.banquetaLbC=pg.TextItem(text="Banqueta em aterro", color=(200,200,200), anchor=(.5,0))
        self.taludeLbC=pg.TextItem(text="Talude de aterro", anchor=(.5,0))
        self.pistaLb=pg.TextItem(text="Pista", anchor=(.5,0))
        self.banquetaLbA=pg.TextItem(text="Banqueta em corte", color=(200,200,200), anchor=(.5,0))
        self.taludeLbA=pg.TextItem(text="Talude de corte", anchor=(.5,0))


    def perfil_grafico(self):
        self.perfilPlot.setWindowTitle('Sessao Tipo')
        self.createLabels()

        if self.greide:
            lastHandleIndex=len(self.greide)-1
            L=[]
            for pt in self.greide:
                x=pt[0]
                cota=pt[1]
                pos=(x,cota)
                L.append(pos)

            self.roi = CustomPolyLineROI(L)
            self.roi.wasModified.connect(self.setAsNotSaved)
            self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
            self.perfilPlot.addItem(self.roi)


        self.lastGreide=self.getVertices()
        self.lastCurvas=self.getCurvas()
        self.roi.setPlotWidget(self.perfilPlot)

        X=[]
        Y=[]
        for x, y in self.terreno[self.current]:
            X.append(x)
            Y.append(y)

        self.perfilPlot.plot(X,Y)

        self.updateLabels()


    def updateLabels(self):

        self.banquetaLbC.setPos(self.roi.getHandlePos(0).x(), self.roi.getHandlePos(0).y())
        self.taludeLbC.setPos((self.roi.getHandlePos(2).x()+self.roi.getHandlePos(1).x())/2, (self.roi.getHandlePos(1).y()+self.roi.getHandlePos(2).y())/2)
        middle=self.st[self.current][int(len(self.st[self.current])/2)][1]
        self.pistaLb.setPos(0, middle)
        self.banquetaLbA.setPos(self.roi.getHandlePos(len(self.roi.handles)-1).x(), self.roi.getHandlePos(len(self.roi.handles)-1).y())
        self.taludeLbA.setPos((self.roi.getHandlePos(len(self.roi.handles)-3).x()+self.roi.getHandlePos(len(self.roi.handles)-2).x())/2, (self.roi.getHandlePos(len(self.roi.handles)-3).y()+self.roi.getHandlePos(len(self.roi.handles)-2).y())/2)

        self.perfilPlot.removeItem(self.banquetaLbA)
        self.perfilPlot.removeItem(self.taludeLbA)
        self.perfilPlot.removeItem(self.banquetaLbC)
        self.perfilPlot.removeItem(self.taludeLbC)
        self.perfilPlot.removeItem(self.pistaLb)

        self.perfilPlot.addItem(self.banquetaLbA)
        self.perfilPlot.addItem(self.taludeLbA)
        self.perfilPlot.addItem(self.banquetaLbC)
        self.perfilPlot.addItem(self.taludeLbC)
        self.perfilPlot.addItem(self.pistaLb)


    def updateData(self):
        self.updateLabels()
        if not self.editMode:
            self.plotTransCurve()

#        if self.editMode:
        vt=self.getVertices()
        self.st[self.current]=vt
        self.prismoide.st=self.st
        self.createPrismoid(self.current)

        self.perfilPlot.scale(1,1)


    def getMatrixVertices(self):

        r=[]
        r.append([])
        r.append([])

        for i,_ in enumerate(self.progressiva):
            r[1].append(self.terreno[i])
            r[0].append(self.st[i])

        return r

    def getTerrenoVertices(self):
        return self.terreno

    def getxList(self):
        return self.progressiva


    def setAsNotSaved(self):
        self.lblTipo.setText("Modificado")
        self.saved=False


    def plotTrans(self):

        items=["Plotar transversal atual", "Plotar todas transversais"]
        item, ok = QtWidgets.QInputDialog.getItem(None, "Plotar transversais", u"Escolha uma opção para gerar as linhas:",
                                              items, 0, False)

        if ok:
            if item == items[0]:
                self.plotar.emit(self.current)
            elif item == items[1]:
                self.plotar.emit(-1)



    def calcularGreide(self):
        pass


    def setupUi(self, PerfilTrecho):


        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(680, 320)

        self.perfil_grafico()

        self.lblTipo = QtWidgets.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.plotTrans)

        self.btnAutoRange=QtWidgets.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Zoom")
        self.btnAutoRange.clicked.connect(lambda: self.vb.autoRange())


        self.btnSave=QtWidgets.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Salvar")
        self.btnSave.clicked.connect(self.salvarPerfil)

        self.btnCancel=QtWidgets.QPushButton(PerfilTrecho)
        self.btnCancel.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCancel.setText("Fechar")
        self.btnCancel.clicked.connect(self.close)


        self.btnPrevious=QtWidgets.QPushButton(PerfilTrecho)
        self.btnPrevious.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnPrevious.setText("Anterior")
        self.btnPrevious.clicked.connect(self.previousEstaca)


        self.btnNext=QtWidgets.QPushButton(PerfilTrecho)
        self.btnNext.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnNext.setText("Próxima")
        self.btnNext.clicked.connect(self.nextEstaca)

        self.btnEditToggle=QtWidgets.QPushButton(PerfilTrecho)
        self.btnEditToggle.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnEditToggle.setText("Visualizar")
        self.btnEditToggle.clicked.connect(self.editToggle)


        self.selectEstacaComboBox=QtWidgets.QComboBox(PerfilTrecho)
        self.selectEstacaComboBox.addItems(list(map(str, self.progressiva)))
        self.selectEstacaComboBox.currentIndexChanged.connect(self.changeEstaca)

        self.applyBtn=QtWidgets.QPushButton(PerfilTrecho)
        self.applyBtn.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.applyBtn.setText("Aplicar")
        self.applyBtn.clicked.connect(self.applyTrans)

        self.ctatiBtn=QtWidgets.QPushButton(PerfilTrecho)
        self.ctatiBtn.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.ctatiBtn.setText("Pontos")
        self.ctatiBtn.clicked.connect(self.setAtCti)

        self.areaCtLb=QtWidgets.QLabel(PerfilTrecho)
        self.areaAtLb=QtWidgets.QLabel(PerfilTrecho)
        self.areaLb=QtWidgets.QLabel(PerfilTrecho)
        self.progressivaLb=QtWidgets.QLabel(PerfilTrecho)
        self.volumeTotal=QtWidgets.QLabel(PerfilTrecho)

        self.btnNext.setDisabled(self.current >= len(self.progressiva)-1)
        self.btnPrevious.setDisabled(self.current == 0)
        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)

        self.layAllOut()

        PerfilTrecho.setWindowTitle(_translate("PerfilTrecho", "Perfil do trecho", None))
        self.calcularGreide()
        self.btnCalcular.setText("Plotar")
        self.btnCalcular.setToolTip("Plotar Layers com as tranversais sobre o traçado horizontal")

        self.changingEstaca=False


    def layAllOut(self):

        layout=self.layout()

        if layout is not None:
            index = layout.count()-1
            while (index >= 0):
                element = layout.itemAt(index).widget()
                if element is None:
                    element = layout.itemAt(index).layout()
                if element is not None:
                    element.setParent(None)

                index -= 1

        Hlayout=QtWidgets.QHBoxLayout()
        Hlayout2=QtWidgets.QHBoxLayout()
        Hlayout3=QtWidgets.QHBoxLayout()
        Vlayout=QtWidgets.QVBoxLayout()

        Hlayout.addWidget(self.btnCalcular)
        Hlayout.addWidget(self.applyBtn)
        Hlayout.addWidget(self.btnAutoRange)
        Hlayout.addWidget(self.btnSave)
        Hlayout.addWidget(self.btnCancel)

        Hlayout3.addWidget(self.areaLb)
        Hlayout3.addWidget(self.areaCtLb)
        Hlayout3.addWidget(self.areaAtLb)
        Hlayout3.addWidget(self.volumeTotal)
        Hlayout3.addWidget(self.progressivaLb)

        Hlayout2.addWidget(self.btnEditToggle)
        Hlayout2.addWidget(self.ctatiBtn)
        Hlayout2.addWidget(self.selectEstacaComboBox)
        Hlayout2.addWidget(self.btnPrevious)
        Hlayout2.addWidget(self.btnNext)


        Vlayout.addLayout(Hlayout)
        Vlayout.addLayout(Hlayout3)
        Vlayout.addWidget(self.lblTipo)
        Vlayout.addWidget(self.perfilPlot)
        Vlayout.addLayout(Hlayout2)

        self.setLayout(Vlayout)
        self.Vlayout=Vlayout

    def disableArrowButtons(self, bool):
        self.btnEditToggle.setDisabled(bool)
        self.btnPrevious.setDisabled(bool)
        self.btnNext.setDisabled(bool)
        self.selectEstacaComboBox.setDisabled(bool)


    def nextEstaca(self):
        self.current+=1
        self.changingEstaca=True
        self.reset()

    def previousEstaca(self):
        self.current-=1
        self.changingEstaca=True
        self.reset()


    def editToggle(self):
        if self.editMode:
            self.btnEditToggle.setText(u"Esconder")
            self.plotTransCurve()

        else:
            self.btnEditToggle.setText("Visualizar")
            self.curve.clear()
            self.perfilPlot.removeItem(self.curve)

        self.editMode = not self.editMode

    def changeEstaca(self):

        if not self.changingEstaca:

            self.current = int(self.progressiva.index(float(self.selectEstacaComboBox.currentText())))
            self.reset()


    def reset(self):

        perfilPlot=self.perfilPlot
        self.disableArrowButtons(True)

        self.initVars(self.iface, 0, 0, self.st[self.current], [], "Perfil Transversal")
        self.perfil_grafico()
        self.roi.sigRegionChangeFinished.connect(self.updateData)

        self.btnNext.setDisabled(self.current == len(self.progressiva))
        self.btnPrevious.setDisabled(self.current == 0)
        self.selectEstacaComboBox.setCurrentIndex(self.current)

        self.changingEstaca=False
        self.Vlayout.replaceWidget(perfilPlot, self.perfilPlot)

        self.disableArrowButtons(False)

        if not self.editMode:
            self.plotTransCurve()

        if self.prismoide.lastGeneratedIndex<self.current:
            self.createPrismoid(self.current)

        self.btnNext.setDisabled(self.current >= len(self.progressiva)-1)
        self.btnPrevious.setDisabled(self.current == 0)
        self.updateAreaLabels()

    def updateAreaLabels(self):

        self.areaLb.setText("Area: " + str(round(self.prismoide.getFace(self.current).getArea(),4))+"m²")
        self.progressivaLb.setText("E: " + str(int(self.progressiva[self.current]/20))+" + "+str(round((self.progressiva[self.current]/20-int(self.progressiva[self.current]/20))*20,4)))
        act,aat = self.prismoide.getAreasCtAt(self.current)
        self.areaCtLb.setText("Corte: " + str(round(act,4))+"m²")
        self.areaAtLb.setText("Aterro: " + str(round(aat,4))+"m²")

        if self.prismoide.lastGeneratedIndex>=self.prismoide.lastIndex:
            self.volumeTotal.setText("Volume: " + str(round(self.prismoide.getVolume(),4)) + "m³")

    def plotTransCurve(self):

            if self.everPloted:
                self.curve.clear()
                self.perfilPlot.removeItem(self.curve)

            self.everPloted = True

            self.curve = pg.PlotCurveItem()

            X, Y = Figure.plotCurve(self.prismoide.getCurve(self.current))

            self.curve.clear()
            self.curve.setData(X, Y, pen=pg.mkPen('b', width=4, style=QtCore.Qt.SolidLine))
            self.perfilPlot.addItem(self.curve)


    def applyTrans(self):
        diag=ApplyTransDialog(self.iface,self.progressiva)
        diag.show()
        if diag.exec_()==QtWidgets.QDialog.Accepted:
            st=self.st[self.current]

            for p in diag.progressivas:
                newST=[]
                for pt in st:
                    t=interpolList(self.terreno[self.current],1)
                    tn=interpolList(self.terreno[p],1)
                    newST.append([float(pt[0]),float(pt[1])-float(t)+float(tn)])

                self.st[p]=newST

            self.prismoide.st = self.st
            for p in diag.progressivas:
                self.createPrismoid(p)

    def setAtCti(self):
        diag=SetCtAtiDialog(self.iface, self.roi.getVerticesList())
        diag.show()
        if diag.exec_()==QtWidgets.QDialog.Accepted:
            self.prismoide.ati=diag.ati
            self.prismoide.cti=diag.cti
