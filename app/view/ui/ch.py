from copy import deepcopy

from qgis.PyQt import QtGui, uic, Qt, QtWidgets
import os
from qgis.PyQt.QtCore import pyqtSignal

from ...model.utils import msgLog

COMPOSI, _= uic.loadUiType(os.path.join(os.path.dirname(__file__), 'compor_curvas.ui'))
CWIDGET, _= uic.loadUiType(os.path.join(os.path.dirname(__file__), 'curvaWidget.ui'))

class CurvasWidget(QtWidgets.QWidget, CWIDGET):
    edited=pyqtSignal()

    def __init__(self, parent):
        super(CurvasWidget,self).__init__(parent)
        self.iface=parent
        self.setupUi(self)
        self.Form: QtWidgets.QWidget

        self.T: QtWidgets.QDoubleSpinBox
        self.checkBox: QtWidgets.QCheckBox
        self.comprimento: QtWidgets.QDoubleSpinBox
        self.deflexao: QtWidgets.QDoubleSpinBox
        self.k: QtWidgets.QLineEdit
        self.label: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.label_5: QtWidgets.QLabel
        self.label_6: QtWidgets.QLabel
        self.nome: QtWidgets.QLabel
        self.pushButton: QtWidgets.QPushButton
        self.raio: QtWidgets.QDoubleSpinBox
        self.vmax: QtWidgets.QLineEdit
        self.parent.comboBox: QtWidgets.QComboBox

        self.setTipo(self.iface.comboBox.currentIndex())

        if self.tipo=="T":
            self.raio.setEnabled(False)

        self.modified="S" #Started
        self.events()

        self.vmax.hide()
        self.label_2.hide()
        self.k.hide()
        self.label.hide()

    def fill(self, data, k='',vmax=''):
        T=data["T"]
        raio=data["R"]
        deflexao=data["D"]
        comprimento=data["L"]
        checkBoxState=data["C"] if data["C"] else False

        self.eventsDisconnect()
        self.T: QtWidgets.QDoubleSpinBox
        try:
            self.k.setText(str(k))
            self.vmax.setText(str(vmax))
            self.T.setValue(T)
            self.deflexao.setValue(deflexao)
            self.raio.setValue(raio)
            self.comprimento.setValue(comprimento)
            self.checkBox.setChecked(checkBoxState)

            self.T.setEnabled(True)
            self.raio.setEnabled(True)
            self.deflexao.setEnabled(True)
            self.comprimento.setEnabled(True)
            self.checkBox.setEnabled(True)

            if "Disable" in data:
                D=data["Disable"]
                for d in D:
                    if d=="T":
                        self.T.setEnabled(False)
                    if d=="R":
                        self.raio.setEnabled(False)
                    if d=="D":
                        self.deflexao.setEnabled(False)
                    if d=="L":
                        self.comprimento.setEnabled(False)
                    if d=="C":
                        self.checkBox.setEnabled(False)

            self.events()

        except:
            pass


    def eventsDisconnect(self):
        try:
            self.raio.valueChanged.disconnect()
            self.comprimento.valueChanged.disconnect()
            self.T.valueChanged.disconnect()
            self.deflexao.valueChanged.disconnect()
            self.checkBox.stateChanged.disconnect()
        except:
            pass
            

    def events(self):
        self.raio.valueChanged.connect(lambda: self.setModified("R"))
        self.raio.valueChanged.connect(self.edited.emit)
        self.comprimento.valueChanged.connect(lambda: self.setModified("L"))
        self.comprimento.valueChanged.connect(self.edited.emit)
        self.T.valueChanged.connect(lambda: self.setModified("T"))
        self.T.valueChanged.connect(self.edited.emit)
        self.deflexao.valueChanged.connect(lambda: self.setModified("D"))
        self.deflexao.valueChanged.connect(self.edited.emit)
        self.checkBox.stateChanged.connect(lambda: self.setModified("C"))
        self.checkBox.stateChanged.connect(self.edited.emit)


    def setModified(self, s):
        self.modified=s

    def setTipo(self, i=-1):
        if i>=0:
            if i==3:
                self.tipo="EE"
            elif i==0:
                self.tipo="C"
            elif i==1:
                self.tipo="EC"
            elif i==4:
                self.tipo="ES"
            elif i==2:
                self.tipo= "T"
            else:
                msgLog("Os valores do combobox estão errados!")
                self.tipo=None
        return self.tipo

    def read(self):
        try:
            return self.tipo, self.modified, {"R": self.raio.value(), "L": self.comprimento.value(),
        "T": self.T.value(), "D": self.deflexao.value(), "C": self.checkBox.isChecked(), "Disable": []} #tipo de curva, raio, comprimento (L)
        except:
            return self.tipo, None, None

#DADOS: R, L, T, D float
#       C bool
#       Disable list (of index to setEnabled(false)

EMPTY_DATA={"R":0.0, "L":0.0, "T":0.0, "D":0.0, "C": False}
def empty_data():
   return deepcopy(EMPTY_DATA)


class CurvasCompositorDialog(QtWidgets.QDialog, COMPOSI):
    edited=pyqtSignal()
    def __init__(self, parent):
        super(CurvasCompositorDialog, self).__init__(parent)
        self.iface=parent
        self.setupUi(self)

        self.Dialog: QtWidgets.QDialog
        self.btnAdd: QtWidgets.QPushButton
        self.buttonBox: QtWidgets.QDialogButtonBox
        self.comboBox: QtWidgets.QComboBox
        self.listWidget: QtWidgets.QListWidget
        self.lastWidget=False
        self.btnAdd.clicked.connect(lambda: self.addCurva())

        if self.iface.comboElemento.currentIndex() == 0: #Circular simples
            self.comboBox.setCurrentIndex(0)
            self.addCurva({'D': float(self.iface.txtDelta.text()), 'R': self.iface.txtRUtilizado.value(), 'T': float(self.iface.txtT.text()), 'L': 0, 'C': True})
        elif self.iface.comboElemento.currentIndex() == 1: #Circular simétrica com transição
            self.comboBox.setCurrentIndex(1)
            self.addCurva({'D': float(self.iface.txtDelta.text())-2*float(self.iface.theta.text()), 'R': self.iface.txtRUtilizado.value(), 'T': float(self.iface.txtT.text()), 'L': self.iface.Ls.value(), 'C': True})

    def addCurva(self, data=None):
        self.listWidget: QtWidgets.QListWidget
        self.comboBox: QtWidgets.QComboBox
        itemN = QtWidgets.QListWidgetItem()
        widget = CurvasWidget(self)
        widget.nome.setText(self.comboBox.currentText().upper())
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        if data==None:
            try:
                _,_,data=self.lastWidget.read()
                data["D"]=0
                data["C"]=False
                widget.fill(data, k=self.lastWidget.k.text(), vmax=self.lastWidget.vmax.text())
            except:
                pass
        else:
            widget.fill(data)
            self.comboBox.hide()
            self.btnAdd.hide()
            #self.horizontalSpacer.hide()

        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)

        widget.pushButton.clicked.connect(lambda: self.listWidget.takeItem(self.listWidget.row(itemN)))
        widget.pushButton.clicked.connect(lambda: self.deleteCurva)
        widget.pushButton.clicked.connect(self.edited.emit)
        widget.edited.connect(self.edited.emit)

#        try:
#            if self.lastWidget:
#                self.lastWidget.pushButton : QtWidgets.QPushButton
#                self.lastWidget.setDisabled(True)
#                lastWidget=self.lastWidget
#                widget.pushButton.clicked.connect(lambda: lastWidget.setDisabled(False))
#        except:
#            pass

        self.lastWidget=widget
        itemN.setSizeHint(widget.sizeHint())
        self.listWidget.scrollToBottom()
        self.edited.emit()

    def deleteCurva(self):
        self.lastWidget=[self.listWidget.itemWidget(self.listWidget.item(i)) for i in range(self.listWidget.count())][-1]
        if self.listWidget.count()==0:
            self.lastWidget=False

    def readData(self):
        for i in range(self.listWidget.count()):
            yield self.listWidget.itemWidget(self.listWidget.item(i)).read()

    def read(self):
        return self.lastWidget.read()

    def activeWidget(self):
        return self.lastWidget

    def show(self):
        self.edited.emit()
        return super(CurvasCompositorDialog, self).show()

