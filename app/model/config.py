# -*- coding: utf-8 -*-
import json
import os
import shutil
import sqlite3
import zipfile
from builtins import object
from builtins import str
from pathlib import Path

from qgis._core import QgsApplication, QgsProject


def extractZIP(filename):
    z = zipfile.ZipFile(filename, "r")
    os.chdir(os.path.dirname(filename))
    if not os.path.exists(Config.instance().TMP_DIR_PATH+'tmp'):
        os.makedirs(Config.instance().TMP_DIR_PATH+'tmp')
    z.extractall(Config.instance().TMP_DIR_PATH+"tmp")
    z.close()
    return Path(Config.instance().TMP_DIR_PATH+'tmp/data/').rglob("*.gpkg*")


def compactZIP(filename):
    z = zipfile.ZipFile(filename, "w")
    os.chdir(os.path.dirname(filename))
    z.write(Config.instance().TMP_DIR_PATH+'tmp/data/data.db','data/data.db',zipfile.ZIP_DEFLATED)
    z.write(Config.instance().TMP_DIR_PATH+'tmp/data/config.json','data/config.json',zipfile.ZIP_DEFLATED)
    tracs=Path(Config.instance().TMP_DIR_PATH+'tmp/data/').rglob("*.gpkg*")
    for trac in tracs:
        z.write(str(trac),'data/'+trac.name,zipfile.ZIP_DEFLATED)
    tracs = Path(Config.instance().TMP_DIR_PATH+'tmp/data/').rglob("*.prism")
    for trac in tracs:
        z.write(str(trac), 'data/' + trac.name, zipfile.ZIP_DEFLATED)
    tracs = Path(Config.instance().TMP_DIR_PATH+'tmp/data/').rglob("*.bruck")
    for trac in tracs:
        z.write(str(trac), 'data/' + trac.name, zipfile.ZIP_DEFLATED)

    z.close()
    shutil.rmtree(Config.instance().TMP_DIR_PATH+'tmp')


class Config(object):
    # Valore padrão

    FILE_PATH=""
    PLUGIN_NAME="GeoRoad"
    fileName = ''
    UNITS = 'm'
    CSV_DELIMITER = ';'
    DIST=20
    RANDOM="__ix35-_-xxx901381asdioADJ398(__"
    TMP_FOLDER="GeoRoadPluginTemporaryLayers/"
    T_SPACING=50
    CLASSE_INDEX=4
    crs = 2676
    planoMin = 0.0
    planoMax = 8.0
    onduladoMin = 8.0
    onduladoMax = 20.0
    montanhosoMin = 20.0
    montanhosoMax = 100.0
    TMP_DIR_PATH = RANDOM
    T_OFFSET = 6
    interpol="True"
    velproj=100.0
    emax=0.08

    #   DADOS para serem armazenados no projeto do qgis.
    #   Cada string nessa lista é criada como um atributo de Config.instance() que pode ser lida por
    #Config.instance().nome e armazenada com Config.instance().store(nome, valor)
    # Chamadas de Config.instance() em loop são pouco eficientes! Não utilizar

    data=["UNITS",
         "CSV_DELIMITER",
         "DIST",
         "T_SPACING",
         "CLASSE_INDEX",
         "crs",
         "planoMin",
         "planoMax",
         "onduladoMin",
         "onduladoMax",
         "montanhosoMin",
         "montanhosoMax",
         "T_OFFSET",
         "FILE_PATH",
          "interpol",
          "velproj",
          'emax',
         "TMP_FOLDER",
         "TMP_DIR_PATH"
          ]



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
                    "cota DOUBLE,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"

                    ")")

        con.execute("CREATE TABLE if not exists CURVA_VERTICAL_DADOS"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "CURVA_id INTEGER,"
                    "L DOUBLE,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")

        con.execute("CREATE TABLE if not exists TRANSVERSAL"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "x DOUBLE,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")

        con.execute("CREATE TABLE if not exists SESSAO_TIPO"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "y DOUBLE,"
                    "cota DOUBLE,"
                    "TRANSVERSAL_id INTEGER,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TRANSVERSAL_id) REFERENCES TRANSVERSAL(id),"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"                 
                    ")")

        con.execute("CREATE TABLE if not exists RELEVO_SESSAO"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "y DOUBLE,"
                    "cota DOUBLE,"
                    "TRANSVERSAL_id INTEGER,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TRANSVERSAL_id) REFERENCES TRANSVERSAL(id),"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"                 
                    ")")

        con.execute("CREATE TABLE if not exists VERTICAIS_TABLE"
                    "(id INTEGER primary key AUTOINCREMENT,"
                    "estaca text,"
                    "descricao text,"
                    "progressiva text,"
                    "greide text,"     
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")

        con.execute("CREATE TABLE if not exists INTERSECT_TABLE"
                    "(id INTEGER primary key AUTOINCREMENT,"                    
                    "estaca text,"
                    "descricao text,"
                    "progressiva text,"
                    "norte text,"
                    "este text,"
                    "greide text,"                   
                    "cota text,"
                    "azimute text,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")

        con.execute("CREATE TABLE if not exists BRUCKNER_TABLE"
                    "(id INTEGER primary key AUTOINCREMENT,"                    
                    "estaca text,"
                    "volume text,"
                    "TABLEESTACA_id INTEGER,"
                    "FOREIGN KEY(TABLEESTACA_id) REFERENCES TABLEESTACA(id)"
                    ")")

        con.commit()
        return con


    def newfile(self, filename):
        self.filename = filename
        if self.filename.endswith('zip'):
            zip_arch_path = u"%s" % filename
        else:
            zip_arch_path = u"%s.zip" % filename
        self.filename = zip_arch_path
        Config.fileName = self.filename
        f = open(zip_arch_path, 'w')
        f.write('')
        f.close()
        os.chdir(os.path.dirname(zip_arch_path))
        if os.path.exists(Config.instance().TMP_DIR_PATH+'tmp'):
            shutil.rmtree(Config.instance().TMP_DIR_PATH+'tmp')
        z = zipfile.ZipFile(zip_arch_path, "w")
        if not os.path.exists(Config.instance().TMP_DIR_PATH+'tmp/data'):
            os.makedirs(Config.instance().TMP_DIR_PATH+'tmp/data')
        os.chdir(Config.instance().TMP_DIR_PATH+'tmp')

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
            })
            outfile.write(j)

        z.write('data/data.db', "data/data.db", zipfile.ZIP_DEFLATED)
        z.write('data/config.json', "data/config.json", zipfile.ZIP_DEFLATED)
        os.chdir('..')
        z.close()
        shutil.rmtree(Config.instance().TMP_DIR_PATH+'tmp')

    def openfile(self, filename):
        self.filename = filename
        Config.fileName = self.filename
        extractZIP(filename)
        self.create_datatable(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
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
        with open(Config.instance().TMP_DIR_PATH+'tmp/data/config.json', 'r') as outfile:
            dados = json.load(outfile)
            self.CSV_DELIMITER = dados['csv_delimiter']
            self.UNITS = dados['units']
            Config.UNITS = self.UNITS
            Config.CSV_DELIMITER = self.CSV_DELIMITER
        shutil.rmtree(Config.instance().TMP_DIR_PATH+'tmp')

    def savefile(self, fromf=None):
        if fromf==None:
            if self.filename in [None,'']:
                raise Exception(u'Não é possivel salvar pois não foi aberto ou criado um novo arquivo')
            extractZIP(self.filename)
        else:
            extractZIP(fromf)
        con = sqlite3.connect(Config.instance().TMP_DIR_PATH+"tmp/data/data.db")
        con.execute("UPDATE PROJECT SET crs=?,classeprojeto=?,maxplano=?,maxondulado=?,maxmontanhoso=?,tipomapa=? WHERE id=1",(self.crs,self.class_project,self.dataTopo[1],self.dataTopo[3],self.dataTopo[5],self.tipo_mapa))
        con.commit()
        con.close()
        Config.UNITS = self.UNITS
        Config.CSV_DELIMITER = self.CSV_DELIMITER
        dados = {}
        dados['csv_delimiter']= self.CSV_DELIMITER
        dados['units'] = self.UNITS
        with open(Config.instance().TMP_DIR_PATH+'tmp/data/config.json', 'w') as outfile:
            json_formatado = json.dumps(dados)
            outfile.write(json_formatado)

        z = zipfile.ZipFile(u"%s" % self.filename, "w")
        z.write(Config.instance().TMP_DIR_PATH+'tmp/data/data.db','data/data.db',zipfile.ZIP_DEFLATED)
        z.write(Config.instance().TMP_DIR_PATH+'tmp/data/config.json','data/config.json',zipfile.ZIP_DEFLATED)
        tracs = Path(Config.instance().TMP_DIR_PATH + 'tmp/data/').rglob("*.gpkg*")
        for trac in tracs:
            z.write(str(trac), 'data/' + trac.name, zipfile.ZIP_DEFLATED)
        tracs = Path(Config.instance().TMP_DIR_PATH + 'tmp/data/').rglob("*.prism")
        for trac in tracs:
            z.write(str(trac), 'data/' + trac.name, zipfile.ZIP_DEFLATED)
        tracs = Path(Config.instance().TMP_DIR_PATH + 'tmp/data/').rglob("*.bruck")
        for trac in tracs:
            z.write(str(trac), 'data/' + trac.name, zipfile.ZIP_DEFLATED)
        z.close()
        shutil.rmtree(Config.instance().TMP_DIR_PATH+'tmp')

    def listCRS(self, txt=''):
        con = sqlite3.connect(QgsApplication.srsDatabaseFilePath())
        cur = con.cursor()
        cur.execute(
            "select description, srs_id from vw_srs where description like '%" + txt + "%' ORDER BY srs_id limit 0,30")
        crs = self.rowCRS = cur.fetchall()

        return crs

    def listCRSID(self):
        txt = 'select description from vw_srs where srs_id=' + str(self.crs)
        con = sqlite3.connect(QgsApplication.srsDatabaseFilePath())
        cur = con.cursor()
        cur.execute(txt)
        f = cur.fetchone()
        con.close()
        return '' if f is None else f[0]

    def itemClick(self, crs):
        self.crs = crs

    def mudancaClasseProjeto(self, pos):
        self.class_project = pos - 1

    def store(self, key, value):
        assert len(key) > 0 and type(key) == str and key in self.data, "Invalid key!"
        if key=="interpol":
            proj = QgsProject.instance()
            proj.writeEntry(Config.PLUGIN_NAME, key, str(int(value)))
        else:
            proj = QgsProject.instance()
            proj.writeEntry(Config.PLUGIN_NAME, key, str(value))

    def read(self, key):
        assert len(key) > 0 and type(key) == str and key in self.data, "Invalid key!"
        proj = QgsProject.instance()
        value : str
        value = proj.readEntry(Config.PLUGIN_NAME, key, str(getattr(Config, key)))[0]
        if value.isdigit():
            value=int(value)
        else:
            try:
                value=float(value)
            except:
                pass
        setattr(self, key, value)
        return value

    @classmethod
    def instance(cls):
        cfg=cls()
        for d in cfg.data:
            cfg.read(d)
            setattr(Config, d, getattr(cfg, d))
        Config.fileName = cfg.FILE_PATH
        try:
            cfg.interpol = bool(int(cfg.interpol))
        except ValueError:
            if cfg.interpol=='False':
                cfg.interpol = False
            if cfg.interpol=='True':
                cfg.interpol = True
        return cfg

