from __future__ import absolute_import
from builtins import zip
from builtins import str
from builtins import range

# -*- coding: utf-8 -*-


from qgis.PyQt import QtCore, QtWidgets, QtGui
import numpy as np

from ... import PyQtGraph as pg
from ..view.estacas import cvEdit, closeDialog, rampaDialog, QgsMessageLog
import functools
from copy import deepcopy


##############################################################################################################
#TODO:
#Corrigir bugs: reposicionamento dos handles quando outro é arrastado, 
#limpar curva vertical quando outra é criada por cima (handle.curve) ou quando handle é exluído
#reposicionar curvas verticais e replotar quando segmentos ou handles são movidos
#checar se as curvas são possíveis
#Features to  add
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

        if i>=roi.countHandles()-1 or i==0 :
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

    def __init__(self, *args, **kwds):
        self.wasInitialized=False
        pg.PolyLineROI.__init__(self,*args,**kwds)

    def setPlotWidget(self, plotWidget):
        self.plotWidget=plotWidget

    def HandleEditDialog(self, i):
        dialog=cvEditDialog(self, i)
        dialog.exec_()


    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()

        self.wasModified.emit()
        ev.accept()
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


    def updateHandles(self):

        if self.wasInitialized:
            for i in range(0, len(self.handles)-1):
    
                try:
                    self.handles[i]['item'].sigEditRequest.disconnect()
                except:
                    pass

            QgsMessageLog.logMessage("Atualiando Vertices", "Topografia", level=0)
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

        elif ev.button() == QtCore.Qt.LeftButton:
            h1 = segment.handles[0]['item']
            h2 = segment.handles[1]['item']
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i+1)
            segment.replaceHandle(h2, h3)
            self.wasModified.emit()

    def getHandlePos(self, i):
       
        return self.handles[i]['item'].pos()
       


                

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

    def __init__(self, ref_estaca, tipo, classeProjeto, greide, cvList):
        super(Ui_Perfil, self).__init__(None)

        self.ref_estaca = ref_estaca
        self.tipo = tipo
        self.classeProjeto = classeProjeto
        self.estaca1txt = -1
        self.estaca2txt = -1
        self.greide=greide
        self.cvList=cvList
        self.vb=CustomViewBox() 
        self.perfilPlot = pg.PlotWidget(viewBox=self.vb,  enableMenu=False, title="Perfil Longitudinal")
        self.perfilPlot.curves=[]
        self.saved=False 
        self.setupUi(self)

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




class Ui_sessaoTipo(Ui_Perfil):
    def __init__(self, iface):
        super(Ui_sessaoTipo, self).__init__(iface, 0, 0, [[0,0],[5,0],[5,2], [12,2], [12,0], [17,0]], [0])

    def perfil_grafico(self):


        self.perfilPlot.setWindowTitle('Sessao Tipo')

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


    def setAsNotSaved(self):
        self.lblTipo.setText("Modificado")
        self.saved=False


    def calcularGreide(self):
        pass
