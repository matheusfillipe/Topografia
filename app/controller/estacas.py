from __future__ import print_function
# -*- coding: utf-8 -*-
import webbrowser
from copy import deepcopy

from PyQt5.QtCore import QVariant, QFile
from pathlib import Path
from qgis.PyQt import QtGui, QtWidgets

from qgis._gui import QgsMapToolEmitPoint

from ..controller.Geometria.Prismoide import QPrismoid

try:
    from PIL import Image
except:
    from platform import system
    if system() == "Linux":
        from ...PIL import Image
    elif system() == "Windows":
        from ...PILWin import Image

from ..controller.perfil import Ui_Perfil, cv as CV, Ui_sessaoTipo
from ..model.config import Config
from ..model.estacas import Estacas as EstacasModel
from ..model.knn import KNN
from ..model.utils import *
from ..view.estacas import Estacas as EstacasView, EstacasUI, EstacasCv, EstacasIntersec, ProgressDialog, \
    EstacaRangeSelect
from ..view.curvas import Curvas as CurvasView


class Estacas(object):
    def __init__(self, iface):

        self.iface = iface

        self.estacasVerticalList=[]
        self.estacasHorizontalList=[]

        self.model = EstacasModel()
        self.model.iface=iface
        self.preview = EstacasUI(iface)
        self.view = EstacasView(iface, self)
        self.viewCv = EstacasCv(iface)

        self.events()
        self.elemento = -1
        self.click = False
        self.edit = False
        self.points = []

        self.nextView=self.view

    def mudancaCelula(self,item):
        if item.column() > 1:
            campo = float(self.view.tableWidget.item(item.row(), item.column()).text().replace(',','.'))
            self.view.tableWidget.setItem(item.row(), item.column(),QtWidgets.QTableWidgetItem('%s'%campo))

    def linkGoogle(self, item):
        if item.column() == 0:
            este = float(self.view.tableWidget.item(item.row(), 4).text())
            north = float(self.view.tableWidget.item(item.row(), 3).text())
            crs = int(self.model.getCRS())
            point = QgsPointXY(este, north)
            epsg4326 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
            mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
            reprojectgeographic = QgsCoordinateTransform(mycrs, epsg4326, QgsProject.instance())
            pt = reprojectgeographic.transform(point)

            webbrowser.open('https://www.google.com.br/maps/@%f,%f,15z?hl=pt-BR' % (pt.y(), pt.x()))

    def events(self):
        self.preview.tableEstacas:QtWidgets.QTableWidget
        self.preview.btnNovo.clicked.connect(self.new)
        self.preview.btnOpen.clicked.connect(self.openEstaca)
        self.preview.tableEstacas.doubleClicked.connect(self.openEstaca)
        self.preview.btnOpenCSV.clicked.connect(self.openEstacaCSV)
        self.preview.btnApagar.clicked.connect(self.deleteEstaca)
        self.preview.btnGerarTracado.clicked.connect(self.geraTracado)
        self.preview.tableEstacas.itemClicked.connect(self.itemClickTableEstacas)
        self.preview.tableEstacas.itemActivated.connect(self.itemClickTableEstacas)
        self.preview.tableEstacas.itemSelectionChanged.connect(self.itemClickTableEstacas)
        self.preview.btnOpenCv.clicked.connect(self.openCv)
        self.preview.deleted.connect(self.deleteEstaca)
        self.preview.btnDuplicar.clicked.connect(self.duplicarEstaca)
        self.preview.btnGerarCurvas.clicked.connect(self.geraCurvas)

        '''
            ------------------------------------------------
        '''
        self.view.btns=[self.view.btnSave, self.view.btnSaveCSV, self.view.btnLayer, self.view.btnEstacas,
        self.view.btnPerfil, self.view.btnCurva,self.view.btnCotaTIFF, self.view.btnCotaPC, self.view.btnCota]
        for btn in self.view.btns:
            btn.clicked.connect(self.view.clearLayers)

        self.view.btnSave.clicked.connect(self.saveEstacas)
        self.view.btnSaveCSV.clicked.connect(self.saveEstacasCSV)
        self.view.btnLayer.clicked.connect(self.plotar)
        self.view.btnEstacas.clicked.connect(self.recalcular)
        self.view.btnPerfil.clicked.connect(self.perfilView)
        self.view.btnCurva.clicked.connect(self.curva)
        self.view.btnCotaTIFF.clicked.connect(self.obterCotasTIFF)
        self.view.btnCotaPC.clicked.connect(self.obterCotasPC)
        self.view.btnCota.clicked.connect(self.obterCotas)
        self.view.btnCota.hide() #TODO Add google Elevation API ?
        self.view.tableWidget.itemDoubleClicked.connect(self.linkGoogle)
        self.view.tableWidget.itemDoubleClicked.connect(self.mudancaCelula)
        self.view.btnDuplicar.clicked.connect(self.duplicarEstaca)
#        self.view.layerUpdated.connect(self.joinFeatures)

        self.viewCv.btnGen.clicked.connect(self.generateIntersec)
        self.viewCv.btnTrans.clicked.connect(self.generateTrans)
        self.viewCv.btnBruck.clicked.connect(self.bruckner)
        self.viewCv.btnPrint.clicked.connect(self.exportDXF)
        self.viewCv.btnCsv.clicked.connect(self.exportCSV)
        self.viewCv.btnClean.clicked.connect(self.cleanTrans)


    def bruckner(self):
        X, est, prism = self.model.getTrans(self.model.id_filename)
        if X:
            #Database Trans
            self.trans=Ui_sessaoTipo(self.iface, est[1], self.estacasHorizontalList, X, est[0], prism=prism)
        else:
            messageDialog(None,"Erro!", message="A sessão transversal não está definida!")
            return
        prismoide:QPrismoid
        prismoide=self.trans.prismoide

        dialog=EstacaRangeSelect(None, [prog2estacaStr(x) for x in X])
        if not dialog.exec_():
            return

        X=[float(x) for x in X]
        ei=int(dialog.inicial.currentIndex())
        ef=int(dialog.final_2.currentIndex())
        X=X[ei:ef+1]
        V=[]
        vAcumulado=0
        for x in range(1,len(X)+1):
            vAcumulado+=-prismoide.getVolume(ei+x-1,ei+x)
            V.append(vAcumulado)
        V=[v + abs(min(V))+1000 for v in V]
        X=[x/Config.instance().DIST for x in X]

        import matplotlib.pyplot as plt
        line, = plt.plot(X, V, lw=2)
        plt.title("Diagrama de Bruckner")
        plt.xlabel(u'Estacas')
        plt.ylabel(u'Volume m³')
        plt.grid(True)
        plt.show()


    def exportDXF(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(caption="Save dxf",filter="Arquivo DXF (*.dxf)")
        if filename[0] in ["", None]: return
        estacas=self.viewCv.get_estacas()

        Lpoints=[]
        if self.viewCv.mode=="CV":
            points=[]
            for e in estacas:
                points.append(QgsPoint(float(e[-2]), float(e[-1])))
            Lpoints.append(points)

        elif self.viewCv.mode=="T":
            points=[]
            for e in estacas:
                points.append(QgsPoint(float(e[4]), float(e[3]), float(e[-3])))
            Lpoints.append(points)

        self.saveDXF(filename[0], Lpoints)


    def saveDXF(self, filename, listOfListOfPoints):   #[ [ QgsPoint[ x,y], [x,y] ...] , [ [ x,y] , [x,y] ...] ....] Each list is a feature
        layer=QgsVectorLayer("LineStringZ?crs=%s"%(QgsProject.instance().crs().authid()), "Perfil: " if self.viewCv.mode=="CV" else "Traçado Horizontal: "
                                                                                            + self.model.getNameFromId(self.model.id_filename), "memory")
        layer.setCrs(QgsCoordinateReferenceSystem(QgsProject.instance().crs()))
        features=[]
        for points in listOfListOfPoints:
            feat=QgsFeature()
            feat.setGeometry(QgsGeometry.fromPolyline(points))
            features.append(feat)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()

#        QgsProject.instance().addMapLayer(layer)
        dxfExport=QgsDxfExport()
        dxfExport.setMapSettings(self.iface.mapCanvas().mapSettings())
        dxfExport.addLayers([QgsDxfExport.DxfLayer(layer)])
        dxfExport.setSymbologyScale(1)
        dxfExport.setSymbologyExport(QgsDxfExport.SymbolLayerSymbology)
        dxfExport.setLayerTitleAsName(True)
        dxfExport.setDestinationCrs(layer.crs())
        dxfExport.setForce2d(False)
        dxfExport.setExtent(layer.dataProvider().extent())

        error=dxfExport.writeToFile(QFile(filename), "UTF-8")
        if error[0] != QgsVectorFileWriter.NoError:
            msgLog(str(error))
            messageDialog(title="Erro!", message="Não foi possível realizar a conversão para DXF!")


    def exportCSV(self):
        filename = self.view.saveEstacasCSV()
        if filename[0] in ["", None]: return
        estacas = self.viewCv.get_estacas()
        self.model.table = estacas
        if self.viewCv.mode=="CV":
            self.model.saveCSV(filename, noWGS=True)
        else:
            self.model.saveCSV(filename)

    def geraCurvas(self, arquivo_id=None):
        table=self.preview.tableEstacas
        table : QtWidgets.QTableWidget

        if not arquivo_id:
            l=len(table.selectionModel().selectedRows())
        else: #curva para traçado
            self.newEstacasLayer(name=self.model.getNameFromId(arquivo_id))
            self.view.openLayers()
            return

        if l>1:
            self.preview.error(u"Selecione um único arquivo!")
        elif l<1: #criar traçado, iniciar edição
            name=self.fileName("Traçado "+str(len(self.model.listTables())+1))
            if not name: return
            self.new(dados=(name, self.newEstacasLayer(name=name), Config.instance().DIST, []))
        else:
            self.openEstaca()
            self.view.btnCurva.click()

    def joinFeatures(self):
        layer=self.view.curvaLayers[0]
        layer.layerModified.disconnect()
        layer.commitChanges()
        id=[f for f in layer.getFeatures()][-1].id()
        if id>1:
            moveLine(layer,id,getLastPoint(layer, id))
        self.iface.mapCanvas().refresh()
        layer.startEditing()
        layer.layerModified.connect(lambda: self.view.add_row(layer))

#        self.updateTables()

    def fillView(self, table):
        self.estacasHorizontalList=[]
        empty=True
        self.view.clear()
        for item in table:
            self.view.fill_table(tuple(item))
            self.estacasHorizontalList.append(tuple(item))
            empty=False
        self.view.empty=empty
        self.model.save(self.model.id_filename)

    def fileName(self, suggestion=False):
        filename = ""
        names = [self.preview.tableEstacas.item(i, 1).text() for i in range(self.preview.tableEstacas.rowCount())]
        first = True
        while filename == "" or filename in names:
            if not first:
                from ..model.utils import messageDialog
                messageDialog(None, title="Erro", message="Já existe um arquivo com esse nome")

            filename, ok = QtWidgets.QInputDialog.getText(None, "Nome do arquivo", u"Nome do arquivo:",
                                                          text=suggestion if suggestion else  "Traçado " + str(len(self.model.listTables()+1)))
            if not ok:
                return False
            first = False
        return filename


    def duplicarEstaca(self):
        if self.model.id_filename == -1: return
        filename=self.fileName(suggestion="Cópia de " + self.model.getNameFromId(self.model.id_filename))
        if not filename:
            return None
        self.openEstaca()
        estacas = self.view.get_estacas()

        if not hasattr(self,"perfil"):
            tipo, class_project = self.model.tipo()
            self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename), iface=self)
        table = deepcopy(self.perfil.getVertices())
        cvData=deepcopy(self.perfil.getCurvas())

        self.model=self.model.saveEstacas(filename, estacas)
        self.model.table = table
        self.model.cvData=cvData
        self.model.saveGreide(self.model.id_filename)
        self.update()

        self.view.clear()
        estacas = self.model.loadFilename()
        self.estacasHorizontalList=[]
        for e in estacas:
            self.view.fill_table(tuple(e), True)
            self.estacasHorizontalList.append(tuple(e))
        self.nextView=self.view
        self.view.setCopy()
        self.updateTables()
        self.geraCurvas(self.model.id_filename)

        prog, est, prism = self.model.getTrans(self.model.id_filename)
        if prog:
            self.trans=Ui_sessaoTipo(self.iface, est[1], self.estacasHorizontalList, prog, est[0], prism=prism)
            self.saveTrans()

    def cleanTrans(self):
        if yesNoDialog(None, message="Tem certeza que quer excluir os dados transversais?"):
            self.model.cleanTrans(idEstacaTable=self.model.id_filename)

    def generateIntersec(self):
        self.openEstaca()
        horizontais = self.view.get_estacas()  #x = 4, y =3

        points=[]
        progs=[]
        for h in horizontais:
            points.append(QgsPoint(float(h[4]), float(h[3])))
            progs.append(float(h[2]))
        road=QgsGeometry.fromPolyline(points)

        QgsMessageLog.logMessage("Iniciando comparação", "Topografia", level=0)
        verticais=[]
        self.openCv()
        vprogs=[]
        for v in self.viewCv.get_estacas():  # prog=2 em ambos
           if float(v[2]) in progs:
                h = horizontais[progs.index(float(v[2]))]
                desc="" if h[1]=="" and v[1]=="" else h[1]+" + "+v[1]
                verticais.append([v[0], desc, v[2], h[3], h[4], v[3], h[5], h[6]])
           else:
                pt=road.interpolate(float(v[2])).asPoint()
                pt2=road.interpolate(float(v[2])+.1).asPoint()
                verticais.append([v[0], v[1], v[2], pt.y(), pt.x(),v[3], None, azimuth(pt, pt2)])  #Não sei a cota 6
           vprogs.append(float(v[2]))

        table=verticais
        i=0
        for h in horizontais:
            if float(h[2]) not in vprogs:
                table.append([h[0],h[1],h[2],h[3],h[4],None,h[5],h[6]])  #Não sei o greide 5

        table = sorted(table, key=lambda x: float(x[2]))  #Organizar em ordem da progressiva

        progAnt=float(table[0][2])
        anterior=[table[0][-2],table[0][-3]] #cota, greide
        for i,t in enumerate(table):  #Interpolar greides e cotas desconhecidos
            atual=[t[-2],t[-3]] #cota, greide
            if None in atual:
                if i==0:
                    distAnt=1000000
                else:
                    distAnt=float(t[2])-progAnt
                j=1
                while i+j < len(table)-1:  # Próxima estaca inteira
                    if float(table[i+j][2])%Config.instance().DIST==0:
                        proxima=[table[i+j][-2],table[i+j][-3]] #cota, greide
                        distProx=float(table[i+j][2])-float(t[2])
                        break
                    j+=1
                else:
                    proxima=anterior
                    distProx=1000000

                try:
                    from numpy import interp  # Interpola os valores de greide e cota desconhecidos em pontos críticos
                    table[i][-2]=interp(0, [-distAnt, distProx], [float(anterior[0]), float(proxima[0])])
                    table[i][-3]=interp(0, [-distAnt, distProx], [float(anterior[1]), float(proxima[1])])
                except Exception as e:
                    msgLog(str(e))
                    table[i][-2]=0
                    table[i][-3]=0

            if float(t[2])%Config.instance().DIST==0: #se é uma estaca inteira se torna a anterior
                anterior=atual
                progAnt=float(t[2])


        QgsMessageLog.logMessage("Fim comparação", "Topografia", level=0)

        self.viewCv.clear()
        self.viewCv.setIntersect()
        for e in table:
            self.viewCv.fill_table(tuple(e), True)
        self.viewCv.setWindowTitle(self.model.getNameFromId(self.model.id_filename) + ": Estacas")
        self.viewCv.btnGen.clicked.connect(self.openCv)
        self.nextView=self.viewCv

    def new(self, layer=None, dados=None):
        self.view.clear()

        isGeopckg=True if dados else False
        dados = dados if dados else self.preview.new(lastIndex=len(self.model.listTables())+1)
        self.model.iface=self.iface
        if not dados is None:
            filename, lyr, dist, estaca = dados
            id_estaca, table = self.model.new(dist, estaca, lyr, filename) if not isGeopckg else self.model.newEmpty(Config.instance().DIST,filename)
            self.elemento = id_estaca
            self.model.id_filename = id_estaca
            self.estacasHorizontalList=[]

            empty=True
            for item in table:
                self.view.fill_table(tuple(item))
                self.estacasHorizontalList.append(tuple(item))
                empty=False

            self.view.empty=empty
            self.model.save(id_estaca)
            self.updateTables()
            Config.instance().store("DIST",dados[-2])

            return self.model.getNewId()

        return False

    def perfilView(self):
        tipo, class_project = self.model.tipo()
        self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename), iface=self)
        self.perfil.save.connect(self.saveGreide)
        self.perfil.reset.connect(self.cleanGreide)
        self.perfil.showMaximized()
        self.perfil.exec_()

    def saveGreide(self):
        if self.model.id_filename == -1: return
        self.model.table = self.perfil.getVertices()
        self.model.cvData=self.perfil.getCurvas()
        self.model.saveGreide(self.model.id_filename)

    def cleanGreide(self):
        if self.model.id_filename == -1: return
        self.model.cleanGreide(self.model.id_filename)
        self.perfil.justClose()
        self.perfilView()

    def generateTrans(self):
        prog, est, prism = self.model.getTrans(self.model.id_filename)
        if prog:
            #Database Trans
            self.trans=Ui_sessaoTipo(self.iface, est[1], self.estacasHorizontalList, prog, est[0], prism=prism)
        else:
            #New trans
            terreno = self.obterTerrenoTIFF()
            self.trans=Ui_sessaoTipo(self.iface, terreno, self.estacasHorizontalList, self.estacasVerticalList, greide=self.model.getGreide(self.model.id_filename), title="Transversal: "+str(self.model.getNameFromId(self.model.id_filename)))
        self.trans.save.connect(self.saveTrans)
        self.trans.plotar.connect(self.plotTransLayer)
        self.trans.show()
        self.trans.exec_()


    def saveTrans(self):
        if self.model.id_filename == -1: return
        self.model.table = self.trans.getMatrixVertices()
        self.model.xList = self.trans.getxList()
        self.model.saveTrans(self.model.id_filename, self.trans.prismoide.getPrismoide())


    def recalcular(self):
        id=self.model.id_filename
        dados = self.preview.new(True)
        if dados is None: return
        _, layer, dist, estaca = dados
        table = self.model.recalcular(dist, estaca, layer)
        self.view.clear()
        for item in table:
            self.view.fill_table(tuple(item))
        self.model.id_filename=id
        self.model.save(id)
        self.geraCurvas(self.model.id_filename)

    def saveEstacas(self):
        if self.model.id_filename == -1: return
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.save(self.model.id_filename)

    def saveEstacasCSV(self):
        filename = self.view.saveEstacasCSV()
        if filename[0] in ["", None]: return
        self.saveEstacas()
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.saveCSV(filename)

    def deleteEstaca(self):
        table=self.preview.tableEstacas
        table : QtWidgets.QTableWidget
        if len(table.selectionModel().selectedRows(0))==0: return
        if not yesNoDialog(self.preview, title="Atenção", message="Tem certeza que deseja remover o arquivo?"):
            return
        indexes=[i.row() for i in table.selectionModel().selectedRows(0)]
        if len(indexes)>1:
            for i in indexes:
                id=table.item(i,0).text()
                self.model.deleteEstaca(id)
        else:
            self.model.deleteEstaca(self.model.id_filename)
        self.update()
        self.model.id_filename = -1
        self.click = False

    def curva(self):
        curvas = self.model.getCurvas(self.model.id_filename)
        vertices = [[v[1], QgsPoint(float(v[4]), float(v[3]))] for v in self.model.loadFilename() if v[1]!='']
        if len(self.view.curvaLayers)==0:
            self.geraCurvas(self.model.id_filename)
        curvaView = CurvasView(self.view, self.iface, self.model.id_filename,curvas, vertices,self.model.tipo())
        self.view.showMinimized()
        curvaView.accepted.connect(self.raiseView)
        curvaView.rejected.connect(self.raiseView)
        curvaView.exec_()

    def raiseView(self):
        self.view.setWindowState(self.view.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        self.view.activateWindow()


    def plotTransLayer(self, index):
        self.obterTerrenoTIFF(True, index)


    def obterTerrenoTIFF(self, plotTrans=False, index=-1):
        filename = self.view.openTIFF()
        if filename in ['', None]: return
        terreno=[]

        #progressBar=ProgressDialog(None)
        #progressBar.show()

        try:
            layer=None
            for l in self.iface.mapCanvas().layers():
                if l.source() == filename:
                    layer=l
            if layer is None:
                msgLog("Layer não encontrada")
                return []
            msgLog("Interpolando Layer: "+str(layer.name()))
            estacas = self.estacas = self.view.get_estacas()

            # fazer multithreading
            for i, _ in enumerate(estacas):
                if plotTrans and index !=-1:
                    i=index

                v=[]
                az=float(estacas[i][6])
                perp=az+90


                if perp>360:
                    perp=perp-360

                nsign=1
                esign=1
                if perp<90:
                    nsign=1
                    esign=1
                elif perp<180:
                    nsign=-1
                    esign=1
                elif perp<270:
                    nsign=-1
                    esign=-1
                elif perp<360:
                    nsign=1
                    esign=-1

                pointsList=[]

                #TODO: Change fixed offset between transversal points and allow user to decide transversal sampled spacement
                for y in range(-Config.instance().T_SPACING, Config.instance().T_SPACING+1):
                    yangleE=esign*y*abs(math.sin(perp*math.pi/180))
                    yangleN=nsign*y*abs(math.cos(perp*math.pi/180))

                    try:
                        xPoint=float(float(estacas[i][4])+yangleE)
                        yPoint=float(float(estacas[i][3])+yangleN)

                        cota = cotaFromTiff(layer, QgsPointXY(xPoint, yPoint))
                        v.append([y,float(cota)])
                        pointsList.append([xPoint, yPoint])

                    except ValueError as e:
                        self.preview.error(u"GeoTIFF não compativel com a coordenada!!!")
                        return False
                    except IndexError as e:
                        continue

                terreno.append(v)


                if plotTrans:
                    if index==-1:
                        self.drawPoints(pointsList, str(i))
                        self.drawPoint(pointsList[0], str(i))
                    if index==i:
                        self.drawPoints(pointsList, str(i))
                        self.drawPoint(pointsList[0], str(i))
                        return

        except e:
            msgLog("Interpolação Falhou: "+str(e))
            img = Image.open(filename)
            img.size = tuple(img.tile[-1][1][2:])
            self.img_origem = img.tag.get(33922)[3:5]
            self.tamanho_pixel = img.tag.get(33550)[:2]
            self.estacas = self.view.get_estacas()

            estacas = self.estacas

            # fazer multithreading
            for i, _ in enumerate(estacas):
                v=[]
                az=float(estacas[i][6])
                perp=az+90
                if perp>360:
                    perp=perp-360

                nsign=1
                esign=1
                if perp<90:
                    nsign=1
                    esign=1
                elif perp<180:
                    nsign=-1
                    esign=1
                elif perp<270:
                    nsign=-1
                    esign=-1
                elif perp<360:
                    nsign=1
                    esign=-1

                pointsList=[]

                #TODO: Change fixed offset between transversal points and allow user to decide transversal sampled spacement
                for y in range(-Config.instance().T_SPACING, Config.instance().T_SPACING+1):
                    yangleE=esign*y*abs(math.sin(perp*math.pi/180))*self.tamanho_pixel[0]
                    yangleN=nsign*y*abs(math.cos(perp*math.pi/180))*self.tamanho_pixel[1]

                    try:
                        xPoint=float(float(estacas[i][4])+yangleE)
                        yPoint=float(float(estacas[i][3])+yangleN)

                        pixel = (int(abs(xPoint - self.img_origem[0]) / self.tamanho_pixel[0]),
                                 int(abs(yPoint - self.img_origem[1]) / self.tamanho_pixel[1]))

                        v.append([y,float(img.getpixel(pixel))])
                        pointsList.append([xPoint, yPoint])

                    except ValueError as e:
                        self.preview.error(u"GeoTIFF não compativel com a coordenada!!!")
                        return False
                    except IndexError as e:
                        continue

                terreno.append(v)


                if plotTrans:
                    if index==-1:
                        self.drawPoints(pointsList, str(i))
                        self.drawPoint(pointsList[0], str(i))
                    if index==i:
                        self.drawPoints(pointsList, str(i))
                        self.drawPoint(pointsList[0], str(i))

        return terreno


    def drawPoint(self, point, name):
        layer = QgsVectorLayer("Point", name, "memory")
        pr = layer.dataProvider()
        ft = QgsFeature()
        ft.setAttributes([1])
        ft.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point[0], point[1])))
        pr.addFeatures([ft])
        layer.setCrs(QgsProject.instance().crs())
        QgsProject.instance().addMapLayer(layer)

    def drawPoints(self, pointsList, name):
        layer = QgsVectorLayer('LineString', name, "memory")
        pr = layer.dataProvider()
        poly = QgsFeature()

        points=[]

        for i, _ in enumerate(pointsList):

            point = QgsPointXY(float(pointsList[i][0]), float(pointsList[i][1]))
            points.append(point)

        poly.setGeometry(QgsGeometry.fromPolylineXY(points))
        pr.addFeatures([poly])
        layer.updateExtents()
        layer.setCrs(QgsProject.instance().crs())
        QgsProject.instance().addMapLayers([layer])



    def newEstacasLayer(self, name):
        fields = QgsFields()
        fields.append(QgsField("Tipo", QVariant.String)) # C, T, E (Circular, tangente, Espiral ... startswith)
        fields.append(QgsField("Descricao", QVariant.String))

        #TODO add argument if existing project and change path declaration

        self.model.saveGeoPackage(name, [], fields, QgsWkbTypes.MultiCurveZ, 'GPKG')

    def saveEstacasLayer(self, estacas, name=None):
        name =str(self.model.getNameFromId(self.model.id_filename)) if name==None else name
        #path = QtWidgets.QFileDialog.getSaveFileName(self.iface.mainWindow(), "Caminho para salvar o traçado com as curvas", filter="Geopackage (*.gpkg)")[0]
        #if not path: return None

        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("Descricao", QVariant.String))
        fields.append(QgsField("type", QVariant.Int)) # 0 -> sem curva, 1 -> espiral, 2-> circular

        poly = QgsFeature()
        points=[]
        for i, _ in enumerate(estacas):
            point = QgsPointXY(float(estacas[i][4]), float(estacas[i][3]))
            points.append(point)
        poly.setGeometry(QgsGeometry.fromPolylineXY(points))
        path=self.model.saveGeoPackage(name, [poly], fields, QgsWkbTypes.MultiCurveZ, 'GPKG')

        layer=self.iface.addVectorLayer(path,name,"ogr")
        self.iface.digitizeToolBar().show()
        self.iface.shapeDigitizeToolBar().show()

        addLineAction = self.iface.digitizeToolBar().actions()[8]
        toggleEditAction = self.iface.digitizeToolBar().actions()[1]
        if not addLineAction.isChecked():
            toggleEditAction.trigger()
        addLineAction.setChecked(True)
        addLineAction.trigger()

        return layer


    def drawEstacas(self, estacas):
        layer = QgsVectorLayer('LineString?crs=%s'%(QgsProject.instance().crs().authid()), str(self.model.getNameFromId(self.model.id_filename)), "memory")
        layer.setCrs(QgsCoordinateReferenceSystem(QgsProject.instance().crs()))
        pr = layer.dataProvider()
        poly = QgsFeature()

        points=[]
        for i, _ in enumerate(estacas):

            point = QgsPointXY(float(estacas[i][4]), float(estacas[i][3]))
            points.append(point)

        poly.setGeometry(QgsGeometry.fromPolylineXY(points))
        pr.addFeatures([poly])
        layer.updateExtents()
        QgsProject.instance().addMapLayers([layer], False)
        QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
        return layer



    def obterCotasTIFF(self):

        filename = self.view.openTIFF()
        if filename in ['', None]:  return

        try:
            l=False
            for l in self.iface.mapCanvas().layers():
                if l.source() == filename:
                    layer=l
                    break
            if not l:
                self.preview.error(u"Salve a layer antes de usa-lá!")
                return
            from ..model.utils import cotaFromTiff
            self.estacas = self.view.get_estacas()
            estacas = self.estacas
            for i, _ in enumerate(estacas):
                cota = cotaFromTiff(layer,QgsPointXY(float(estacas[i][4]),float(estacas[i][3])))
                if cota:
                    estacas[i][5] = "%f" % cota
                else:
                    self.preview.error(u"Pontos do traçado estão fora do raster selecionado!!!")
                    break
        except Exception as e:

            try:
                img = Image.open(filename)
                img.size = tuple(img.tile[-1][1][2:])
                self.img_origem = img.tag.get(33922)[3:5]
                self.tamanho_pixel = img.tag.get(33550)[:2]
                self.estacas = self.view.get_estacas()
                estacas = self.estacas

                # fazer multithreading
                for i, _ in enumerate(estacas):
                        pixel = (int(abs(float(estacas[i][4]) - self.img_origem[0]) / self.tamanho_pixel[0]),
                                 int(abs(float(estacas[i][3]) - self.img_origem[1]) / self.tamanho_pixel[1]))
                        estacas[i][5] = "%f" % img.getpixel(pixel)

            except Exception as e:
                from osgeo import gdal
                dataset = gdal.Open(filename, gdal.GA_ReadOnly)
                for x in range(1, dataset.RasterCount + 1):
                    band = dataset.GetRasterBand(x)
                    img = band.ReadAsArray()
                self.img_origem = dataset.GetGeoTransform()[0],dataset.GetGeoTransform()[3]
                self.tamanho_pixel = abs(dataset.GetGeoTransform()[1]),abs(dataset.GetGeoTransform()[5])
                self.estacas = self.view.get_estacas()
                estacas = self.estacas
                for i, _ in enumerate(estacas):
                    try:
                        pixel = (int(abs(float(estacas[i][4]) - self.img_origem[0]) / self.tamanho_pixel[0]),
                                 int(abs(float(estacas[i][3]) - self.img_origem[1]) / self.tamanho_pixel[1]))
                        estacas[i][5] = "%f" % img[pixel]
                    except Exception as e:
                        #self.drawEstacas(estacas)
                        self.preview.error(u"GeoTIFF não compativel com a coordenada!!!")
                        return

        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca()


    def obterCotasThread(self, estacas, inicio=0, fim=None):

        for i in range(inicio, fim):
            # fix_print_with_import
            print(i)
            try:
                pixel = (int(abs(float(estacas[i][4]) - self.img_origem[0]) / self.tamanho_pixel[0]),
                         int(abs(float(estacas[i][3]) - self.img_origem[1]) / self.tamanho_pixel[1]))
                self.estacas[i][5] = "%f" % img.getpixel(pixel)
            except:
                self.terminou += 1
                self.preview.error(u"GeoTIFF não compativel com a coordenada!!!")
                return
        # fix_print_with_import
        print("Terminou")
        self.terminou += 1

    def obterCotasPC3(self):

        filename = self.view.openTIFF()
        if filename in ['', None] or not filename.endswith('dxf'):  return
        self.estacas = self.view.get_estacas()
        estacas = self.estacas
        points = []
        # fazer multithreading
        for i, _ in enumerate(estacas):
            points.append((int("%d" % float(estacas[i][4])), int("%d" % float(estacas[i][3]))))

        dwg = dxfgrabber.readfile(filename, options={"assure_3d_coords": True})
        dxfversion = dwg.header['$ACADVER']
        all_points = []
        for entity in dwg.entities:
            if entity.dxftype == 'POINT':
                pe = "%d" % entity.point[0]
                pn = "%d" % entity.point[1]
                p = (int(pe), int(pn))
                if p in points:
                    all_points.append(p)

        for p in all_points:
            ponto = points.index((int(p[0]), int(p[1])))
            estacas[ponto][5] = p[2]
            # fix_print_with_import
            print(estacas[ponto])
        # fix_print_with_import
        print("terminou")
        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca()

    def elevate(self):
        import ctypes, win32com.shell.shell, win32event, win32process
        outpath = r'%s\%s.out' % (os.environ["TEMP"], os.path.basename(__file__))
        if ctypes.windll.shell32.IsUserAnAdmin():
            if os.path.isfile(outpath):
                sys.stderr = sys.stdout = open(outpath, 'w', 0)
                return
        with open(outpath, 'w+', 0) as outfile:
            hProc = \
                win32com.shell.shell.ShellExecuteEx(lpFile=sys.executable, lpVerb='runas', lpParameters=' '.join(sys.argv),
                                                    fMask=64, nShow=0)['hProcess']
            while True:
                hr = win32event.WaitForSingleObject(hProc, 40)
                while True:
                    line = outfile.readline()
                    if not line: break
                    sys.stdout.write(line)
                if hr != 0x102: break
        os.remove(outpath)
        sys.stderr = ''
        sys.exit(win32process.GetExitCodeProcess(hProc))

    def obterCotasPC(self):
        try:
            import dxfgrabber
            from sklearn.svm import SVR
            from sklearn.neighbors import KNeighborsRegressor
            from sklearn import linear_model
        except:
            import os
            import re
            if not re.match("win{1}.*", os.sys.platform) is None:
                saida = os.system(
                    "C:\\Users\\%%USERNAME%%\\.qgis2\\python\\plugins\\TopoGrafia\\app\\controller\\install.bat")
            else:
                saida = os.system("sudo apt install python-pip&&pip install scikit-learn&&pip install dxfgrabber")
            if saida != 0:
                self.preview.error(
                    u"Para usar este recurso você deve instalar os pacotes abaixo:\nSKLearn e dxfgrabber: (Linux) 'sudo pip install scikit-learn&&pip install dxfgrabber' (Windows) Deve seguir o tutorial https://github.com/lennepkade/dzetsaka#installation-of-scikit-learn")
            return
        filename,_ = self.view.openDXF()
        if filename in ['', None] or not (filename.endswith('dxf') or filename.endswith('DXF')):  return
        estacas = self.view.get_estacas()
        dwg = dxfgrabber.readfile(filename, options={"assure_3d_coords": True})
        all_points = []
        all_points_Y = []
        inicial = (float(estacas[0][4]), float(estacas[0][3]))
        az_inicial = float(estacas[0][6])
        for entity in dwg.entities:
            if entity.dxftype == 'POINT':
                dist = math.sqrt((inicial[0] - entity.point[0]) ** 2 + (inicial[1] - entity.point[1]) ** 2)
                az = float(azimuth(QgsPoint(inicial[0], inicial[1]), QgsPoint(entity.point[0], entity.point[1])))
                all_points.append([entity.point[0], entity.point[1]])
                all_points_Y.append([entity.point[2]])

        points = []
        for i, _ in enumerate(estacas):
            points.append([float(estacas[i][4]), float(estacas[i][3])])
        X = all_points
        y = all_points_Y
        # clf = SVR(C=1.0, epsilon=0.2)
        #clf = KNeighborsRegressor(n_neighbors=3)
        itens = [u'KNN Regressão (Classico)',u'KNN Regressão (K Inteligente)',u'SVM',u'Regressão Linear']
        itens_func = [KNeighborsRegressor,KNN,SVR,linear_model.ARDRegression] 
        item, ok = QtWidgets.QInputDialog.getItem(None, "Selecione:", u"Selecione o método de predição:",
                                                  itens,
                                                  0, False)
        if not(ok) or not(item):
            return None

        clf = itens_func[item.index(item)](5)
        if itens.index(item) < 2:
            k, ok = QtWidgets.QInputDialog.getInteger(None, "Escolha o valor de K", u"Valor de K:", 3, 2, 10000, 2)
            if k<1 or not(ok):
                return None
            clf = itens_func[itens.index(item)](k)
        #clf = KNN(5)
        # clf = linear_model.LinearRegression()
        # clf = linear_model.ARDRegression()
        modelo = clf.fit(X, y)
        pred = modelo.predict(points)
        for i, predito in enumerate(pred):
            estacas[i][5] = "%f" % predito
        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca()

    def obterCotas(self):
        self.model.table = self.view.get_estacas()
        crs = int(self.model.getCRS())
        for i, _ in enumerate(self.model.table):
            try:
                self.model.table[i][5] = u"%d" % getElevation(crs, QgsPoint(float(self.model.table[i][4]),
                                                                            float(self.model.table[i][3])))
                if self.model.table[i][5] == 0:
                    return
            except Exception as e:
                # fix_print_with_import
                print(e.message)
                break
        self.model.save(self.model.id_filename)
        self.openEstaca()

    '''
        Metodos responsaveis por gerar o traçado de acordo com cliques na tela.
    '''

    def geraTracado(self,parte=0,pontos=None):
        crs = self.model.getCRS()
        self.preview.drawShapeFileAndLoad(crs)

    def get_click(self, point, mouse):

        if not self.edit: return
        self.edit = False
        # if mouse == 2: return
        if mouse == 1:
            self.preview.create_point(QgsPoint(point), 'vertice')
            self.points.append(QgsPoint(point))

        self.edit = True

    def get_click_coordenate(self, point, mouse):

        if not self.edit: return
        self.edit = False
        # if mouse == 2: return
        if mouse == 1:
            self.preview.create_point(QgsPoint(point), 'vertice')
            self.points.append(QgsPoint(point))

        self.edit = True

    def exit_dialog(self):
        self.points.append(QgsPoint(self.points_end))
        self.iface.mapCanvas().setMapTool(QgsMapToolEmitPoint(self.iface.mapCanvas()))
        self.edit = False
        self.preview.exit_dialog(self.points, self.crs)
        self.new()
        self.view.show()
        self.view.exec_()

    def gera_tracado_vertices(self, p1, p2, crs):
        self.crs = crs
        self.points = [p1]
        self.edit = True
        self.points_end = p2
        self.pointerEmitter = QgsMapToolEmitPoint(self.iface.mapCanvas())

        self.pointerEmitter.canvasClicked.connect(self.get_click)
        name_tracado = self.preview.gera_tracado_vertices(self.pointerEmitter)
        self.preview.dialog.btnClose.clicked.connect(self.exit_dialog)
        return name_tracado

    '''
        --------------------------------------------------
    '''

    def openEstaca(self, i=0):
        if self.model.id_filename == -1: return
        self.view.clear()
        estacas = self.model.loadFilename()
        self.estacasHorizontalList=[]
        for e in estacas:
            self.view.fill_table(tuple(e), True)
            self.estacasHorizontalList.append(tuple(e))
        self.nextView=self.view 
        self.view.setCopy()
        self.updateTables()

    def openCv(self):
        self.openEstaca()
        self.viewCv.clear()
        self.viewCv.setWindowTitle(str(self.model.getNameFromId(self.model.id_filename))+": Verticais")
        estacas=[]
        tipo, class_project = self.model.tipo()
        
        try:
            self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename))
        except Exception as e:
            messageDialog(None, title="Erro!", message="Perfil Vertical ainda não foi definido!")
            msgLog(str(e))
            return None

        (estaca,descricao,progressiva,cota) = (0, "V1", 0, self.perfil.getVertices()[0][1])
        estacas.append((estaca,descricao,progressiva,cota))
        missingCurveDialog=[]
        y=float(cota)
        points=[]

        for i in range(1, len(self.perfil.roi.handles)-1):
            i1=self.perfil.roi.getSegIncl(i-1,i)
            i2=self.perfil.roi.getSegIncl(i,i+1)
            L=0
            if self.perfil.cvList[i][1]!="None":
                L=float(self.perfil.cvList[i][1])

            pontosCv=CV(i1, i2, L,self.perfil.roi.getHandlePos(i), self.perfil.roi.getHandlePos(i-1))
            points.append({"cv": pontosCv, "i1": i1/100, "i2": i2/100, "L": L, "i": i})

        if len(points)==0:
            messageDialog(None, title="Erro!", message="Perfil Vertical ainda não foi definido!")
            msgLog("len(points)==0")
            return None

        x=0
        i=points[0]["i1"]
        s=0
        c=1
        fpcv=0
        fptv=0
        est=1

        while est <= int(self.perfil.roi.getHandlePos(self.perfil.roi.countHandles()-1).x()/20):

             if fptv:
                 dx=20-dx
                 dy=point["i1"]*dx
                 fptv=0

             elif fpcv:
                 dx=20-dx
                 dy=point["i1"]*dx
                 fpcv=0
             else:
                dx=20
                dy=i*dx

             desc=""

             if len(points)>0:
                 point=points[0]

                 try:
                     pt=x+dx>=point["cv"].xptv
                     pv=x+dx>=point["cv"].xpcv and not pt and not s

                 except AttributeError:
                    point["cv"].xptv=point["cv"].handlePos.x()
                    point["cv"].xpcv=point["cv"].handlePos.x()
                    point["cv"].ypcv=point["cv"].handlePos.y()
                    point["cv"].yptv=point["cv"].handlePos.y()

                    missingCurveDialog.append(c)

                    pt=x+dx>=point["cv"].xptv
                    pv=x+dx>=point["cv"].xpcv and not pt and not s

                 i=points[0]["i1"]
             else:
                 pt=False
                 pv=False
                 i=point["cv"].i2/100

             if(pv):
                 #estacas.append(("debug",point["i"],point["i1"],point["cv"].ypcv))
                 dx=point["cv"].xpcv-x
                 desc="PCV"+str(c)
                 s=1
                 dy=point["cv"].ypcv-y
                 est-=1
                 fpcv=1

             elif(pt):
                  dx=point["cv"].xptv-x

                  if point["cv"].xptv == point["cv"].handlePos.x():
                      desc="PV"+str(c)
                  else:
                      desc="PTV"+str(c)

                  s=0
                  dy=point["cv"].yptv-y
                  est-=1
                  points.pop(0)
                  fptv=1
                  c+=1

             x+=dx

             if s and not (pv or pt):
                 dy=point["cv"].getCota(x)-y

             y+=dy

             (estaca,descricao,progressiva,cota) = (
                est if not (pv or pt) else str(est)+' + ' + str(dx),
                desc,
                x,
                y
             )
             estacas.append((estaca,descricao,progressiva,cota))


             est+=1

        if len(missingCurveDialog) > 0:
            messageDialog(self.viewCv, "Atenção!", message="Nenhum comprimento de curva foi definido no perfil vertical para os vértices: " + str(missingCurveDialog)[1:-1])

        dx=float(self.perfil.getVertices()[-1:][0][0])-x
        x+=dx
        dy=float(self.perfil.getVertices()[-1:][0][1])-y
        y+=dy


        (estaca,descricao,progressiva,cota) = (str(est-1)+' + ' + str(dx),"V2",x,y)
        estacas.append((estaca,descricao,progressiva,cota))

        self.estacasVerticalList=estacas
        self.viewCv.clear()
        self.viewCv.setCv()
        for e in estacas:
            self.viewCv.fill_table(tuple(e), True)

        self.viewCv.btnGen.clicked.connect(self.generateIntersec)
        self.nextView=self.viewCv



    def itemClickTableEstacas(self, item=None):
        self.click = True
        if item is None:
            self.preview.tableEstacas: QtWidgets.QTableWidget
            item=self.preview.tableEstacas.currentItem()
        try:
            ident = int(self.preview.tableEstacas.item(item.row(), 0).text())
            self.model.id_filename = ident
        except:
            pass

    def openEstacaCSV(self):
        self.view.clear()
        res = self.preview.openCSV()
        file=res[0]
        if file[0] in ['', None] or res[1] in ['', None] or not (file[0].endswith('csv')): return
        filename, fileDB = file[0], res[1]
        estacas = self.model.openCSV(filename, fileDB)
        self.model.table = estacas
        self.elemento = self.model.ultimo
        for estaca in estacas:
            self.view.fill_table(tuple(estaca), True)
        self.view.setCopy()
        self.model.save(self.elemento)

    def plotar(self):
        self.drawEstacas(self.view.get_estacas())
        #self.view.plotar()

    def update(self):
        files = self.model.listTables()
        self.preview.fill_table_index(files)
        self.view.clear()
        self.view.clearLayers()

    def updateTables(self):
        try:
            self.view.setWindowTitle(self.model.getNameFromId(self.model.id_filename)+": Horizontal")
        except:
            pass

    def run(self):
       # from ..view.estacas import SelectFeatureDialog
       # s=SelectFeatureDialog(self.iface,self.iface.mapCanvas().layer(0).getFeatures())
       # s.exec_()
        self.update()
        self.click = False
        self.preview.show()

        finalResult=False
        result = True

        lastFinalResult=True
        lastResult=False

        while finalResult>0 or result>0:
            self.update()
            result = self.preview.exec_()
            self.nextView.resize(self.nextView.width(), self.nextView.height()+1)
            if result:
                self.preview.close()
                self.nextView.show()
                finalResult = self.nextView.exec_()

            if lastResult == result:
                lastResult = not result

            elif lastFinalResult == finalResult:
                lastFinalResult = not finalResult

            else:
                lastFinalResult=finalResult
                lastResult=result







           
