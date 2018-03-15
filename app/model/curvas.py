# -*- coding: utf-8 -*-
import sqlite3
import math
import csv

from ..model.config import extractZIP, Config, compactZIP


class Curvas:
    def __init__(self, id_filename):
        self.id_filename = id_filename

    def list_curvas(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        curvas = con.execute(
            "SELECT CURVA.id,CURVA.tipo,CURVA.velocidade,CURVA.raio_utilizado,CURVA.emax,CURVA.estaca_inicial_id,CURVA.estaca_final_id FROM CURVA INNER JOIN TABLECURVA ON CURVA.TABLECURVA_id=TABLECURVA.id WHERE TABLECURVA.TABLEESTACA_id=%d" % self.id_filename).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return curvas

    def get_curva_details(self,id_estaca=-1,id_curva=-1):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        if id_curva == -1:
            curva = con.execute("SELECT CURVA_id,g20,t,d,epi,epc,ept FROM CURVA_SIMPLES INNER JOIN CURVA ON CURVA_SIMPLES.CURVA_id=CURVA.id WHERE estaca_final_id=%d"%(id_estaca,)).fetchall()
        else:
            curva = con.execute("SELECT CURVA_id,g20,t,d,epi,epc,ept FROM CURVA_SIMPLES INNER JOIN CURVA ON CURVA_SIMPLES.CURVA_id=CURVA.id WHERE CURVA.id=%d"%(id_curva,)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        if len(curva)>0:
            return curva[0]
        else:
            return None

    def get_curva(self, id_curva):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        curva = con.execute(
            "SELECT CURVA.id,CURVA.tipo,CURVA.velocidade,CURVA.raio_utilizado,CURVA.emax,CURVA.estaca_inicial_id,CURVA.estaca_final_id FROM CURVA WHERE CURVA.id = ?",
            (id_curva,)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        if len(curva) > 0:
            return curva[0]
        else:
            return None

    #LISTA OS VERTICES
    def list_estacas(self):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        est = con.execute(
            "SELECT id,estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ? AND (estaca LIKE '%%+%%' OR estaca LIKE '0')",
            (int(self.id_filename),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return est

    def get_estaca_by_id(self,ident):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        estacas = con.execute(
            "SELECT id,estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE id = ?",
            (int(ident),)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        return [] if len(estacas)==0 else estacas[0]

    def get_estacas_interval(self,de,ate):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        
        estacas = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ? AND (cast(progressiva as REAL)>=? OR cast(progressiva as REAL)<=?)",
            (int(self.id_filename),float(de),float(ate))).fetchall()
        
        con.close()
        compactZIP(Config.fileName)
        return estacas

    def gera_estacas_intermediarias(self,dist,epc,ept,g20):
        estacas = []
        estaca_start_vert = epc//dist
        estaca_end_vert = ept//dist
        estaca_start_sobra = float((epc/dist)-estaca_start_vert)*dist
        estaca_end_sobra = float((ept/dist)-estaca_end_vert)*dist
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        estaca_start = con.execute(
            "SELECT id,estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ? AND estaca LIKE ?",
            (int(self.id_filename),'%d%%'%estaca_start_vert)).fetchall()
        estaca_end = con.execute(
            "SELECT id,estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE TABLEESTACA_id = ? AND estaca LIKE ?",
            (int(self.id_filename),'%d%%'%estaca_end_vert)).fetchall()
        con.close()
        compactZIP(Config.fileName)
        estaca_inicial_north = float(estaca_start[0][4])+(epc-float(estaca_start[0][3]))*math.cos(float(estaca_start[0][7])*math.pi/180)
        estaca_inicial_este = float(estaca_start[0][5])+(epc-float(estaca_start[0][3]))*math.sin(float(estaca_start[0][7])*math.pi/180)
        estaca_inicial = [
                            '%d+%f'%(estaca_start_vert,estaca_start_sobra),
                            'epc',
                            '%f'%epc,
                            '%f'%estaca_inicial_north,
                            '%f'%estaca_inicial_este,
                            '%f'%float(estaca_start[0][6]),
                            '%f'%float(estaca_start[0][7])
                        ]
        estacas.append(estaca_inicial)
        deflexao_acumulada = 0.0
        progressiva = float(estaca_start[0][3])
        est = estaca_start_vert
        for i in range(abs(int(estaca_end_vert-estaca_start_vert))):
            progressiva+=dist
            est += 1
            deflexao = (float(dist)-estaca_start_sobra)*(g20/40) if deflexao_acumulada == 0.0 else (g20/2)
            deflexao_acumulada += deflexao

            azimute = float(estaca_start[0][7])-deflexao_acumulada
            north = float(estaca_start[0][4])+(progressiva-float(estaca_start[0][3]))*math.cos(float(azimute)*math.pi/180)
            este = float(estaca_start[0][5])+(progressiva-float(estaca_start[0][3]))*math.sin(float(azimute)*math.pi/180)
            estaca = [
                            '%d'%est,
                            '',
                            '%f'%progressiva,
                            '%f'%north,
                            '%f'%este,
                            '%f'%float(estaca_start[0][6]),
                            '%f'%azimute
                        ]
            estacas.append(estaca)

        deflexao = estaca_end_sobra*(g20/40.)
        deflexao_acumulada += deflexao
        azimute = float(estaca_start[0][7])-deflexao_acumulada
        estaca_end_north = float(estaca_start[0][4])+(epc-float(estaca_start[0][3]))*math.cos(float(azimute)*math.pi/180)
        estaca_end_este = float(estaca_start[0][5])+(epc-float(estaca_start[0][3]))*math.sin(float(azimute)*math.pi/180)
        
        estaca = [
                            '%d+%f'%(estaca_end_vert,estaca_end_sobra),
                            'ept',
                            '%f'%ept,
                            '%f'%estaca_end_north,
                            '%f'%estaca_end_este,
                            '%f'%float(estaca_start[0][6]),
                            '%f'%azimute
                        ]
        estacas.append(estaca)
        return estacas

    def gera_estacas(self,dist):
        curvas = self.list_curvas() 
        estacas = []
        indice = 0
        for curva in curvas:
            curva_detalhes = self.get_curva_details(id_curva=int(curva[0]))
            if curva_detalhes is None:
                continue
            estaca_inicial = self.get_estaca_by_id(int(curva[5]))
            estaca_final = self.get_estaca_by_id(int(curva[6]))
            estacas_ant = self.get_estacas_interval(float(estaca_inicial[3]),float(estaca_final[3]))
            estacas.extend(estacas_ant)
            
            g20 = float(curva_detalhes[1])
            epc = float(curva_detalhes[5])
            ept = float(curva_detalhes[6])

            estacas.extend(self.gera_estacas_intermediarias(dist,epc,ept,g20))
        return estacas

    def save_CSV(self, filename, estacas):
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        with open(filename, "wb") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect='excel')
            for r in estacas:
                writer.writerow(r)

    def delete_curva(self, id_curva):
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        con.execute("DELETE FROM CURVA WHERE id=?", (id_curva,))
        con.commit()
        con.close()
        compactZIP(Config.fileName)
        return True

    def new(self, tipo, estaca1_id, estaca2_id, velocidade, rutilizado, emax, paramCurva):
        '''Verifico se há curva para o traçado'''
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        curvaTracado = con.execute(
            "SELECT id FROM TABLECURVA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        if curvaTracado is None or len(curvaTracado) == 0:
            # insiro a curvaTracado
            con.execute("INSERT INTO TABLECURVA (TABLEESTACA_id) VALUES (?)", (int(self.id_filename),))
            con.commit()
        curvaTracado = con.execute(
            "SELECT id FROM TABLECURVA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()[0]
        estaca1 = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE id = ?",
            (int(estaca1_id),)).fetchall()
        estaca2 = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE id = ?",
            (int(estaca2_id),)).fetchall()

        con.execute(
            "INSERT INTO CURVA (TABLECURVA_id,estaca_inicial_id,estaca_final_id,tipo,velocidade,raio_utilizado,emax) values (?,?,?,?,?,?,?)",
            (curvaTracado[0], estaca1_id, estaca2_id, tipo, velocidade, rutilizado, emax))
        con.commit()
        id_curva = con.execute("SELECT last_insert_rowid()").fetchall()[0]

        if tipo == 0:
            con.execute("INSERT INTO CURVA_SIMPLES (CURVA_id,g20,t,d,epi,epc,ept) VALUES (?,?,?,?,?,?,?)", (
                id_curva[0], paramCurva['g20'], paramCurva['t'], paramCurva['d'], paramCurva['epi'], paramCurva['epc'],
                paramCurva['ept']))
            con.commit()
        con.close()
        compactZIP(Config.fileName)

    def edit(self, id_curva, tipo, estaca1_id, estaca2_id, velocidade, rutilizado, emax, paramCurva):
        '''Verifico se há curva para o traçado'''
        extractZIP(Config.fileName)
        con = sqlite3.connect("tmp/data/data.db")
        curvaTracado = con.execute(
            "SELECT id FROM TABLECURVA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()
        if curvaTracado is None or len(curvaTracado) == 0:
            # insiro a curvaTracado
            con.execute("INSERT INTO TABLECURVA (TABLEESTACA_id) VALUES (?)", (int(self.id_filename),))
            con.commit()
        curvaTracado = con.execute(
            "SELECT id FROM TABLECURVA WHERE TABLEESTACA_id = ?",
            (int(self.id_filename),)).fetchall()[0]
        estaca1 = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE id = ?",
            (int(estaca1_id),)).fetchall()
        estaca2 = con.execute(
            "SELECT estaca,descricao,progressiva,norte,este,cota,azimute FROM ESTACA WHERE id = ?",
            (int(estaca2_id),)).fetchall()

        con.execute(
            "UPDATE CURVA SET TABLECURVA_id=?,estaca_inicial_id=?,estaca_final_id=?,tipo=?,velocidade=?,raio_utilizado=?,emax=? WHERE id = ?",
            (curvaTracado[0], estaca1_id, estaca2_id, tipo, velocidade, rutilizado, emax, id_curva))
        con.commit()
        #id_curva = con.execute("SELECT last_insert_rowid()").fetchall()[0]

        if tipo == 0:
            # verifica se tem uma curva simples cadastrada com o id.
            res = con.execute("SELECT * FROM CURVA_SIMPLES WHERE CURVA_id = %d"%(id_curva,)).fetchall()
            if len(res) == 0:
                con.execute("INSERT INTO CURVA_SIMPLES (CURVA_id,g20,t,d,epi,epc,ept) VALUES (?,?,?,?,?,?,?)", (
                    id_curva, paramCurva['g20'], paramCurva['t'], paramCurva['d'], paramCurva['epi'], paramCurva['epc'],
                    paramCurva['ept']))
            else:
                con.execute("UPDATE CURVA_SIMPLES SET g20=?,t=?,d=?,epi=?,epc=?,ept=? WHERE CURVA_id=?", (
                    paramCurva['g20'], paramCurva['t'], paramCurva['d'], paramCurva['epi'], paramCurva['epc'],
                    paramCurva['ept'], id_curva))
            con.commit()
        con.close()
        compactZIP(Config.fileName)
