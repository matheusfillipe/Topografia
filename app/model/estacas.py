from builtins import str
from builtins import range
from builtins import object
# -*- coding: utf-8 -*-
import csv
import math
import sqlite3
from copy import copy, deepcopy

from qgis._core import QgsPoint, QgsProject, QgsVectorFileWriter, QgsPointXY

from ..controller.Geometria.Figure import prismoide
from ..model.config import extractZIP, Config, compactZIP
from ..model.curvas import Curvas
from ..model.utils import pairs, length, dircos, diff, azimuth, getElevation, internet_on, pointToWGS84, roundFloat2str
from ..view.estacas import SelectFeatureDialog



from qgis.PyQt import QtGui

#TODO change path tmp/dbatase to variable configurable

class Estacas(object):
    def __init__(self, distancia=20, estaca=0, layer=None, filename='', table=list(), cvData=list(),ultimo=-1, id_filename=-1, iface=None):
        self.iface=iface
        self.distancia = distancia
        self.filename = filename
        self.estaca = estaca
        self.layer = layer
        self.table = table
        self.xList = []
        self.ultimo = ultimo
        self.id_filename = id_filename

    def get_features(self):
        linhas = []
        for feature in self.layer.getFeatures():
           geom = feature.geometry().asPolyline()
           for i in geom:
                linhas.append(i)
        return linhas

    def new(self, distancia, estaca, layer, filename, iface=None):
        self.__init__(distancia, estaca, layer, filename, list(), self.ultimo, self.id_filename, iface=iface)
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + filename + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
        con.close()
        compactZIP(Config.fileName)
        self.ultimo = id_estaca[0]
        self.table = self.create_estacas()
        return self.ultimo, self.table

    def calcular(self, task=None, layer=None):
        self.layer=layer
        self.table = self.create_estacas(isCalc=True, task=task)
        return self.table

    def newEmpty(self, distancia, filename):
        self.__init__(distancia=distancia, filename=filename, ultimo=self.ultimo)
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + filename + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.close()
        compactZIP(Config.fileName)
        return id_estaca, []

    def getNewId(self):
         extractZIP(Config.fileName)
         con = sqlite3.connect("tmp/data/data.db")
         id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
         con.close()
         compactZIP(Config.fileName)
         return id_estaca[0]

    def saveEstacas(self,filename,estacas):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + filename + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
        con.close()
        compactZIP(Config.fileName)
        model=Estacas(filename=filename, id_filename=id_estaca[0])
        model.ultimo = id_estaca[0]
        model.table = estacas
        model.save(id_estaca[0])

        return model

    def getCurvas(self, id_filename):
        # instancia da model de curvas.
        curva_model = Curvas(id_filename)
        return curva_model.list_curvas()

    def getCRS(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        proj = con.execute("SELECT crs FROM PROJECT where id = 1").fetchone()
        crs = proj[0]
        con.close()
        compactZIP(Config.fileName)
        return crs

    def tipo(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        proj = con.execute(
            "SELECT crs, classeprojeto, maxplano,maxondulado,maxmontanhoso,tipomapa FROM PROJECT where id = 1").fetchone()

        class_project = proj[1]
        dataTopo = [
            0.0,
            proj[2],
            proj[2],
            proj[3],
            proj[3],
            proj[4]
        ]
        con.close()
        compactZIP(Config.fileName)
        return dataTopo, class_project

    def recalcular(self, distancia, estaca, layer):
        self.__init__(distancia, estaca, layer, self.filename, list(), self.ultimo, self.id_filename)
        self.table = self.create_estacas()
        return self.table

    def loadFilename(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        est = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def listTables(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        est = con.execute("SELECT id,name,data FROM TABLEESTACA").fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def getNameFromId(self,id):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        name = con.execute("SELECT name FROM TABLEESTACA WHERE id="+str(id)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return name[0][0]

    def deleteEstaca(self, idEstacaTable):
        self.removeGeoPackage(self.getNameFromId(idEstacaTable))
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM TABLEESTACA WHERE id=?", (idEstacaTable,))
        con.commit()
        con.close()
        compactZIP(Config.fileName)


    def save(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.commit()
        for linha in self.table:
            linha.append(int(idEstacaTable))
            lt = tuple(linha)
            con.execute(
                "INSERT INTO ESTACA (estaca,descricao,progressiva,norte,este,cota,azimute,TABLEESTACA_id)values(?,?,REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),REPLACE(?,',','.'),?)",
                lt)
        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''
        con.commit()
        con.close()

        compactZIP(Config.fileName)

    def saveGreide(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM GREIDE WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()
        for linha in self.table:
            linha.append(int(idEstacaTable))

            lt = tuple(linha)

            con.execute(
                   "INSERT INTO GREIDE (x,cota,TABLEESTACA_id)values(?,?,?)",
                   lt)

        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''
 
        con.commit()
        con.execute("DELETE FROM CURVA_VERTICAL_DADOS WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()

        for linha in self.cvData:
            linha.append(int(idEstacaTable))

            lt = tuple(linha)

            con.execute(
                    "INSERT INTO CURVA_VERTICAL_DADOS (CURVA_id, L,TABLEESTACA_id)values(?,?,?)",
                    lt)

        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''
       
 
        con.commit()
      
        con.close()

        compactZIP(Config.fileName)

    def saveTrans(self, id_filename, prismoid:prismoide):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")

        con.execute("DELETE FROM TRANSVERSAL WHERE TABLEESTACA_id = ?", (id_filename,))
        con.commit()

        con.execute("DELETE FROM SESSAO_TIPO WHERE TABLEESTACA_id = ?", (id_filename,))
        con.commit()

        con.execute("DELETE FROM RELEVO_SESSAO WHERE TABLEESTACA_id = ?", (id_filename,))
        con.commit()

        cursor=con.cursor()

        c=0
        for linha in self.xList:
            linha=[linha]
            linha.append(int(id_filename))

            lt = tuple(linha)

            cursor.execute(
                   "INSERT INTO TRANSVERSAL (x,TABLEESTACA_id)values(?,?)",
                   lt)

            transId=int(cursor.lastrowid)

            for rev in list(self.table[1][c]):
                rev=list(rev)
                rev.append(transId)
                rev.append(int(id_filename))
                lt=tuple(rev)
                cursor.execute(
                   "INSERT INTO RELEVO_SESSAO (y, cota,TRANSVERSAL_id,TABLEESTACA_id)values(?,?,?,?)",
                   lt)

            for rev in list(self.table[0][c]):
               rev=list(rev)
               rev.append(transId)
               rev.append(int(id_filename))
               lt=tuple(rev)
               cursor.execute(
                  "INSERT INTO SESSAO_TIPO (y, cota,TRANSVERSAL_id,TABLEESTACA_id)values(?,?,?,?)",
                  lt)
            c+=1

        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''

        con.commit()
        con.close()

        prismoid.save("tmp/data/"+str(id_filename)+".prism")
        compactZIP(Config.fileName)



    def cleanTrans(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")

        con.execute("DELETE FROM TRANSVERSAL WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()

        con.execute("DELETE FROM SESSAO_TIPO WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()

        con.execute("DELETE FROM RELEVO_SESSAO WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()
        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''

        con.commit()


        con.close()

        compactZIP(Config.fileName)




    def getTrans(self, idEstacaTable):
         try:
            extractZIP(Config.fileName)
            con = sqlite3.connect("tmp/data/data.db")

            est = con.execute("SELECT id, x FROM TRANSVERSAL WHERE TABLEESTACA_id = ?",(idEstacaTable,)).fetchall()

            table=[]
            table.append([])
            table.append([])
            c=0
            xList=[]

            for e in est:
                table[0].append(con.execute("SELECT y, cota FROM SESSAO_TIPO WHERE TRANSVERSAL_id = ?", (e[0],)).fetchall())
                table[1].append(con.execute("SELECT y, cota FROM RELEVO_SESSAO WHERE TRANSVERSAL_id = ?", (e[0],)).fetchall())
                xList.append(e[1])
                c+=1

            con.close()
            compactZIP(Config.fileName)
            prismoid=prismoide()

            if prismoid.restore("tmp/data/"+str(idEstacaTable)):
                return xList, table, prismoid
            else:
                return xList, table, None


         except:
            return False, False


    def getGreide(self, idEstacaTable):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect("tmp/data/data.db")
            est = con.execute("SELECT x,cota FROM GREIDE WHERE TABLEESTACA_id = ?",(idEstacaTable,)).fetchall()
            con.close()
            compactZIP(Config.fileName)
            return est

        except sqlite3.OperationalError:
            return False


    def getCv(self, idEstacaTable):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect("tmp/data/data.db")
            
            cv = con.execute("SELECT CURVA_id,L FROM CURVA_VERTICAL_DADOS WHERE TABLEESTACA_id = ?",(idEstacaTable,)).fetchall()

            con.close()
            compactZIP(Config.fileName)
            return cv

        except sqlite3.OperationalError:
            return False



    def openCSV(self, filename, fileDB):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + fileDB + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
        con.close()
        compactZIP(Config.fileName)
        self.ultimo = id_estaca[0]
        estacas = []
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        with open(filename, 'r') as fi:
            for r in csv.reader(fi, delimiter=delimiter, dialect='excel'):
                estaca = []
                for field in r:
                    estaca.append(u"%s" % field)
                estacas.append(estaca)
        self.table = estacas
        return estacas

    def saveCSV(self, filename):
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        table=deepcopy(self.table)
        with open(filename[0], "w") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
            for r in table:
                for i,c in enumerate(r[1:]):
                   r[i+1]=c.replace(".",",")
                writer.writerow(r)

        table=deepcopy(self.table)
        with open(filename[0].split(".")[0]+"_WGS84.csv", "w") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
            for r in table:
                pt=pointToWGS84(QgsPointXY(float(str(r[4]).replace(",",'.')),float(str(r[3]).replace(",","."))))
                r[4],r[3]=roundFloat2str(pt.x()),roundFloat2str(pt.y())
                for i,c in enumerate(r[1:]):
                    r[i+1]=c.replace(".",",")
                writer.writerow(r)


    def gera_vertice(self, isCalc):
        prog = 0.0
        sobra = 0.0
        resto = 0.0
        estaca = 0
        cosa = 0.0
        cosb = 0.0
        crs = int(self.getCRS())
        sem_internet = internet_on()

        if hasattr(self, "iface") and sum(1 for f in self.layer.getFeatures())>1 and not isCalc:
            selectFeatureDialog=SelectFeatureDialog(self.iface, self.layer.getFeatures())
            ok = selectFeatureDialog.exec_()
            result=selectFeatureDialog.result
        else:
            result=-1
            ok=True

        if ok:
            f=0
            i=0
            for elemento in self.layer.getFeatures():
                if f!=result and result>-1:
                    f+=1
                    continue
                f+=1
                for seg_start, seg_end, tipo in pairs(elemento, self.estaca):
                    ponto_inicial = QgsPoint(seg_start)
                    ponto_final = QgsPoint(seg_end)
                    tamanho_da_linha = length(ponto_final, ponto_inicial)
                    ponto = diff(ponto_final, ponto_inicial)

                    cosa, cosb = dircos(ponto)
                    az = azimuth(ponto_inicial, QgsPoint(ponto_inicial.x() + ((self.distancia) * cosa),
                                                         ponto_inicial.y() + ((self.distancia) * cosb)))

                    if tamanho_da_linha == 0:
                        continue

                    estacas_inteiras = int(math.floor((tamanho_da_linha - sobra) / self.distancia))
                    estacas_inteiras_sobra = estacas_inteiras + 1 if sobra > 0 else estacas_inteiras
                    if not sem_internet:
                        cota = getElevation(crs, QgsPoint(float(ponto_inicial.x()), float(ponto_inicial.y())))
                        if cota == 0:
                            sem_internet = True
                    else:
                        cota = 0.0
                    yield ['%d+%f' % (estaca, resto) if resto != 0 else '%d' % (estaca), 'v%d' % i, prog, ponto_inicial.y(),
                       ponto_inicial.x(), cota,
                       az], ponto_inicial, estacas_inteiras, prog, az, sobra, tamanho_da_linha, cosa, cosb

                    prog += tamanho_da_linha
                    resto = (tamanho_da_linha - sobra) - (self.distancia * estacas_inteiras)
                    sobra = self.distancia - resto
                    estaca += estacas_inteiras_sobra
                    i+=1

                if result!=-1:
                    break

            i=int(int(i)+1)
            cota = getElevation(crs, QgsPoint(float(ponto_final.x()), float(ponto_final.y())))
            yield ['%d+%f' % (estaca, resto), 'v%d' % i, prog, ponto_final.y(), ponto_final.x(), cota,
                   az], ponto_final, 0, tamanho_da_linha, az, sobra, tamanho_da_linha, cosa, cosb



    def gera_estaca_intermediaria(self, estaca, anterior, prog, az, cosa, cosb, sobra=0.0):
        dist = sobra if sobra > 0 else self.distancia
        p = QgsPoint(anterior.x() + (dist * cosa), anterior.y() + (dist * cosb))
        prog += dist
        return [estaca, '', prog, p.y(), p.x(), 0.0, az], prog, p

    def create_estacas(self, isCalc=False, task=None):
        estacas = []
        estaca = 0
        progressiva = 0

        for vertice, ponto_anterior, qtd_estacas, progressiva, az, sobra, tamanho_da_linha, cosa, cosb in self.gera_vertice(isCalc):
            if task and task.isCanceled():
                return estacas
            estacas.append(vertice)
            if sobra > 0 and sobra < self.distancia and qtd_estacas > 0:
                tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + 1, ponto_anterior,
                                                                                       progressiva, az, cosa, cosb,
                                                                                       sobra)
                estacas.append(tmp_line)
                estaca += 1

            for e in range(qtd_estacas):
                tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + e + 1, ponto_anterior,
                                                                                       progressiva, az, cosa, cosb)
                estacas.append(tmp_line)
            estaca += qtd_estacas
        return estacas

    def tmpFolder(self):
        import tempfile
        from pathlib import Path
        return str(Path(tempfile.gettempdir()+"/"+Config.TMP_FOLDER))

    def saveGeoPackage(self,name:str, poly, fields, type, driver):
        import shutil
        from pathlib import Path

        extractZIP(Config.fileName)
        tmp=str(Path(self.tmpFolder()+name+".gpkg"))
        path=str(Path("tmp/data/"+name+".gpkg"))
        writer = QgsVectorFileWriter(path, 'UTF-8', fields, type, QgsProject.instance().crs(), driver)
        for p in poly:
            writer.addFeature(p)
        del writer
        shutil.copyfile(path, tmp)
        compactZIP(Config.fileName)
        return tmp

    def saveLayerToPath(self, path):
        import shutil
        return shutil.copy(path, self.tmpFolder())

    def removeGeoPackage(self, name):
        extractZIP(Config.fileName)
        from pathlib import Path
        for path in Path("tmp/data/").rglob("*"+Config.RANDOM+name+".gpkg*"):
            path.unlink()
        for path in Path("tmp/data/").rglob(name+".gpkg*"):
            path.unlink()
        compactZIP(Config.fileName)

    def getSavedLayers(self):
        #TODO extract only necessary layers (.gpkg)
        res = [self.iface.addVectorLayer(self.saveLayerToPath(str(path.absolute())),"","ogr")  for path in extractZIP(Config.fileName) if str(path).endswith(".gpkg")]
        compactZIP(Config.fileName)
        return res

    def saveLayer(self, path):
        from pathlib import Path
        import shutil
        path=Path(path.split('|layername=')[0])
        from qgis.core import QgsWkbTypes
       # QgsVectorFileWriter(str(path), 'UTF-8', l.fields(), QgsWkbTypes.displayString(int(l.wkbType())), l.crs(), "GPKG")

        extractZIP(Config.fileName)
        for p in Path(path.parent).rglob("*"):
            shutil.copy(str(p), "tmp/data/")
            p.unlink()
        compactZIP(Config.fileName)
