# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Topo_dialog_perfil.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import numpy as np
import pyqtgraph as pg



try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class closeDialog(QtGui.QDialog):
    save = QtCore.pyqtSignal()
    dischart = QtCore.pyqtSignal()
    cancel = QtCore.pyqtSignal()

    def __init__(self, *args, **kwds):
        super(closeDialog, self).__init__(*args, **kwds)
        self.wasCanceled=False
        self.setupUI()

    def setupUI(self):

        self.setWindowTitle("Fechar")
        label = QtGui.QLabel(u"Deseja salvar suas alterações?")
        btnSave=QtGui.QPushButton(self)       
        btnSave.setText("Sim")
        btnSave.setToolTip("Salvar o perfil vertical desenhado")
        btnSave.clicked.connect(self.__exitSave)


        btnNot=QtGui.QPushButton(self)       
        btnNot.setText(u"Não")
        btnNot.setToolTip(u"Descartar alterações")
        btnNot.clicked.connect(self.__exitNotSave)


        btnCancel=QtGui.QPushButton(self)       
        btnCancel.setText("Cancelar")
        btnCancel.setToolTip("Voltar para Janela de desenho")
        btnCancel.clicked.connect(self.__exitCancel)


        Vlayout=QtGui.QVBoxLayout()
        HLayout=QtGui.QHBoxLayout()

        Vlayout.addWidget(label)
        HLayout.addWidget(btnSave)
        HLayout.addWidget(btnNot)
        HLayout.addWidget(btnCancel)
        Vlayout.addLayout(HLayout)

        self.setLayout(Vlayout)



    def __exitSave(self):
        self.save.emit()
        self.close()
    def __exitNotSave(self):
        self.dischart.emit()
        self.close()
    def __exitCancel(self):
        self.cancel.emit()
        self.close()



class CustomViewBox(pg.ViewBox):
      def __init__(self, *args, **kwds):
          pg.ViewBox.__init__(self, *args, **kwds)
          self.setMouseMode(self.RectMode)
          
      ## reimplement mid-click to zoom out
      def mouseClickEvent(self, ev):
          if ev.button() == QtCore.Qt.MidButton:
              self.autoRange()

      def mouseDragEvent(self, ev):
          if ev.button() == QtCore.Qt.RightButton:
              ev.ignore()
          else:
              pg.ViewBox.mouseDragEvent(self, ev)


class rampaDialog(QtGui.QDialog):
    def __init__(self, roi, segment, pos):
        super(rampaDialog, self).__init__(None)
        self.setWindowTitle(u"Modificar Rampa")
        self.roi=roi
        self.segment=segment
        self.pos=pos
        self.setupUI()



    def setupUI(self):
        r=[]
        for handle in self.roi.getHandles():
            r.append(handle)
        
        self.firstHandle=r[0]
        self.lastHandle=r[len(r)-1]
 
        H1layout=QtGui.QHBoxLayout()
        H2layout=QtGui.QHBoxLayout()
        H3layout=QtGui.QHBoxLayout()
        Vlayout=QtGui.QVBoxLayout(self)

        label=QtGui.QLabel("Modificar Rampa")

        Incl=QtGui.QLineEdit()
        compr=QtGui.QLineEdit()
        cota=QtGui.QLineEdit()
        abscissa=QtGui.QLineEdit()
        InclLbl=QtGui.QLabel(u"Inclinação: ")
        posInclLbl=QtGui.QLabel(u"%")
        comprLbl=QtGui.QLabel(u"Comprimento: ")
        poscomprLbl=QtGui.QLabel(u"m")
        cotaLbl=QtGui.QLabel(u"Cota:      ")
        poscotaLbl=QtGui.QLabel(u"m")
        abscissalbl=QtGui.QLabel(u"Distância Horizontal: ")
        posabscissaLbl=QtGui.QLabel(u"m")

        
        h1 = self.segment.handles[0]['item']
        h2 = self.segment.handles[1]['item']

        self.h1=h1
        self.h2=h2

        self.initialPos=[h1.pos(),h2.pos()]

        b1 = QtGui.QPushButton("ok",self)
        b1.clicked.connect(self.finishDialog)
        b2 = QtGui.QPushButton("cancelar", self)
        b2.clicked.connect(lambda: self.cleanClose())

        H1layout.addWidget(InclLbl)
        H1layout.addWidget(Incl)
        H1layout.addWidget(posInclLbl)
        H1layout.addItem(QtGui.QSpacerItem(80,20,QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        H1layout.addWidget(comprLbl)
        H1layout.addWidget(compr)
        H1layout.addWidget(poscomprLbl)
        H1layout.addItem(QtGui.QSpacerItem(80,20,QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        H2layout.addWidget(cotaLbl)
        H2layout.addWidget(cota)
        H2layout.addWidget(poscotaLbl)
        H2layout.addItem(QtGui.QSpacerItem(80,20,QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        H2layout.addWidget(abscissalbl)
        H2layout.addWidget(abscissa)
        H2layout.addWidget(posabscissaLbl)
        H2layout.addItem(QtGui.QSpacerItem(80,20,QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

        Vlayout.addWidget(label)
        Vlayout.addLayout(H1layout)
        Vlayout.addLayout(H2layout)
        H3layout.addItem(QtGui.QSpacerItem(80,20,QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        H3layout.addWidget(b1)
        H3layout.addWidget(b2)
        Vlayout.addLayout(H3layout)

        self.InclText=Incl       
        self.Incl=100*(h2.pos().y()-h1.pos().y())/(h2.pos().x()-h1.pos().x())
        self.comprText=compr
        self.compr=np.sqrt((h2.pos().y()-h1.pos().y())**2+(h2.pos().x()-h1.pos().x())**2)
        self.cotaText=cota
        self.cota=h2.pos().y()
        self.abscissaText=abscissa
        self.abscissa=h2.pos().x()

        Incl.setValidator(QtGui.QDoubleValidator())
        compr.setValidator(QtGui.QDoubleValidator())
        cota.setValidator(QtGui.QDoubleValidator())
        abscissa.setValidator(QtGui.QDoubleValidator())

        Incl.setText(str(self.Incl))
        compr.setText(str(self.compr))
        cota.setText(str(self.cota))
        abscissa.setText(str(self.abscissa))

        compr.textChanged.connect(self.updateCompr)
        cota.textChanged.connect(self.updateCota)
        abscissa.textChanged.connect(self.updateAbscissa)
        Incl.textChanged.connect(self.updateIncl)

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.isBeingModified=False 


    def updateCompr(self):
        try:
            if not self.isBeingModified:
                c=self.compr
                self.compr=float(self.comprText.text())
                dc=self.compr-c
                self.cota=self.cota+np.sin(np.deg2rad(self.Incl))*dc
                self.abscissa=self.abscissa+np.cos(np.deg2rad(self.Incl))*dc
                self.update()
                self.redefineUI(1)

        except ValueError:
            pass

     
        
    def updateCota(self):
        try:
            if not self.isBeingModified:  
                self.cota=float(self.cotaText.text())
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(2)
        except ValueError:
            pass


    def updateAbscissa(self):
        try:
            if not self.isBeingModified:
                self.abscissa=float(self.abscissaText.text())
                self.update()
                self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)
                self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())
                self.redefineUI(3)
        except ValueError:
            pass


    def updateIncl(self):
        try:
            if not self.isBeingModified:
               self.Incl=float(self.InclText.text())
               self.cota=np.sin(np.deg2rad(self.Incl))*self.compr+self.h1.pos().y()
               self.abscissa=np.cos(np.deg2rad(self.Incl))*self.compr+self.h1.pos().x()
               self.update()
               self.redefineUI(4)
        except ValueError:
            pass

       
    def update(self): 

        self.h2.setPos(self.abscissa, self.cota)


        if self.firstHandle == self.h2:
            self.firstHandle.setPos(self.initialPos[1].x(),self.cota)   
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())   
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)   
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()
            self.cotaText.setText(str(self.cota))
            self.abscissaText.setText(str(self.abscissa))

        if self.lastHandle == self.h2:
            self.lastHandle.setPos(self.initialPos[1].x(),self.cota)
            self.Incl=100*(self.h2.pos().y()-self.h1.pos().y())/(self.h2.pos().x()-self.h1.pos().x())   
            self.compr=np.sqrt((self.h2.pos().y()-self.h1.pos().y())**2+(self.h2.pos().x()-self.h1.pos().x())**2)   
            self.cota=self.h2.pos().y()
            self.abscissa=self.h2.pos().x()
            self.cotaText.setText(str(self.cota))
            self.abscissaText.setText(str(self.abscissa))

    
    def redefineUI(self, elm):
        self.isBeingModified=True

        if elm==1:       
            self.cotaText.setText(str(self.cota))
            self.abscissaText.setText(str(self.abscissa))
            self.InclText.setText(str(self.Incl))
        elif elm==2:
            self.comprText.setText(str(self.compr))
            self.abscissaText.setText(str(self.abscissa))
            self.InclText.setText(str(self.Incl))
        elif elm==3:           
            self.comprText.setText(str(self.compr))
            self.cotaText.setText(str(self.cota))     
            self.InclText.setText(str(self.Incl))
        elif elm==4:           
            self.comprText.setText(str(self.compr))
            self.cotaText.setText(str(self.cota))
            self.abscissaText.setText(str(self.abscissa))
           

        self.isBeingModified=False


    def finishDialog(self):
        self.close()
    
    def cleanClose(self):
        self.h2.setPos(self.initialPos[1].x(),self.initialPos[1].y())
        self.close()



class CustomPolyLineROI(pg.PolyLineROI):
    wasModified=QtCore.pyqtSignal()

    def __init__(self, *args, **kwds):
        pg.PolyLineROI.__init__(self,*args,**kwds)


    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            ev.accept()
            self.cancelMove()

        self.wasModified.emit()
        ev.accept()
        self.sigClicked.emit(self, ev)

    def setPoints(self, points, closed=None):

        if closed is not None:
            self.closed = closed
        
        self.clearPoints()


        for p in points:
            self.addRotateHandle(p,p)
                      
        start = -1 if self.closed else 0

        for i in range(start, len(self.handles)-1):
            self.addSegment(self.handles[i]['item'], self.handles[i+1]['item']) 
        



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


   
class Ui_Perfil(QtGui.QDialog):
    
    save = QtCore.pyqtSignal()

    def __init__(self, ref_estaca, tipo, classeProjeto, greide):
        super(Ui_Perfil, self).__init__(None)

        self.ref_estaca = ref_estaca
        self.tipo = tipo
        self.classeProjeto = classeProjeto
        self.estaca1txt = -1
        self.estaca2txt = -1
        self.greide=greide
        self.vb=CustomViewBox() 
        self.perfilPlot = pg.PlotWidget(viewBox=self.vb,  enableMenu=False, title="Perfil Longitudinal")
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
               # self.comboEstaca1.addItem(_fromUtf8(e))
            except:
                break
            k += 1
       
        x,y=zip(*pontos)
        x=list(x)
        y=list(y)       
                
        self.perfilPlot.plot(x=x, y=y, symbol='o')

        self.perfilPlot.setWindowTitle('Perfil Vertical')

        A = np.array([x,np.ones(len(x))])
        w = np.linalg.lstsq(A.T,y)[0]
        self.roi = CustomPolyLineROI([(x[0],w[0]*x[0]+w[1]), (x[len(x)-1],w[0]*x[len(x)-1]+w[1])])
        self.roi.wasModified.connect(self.__setAsNotSaved)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.perfilPlot.addItem(self.roi)

        if self.greide:
           # i=0
            lastHandleIndex=len(self.greide)-1
            
            for pt in self.greide:
                x=pt[0]
                cota=pt[1]
                pos=(x,cota)

              #  if i==0:
              #      self.

                h1 = self.roi.segments[0].handles[0]['item']
                h2 = self.roi.segments[0].handles[1]['item']
                i = self.roi.segments.index(self.roi.segments[0])
                h3 = self.roi.addFreeHandle(pos, index=self.roi.indexOfHandle(h2))
                self.roi.addSegment(h3, h2, index=i+1)
                self.roi.segments[0].replaceHandle(h2, h3)

              #  i=i+1
             
        self.lastGreide=self.getVertices()

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
         #           self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(51,153,255))

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
 #                   self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,253,150))
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
#                    self.ref_estaca.tableWidget.item(k, j).setBackground(QtGui.QColor(255,51,51))


    def estaca1(self,ind):
        self.estaca1txt = ind-1

    def estaca2(self,ind):
        self.estaca2txt = ind-1

    def setupUi(self, PerfilTrecho):

    
        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(590, 169)
  
        self.perfil_grafico()

        self.lblTipo = QtGui.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtGui.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.calcularGreide)
        
        self.btnAutoRange=QtGui.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Auto")
        self.btnAutoRange.clicked.connect(lambda: self.vb.autoRange())

        self.btnSave=QtGui.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Salvar")
        self.btnSave.clicked.connect(self.salvarPerfil)

        self.btnCancel=QtGui.QPushButton(PerfilTrecho)
        self.btnCancel.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCancel.setText("Fechar")
        self.btnCancel.clicked.connect(self.close)

        Hlayout=QtGui.QHBoxLayout()
        Vlayout=QtGui.QVBoxLayout()

        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)
        
        Hlayout.addWidget(self.btnCalcular)
        Hlayout.addWidget(self.btnAutoRange) 
        Hlayout.addWidget(self.btnSave)
        Hlayout.addWidget(self.btnCancel)
        Vlayout.addLayout(Hlayout)
        Vlayout.addWidget(self.lblTipo)
        Vlayout.addWidget(self.perfilPlot)

        self.showMaximized()
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
        self.lblTipo.setText("Salvo!")


    def getVertices(self):

        r=[]
        for handle in self.roi.getHandles():
           x=[]
           x.append(str(handle.pos().x())) 
           x.append(str(handle.pos().y())) 
           r.append(x)
        
        return r

    def wasSaved(self):
        if(self.lastGreide==self.getVertices()):
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




