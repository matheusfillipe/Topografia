from builtins import str
# -*- coding: utf-8 -*-
import os
import sip

sip.setapi('QString', 2)

from qgis.PyQt import QtGui, uic, Qt, QtWidgets

import qgis

import shutil
from ..model.config import extractZIP, Config, compactZIP
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QAbstractItemView

from qgis._core import QgsCoordinateReferenceSystem, QgsCoordinateTransform

from qgis._core import QgsRectangle
from qgis._core import QgsVectorFileWriter
from qgis._core import QgsVectorLayer
from qgis._core import Qgis

from qgis.utils import *

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt import  QtWidgets

from ..model.helper.calculos import *
from ..model.curvas import Curvas as CurvasModel

FORMCURVA_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), '../view/ui/Topo_dialog_curva.ui'))
COMPOSI, _= uic.loadUiType(os.path.join(os.path.dirname(__file__), '../view/ui/compor_curvas.ui'))
CWIDGET, _= uic.loadUiType(os.path.join(os.path.dirname(__file__), '../view/ui/curvaWidget.ui'))

ID_ESTACA = 0
ESTACA = 1
DESCRICAO = 2
PROGRESSIVA = 3
NORTH = 4
ESTE = 5
COTA = 6
AZIMUTE = 7

class CurvasWidget(QtWidgets.QWidget, CWIDGET):
    edited=pyqtSignal()

    def __init__(self, parent):
        super(CurvasWidget,self).__init__(parent)
        self.iface=parent
        self.setupUi(self)

        self.Form: QtWidgets.QWidget
        self.k: QtWidgets.QLineEdit
        self.label: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.lineEdit_2: QtWidgets.QLineEdit
        self.pushButton: QtWidgets.QPushButton
        self.raio: QtWidgets.QLineEdit
        self.vmax: QtWidgets.QLineEdit
        self.nome: QtWidgets.QLabel

        self.onlyFloat= QDoubleValidator()
        self.raio.setValidator(self.onlyFloat)
        self.comprimento.setValidator(self.onlyFloat)
        self.raio.editingFinished.connect(self.edited.emit)
        self.comprimento.editingFinished.connect(self.edited.emit)

    def fill(self,k,vmax):
        self.k.setText(str(k))
        self.vmax.setText(str(vmax))

    def read(self):
        return float(self.raio.text()), float(self.comprimento.text())

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
        self.btnAdd.clicked.connect(self.addCurva)

    def addCurva(self):
        self.listWidget: QtWidgets.QListWidget
        self.comboBox: QtWidgets.QComboBox
        itemN = QtWidgets.QListWidgetItem()
        widget = CurvasWidget(self)
        widget.nome.setText(self.comboBox.currentText().upper())
        widget.horizontalLayout.addStretch()
        widget.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.listWidget.addItem(itemN)
        self.listWidget.setItemWidget(itemN, widget)


        widget.pushButton.clicked.connect(self.deleteCurva)
        widget.pushButton.clicked.connect(lambda: self.listWidget.takeItem(self.listWidget.row(itemN)))
        widget.edited.connect(self.edited.emit)
        try:
            if self.lastWidget:
                self.lastWidget.pushButton : QtWidgets.QPushButton
                self.lastWidget.setDisabled(True)
                lastWidget=self.lastWidget
                widget.pushButton.clicked.connect(lambda: lastWidget.setDisabled(False))
        except:
            pass

        self.lastWidget=widget
        itemN.setSizeHint(widget.sizeHint())

    def deleteCurva(self):
        self.listWidget: QtWidgets.QListWidget
        if self.listWidget.count()==0:
            self.lastWidget=False



class Curvas(QtWidgets.QDialog, FORMCURVA_CLASS):
    def __init__(self,parent, iface, id_filename, curvas, tipoClasseProjeto):
        super(Curvas, self).__init__(parent)
        self.iface = iface
        self.model = CurvasModel(id_filename)
        self.estacas = self.model.list_estacas()
        self.estacas_id = [row[0] for row in self.estacas]

        self.curvas = curvas

        self.tipo = tipoClasseProjeto[0]
        self.classe = tipoClasseProjeto[1]
        self.id_filename = id_filename
        self.tipo_curva = 0
        self.estacaInicial = self.estacas[0] if self.estacas else 0
        self.estacaFinal = self.estacas[0] if self.estacas else 0
        self.setupUi(self)


        self.Dialog: QtWidgets.QDialog
        self.btnAjuda: QtWidgets.QPushButton
        self.btnApagar: QtWidgets.QPushButton
        self.btnCalcular: QtWidgets.QPushButton
        self.btnCancela: QtWidgets.QPushButton
        self.btnClose: QtWidgets.QPushButton
        self.btnEditar: QtWidgets.QPushButton
        self.btnInsere: QtWidgets.QPushButton
        self.btnNew: QtWidgets.QPushButton
        self.btnRelatorio: QtWidgets.QPushButton
        self.comboCurva: QtWidgets.QComboBox
        self.comboElemento: QtWidgets.QComboBox
        self.comboEstacaFinal: QtWidgets.QComboBox
        self.comboEstacaInicial: QtWidgets.QComboBox
        self.gDadosCurva: QtWidgets.QGroupBox
        self.groupBox: QtWidgets.QGroupBox
        self.groupBox_2: QtWidgets.QGroupBox
        self.label: QtWidgets.QLabel
        self.label_10: QtWidgets.QLabel
        self.label_11: QtWidgets.QLabel
        self.label_12: QtWidgets.QLabel
        self.label_13: QtWidgets.QLabel
        self.label_14: QtWidgets.QLabel
        self.label_15: QtWidgets.QLabel
        self.label_16: QtWidgets.QLabel
        self.label_17: QtWidgets.QLabel
        self.label_18: QtWidgets.QLabel
        self.label_19: QtWidgets.QLabel
        self.label_2: QtWidgets.QLabel
        self.label_20: QtWidgets.QLabel
        self.label_21: QtWidgets.QLabel
        self.label_22: QtWidgets.QLabel
        self.label_23: QtWidgets.QLabel
        self.label_24: QtWidgets.QLabel
        self.label_3: QtWidgets.QLabel
        self.label_4: QtWidgets.QLabel
        self.label_5: QtWidgets.QLabel
        self.label_6: QtWidgets.QLabel
        self.label_7: QtWidgets.QLabel
        self.label_8: QtWidgets.QLabel
        self.label_9: QtWidgets.QLabel
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.layoutWidget: QtWidgets.QWidget
        self.txtD: QtWidgets.QLineEdit
        self.txtDelta: QtWidgets.QLineEdit
        self.txtDist: QtWidgets.QLineEdit
        self.txtEMAX: QtWidgets.QLineEdit
        self.txtEPC: QtWidgets.QLineEdit
        self.txtEPI: QtWidgets.QLineEdit
        self.txtEPT: QtWidgets.QLineEdit
        self.txtEsteFinal: QtWidgets.QLineEdit
        self.txtEsteInicial: QtWidgets.QLineEdit
        self.txtFMAX: QtWidgets.QLineEdit
        self.txtG20: QtWidgets.QLineEdit
        self.txtI: QtWidgets.QLineEdit
        self.txtNomeFinal: QtWidgets.QLineEdit
        self.txtNomeInicial: QtWidgets.QLineEdit
        self.txtNorthFinal: QtWidgets.QLineEdit
        self.txtNorthInicial: QtWidgets.QLineEdit
        self.txtRMIN: QtWidgets.QLineEdit
        self.txtRUtilizado: QtWidgets.QLineEdit
        self.txtT: QtWidgets.QLineEdit
        self.txtVelocidade: QtWidgets.QLineEdit

        curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])
        self.editando = False
        self.update()
        self.eventos()

    def update(self):
        self.curvas = self.model.list_curvas()
        estacas = self.estacas
        self.comboEstacaInicial.addItems([self.tr(estaca[1]) for estaca in self.estacas])
        self.comboEstacaFinal.addItems([self.tr(estaca[1]) for estaca in self.estacas])
        self.comboCurva.clear()
        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])

    def eventos(self):
        self.comboCurva.currentIndexChanged.connect(self.mudancaCurva)
        self.comboElemento.currentIndexChanged.connect(self.mudancaTipo)
        self.comboEstacaInicial.currentIndexChanged.connect(self.mudancaEstacaInicial)
        self.comboEstacaFinal.currentIndexChanged.connect(self.mudancaEstacaFinal)
        self.btnNew.clicked.connect(self.new)
        self.btnInsere.clicked.connect(self.insert)
        self.btnApagar.clicked.connect(self.apagar)
        self.btnRelatorio.clicked.connect(self.relatorio)
        self.btnEditar.clicked.connect(self.editar)
        self.btnCalcular.clicked.connect(self.calcular)

    def mudancaCurva(self, pos):
        self.curvas = self.model.list_curvas()
        self.curva = list(self.curvas[pos])
        curvas_inicial_id = self.curva[5]
        curvas_final_id = self.curva[6]
        self.mudancaEstacaInicial(self.estacas_id.index(curvas_inicial_id))
        self.mudancaEstacaFinal(self.estacas_id.index(curvas_final_id))
        self.txtVelocidade.setText(str(self.curva[2]))
        self.txtRUtilizado.setText(str(self.curva[3]))
        self.txtEMAX.setText(str(self.curva[4]))

    def mudancaTipo(self, pos):
        self.tipo_curva = pos

    def mudancaEstacaInicial(self, pos):
        self.comboEstacaInicial.setCurrentIndex(pos)
        self.estacaInicial = self.estacas[pos]
        self.txtNomeInicial.setText(self.estacaInicial[DESCRICAO])
        self.txtNorthInicial.setText(self.estacaInicial[NORTH])
        self.txtEsteInicial.setText(self.estacaInicial[ESTE])
        self.velocidadeCalculada()

    def mudancaEstacaFinal(self, pos):
        self.comboEstacaFinal.setCurrentIndex(pos)
        self.estacaFinal = self.estacas[pos]
        self.txtNomeFinal.setText(self.estacaFinal[DESCRICAO])
        self.txtNorthFinal.setText(self.estacaFinal[NORTH])
        self.txtEsteFinal.setText(self.estacaFinal[ESTE])
        self.velocidadeCalculada()

    def habilitarControles(self, signal):

        if type(signal) != type(True):
            return False

        self.comboCurva.setEnabled(not (signal))
        self.btnNew.setEnabled(not (signal))
        self.btnEditar.setEnabled(not (signal))
        self.btnApagar.setEnabled(not (signal))
        self.btnRelatorio.setEnabled(not (signal))
        self.btnInsere.setEnabled(signal)
        self.comboElemento.setEnabled(signal)
        self.comboEstacaInicial.setEnabled(signal)
        self.comboEstacaFinal.setEnabled(signal)
        self.txtVelocidade.setEnabled(signal)
        self.txtEMAX.setEnabled(signal)
        self.txtRUtilizado.setEnabled(signal)
        return True

    def velocidadeCalculada(self):
        self.curvas = self.model.list_curvas()
        if self.estacaInicial[ID_ESTACA] == self.estacaFinal[ID_ESTACA]:
            return

        if len(self.curvas) == 0:
            eptAnt = -1
        else:
            detalhes = self.model.get_curva_details(int(self.estacaInicial[ID_ESTACA]))
            eptAnt = -1 if detalhes is None else detalhes[6]

        i = calculeI(float(self.estacaInicial[PROGRESSIVA]), float(self.estacaFinal[PROGRESSIVA]),
                     float(self.estacaInicial[COTA]), float(self.estacaFinal[COTA]))
        v = velocidade(float(i), self.classe, self.tipo)
        rutilizado = float(self.txtRUtilizado.text())
        delta_val = delta(float(self.estacaInicial[AZIMUTE]), float(self.estacaFinal[AZIMUTE]))
        g20_val = g20(rutilizado)
        t_val = t(rutilizado, delta_val)
        d_val = d_curva_simples(rutilizado, delta_val)
        e_max = float(self.txtEMAX.text())
        f_max = fmax(int(v[0]))

        epi_val = epi(eptAnt, float(self.estacaFinal[PROGRESSIVA]), float(self.estacaInicial[PROGRESSIVA]), t_val)
        epc_val = epc(epi_val, t_val)
        ept_val = ept(epc_val, d_curva_simples(rutilizado, delta_val))
        self.param = {
            'g20': g20_val,
            't': t_val,
            'd': d_val,
            'epi': epi_val,
            'epc': epc_val,
            'ept': ept_val
        }
        self.txtI.setText("%f" % i)
        self.txtT.setText("%f" % t_val)
        self.txtD.setText("%f" % d_val)
        self.txtG20.setText("%f" % g20_val)
        self.txtFMAX.setText("%f" % f_max)
        self.txtRMIN.setText("%f" % rmin(int(v[0]), e_max, f_max))
        self.txtVelocidade.setText(v[0])
        self.txtDelta.setText("%f" % delta_val)
        self.txtEPI.setText("%f" % epi_val)
        self.txtEPT.setText("%f" % ept_val)
        self.txtEPC.setText("%f" % epc_val)

    def insert(self):

        self.habilitarControles(False)

        velocidade = int(self.txtVelocidade.text())
        raio_utilizado = float(self.txtRUtilizado.text())
        e_max = float(self.txtEMAX.text())
        estaca_inicial_id = int(self.estacaInicial[ID_ESTACA])
        estaca_final_id = int(self.estacaFinal[ID_ESTACA])
        model = CurvasModel(self.id_filename)
        if self.editando:
            self.editando = False
            id_curva = int(self.curva[0])
            model.edit(id_curva, int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado,
                       e_max, self.param)
        else:
            model.new(int(self.tipo_curva), estaca_inicial_id, estaca_final_id, velocidade, raio_utilizado, e_max,
                      self.param)
        self.update()

    def apagar(self):
        curva = self.curva
        self.model.delete_curva(curva[0])
        self.update()
        self.comboCurva.clear()
        curvas = [self.tr(str(curva[0])) for curva in self.curvas]
        self.comboCurva.addItems([self.tr(str(curva[0])) for curva in self.curvas])

    def relatorio(self):
        pass

    def new(self):
        c=CurvasCompositorDialog(self)
        c.accepted.connect(self.show)
        c.rejected.connect(self.show)
        c.edited.connect() #--> ? make it happen!
        self.hide()
        c.show()
        return

        self.habilitarControles(True)
        if (len(self.curvas) > 0):
            ultima = self.curvas[-1][0]
        else:
            ultima = -1
        self.curvas.append(["%d" % (ultima + 1,)])
        self.comboCurva.addItems([self.tr("%d" % (ultima + 1,))])

    def editar(self):
        self.habilitarControles(True)
        self.editando = True

    def calcular(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(filter="Arquivo CSV (*.csv)")[0]
        dist = int(self.txtDist.text())
        estacas = self.model.gera_estacas(dist)
        self.model.save_CSV(filename, estacas)

    def gera_estacas_curvas(self):
        pass

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TopoGrafia', message)
