# -*- coding: utf-8 -*-
import csv
import math
import sqlite3
import json
from builtins import object
from builtins import range
from builtins import str
from copy import deepcopy
from pathlib import Path

from qgis._core import QgsPoint, QgsProject, QgsVectorFileWriter, QgsPointXY

from ..controller.Geometria.Figure import prismoide
from ..model.config import extractZIP, Config, compactZIP
from ..model.curvas import Curvas
from ..model.utils import pairs, length, dircos, diff, azimuth, getElevation, pointToWGS84, roundFloat2str, msgLog, p2QgsPoint
from ..view.estacas import SelectFeatureDialog


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
        self.ask=True

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
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
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
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("INSERT INTO TABLEESTACA (name) values ('" + filename + "')")
        con.commit()
        id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        con.close()
        compactZIP(Config.fileName)
        return id_estaca, []

    def getNewId(self):
         extractZIP(Config.fileName)
         con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
         id_estaca = con.execute("SELECT last_insert_rowid()").fetchone()
         con.close()
         compactZIP(Config.fileName)
         return id_estaca[0]

    def saveEstacas(self,filename,estacas):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
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

    def saveVerticais(self, table):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
            con.execute("DELETE FROM VERTICAIS_TABLE WHERE TABLEESTACA_id=?", (self.id_filename,))

            for linha in table:
                linha=list(linha)
                linha.append(int(self.id_filename))
                lt = tuple(linha)
                con.execute(
                    "INSERT INTO VERTICAIS_TABLE (estaca,descricao,progressiva,greide,TABLEESTACA_id)"
                    "values(?,?,?,?,?)",
                    lt)
            con.isolation_level = None
            con.execute("VACUUM")
            con.isolation_level = ''
            con.commit()

            con.close()
            compactZIP(Config.fileName)

            return True
        except sqlite3.OperationalError:
            return False

    def saveIntersect(self, table):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
            con.execute("DELETE FROM INTERSECT_TABLE WHERE TABLEESTACA_id=?", (self.id_filename,))

            for linha in table:
                linha=list(linha)
                linha.append(int(self.id_filename))
                lt = tuple(linha)
                con.execute(
                    "INSERT INTO INTERSECT_TABLE (estaca,descricao,progressiva,norte,este,greide,cota,"
                    "azimute,TABLEESTACA_id)values(?,?,?,?,?,?,?,?,?)",
                    lt)
            con.isolation_level = None
            con.execute("VACUUM")
            con.isolation_level = ''
            con.commit()

            con.close()
            compactZIP(Config.fileName)
            return True

        except sqlite3.OperationalError:
            return False


    def saveBruckner(self, table):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
            con.execute("DELETE FROM BRUCKNER_TABLE WHERE TABLEESTACA_id=?", (self.id_filename,))

            for linha in table:
                linha=list(linha)
                linha.append(int(self.id_filename))
                lt = tuple(linha)
                con.execute(
                    "INSERT INTO BRUCKNER_TABLE (estaca, volume,TABLEESTACA_id)values(?,?,?)",
                    lt)
            con.isolation_level = None
            con.execute("VACUUM")
            con.isolation_level = ''
            con.commit()

            con.close()
            compactZIP(Config.fileName)
            return True

        except sqlite3.OperationalError:
            return False

    def cleanBruckner(self):
        from pathlib import Path
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH + "tmp/data/data.db")
        con.execute("DELETE FROM BRUCKNER_TABLE WHERE TABLEESTACA_id=?", (self.id_filename,))
        con.isolation_level = None
        con.execute("VACUUM")
        con.isolation_level = ''
        con.commit()
        con.close()
        Path(Config.instance().TMP_DIR_PATH+"tmp/data/"+str(self.id_filename)+".bruck").unlink()
        compactZIP(Config.fileName)
        return True

    def getCurvas(self, id_filename):
        # instancia da model de curvas.
        curva_model = Curvas(id_filename)
        return curva_model.list_curvas()

    def getCRS(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        proj = con.execute("SELECT crs FROM PROJECT where id = 1").fetchone()
        crs = proj[0]
        con.close()
        compactZIP(Config.fileName)
        return crs

    def tipo(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
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

    def recalcular(self, distancia, estaca, layer, ask=True):
        self.__init__(distancia, estaca, layer, self.filename, list(), self.ultimo, self.id_filename)
        self.ask=ask
        self.table = self.create_estacas()
        self.ask=False
        return self.table

    def loadFilename(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        est = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def listTables(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        est = con.execute("SELECT id,name,data FROM TABLEESTACA").fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def load_verticais(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        est = con.execute(
            "select estaca,descricao,progressiva,greide from verticais_table where tableestaca_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def load_terreno_long(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH + "tmp/data/data.db")
        est = con.execute(
            "select descricao,progressiva,cota from ESTACA where tableestaca_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def load_intersect(self, id_filename=None):
        if id_filename is None:
            id_filename=self.id_filename
        if id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        est = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,greide,cota,azimute FROM INTERSECT_TABLE WHERE TABLEESTACA_id = ?",
            (int(id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def load_bruckner(self):
        if self.id_filename == -1: return None
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        est = con.execute(
            "SELECT estaca, volume FROM BRUCKNER_TABLE WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def getNameFromId(self,id):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        name = con.execute("SELECT name FROM TABLEESTACA WHERE id=?", (str(id),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        if name[0][0]:
            return str(name[0][0])
        else:
            return ""

    def deleteEstaca(self, idEstacaTable):
        self.removeGeoPackage(self.getNameFromId(idEstacaTable))
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM TABLEESTACA WHERE id=?", (idEstacaTable,))
        con.execute("DELETE FROM VERTICAIS_TABLE WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM INTERSECT_TABLE WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM RELEVO_SESSAO WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM SESSAO_TIPO WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM TRANSVERSAL WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM CURVA_VERTICAL_DADOS WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM GREIDE WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.execute("DELETE FROM BRUCKNER_TABLE WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.commit()
        con.close()
        from pathlib import Path
        p=Path(Config.instance().TMP_DIR_PATH + "tmp/data/"+str(idEstacaTable)+".prism")
        if p.is_file():
            p.unlink()
        p=Path(Config.instance().TMP_DIR_PATH + "tmp/data/"+str(idEstacaTable)+".bruck")
        if p.is_file():
            p.unlink()
        compactZIP(Config.fileName)


    def save(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("DELETE FROM ESTACA WHERE TABLEESTACA_id=?", (idEstacaTable,))
        con.commit()
        for linha in self.table:
            linha=list(linha)
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
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("DELETE FROM GREIDE WHERE TABLEESTACA_id = ?", (idEstacaTable,))
        con.commit()
        for linha in self.table:
            linha=list(linha)
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

    def cleanGreide(self,id_filename):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("DELETE FROM GREIDE WHERE TABLEESTACA_id = ?", (id_filename,))
        con.commit()
        con.close()
        compactZIP(Config.fileName)

    def saveTrans(self, id_filename, prismoid:prismoide):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")

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
        prismoid.save(Config.instance().TMP_DIR_PATH+"tmp/data/"+str(id_filename)+".prism")
        compactZIP(Config.fileName)



    def cleanTrans(self, idEstacaTable):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")

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
        from pathlib import Path
        p = Path(Config.instance().TMP_DIR_PATH + "tmp/data/" + str(idEstacaTable) + ".prism")
        if p.is_file():
            p.unlink()
        p = Path(Config.instance().TMP_DIR_PATH + "tmp/data/" + str(idEstacaTable) + ".bruck")
        if p.is_file():
            p.unlink()
        compactZIP(Config.fileName)


    def getTrans(self, idEstacaTable):
         try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")

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
            prismoid=prismoide()
            if prismoid.restore(Config.instance().TMP_DIR_PATH+"tmp/data/"+str(idEstacaTable)+".prism"):
                return xList, table, prismoid
            else:
                return xList, table, None
            compactZIP(Config.fileName)

         except:
            return False, False, False
#

    def getGreide(self, idEstacaTable):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
            est = con.execute("SELECT x,cota FROM GREIDE WHERE TABLEESTACA_id = ?",(idEstacaTable,)).fetchall()
            con.close()
            compactZIP(Config.fileName)
            return est

        except sqlite3.OperationalError:
            return False


    def getCv(self, idEstacaTable):
        try:
            extractZIP(Config.fileName)
            con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
            
            cv = con.execute("SELECT CURVA_id,L FROM CURVA_VERTICAL_DADOS WHERE TABLEESTACA_id = ?",(idEstacaTable,)).fetchall()

            con.close()
            compactZIP(Config.fileName)
            return cv

        except sqlite3.OperationalError:
            return False



    def openCSV(self, filename, fileDB):
        extractZIP(Config.fileName)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
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
                    s=str(field).replace(",", ".")
                    estaca.append(u"%s" % s)
                estacas.append(estaca)
        self.table = estacas
        return estacas

    def saveCSV(self, filename, noWGS=False, header=None):
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        table=deepcopy(self.table)
        with open(filename[0], "w") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
            if type(header)==list:
                writer.writerow(header)
            for r in table:
                for i,c in enumerate(r):
                   r[i]=c.replace(".",",")
                writer.writerow(r)

        if not noWGS:
            table=deepcopy(self.table)
            with open(filename[0].split(".")[0]+"_WGS84.csv", "w") as fo:
                writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
                if type(header) == list:
                    writer.writerow(header)
                for r in table:
                    pt=pointToWGS84(QgsPointXY(float(str(r[4]).replace(",",'.')),float(str(r[3]).replace(",","."))))
                    r[4],r[3]=str(pt.x()),str(pt.y())
                    for i,c in enumerate(r):
                        r[i]=c.replace(".",",")
                    writer.writerow(r)


    def gera_vertice(self, isCalc):
        prog = 0.0
        sobra = 0.0
        resto = 0.0
        estaca = 0
        cosa = 0.0
        cosb = 0.0
        crs = int(self.getCRS())
        sem_internet = True# not internet_on()

        if not self.distancia or self.distancia<=0:
            self.distancia=Config.instance().DIST

        if hasattr(self, "iface") and sum(1 for f in self.layer.getFeatures())>1 and not isCalc and self.ask:
            selectFeatureDialog=SelectFeatureDialog(self.iface, self.layer)
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
                    ponto_inicial = p2QgsPoint(seg_start.x(), seg_start.y())
                    ponto_final = p2QgsPoint(seg_end.x(), seg_end.y())
                    tamanho_da_linha = length(ponto_final, ponto_inicial)
                    ponto = diff(ponto_final, ponto_inicial)

                    cosa, cosb = dircos(ponto)
                    az = azimuth(ponto_inicial, p2QgsPoint(ponto_inicial.x() + ((self.distancia) * cosa),
                                                         ponto_inicial.y() + ((self.distancia) * cosb)))

                    if tamanho_da_linha == 0:
                        continue

                    estacas_inteiras = int(math.floor((tamanho_da_linha - sobra) / self.distancia))
                    estacas_inteiras_sobra = estacas_inteiras + 1 if sobra > 0 else estacas_inteiras
                    if not sem_internet:
                        cota = getElevation(crs, p2QgsPoint(float(ponto_inicial.x()), float(ponto_inicial.y())))
                        if cota == 0:
                            sem_internet = True
                    else:
                        cota = 0.0
                    estaca=int(estaca)
                    yield ['%d+%f' % (estaca, resto) if resto != 0 else '%d' % (estaca), 'PI%d' % i, prog, ponto_inicial.y(),
                       ponto_inicial.x(), cota,
                       az], ponto_inicial, estacas_inteiras, prog, az, sobra, tamanho_da_linha, cosa, cosb, tipo, elemento, resto

                    prog += tamanho_da_linha
                    resto = (tamanho_da_linha - sobra) - (self.distancia * estacas_inteiras)
                    sobra = self.distancia - resto
                    estaca += estacas_inteiras_sobra
                    i+=1

                if result!=-1:
                    break
            estaca=int(estaca)
            i=int(int(i)+1)
            cota = getElevation(crs, p2QgsPoint(float(ponto_final.x()), float(ponto_final.y())))
            yield ['%d+%f' % (estaca, resto), 'PI%d' % i, prog, ponto_final.y(), ponto_final.x(), cota,
                   az], ponto_final, 0, tamanho_da_linha, az, sobra, tamanho_da_linha, cosa, cosb, tipo, elemento, resto


    def gera_estaca_intermediaria(self, estaca, anterior, prog, az, cosa, cosb, sobra=0.0):
        dist = sobra if sobra > 0 else self.distancia
        p = p2QgsPoint(anterior.x() + (dist * cosa), anterior.y() + (dist * cosb))
        prog += dist
        return [str(int(estaca)), '', prog, p.y(), p.x(), 0.0, az], prog, p

    def gera_estaca_intermediaria_curva(self, geom, estaca, prog, sobra):
        dist=sobra if sobra > 0 else self.distancia
        initalProg=prog
        pg = geom.interpolate(dist)
        prog += dist
        while pg:
            p = pg.asPoint()
            az = azimuth(p, geom.interpolate(prog-initalProg + 0.001).asPoint())
            yield [str(int(estaca)), '', prog, p.y(), p.x(), 0.0, az], prog, p
            prog += self.distancia
            pg = geom.interpolate(prog-initalProg)
            estaca += 1


    def create_estacas(self, isCalc=False, task=None):
        estacas = []
        estaca = 0
        curvaComputadaCount=0
        curvaCount=0
        vertexCount=0
        progressiva=0
        lastDesc="T"

        for vertice, ponto_anterior, qtd_estacas, progressiva, az, sobra, tamanho_da_linha, cosa, cosb, tipo, feature, resto in self.gera_vertice(isCalc):
            if task and task.isCanceled():
                return estacas

            emCurva=tipo in ["C", "S"]
            desc=lastDesc+tipo
            resto=roundFloat2str(resto)

            if desc in ["TS","TC"]: #Entrou em curva
                vertice[0],vertice[1]=str(estaca)+"+"+str(resto) if estaca else vertice[0],desc+str(vertexCount)
                estacas.append(vertice)

            elif desc in ["ST", "CT"]: #Saiu da curva
                vertice[0],vertice[1]=str(estaca)+"+"+str(resto) if estaca else vertice[0],desc+str(vertexCount)
                estacas.append(vertice)
                vertexCount+=1
                curvaCount+=1

            elif desc in ["SC", "CS"]: #Transição
                 vertice[0],vertice[1]=str(estaca)+"+"+str(resto) if estaca else vertice[0],desc+str(vertexCount)
                 estacas.append(vertice)
                 curvaComputadaCount-=1

            elif not emCurva: #Vértice
                vertice[0],vertice[1]=str(estaca)+"+"+str(resto) if estaca else vertice[0],"PI"+str(vertexCount)
                estacas.append(vertice)
                vertexCount+=1

            if emCurva and curvaComputadaCount==curvaCount:  #Estacas intermediárias internas em curvas
                e=0
                for tmp_line, progressiva, ponto_anterior in self.gera_estaca_intermediaria_curva(feature.geometry(), estaca + 1,
                                                                                     progressiva, sobra):
                    estacas.append(tmp_line)
                    e+=1
                estaca+=e
                curvaComputadaCount+=1

            if not emCurva: #Estacas intermediárias em tangentes
                if sobra > 0 and sobra < self.distancia and qtd_estacas > 0:
                    tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + 1, ponto_anterior,
                                                                                           progressiva, az, cosa, cosb, sobra)
                    estacas.append(tmp_line)
                    estaca += 1

                for e in range(qtd_estacas):
                    tmp_line, progressiva, ponto_anterior = self.gera_estaca_intermediaria(estaca + e + 1, ponto_anterior,
                                                                                           progressiva, az, cosa, cosb)
                    estacas.append(tmp_line)
                estaca += qtd_estacas

            lastDesc=tipo


        return estacas

    def tmpFolder(self):
        import tempfile
        from pathlib import Path
        return str(Path(tempfile.gettempdir()+"/"+Config.TMP_FOLDER))

    def saveGeoPackage(self,name:str, poly, fields, type, driver):
        import shutil
        from pathlib import Path
        extractZIP(Config.fileName)
        tmp=str(Path(self.tmpFolder()+"/"+name+".gpkg"))
        path=str(Path(Config.instance().TMP_DIR_PATH+"tmp/data/"+name+".gpkg"))
        shutil.rmtree(str(path),  ignore_errors=True)
        shutil.rmtree(str(tmp),  ignore_errors=True)
        writer = QgsVectorFileWriter(path, 'UTF-8', fields, type, QgsProject.instance().crs(), driver)
        for p in poly:
            writer.addFeature(p)
        del writer
        shutil.copy(path, tmp)
        shutil.copy(tmp, Config.instance().TMP_DIR_PATH+'tmp/data/'+name+".gpkg")
        compactZIP(Config.fileName)
        return tmp

    def saveLayerToPath(self, path):
        import shutil
        return shutil.copy(path, self.tmpFolder())

    def removeGeoPackage(self, name):
        extractZIP(Config.fileName)
        from pathlib import Path
        for path in Path(Config.instance().TMP_DIR_PATH+"tmp/data/").rglob("*"+Config.RANDOM+name+".gpkg*"):
            path.unlink()
        for path in Path(Config.instance().TMP_DIR_PATH+"tmp/data/").rglob(name+".gpkg*"):
            path.unlink()
        compactZIP(Config.fileName)

    def getSavedLayers(self, name):
        from pathlib import Path
        import shutil

        try:
            shutil.rmtree(Config.instance().TMP_DIR_PATH)
        except Exception as e:
            msgLog("Erro ao remover diretório temporário: "+Config.instance().TMP_DIR_PATH+"    "+str(e))
        Path(Config.instance().TMP_DIR_PATH).mkdir(parents=True, exist_ok=True)

        R = [Path(self.saveLayerToPath(str(path.absolute()))) for path in extractZIP(Config.fileName)
               if (str(path).endswith(".gpkg") or str(path).endswith(".gpkg-shm") or str(path).endswith(".gpkg-wal"))
                and Path(path).stem==name]

        res=[r for r in R if str(r).endswith(".gpkg")]

        if len(res)>1:
            path=res[0]
            for p in res:
                if p.stat().st_mtime>path.stat().st_mtime:
                    path=p
            layer=self.iface.addVectorLayer((str(path.absolute())),"","ogr")
        elif len(res)==1:
            path=res[0]
            layer=self.iface.addVectorLayer((str(path.absolute())),"","ogr")
        else:
            layer=None

        compactZIP(Config.fileName)
        return layer

    def saveLayer(self, path):
        from pathlib import Path
        import shutil
        for name in dir():
            if not name.startswith('_'):
                try:
                    del globals()[name]
                except:
                    pass
#        from qgis.core import *
        path=Path(path.split('|layername=')[0])
        msgLog("Armazenando layer em " + str(path))
        extractZIP(Config.fileName)
        for p in Path(Config.instance().TMP_DIR_PATH+"tmp/data/").rglob("*"):
            if p.stem==path.stem:
                try:
                    p.unlink()
                except:
                    msgLog("Failed to erase " + str(p) + "  at model/estacas.py saveLayer")
        for p in Path(path.parent).rglob("*"):
            shutil.copy(str(p), Config.instance().TMP_DIR_PATH+"tmp/data/")
            try:
                p.unlink()
            except:
                msgLog("Failed to erase "+str(p)+"  at model/estacas.py saveLayer")
        compactZIP(Config.fileName)

    def bruckfilename(self):
        name=str(self.id_filename)
        return Config.instance().TMP_DIR_PATH+'tmp/data/'+name+".bruck"

    '''
    bruck file format reference
    cat 1.bruck (json file)
    
    {"table":[{"estaca":prog2estacaStr(X[0]), "corte": abs(ct), "aterro": abs(at), "at.cor.": abs(at*fh), "soma": "", "semi-distancia": "",
                             "vol.corte":"", "vol.aterro":"", "volume":"", "vol.acum":""}, ......,....],
    "5-30+1.2345":   [], #--> pontos da linha de terra (roi)
    "30+1.2345-50+1":  [],
    "Estaca_interval_string_separated_by_"-"": [],
    .....,....,
    } == bruck

    '''


    def save_bruck(self, bruck):
        msgLog("Salvando arquivo bruckner")
        data=self.load_bruck(True)
        extractZIP(Config.fileName)
        #data.update(bruck)
        bruck['table']=data["table"]
        with open(self.bruckfilename(), 'w') as outfile:
            json.dump(bruck, outfile)
        compactZIP(Config.fileName)

    def load_bruck(self, retry=False):
        from pathlib import Path
        msgLog("Carregando arquivo bruckner")
        extractZIP(Config.fileName)
        data={}
        if Path(self.bruckfilename()).is_file():
            with open(self.bruckfilename()) as json_file:
                data = json.load(json_file)
            compactZIP(Config.fileName)
            return data
        else:
            with open(self.bruckfilename(), 'w') as outfile:
                json.dump(data, outfile)
            compactZIP(Config.fileName)
            if retry:
                msgLog("Falha ao carregar arquivo!")
                return {}
            else:
                return self.load_bruck(retry=True)


