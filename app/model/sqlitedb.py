import sqlite3
from pathlib import Path
from copy import copy

class DB():
    def __init__(self, caminhoDoArquivo, tableName, dataNameList):    
            '''caminhoDoArquivo: String com o caminho do arquivo
               tableName: String com o nome da tabela
               dataNameList: Lista de strings com  os nomes de cada atributo
            '''
            self.filepath=caminhoDoArquivo
            self.tableName=tableName
            self.dataNameList=dataNameList
            self.checkIfExistsIfNotCreate()

    def toDict(self, data):        
            return {n : data[i] for i, n in enumerate(self.dataNameList)}

    def toDictComId(self, data):        
            return {n : data[i] for i, n in enumerate(["id"]+self.dataNameList)}

           
    def toList(self, data):
            return [data[n] if n in data.keys() else "" for n in self.dataNameList]            


    def checkIfExistsIfNotCreate(self):				
            self.connect()
            try:
                self.cursor.execute("SELECT * FROM "+self.tableName)
                col_name_list = [tuple[0] for tuple in self.cursor.description]
                col_name_list.remove('id')
            except:
                col_name_list=[]
            self.close()
            if not sorted(col_name_list)==sorted(self.dataNameList):
                self.apagarTabela()
                self.connect()
                self.cursor.execute("CREATE TABLE IF NOT EXISTS " + self.tableName +
                    " (id INTEGER primary key AUTOINCREMENT,"+ str(self.dataNameList)[1:-1] +")")
                self.close()

    
    def connect(self):
            self.connection = sqlite3.connect(self.filepath)
            self.cursor = self.connection.cursor()
            self.connected = True
    
    def close(self):
            self.connection.commit()
            self.connection.close()
            self.connected = False
    
    def _salvarDado(self, dado):
            dado=self.toList(dado)
            self.cursor.execute("INSERT INTO "+self.tableName+" ("+str(self.dataNameList)[1:-1] +")VALUES (" + (len(self.dataNameList)*"?,")[:-1]+")", dado)		

    def salvarDado(self, dado):
           # assert len(dado)==len(self.dataNameList), "ERRO: O dado deve ter o tamanho " + str(len(self.dataNameList))
            self.connect()
            self._salvarDado(dado)
            id=copy(self.cursor.lastrowid)
            self.close()
            return id


    def salvarDados(self, lista): 
            self.connect()
            [self._salvarDado(dado) for dado in lista]
            self.close()

    def _getDado(self, id):
            return self.toDict(list(list(self.cursor.execute("SELECT * FROM " + self.tableName + " WHERE id = ?", (id,)))[0])[1:])
                                
    def getDado(self, id):
            self.connect()
            dado=self._getDado(id)
            self.close()
            return dado

    def getDadoComId(self, id):
            self.connect()
            dado=self._getDado(id)
            self.close()
            dado.update({"id": id})
            return dado

    def todosOsDados(self):
            self.connect()
            dados = [self.toDict(row[1:]) for row in self.cursor.execute("SELECT * FROM "+ self.tableName)]
            self.close()
            return dados

    def todosOsDadosComId(self):
            self.connect()
            dados = [self.toDictComId(row) for row in self.cursor.execute("SELECT * FROM "+ self.tableName)]
            self.close()
            return dados
        

                    
    def acharDado(self, key, nome): 
            func=str
            try:
                float(nome)
                func=float
            except:
                pass           
            self.connect()					
            if type(nome)==str:
                key=key
                idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if nome.lower() in str(self.toDict(list(dado)[1:])[key]).lower()]
            else:
                idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if str(nome) == str(self.toDict(list(dado)[1:])[key])]
            self.close()			
            try:
                return [x[0] for x in sorted(idList, key=lambda x: func(x[1]))]
            except ValueError as e:
                return [x[0] for x in sorted(idList, key=lambda x: str(x[1]))]


    def acharDadoExato(self, key, nome): 
            func=str
            try:
                float(nome)
                func=float
            except:
                pass           
            self.connect()					
            if type(nome)==str:
                key=key
                idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if nome.lower() == str(self.toDict(list(dado)[1:])[key]).lower()]
            else:
                idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if str(nome) == str(self.toDict(list(dado)[1:])[key])]
            self.close()			
            try:
                return [x[0] for x in sorted(idList, key=lambda x: func(x[1]))]
            except ValueError as e:
                return [x[0] for x in sorted(idList, key=lambda x: str(x[1]))]





    def getDados(self, listaDeIds):
            return [self.getDado(id) for id in listaDeIds]

    def getDadosComId(self, listaDeIds):
            return [self.getDadoComId(id) for id in listaDeIds]
    
    def acharDados(self, key, nome):
            return sorted(self.getDados(self.acharDado(key, nome)), key=lambda x: x[key])

    def acharMaiorQue(self, key, valor): 
        assert type(valor) == int or type(valor) == float, "Entre com valores numéricos"
        self.connect()
        idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if float(valor) <= float(self.toDict(list(dado)[1:])[key])]
        self.close()			
        return [x[0] for x in sorted(idList, key=lambda x: x[1])]

    def acharMenorQue(self, key, valor):    
        assert type(valor) == int or type(valor) == float, "Entre com valores numéricos"
        self.connect()
        idList=[[list(dado)[0], self.toDict(list(dado)[1:])[key]] 
                        for dado in list(self.cursor.execute("SELECT * FROM "+self.tableName)) 
                        if float(valor) >= float(self.toDict(list(dado)[1:])[key])]
        self.close()			
        return [x[0] for x in sorted(idList, key=lambda x: x[1])]

    def acharDadosMaioresQue(self,key,valor):
        return sorted(self.getDados(self.acharMaiorQue(key, valor)), key=lambda x: x[key])

    def acharDadosMenoresQue(self,key,valor):
        return sorted(self.getDados(self.acharMenorQue(key, valor)), key=lambda x: x[key])
   
    def apagarDado(self, id):
            self.connect()
            id=str(id)
            self.cursor.execute("DELETE FROM "+ self.tableName +" WHERE ID = ?", (id,))		
            self.close()			

    def update(self, id, dado):
        '''
        id do dado a se modificar
        dado: pode ser um dicionário só com as modificações
        '''     
        d=self.getDado(id)
        d.update(dado)
        d=self.toList(d)
        self.connect()
        self.cursor.execute("UPDATE "+ self.tableName +" SET " + " = ?,".join(self.dataNameList) +"= ? WHERE id= ?",
                (d+[id]))
        self.close()

    def apagarTabela(self):
            self.connect()
            self.cursor.execute("DROP TABLE IF EXISTS "+ self.tableName)		
            self.close()			       

    def apagarTudo(self):	
            Path(self.filepath).unlink()




def test():
     caminho='/home/matheus/test.db'

     attr=["nome", "matricula", "dataNasc", "RG", "CPF", "nomeDaMae", "nomeDoPai", "telefone", "endereco",
 "serie", "escola", "idade", "lat", "long"] 
     db=DB(caminho, 'haha', attr)   

     d1={"nome":'majose', "matricula":"ER215", "dataNasc":'12/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":2, "escola":1, "idade":13, "lat":-19.231, "long":47.12331}
     d2={"nome":'matheus', "matricula":"ER128", "dataNasc":'17/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":5, "escola":1, "idade":21, "lat":-19.231, "long":47.12331}
     d3={"nome":'carlos', "matricula":"ER125", "dataNasc":'18/05/87', "RG":'askfasj1545', "CPF":'15618684',
      "nomeDaMae":'josefina', "nomeDoPai":'Jão', "telefone":'121839128', "endereco":'fksdkf 239j 29r',
 "serie":8, "escola":3, "idade":15, "lat":-19.231, "long":47.12331}

     db.salvarDados([d1,d2,d3]) 
     print("TODOS: \n", db.todosOsDados(), "\n\n")
     print("Nomes com ma: \n", db.acharDados('nome', 'ma'), "\n\n")
     print("Idade 13 \n", db.acharDados('idade', 13), "\n\n")
     print("Idade maior que 14: \n", db.acharDadosMaioresQue('idade', 14), "\n\n")
     print("Idade menor que 14: \n", db.acharDadosMenoresQue('idade', 14), "\n\n")
     id=db.acharDado('nome','matheus')[0]
     db.update(id, {'idade': 40})
     print("dado matheus atualizado: \n", db.getDado(id), "\n\n")  
     db.apagarDado(id)
     print("Matheus Excluído: \n", db.todosOsDados(), "\n\n")
     print("Dados com id \n", db.todosOsDadosComId(), "\n\n")
     print("Dados com id 3 \n", db.getDadoComId(3), "\n\n")
     id=db.salvarDado(d1)
     print("ultimo id: ", id)

     db.apagarTabela()
     db.apagarTudo()

if __name__=="__main__":    
     test()