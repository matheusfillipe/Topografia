from __future__ import print_function
# -*- coding: utf-8 -*-
import webbrowser
from qgis.PyQt import QtGui

from qgis._gui import QgsMapToolEmitPoint
try:
    from PIL import Image
except:
    from ...PIL import Image

from ..controller.perfil import Ui_Perfil, cv as CV
from ..model.estacas import Estacas as EstacasModel
from ..model.knn import KNN
from ..model.utils import *
from ..view.estacas import Estacas as EstacasView, EstacasUI, EstacasCv
from ..view.curvas import Curvas as CurvasView


class Estacas(object):
    def __init__(self, iface):
        self.iface = iface
        self.model = EstacasModel()
        self.preview = EstacasUI(iface)
        self.view = EstacasView(iface)

        self.events()
        self.elemento = -1
        self.click = False
        self.edit = False
        self.points = []

        self.nextView=self.view 
        self.viewCv = EstacasCv(iface)


    def mudancaCelula(self,item):
        if item.column() > 1:
            campo = float(self.view.tableWidget.item(item.row(), item.column()).text().replace(',','.'))
            self.view.tableWidget.setItem(item.row(), item.column(),QtGui.QTableWidgetItem('%s'%campo))

    def linkGoogle(self, item):
        if item.column() == 0:
            este = float(self.view.tableWidget.item(item.row(), 4).text())

            north = float(self.view.tableWidget.item(item.row(), 3).text())
            crs = int(self.model.getCRS())
            point = QgsPoint(este, north)
            epsg4326 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
            mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
            reprojectgeographic = QgsCoordinateTransform(mycrs, epsg4326)
            pt = reprojectgeographic.transform(point)

            webbrowser.open('https://www.google.com.br/maps/@%f,%f,15z?hl=pt-BR' % (pt.y(), pt.x()))

    def events(self):
        self.preview.btnNovo.clicked.connect(self.new)
        self.preview.btnOpen.clicked.connect(self.openEstaca)
        self.preview.btnOpenCSV.clicked.connect(self.openEstacaCSV)
        self.preview.btnApagar.clicked.connect(self.deleteEstaca)
        self.preview.btnGerarTracado.clicked.connect(self.geraTracado)
        self.preview.tableEstacas.itemClicked.connect(self.itemClickTableEstacas)
        self.preview.btnOpenCv.clicked.connect(self.openCv)
       

        '''
            ------------------------------------------------
        '''

        self.view.btnSave.clicked.connect(self.saveEstacas)
        self.view.btnSaveCSV.clicked.connect(self.saveEstacasCSV)
        self.view.btnLayer.clicked.connect(self.plotar)
        self.view.btnEstacas.clicked.connect(self.recalcular)
        self.view.btnRead.clicked.connect(self.run)
        self.view.btnPerfil.clicked.connect(self.perfilView)
        self.view.btnCurva.clicked.connect(self.curva)
        self.view.btnCotaTIFF.clicked.connect(self.obterCotasTIFF)
        self.view.btnCotaPC.clicked.connect(self.obterCotasPC)
        self.view.btnCota.clicked.connect(self.obterCotas)
        self.view.tableWidget.itemDoubleClicked.connect(self.linkGoogle)
        self.view.tableWidget.itemClicked.connect(self.mudancaCelula)





    def new(self, bool=False, layer=None):
        self.view.clear()
        dados = self.preview.new()
        if not dados is None:
            filename, lyr, dist, estaca = dados
            id_estaca, table = self.model.new(dist, estaca, lyr, filename)
            self.elemento = id_estaca
            self.model.id_filename = id_estaca
            for item in table:
                self.view.fill_table(tuple(item))
            self.model.save(id_estaca)

    def perfilView(self):
        tipo, class_project = self.model.tipo()
        self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename))

        self.perfil.save.connect(self.saveGreide)
       
        self.perfil.showMaximized()
        self.perfil.exec_()

    def saveGreide(self):
        if self.model.id_filename == -1: return
        self.model.table = self.perfil.getVertices()
        self.model.cvData=self.perfil.getCurvas()
        self.model.saveGreide(self.model.id_filename)       

    def recalcular(self):
        self.view.clear()
        dados = self.preview.new(True)
        if dados is None: return
        _, layer, dist, estaca = dados
        table = self.model.recalcular(dist, estaca, layer)
        for item in table:
            self.view.fill_table(tuple(item))

    def saveEstacas(self):
        if self.model.id_filename == -1: return
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.save(self.model.id_filename)

    def saveEstacasCSV(self):
        filename = self.view.saveEstacasCSV()
        if filename in ["", None]: return
        self.saveEstacas()
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.saveCSV(filename)

    def deleteEstaca(self):
        if self.click == False: return
        self.model.deleteEstaca(self.model.id_filename)
        self.update()
        self.model.id_filename = -1
        self.click = False

    def curva(self):
        curvas = self.model.getCurvas(self.model.id_filename)
        curvaView = CurvasView(self.iface,self.model.id_filename,curvas,self.model.tipo())
        curvaView.exec_()
        

    def obterCotasTIFF(self):
        filename = self.view.openTIFF()
        if filename in ['', None]:  return
        try:
            img = Image.open(filename)
            self.img_origem = img.tag.get(33922)[3:5]
            self.tamanho_pixel = img.tag.get(33550)[:2]
            self.estacas = self.view.get_estacas()
            estacas = self.estacas
            # fazer multithreading
            for i, _ in enumerate(estacas):
                try:
                    pixel = (int(abs(float(estacas[i][4]) - self.img_origem[0]) / self.tamanho_pixel[0]),
                             int(abs(float(estacas[i][3]) - self.img_origem[1]) / self.tamanho_pixel[1]))
                    estacas[i][5] = "%f" % img.getpixel(pixel)
                except:
                    self.preview.error(u"GeoTIFF não compativel com a coordenada!!!")
                    return
        except:
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
                except:
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
        filename = self.view.openDXF()
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
        item, ok = QtGui.QInputDialog.getItem(None, "Selecione:", u"Selecione o método de predição:",
                                                  itens,
                                                  0, False)
        if not(ok) or not(item):
            return None

        clf = itens_func[item.index(item)](5)
        if itens.index(item) < 2:
            k, ok = QtGui.QInputDialog.getInteger(None, "Escolha o valor de K", u"Valor de K:", 3, 2, 10000, 2)
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
        if parte == 0:
            # pega as coordenadas norte e este dos pontos inicial e final
            self.preview.gera_tracado_pontos(callback_inst=self,callback_method='geraTracado',crs=crs)
        if parte == 1:
            if pontos is None:
                self.preview.error(u"Pelo fato dos dados estarem incorretos não foi possivel criar o traçado!!!")
                return
            ponto_inicial, ponto_final = pontos
            self.name_tracado = self.gera_tracado_vertices(ponto_inicial, ponto_final, crs)


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

    def openEstaca(self):
      
        if self.model.id_filename == -1: return
        self.view.clear()
        estacas = self.model.loadFilename()
        for e in estacas:
            self.view.fill_table(tuple(e), True)
        self.nextView=self.view 

    def openCv(self):
        self.openEstaca()
        if self.model.id_filename == -1: return
        self.viewCv.clear()

        estacas=[]

        tipo, class_project = self.model.tipo()
        self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename))

        (estaca,descricao,progressiva,cota) = (0,"V1",0,self.perfil.getVertices()[0][1])
        estacas.append((estaca,descricao,progressiva,cota))



######################################
#TODO: Detectar V's sem curvas e colocar a descrição
#
#
#
#
######################################



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

        dx=float(self.perfil.getVertices()[-1:][0][0])-x
        x+=dx
        dy=float(self.perfil.getVertices()[-1:][0][1])-y
        y+=dy


        (estaca,descricao,progressiva,cota) = (str(est-1)+' + ' + str(dx),"V2",x,y)
        estacas.append((estaca,descricao,progressiva,cota))


        for e in estacas:
            self.viewCv.fill_table(tuple(e), True)

        self.nextView=self.viewCv



    def itemClickTableEstacas(self, item):
        self.click = True
        ident = int(self.preview.tableEstacas.item(item.row(), 0).text())
        self.model.id_filename = ident

    def openEstacaCSV(self):
        self.view.clear()
        res = self.preview.openCSV()
        if res in ['', None] or res[1] in ['', None] or not (res[0].endswith('csv')): return
        filename, fileDB = res
        estacas = self.model.openCSV(filename, fileDB)
        self.model.table = estacas
        self.elemento = self.model.ultimo
        for estaca in estacas:
            self.view.fill_table(tuple(estaca), True)
        self.model.save(self.elemento)

    def plotar(self):
        self.view.plotar()

    def update(self):
        files = self.model.listTables()
        self.preview.fill_table_index(files)

    def run(self):
        self.update()
        self.click = False
        self.preview.show()

        result = self.preview.exec_()

        if result:
            self.preview.close()
            self.nextView.show()
            self.nextView.exec_()
           
