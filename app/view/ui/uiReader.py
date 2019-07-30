# coding: utf-8
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon

PATH="src/main/python/ui/"

def readUi(path):
    with open(path,'r') as f:
        R=[]
        for line in f.readlines():
            l=line.strip()
            if l[0:7]=="<widget":
                s=''
                if l[-2:]=='/>':
                    s=l[8:-2]
                else:
                    s=l[8:-1]
                s=s.replace('class="','').replace('name="','').split(' ')    
                cla=s[0][0:-1]
                name=s[1][0:-1]
                cla.replace('"','')
                name.replace('"','')                
                #print('linstr(e: '+name+"  "+cla)  
                if len(name)!=0 and len(cla)!=0:
                    R.append("self."+name+" : "+"QtWidgets."+cla)
        c=''
        R.sort()
        for r in R:
            print(r)
            c+=r+'\n'
            
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setText(c, mode=cb.Clipboard)                
        return R   


class QFile(QWidget):
    
    def __init__(self,app):
        super().__init__()
        self.title = 'UI FILE'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.app=app
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)    
        self.button=QtWidgets.QPushButton("ui file")
        self.button.clicked.connect(self.openFileNameDialog)
        self.button.show()
        self.openFileNameDialog()
    
    def openFileNameDialog(self):        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog        
        dialog=QFileDialog()
        dialog.setDirectory(PATH)
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Designer Files (*.ui);;All Files (*)", options=options)
        if fileName:
            readUi(fileName)
            self.close()
            self.app.quit()


if __name__ == "__main__":
    if len(sys.argv)==1:        
        app = QtWidgets.QApplication(sys.argv)    
        win=QFile(app)
        sys.exit(app.exec_())
    elif len(sys.argv)>2:
        print("Usage: "+str(sys.argv[0])+" + 'file_path'")
        sys.exit()
    else:
        readUi(sys.argv[1])

    
       
