# -*- coding: utf-8 -*-
import json
import os
import shutil
import sqlite3
import zipfile

from qgis._core import QgsApplication


def extractZIP(filename):
    z = zipfile.ZipFile(filename, "r")
    os.chdir(os.path.dirname(filename))
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    z.extract('data/data.db', 'tmp')
    z.extract('data/config.json', 'tmp')


def compactZIP(filename):
    z = zipfile.ZipFile(filename, "w")
    os.chdir(os.path.dirname(filename))
    z.write('tmp/data/data.db','data/data.db',zipfile.ZIP_DEFLATED)
    z.write('tmp/data/config.json','data/config.json',zipfile.ZIP_DEFLATED)
    shutil.rmtree('tmp')


class Config:
    fileName = ''
    UNITS = 'm'
    CSV_DELIMITER = ';'
    

    def __init__(self):
        self.crs = 2676
        self.class_project = -1
        self.dataTopo = [
            0.0,
            8.0,
            8.0,
            20.0,
            20.0,
            100.0
        ]
        self.rowCRS = self.listCRS()
        #self.tableCRS = self.tableCRS
        #self.comboClasse = self.comboClasse
        self.filename = ""
        self.tipo_mapa = 3
        self.ordem_mapa = [3, 1, 10, 9]
        self.ordem_units = ['m','km', 'mm']
        Config.fileName = self.filename
        self.UNITS = 'm'
        self.CSV_DELIMITER = ';'
        Config.UNITS = self.UNITS
        Config.CSV_DELIMITER = self.CSV_DELIMITER

    def create_datatable(self,dbPath='data/data.db'):
        con = sqlite3.connect(dbPath)
        con.execute("CREATE TABLE if not exists PROJECT"
                    "(id INTEGER primary key AUTOINCREMENT, crs varchar(255), "
                    "classeprojeto int,"
                    " maxplano double,"
                    " minplano double,"
                    "maxondulado double,"
                    " minondulado double,"
                    " maxmontanhoso double,"
                    " minmontanhoso double,"
                    " tipomapa int )")

        con.execute("CREATE TABLE if not exists TABLEESTACA"
                    "(id INTEGER primary key AUTOINCREMENT,name varchar(255),"
                    "data DATETIME DEFAULT CURRENT_TIMESTAMP)")
        con.execute("CREATE TABLE if not exists ESTACA"
                    "(id INTEGER primary key AUTOINCREMENT,estaca varchar(255),"
                    "descricao text,"
                    "progressiva text,"
                    "norte text,"
                    "este text,"
                    "cota text,"
                    "azimute text,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")
        con.execute("CREATE TABLE if not exists TABLECURVA"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "TABLEESTACA_id INTEGER,"
                    "data DATETIME DEFAULT CURRENT_TIMESTAMP,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"

                    ")")
        con.execute("CREATE TABLE if not exists CURVA"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "tipo INTEGER,"
                    "estaca_inicial_id INTEGER,"
                    "estaca_final_id INTEGER,"
                    "velocidade INTEGER,"
                    "raio_utilizado DOUBLE,"
                    "emax DOUBLE,"
                    "TABLECURVA_id INTEGER,"
                    "data DATETIME DEFAULT CURRENT_TIMESTAMP,"
                    "FOREIGN KEY(estaca_inicial_id) REFERENCES ESTACA(id)"
                    "FOREIGN KEY(estaca_final_id) REFERENCES ESTACA(id)"
                    "FOREIGN KEY(TABLECURVA_id) REFERENCES TABLECURVA(id)"
                    ")")
        con.execute("CREATE TABLE if not exists CURVA_SIMPLES"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "g20 DOUBLE,"
                    "t DOUBLE,"
                    "d DOUBLE,"
                    "epi DOUBLE,"
                    "epc DOUBLE,"
                    "ept DOUBLE,"
                    "CURVA_id INTEGER,"
                    "data DATETIME DEFAULT CURRENT_TIMESTAMP,"
                    "FOREIGN KEY(CURVA_id) REFERENCES CURVA(id)"
                    ")")
        con.execute("CREATE TABLE if not exists GREIDE"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "x DOUBLE,"
                    "cota DOUBLE"
                    ")")
## TABELA A IMPLEMENTAR:
        con.execute("CREATE TABLE if not exists CURVA_VERTICAL"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "x DOUBLE,"
                    "cota DOUBLE"
                    ")")

        con.commit()
        return con


    def newfile(self, filename):
        self.filename = filename
        if self.filename.endswith('lzip'):
            zip_arch_path = u"%s" % filename
        else:
            zip_arch_path = u"%s.lzip" % filename
        self.filename = zip_arch_path
        Config.fileName = self.filename
        f = open(zip_arch_path, 'w')
        f.write('')
        f.close()
        os.chdir(os.path.dirname(zip_arch_path))
        if os.path.exists('tmp'):
            shutil.rmtree('tmp')
        z = zipfile.ZipFile(zip_arch_path, "w")
        if not os.path.exists('tmp/data'):
            os.makedirs('tmp/data')
        os.chdir('tmp')

        con = self.create_datatable()
        res = con.execute("SELECT id FROM PROJECT").fetchall()
        if res is None or len(res)==0:
            con.execute("INSERT INTO PROJECT"
                        "(id,crs,classeprojeto,maxplano,minplano,"
                        "maxondulado,minondulado,maxmontanhoso,"
                        "minmontanhoso,tipomapa)"
                        "values (1,31983,0,8.0,0.0,20.0,8.0,100.0,20.0,3)")
            con.commit()

        con.close()

        with open('data/config.json', 'w') as outfile:
            j = json.dumps({
                'csv_delimiter': ';',
                'units': 'm'
            },outfile)
            outfile.write(j)

        z.write('data/data.db', "data/data.db", zipfile.ZIP_DEFLATED)
        z.write('data/config.json', "data/config.json", zipfile.ZIP_DEFLATED)
        os.chdir('..')
        z.close()
        shutil.rmtree('tmp')

    def openfile(self, filename):
        self.filename = filename
        Config.fileName = self.filename
        extractZIP(filename)
        self.create_datatable("tmp/data/data.db")
        con = sqlite3.connect("tmp/data/data.db")
        cur = con.execute("SELECT crs, classeprojeto, maxplano,maxondulado,maxmontanhoso,tipomapa FROM PROJECT")
        proj = cur.fetchone()
        self.crs = proj[0]
        self.class_project = proj[1]
        self.dataTopo = [
            0.0,
            proj[2],
            proj[2],
            proj[3],
            proj[3],
            proj[4]
        ]
        con.close()
        self.tipo_mapa = proj[5]
        with open('tmp/data/config.json', 'r') as outfile:
            dados = json.load(outfile)
            self.CSV_DELIMITER = dados['csv_delimiter']
            self.UNITS = dados['units']
            Config.UNITS = self.UNITS
            Config.CSV_DELIMITER = self.CSV_DELIMITER
        shutil.rmtree('tmp')

    def savefile(self):
        if self.filename in [None,'']:
            raise Exception(u'Não é possivel salvar pois não foi aberto ou criado um novo arquivo')
        extractZIP(self.filename)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("UPDATE PROJECT SET crs=?,classeprojeto=?,maxplano=?,maxondulado=?,maxmontanhoso=?,tipomapa=? WHERE id=1",(self.crs,self.class_project,self.dataTopo[1],self.dataTopo[3],self.dataTopo[5],self.tipo_mapa))
        con.commit()
        con.close()
        Config.UNITS = self.UNITS
        Config.CSV_DELIMITER = self.CSV_DELIMITER
        dados = {}
        dados['csv_delimiter']= self.CSV_DELIMITER
        dados['units'] = self.UNITS
        with open('tmp/data/config.json', 'w') as outfile:
            json_formatado = json.dumps(dados)
            outfile.write(json_formatado)

        z = zipfile.ZipFile(u"%s" % self.filename, "w")
        z.write('tmp/data/data.db','data/data.db',zipfile.ZIP_DEFLATED)
        z.write('tmp/data/config.json','data/config.json',zipfile.ZIP_DEFLATED)
        z.close()
        shutil.rmtree('tmp')

    def listCRS(self, txt=''):
        con = sqlite3.connect(QgsApplication.srsDbFilePath())
        cur = con.cursor()
        cur.execute(
            "select description, srs_id from vw_srs where description like '%" + txt + "%' ORDER BY srs_id limit 0,30")
        crs = self.rowCRS = cur.fetchall()

        return crs

    def listCRSID(self):
        txt = 'select description from vw_srs where srs_id=' + str(self.crs)
        con = sqlite3.connect(QgsApplication.srsDbFilePath())
        cur = con.cursor()
        cur.execute(txt)
        f = cur.fetchone()
        con.close()
        return '' if f is None else f[0]

    def itemClick(self, crs):
        self.crs = crs

    def mudancaClasseProjeto(self, pos):
        self.class_project = pos - 1

