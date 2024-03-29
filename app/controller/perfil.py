from __future__ import absolute_import

import functools
from builtins import zip
from copy import deepcopy

import numpy as np
from PyQt5.QtCore import QPointF, QThread
from qgis.PyQt import QtGui

from ... import PyQtGraph as pg
from ..model import constants
from ..model.helper.calculos import fmax, vmedia
from ..model.utils import *
from ..view.estacas import (ApplyTransDialog, QgsMessageLog, SetCtAtiDialog,
                            VolumeDialog, brucknerRampaDialog, closeDialog,
                            cvEdit, rampaDialog, setEscalaDialog,
                            ssRampaDialog)
from .Geometria import Figure, Prismoide


##############################################################################################################
# TODO:

# Features to  ADD
# ctrl+Z utility
# add menu interface and grid and printing scale export

##############################################################################################################


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:

    def _fromUtf8(s):
        return s


try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)

except AttributeError:

    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.PanMode)

    # reimplement mid-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MidButton:
            self.autoRange()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)


PREC = 5  # draw precision in meters


class cv:
    def __init__(self, i1, i2, L, handlePos, lastHandlePos):

        self.i1 = i1
        self.i2 = i2
        self.G = (i1 - i2) / 100
        self.L = L
        self.lastHandlePos = lastHandlePos
        self.handlePos = handlePos
        self.curve = pg.PlotCurveItem()
        self.update(i1, i2, L, handlePos, lastHandlePos)

    def update(self, i1, i2, L, handlePos, lastHandlePos):
        if L != 0:
            self.i1 = i1
            self.i2 = i2
            self.G = (i1 - i2) / 100
            self.L = L

            G = self.G
            i1 = self.i1 / 100
            L = self.L
            xpcv = handlePos.x() - L / 2
            ypcv = lastHandlePos.y() + i1 * (xpcv - lastHandlePos.x())

            x = []

            for n in range(0, int(L / PREC) + 1):
                x.append(n * PREC)

            x = np.array(x)
            y = (-G / (2 * L)) * x * x + i1 * x + ypcv

            x = []
            for n in range(0, int(L / PREC) + 1):
                x.append(n * PREC + xpcv)

            self.xpcv = xpcv
            self.ypcv = ypcv
            self.xptv = xpcv + L
            self.yptv = self.getCota(self.xptv)
            self.x = x
            self.y = y

            self.curve.clear()

            self.curve.setData(
                x, y, pen=pg.mkPen("r", width=3, style=QtCore.Qt.DashLine)
            )

        else:
            self.L = 0

    def getCota(self, x):
        return (
            False
            if x < self.xpcv or x > self.xptv
            else (-self.G / (2 * self.L)) * (x - self.xpcv) ** 2
            + self.i1 * (x - self.xpcv) / 100
            + self.ypcv
        )


class cvEditDialog(cvEdit):
    def __init__(self, roi, i):
        super(cvEditDialog, self).__init__(None)
        #        self.addCurveBtn.clicked.connect(self.raiseCurveGroupeBox)
        # self.setupUi(self)
        self.isBeingModified = False
        self.i = i
        self.initialHandlesPos = []
        self.i1 = 0
        self.i2 = 0
        self.G = 0
        self.Lutilizado = 0

        self.roi = roi
        estacas = self.roi.perfil.iface.view.get_estacas()
        est = []
        for linha in estacas:
            est.append(linha[0])
        self.estacas = est

        self.cota = self.getHandlePos(i).y()
        self.horizontal = self.getHandlePos(i).x()

        self.updateCota()
        self.uicota.returnPressed.connect(self.updateCota)
        self.uihorizontal1.returnPressed.connect(self.updateAbscissa1)
        self.uihorizontal1.returnPressed.connect(self.updateAbscissa2)

        self.okBtn.clicked.connect(self.save)
        self.cancelBtn.clicked.connect(self.reset)

        # set readonly textEdits

        for j in range(0, roi.countHandles()):
            self.initialHandlesPos.append(self.getHandlePos(j))

        self.handle = self.roi.handles[i]["item"]

        # checking curve existence

        try:
            self.Lutilizado = self.handle.curve.L
            self.groupBox_2.setEnabled(True)
        except AttributeError:
            self.handle.curve = cv(
                self.i1, self.i2, 0, self.handle.pos(), self.getHandlePos(i - 1)
            )

        self.initialCurve = cv(
            self.handle.curve.i1,
            self.handle.curve.i2,
            self.handle.curve.L,
            self.handle.curve.handlePos,
            self.handle.curve.lastHandlePos,
        )
        self.uiLutilizado.valueChanged.connect(self.updateL)
        self.addCurveBtn.clicked.connect(self.updateL)

        self.uicota1.setText(shortFloat2String(self.getHandlePos(i - 1).y()))
        self.uicota2.setText(shortFloat2String(self.getHandlePos(i + 1).y()))

        self.setupValidators()
        self.redefineUI(-10)
        self.updateVerticesCb()

        #       self.helpBtn.clicked.connect(self.displayHelp)
        self.viewCurveBtn.clicked.connect(self.viewCurva)

        self.shortcut1 = QtWidgets.QShortcut(QtGui.QKeySequence.MoveToNextChar, self)
        self.shortcut2 = QtWidgets.QShortcut(
            QtGui.QKeySequence.MoveToPreviousChar, self
        )
        self.shortcut1.activated.connect(self.nextVertex)
        self.shortcut2.activated.connect(self.previousVertex)
        self.velproj.valueChanged.connect(lambda: self.redefineUI(self.elm))
        self.generateAll.clicked.connect(self.generateAllC)

        self.generateAll.hide()

    def generateAllC(self):
        self.verticeCb.setCurrentIndex(1)
        while self.nextBtn.isEnabled():
            self.updateL()
            self.nextVertex()
        self.updateL()

    def nextVertex(self):
        if self.nextBtn.isEnabled():
            self.next()

    def previousVertex(self):
        if self.previousBtn.isEnabled():
            self.previous()

    def viewCurva(self):
        center = self.getHandlePos(self.i)
        self.roi.perfil.vb.scaleBy((0.5, 0.5), center)

    def displayHelp(self):
        dialog = imgDialog(
            imagepath="../view/ui/helpCV.png", title="Ajuda: Curvas Verticais"
        )
        dialog.show()
        dialog.exec_()

    def setupValidators(self):
        self.uicota.setValidator(QtGui.QDoubleValidator())
        self.uihorizontal1.setValidator(QtGui.QDoubleValidator())
        self.uihorizontal2.setValidator(QtGui.QDoubleValidator())

        self.uiL.setValidator(QtGui.QDoubleValidator())

    def raiseCurveGroupeBox(self):
        self.groupBox_2.setEnabled(True)

    def save(self):
        self.redefineUI(-1)
        self.close()

    def reset(self):
        j = 0
        for pos in self.initialHandlesPos:
            self.roi.handles[j]["item"].setPos(pos)
            j += 1
        self.handle.curve.curve.clear()
        self.handle.curve = self.initialCurve
        self.uiL.setText(str(self.handle.curve.L))

        self.roi.plotWidget.addItem(self.handle.curve.curve)
        self.close()

    def getHandlePos(self, i):
        return self.roi.handles[i]["item"].pos()

    def getSegIncl(self, i, j):
        try:
            return round(
                100
                * (self.getHandlePos(j).y() - self.getHandlePos(i).y())
                / (self.getHandlePos(j).x() - self.getHandlePos(i).x()),
                4,
            )
        except IndexError:
            return None

    def updateCota(self):
        try:
            if not self.isBeingModified:
                self.cota = float(self.uicota.text())
                self.update()
                self.redefineUI(3)

        except ValueError:
            pass

    def updateAbscissa1(self):
        try:
            if not self.isBeingModified:
                self.horizontal = (
                    float(self.uihorizontal1.text()) + self.getHandlePos(self.i - 1).x()
                )
                self.update()
                self.redefineUI(4)
                self.updateVerticesCb()

        except ValueError:
            pass

    def updateAbscissa2(self):
        try:
            if not self.isBeingModified:
                self.horizontal = (
                    -float(self.uihorizontal2.text())
                    + self.getHandlePos(self.i + 1).x()
                )
                self.update()
                self.redefineUI(4)

        except ValueError:
            pass

    def updateL(self):
        try:
            if not self.isBeingModified:
                self.Lutilizado = float(self.uiLutilizado.value())
                self.uif.setText(
                    ("{:0.6e}".format(self.G / (100 * 2 * float(self.Lutilizado))))
                )
                self.handle.curve.update(
                    self.i1,
                    self.i2,
                    self.Lutilizado,
                    self.getHandlePos(self.i),
                    self.getHandlePos(self.i - 1),
                )
                self.roi.plotWidget.addItem(self.handle.curve.curve)
                self.updateAlert()
        except ValueError:
            pass

    def update(self):
        self.roi.handles[self.i]["item"].setPos(self.horizontal, self.cota)
        self.updateAlert()

    def redefineUI(self, elm):
        self.elm = elm
        self.isBeingModified = True
        i = self.i
        roi = self.roi
        self.groupBox_2.setTitle("Curva Vertical: " + str(i))

        if i >= roi.countHandles() - 1 or i == 0:
            self.removeCv()
        else:
            self.i1 = self.getSegIncl(i - 1, i)
            self.i2 = self.getSegIncl(i, i + 1)
            self.G = self.i1 - self.i2

        self.horizontal1 = self.horizontal - self.getHandlePos(i - 1).x()
        self.horizontal2 = self.getHandlePos(i + 1).x() - self.horizontal
        self.uihorizontal1.setText(shortFloat2String(self.horizontal1))
        self.uihorizontal2.setText(shortFloat2String(self.horizontal2))
        self.uii1.setText(shortFloat2String(self.i1))
        self.uii2.setText(shortFloat2String(self.i2))
        self.uiG.setText(shortFloat2String(self.G))
        self.uicota.setText(shortFloat2String(self.cota))

        concave = False
        if self.G < 0:
            self.uiCurveType.setText("Côncava")
            concave = True
        else:
            self.uiCurveType.setText("Convexa")

        g = self.G

        if self.velproj.value() == 0:
            v = velproj = Config.instance().velproj
        else:
            v = velproj = self.velproj.value()

        self.roi.perfil.calcularGreide()
        vv = self.roi.perfil.velProj

        self.velproj.setValue(v)
        # constants.Kmin[min(max(30,(round(velproj/10)*10)),120)][self.G>0]
        Kmin = velproj**2 / (1296 * 9.8 * 1.5 / 100)
        Kdes = constants.Kdes[min(max(30, (round(velproj / 10) * 10)), 120)][self.G > 0]
        fmax = constants.f[min(max(30, (round(velproj / 10) * 10)), 120)]
        # dp=0.7*vmedia(v)+vmedia(v)**2/(255*(fmax))
        dp = 0.7 * v + v**2 / (255 * (fmax))
        self.uiDp.setText(shortFloat2String(dp))

        self.uiLutilizado: QtWidgets.QDoubleSpinBox
        self.uiLutilizado.setSingleStep(Config.instance().DIST)
        l1 = 0
        l2 = 0
        msgLog("Curva: " + str(self.i))
        msgLog("v: " + str(velproj))
        msgLog("kmin: " + str(Kmin))
        if not concave:
            l1 = max(0, abs(self.G) * dp**2 / 412)
            msgLog("G: " + str(self.G))
            msgLog("dp: " + str(dp))
            l2 = max(0, 2 * dp - 412 / abs(self.G))
        else:
            l1 = max(0, abs(self.G) * dp**2 / (122 + 3.5 * dp))
            l2 = max(0, 2 * dp - (122 + 3.5 * dp) / abs(self.G))

        self.lmin1: QtWidgets.QLabel
        self.lmin2: QtWidgets.QLabel

        self.lmin1.setText(shortFloat2String(l1))
        self.lmin2.setText(shortFloat2String(l2))
        lsmin = l1 if l1 >= dp else l2

        if self.Lutilizado == 0:
            dist = Config.instance().DIST
            self.Lutilizado = max(0.6 * v, Kmin * abs(g), lsmin)
            self.Lutilizado = self.Lutilizado + dist - self.Lutilizado % dist

        self.uif.setText(
            ("{:0.6e}".format(self.G / (100 * 2 * float(self.Lutilizado))))
        )
        self.uiLmin.setText(shortFloat2String(Kmin * abs(g)))

        self.uiLutilizado.setValue(self.Lutilizado)
        self.uiL.setText(shortFloat2String(velproj * 0.6))
        self.uiff.setText(shortFloat2String(fmax))

        self.isBeingModified = False

        self.roi.update()

        txt = "Cota"
        self.cotaLabel_6.setText(txt + " V" + str(i - 1) + ":")
        self.cotaLabel.setText(txt + " V" + str(i) + ":")
        self.cotaLabel_8.setText(txt + " V" + str(i + 1) + ":")

        txt = "Horizontal"
        self.label_9.setText(txt + " V" + str(i - 1) + "-" + "V" + str(i) + ":")
        self.label_12.setText(txt + " V" + str(i) + "-" + "V" + str(i + 1) + ":")

        self.updateAlert()

    def updateAlert(self):
        vv = self.roi.perfil.velProj
        if self.velproj.value() == 0:
            v = Config.instance().velproj
        else:
            v = self.velproj.value()
        try:
            self.uiAlertaLb: QtWidgets.QLabel
            if v > vv:
                self.uiAlertaLb2.setText(
                    "Alerta: " + roundFloat2str(v) + ">" + roundFloat2str(vv) + "!"
                )
                self.uiAlertaLb2.setToolTip(
                    "A velocidade de projeto configurada é maior que a recomendada para esse perfil"
                )
            else:
                self.uiAlertaLb2.setText("")
                self.uiAlertaLb2.setToolTip("")

            if (
                self.getHandlePos(self.i).x() + self.Lutilizado / 2
                > self.getHandlePos(self.i + 1).x()
                - self.roi.handles[self.i + 1]["item"].curve.L / 2
                or self.getHandlePos(self.i).x() - self.Lutilizado / 2
                < self.getHandlePos(self.i - 1).x()
                + self.roi.handles[self.i - 1]["item"].curve.L / 2
            ):
                self.uiAlertaLb.setText("Alerta: Sobreposição de curvas!")
                self.uiAlertaLb.setToolTip("")
            else:
                self.uiAlertaLb.setText("")
                self.uiAlertaLb.setToolTip("")

        except:
            msgLog("Falha ao mostrar alertas")

    def updateVerticesCb(self):

        self.verticeCb: QtWidgets.QComboBox
        self.verticeCb.clear()
        for i in range(1, len(self.roi.handles)):
            self.verticeCb.addItem(str(i - 1))

        try:
            self.verticeCb.currentIndexChanged.disconnect()
            self.nextBtn.clicked.disconnect()
            self.previousBtn.clicked.disconnect()
        except:
            pass

        self.verticeCb.setCurrentIndex(self.i)
        self.verticeCb.currentIndexChanged.connect(self.changeVertice)
        self.nextBtn.clicked.connect(self.next)
        self.previousBtn.clicked.connect(self.previous)

        if self.i == 1:
            self.previousBtn.setEnabled(False)
        else:
            self.previousBtn.setEnabled(True)

        if self.i == i - 1:
            self.nextBtn.setEnabled(False)
        else:
            self.nextBtn.setEnabled(True)

    def changeVertice(self, i):
        if i <= 0:
            i = self.i
        elif i >= len(self.roi.handles) - 1:
            i = self.i

        self.save()
        c = cvEditDialog(self.roi, i)
        c.move(self.x(), self.y())
        c.show()
        c.exec_()

    def next(self):
        self.verticeCb.setCurrentIndex(self.i + 1)

    def previous(self):
        self.verticeCb.setCurrentIndex(self.i - 1)


class CustomPolyLineROI(pg.PolyLineROI):
    wasModified = QtCore.pyqtSignal()
    modified = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwds):
        self.wasInitialized = False
        self.labels = []
        self.setPlotWidget(kwds.get("plot", False))
        pg.PolyLineROI.__init__(self, *args, **kwds)
        self.ismodifying = False

    def setPlotWidget(self, plotWidget):
        if plotWidget:
            self.plotWidget = plotWidget

    def HandleEditDialog(self, i):
        dialog = cvEditDialog(self, i)
        dialog.show()
        dialog.exec_()
        self.sigRegionChangeFinished.emit(self)
        self.modified.emit(self)

    def mouseClickEvent(self, ev):

        if ev.button() == QtCore.Qt.RightButton and self.isMoving:
            self.modified.emit(self)
            ev.accept()
            self.cancelMove()

        self.wasModified.emit()
        ev.accept()
        self.modified.emit(self)
        self.sigClicked.emit(self, ev)

    def setPoints(self, points, closed=None):
        self.wasInitialized = False
        QgsMessageLog.logMessage("Iniciando pontos do perfil", "GeoRoad", level=0)
        if closed is not None:
            self.closed = closed
        self.clearPoints()

        for i, p in enumerate(points):
            self.addRotateFreeHandle(p, p)

        start = -1 if self.closed else 0

        self.handles[0]["item"].sigEditRequest.connect(lambda: self.HandleEditDialog(0))
        self.handles[0]["item"].fixedOnX = True
        self.handles[0]["item"].edge = True

        for i in range(start, len(self.handles) - 1):
            self.addSegment(self.handles[i]["item"], self.handles[i + 1]["item"])
            j = i + 1
            self.handles[j]["item"].sigEditRequest.connect(
                functools.partial(self.HandleEditDialog, j)
            )

        self.handles[j]["item"].fixedOnX = True
        self.handles[j]["item"].edge = True

        self.wasInitialized = True
        self.updateHandles()

    def removeLabel(self, i):
        for text in self.labels[i + 1 :]:
            try:
                self.plotWidget.removeItem(text)
            except:
                pass

    def updateLabel(self, handle, i):
        msg = "V" + str(i - 1)
        i = i - 1
        text: pg.TextItem
        if i >= len(self.labels):
            text = pg.TextItem(msg)
        else:
            text = self.labels[i]
            text.setText(msg)
        text.setPos(handle.pos().x(), handle.pos().y())
        text.setAnchor((0.5, 1))
        if i >= len(self.labels):
            self.plotWidget.addItem(text)
            self.labels.append(text)

    def updateHandles(self):
        if self.wasInitialized:
            for i in range(0, len(self.handles) - 1):

                try:
                    self.handles[i]["item"].sigEditRequest.disconnect()
                except:
                    pass

            handle = self.handles[0]["item"]
            handle.sigEditRequest.connect(lambda: self.HandleEditDialog(0))
            start = -1 if self.closed else 0
            self.updateLabel(handle, 1)

            for i in range(start, len(self.handles) - 1):
                j = i + 1
                handle = self.handles[j]["item"]
                handle.sigEditRequest.connect(
                    functools.partial(self.HandleEditDialog, j)
                )
                self.updateLabel(handle, j + 1)

                try:
                    diag = cvEditDialog(self, j)
                    diag.reset()
                except:
                    pass
            self.removeLabel(len(self.handles) - 1)
            pg.QtGui.QGuiApplication.processEvents()
            self.wasInitialized = True

    def removeCurva(self, handle):
        if hasattr(handle, "curve"):
            self.plotWidget.removeItem(handle.curve.curve)
            handle.curve.curve.clear()

        self.removeHandle(handle)
        self.update()

    def addHandle(self, info, index=None):
        h = pg.ROI.addHandle(self, info, index=index)
        h.sigRemoveRequested.connect(self.removeHandle)
        self.stateChanged(finish=True)
        self.wasInitialized = True
        self.updateHandles()
        return h

    def countHandles(self):
        return len(self.handles)

    # pos should be in this item's coordinate system
    def segmentClicked(self, segment, ev=None, pos=None):
        msgLog("Segment click!!")
        if ev is not None:
            pos = segment.mapToParent(ev.pos())
        elif pos is not None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        msgLog("button:", ev.button())
        if ev.button() == QtCore.Qt.RightButton:
            msgLog("right click detected")
            i = self.segments.index(segment)
            d = rampaDialog(self, segment, pos, i + 2)
            self.ismodifying = True
            d.exec_()
            self.ismodifying = False
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

        elif ev.button() == QtCore.Qt.LeftButton:
            h1 = segment.handles[0]["item"]
            h2 = segment.handles[1]["item"]
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i + 1)
            segment.replaceHandle(h2, h3)
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

    def getHandlePos(self, i):
        return self.handles[i]["item"].pos()

    def getVerticesList(self):
        l = []
        for i in range(0, len(self.handles)):
            p = self.getHandlePos(i)
            l.append([p.x(), p.y()])

        return l

    def getYfromX(self, x):
        for i in range(0, self.countHandles() - 2):
            h = self.handles[i]["item"].pos()
            nh = self.handles[1 + i]["item"].pos()
            if h.x() <= x and nh.x() >= x:
                return (nh.y() - h.y()) / (nh.x() - h.x()) * (x - h.x()) + h.y()
        raise ValueError

    def getSegIncl(self, i, j):
        try:
            return round(
                100
                * (self.getHandlePos(j).y() - self.getHandlePos(i).y())
                / (self.getHandlePos(j).x() - self.getHandlePos(i).x()),
                4,
            )
        except IndexError:
            return None

    def addCvs(self, cvList):

        if cvList == False or len(cvList) <= 2:

            for i in range(0, len(self.handles) - 1):
                i1 = self.getSegIncl(i - 1, i)
                i2 = self.getSegIncl(i, i + 1)
                L = 0
                self.handles[i]["item"].curve = cv(
                    i1, i2, L, self.getHandlePos(i), self.getHandlePos(i - 1)
                )
                self.handles[i]["item"].sigRemoveRequested.disconnect()
                self.handles[i]["item"].sigRemoveRequested.connect(self.removeCurva)
                self.plotWidget.addItem(self.handles[i]["item"].curve.curve)

            return

        for i in range(0, len(self.handles) - 1):
            if cvList[i][1] != "None":
                i1 = self.getSegIncl(i - 1, i)
                i2 = self.getSegIncl(i, i + 1)
                L = float(cvList[i][1])
                self.handles[i]["item"].curve = cv(
                    i1, i2, L, self.getHandlePos(i), self.getHandlePos(i - 1)
                )
                self.handles[i]["item"].sigRemoveRequested.disconnect()
                self.handles[i]["item"].sigRemoveRequested.connect(self.removeCurva)
                self.plotWidget.addItem(self.handles[i]["item"].curve.curve)
            else:

                i1 = self.getSegIncl(i - 1, i)
                i2 = self.getSegIncl(i, i + 1)
                L = 0
                self.handles[i]["item"].curve = cv(
                    i1, i2, L, self.getHandlePos(i), self.getHandlePos(i - 1)
                )
                self.handles[i]["item"].sigRemoveRequested.disconnect()
                self.handles[i]["item"].sigRemoveRequested.connect(self.removeCurva)
                self.plotWidget.addItem(self.handles[i]["item"].curve.curve)

    def update(self):
        try:
            for i in range(0, len(self.handles) - 1):
                i1 = self.getSegIncl(i - 1, i)
                i2 = self.getSegIncl(i, i + 1)
                L = self.handles[i]["item"].curve.L
                # self.handles[i]['item'].curve.curve.clear()
                # self.handles[i]['item'].curve=cv(i1, i2, L,self.getHandlePos(i), self.getHandlePos(i-1))
                self.handles[i]["item"].curve.update(
                    i1, i2, L, self.getHandlePos(i), self.getHandlePos(i - 1)
                )
                # self.plotWidget.addItem(self.handles[i]['item'].curve.curve)
        except:
            pass

    def removeRect(self, handle):
        try:
            self.plotWidget.removeItem(handle.leg1)
            self.plotWidget.removeItem(handle.leg2)
            self.plotWidget.removeItem(handle.rect1)
            self.plotWidget.removeItem(handle.rect2)
        except:
            pass
        pg.QtGui.QGuiApplication.processEvents()


class ssRoi(CustomPolyLineROI):
    wasModified = QtCore.pyqtSignal()
    modified = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwds):
        super(ssRoi, self).__init__(*args, **kwds)
        self.cota = kwds["cota"]

    # pos should be in this item's coordinate system
    def segmentClicked(self, segment, ev=None, pos=None):
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        if ev.button() == QtCore.Qt.RightButton:
            d = ssRampaDialog(self, segment, pos, self.cota)
            d.exec_()
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

        elif ev.button() == QtCore.Qt.LeftButton:
            h1 = segment.handles[0]["item"]
            h2 = segment.handles[1]["item"]
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i + 1)
            segment.replaceHandle(h2, h3)
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

    def setPoints(self, points, closed=None):
        self.wasInitialized = False
        QgsMessageLog.logMessage(
            "Iniciando pontos do perfil transversal", "GeoRoad", level=0
        )
        if closed is not None:
            self.closed = closed
        self.clearPoints()

        for p in points:
            self.addRotateHandle(p, p)
            # self.addTranslateHandle(p)

        start = -1 if self.closed else 0

        self.handles[0]["item"].sigEditRequest.connect(lambda: self.HandleEditDialog(0))

        for i in range(start, len(self.handles) - 1):
            self.addSegment(self.handles[i]["item"], self.handles[i + 1]["item"])
            j = i + 1
            self.handles[j]["item"].sigEditRequest.connect(
                functools.partial(self.HandleEditDialog, j)
            )

        self.wasInitialized = True
        self.updateHandles()

    def updateHandles(self):

        if self.wasInitialized:
            for i in range(0, len(self.handles) - 1):

                try:
                    self.handles[i]["item"].sigEditRequest.disconnect()
                except:
                    pass

            self.handles[0]["item"].sigEditRequest.connect(
                lambda: self.HandleEditDialog(0)
            )
            start = -1 if self.closed else 0

            for i in range(start, len(self.handles) - 1):
                j = i + 1
                self.handles[j]["item"].sigEditRequest.connect(
                    functools.partial(self.HandleEditDialog, j)
                )
                try:
                    diag = cvEditDialog(self, j)
                    diag.reset()
                except:
                    pass

            self.wasInitialized = True
            self.wasModified.emit()


class brucknerRoi(CustomPolyLineROI):
    wasModified = QtCore.pyqtSignal()
    modified = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwds):
        super(brucknerRoi, self).__init__(*args, **kwds)
        self.ismodifying = False
        self.ypos = self.pos().y()

    def removeRect(self, handle):
        try:
            self.plotWidget.removeItem(handle.leg)
            self.plotWidget.removeItem(handle.rect1)
            self.plotWidget.removeItem(handle.rect2)
        except:
            pass
        pg.QtGui.QGuiApplication.processEvents()

    def moveCota(self, y):
        self.setPos(QPointF(self.pos().x(), y - self.ymed))
        self.ypos = y - self.ymed
        for handle in self.getHandles()[1:-1]:
            handle.sigRemoveRequested.emit(handle)
        self.removeRect(self.getHandles()[0])
        self.removeRect(self.getHandles()[-1])

    # pos should be in this item's coordinate system
    def segmentClicked(self, segment, ev=None, pos=None):
        if ev != None:
            pos = segment.mapToParent(ev.pos())
        elif pos != None:
            pos = pos
        else:
            raise Exception("Either an event or a position must be given.")
        if ev.button() == QtCore.Qt.RightButton:
            d = brucknerRampaDialog(self, segment, pos)
            d.cotasb.setValue((self.pos().y() + self.ymed) / 1000000)
            d.cotasb.valueChanged.connect(
                lambda: self.moveCota(d.cotasb.value() * 1000000)
            )
            self.ismodifying = True
            d.exec_()
            self.ismodifying = False
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

        elif ev.button() == QtCore.Qt.LeftButton:
            h1 = segment.handles[0]["item"]
            h2 = segment.handles[1]["item"]
            i = self.segments.index(segment)
            h3 = self.addFreeHandle(pos, index=self.indexOfHandle(h2))
            self.addSegment(h3, h2, index=i + 1)
            segment.replaceHandle(h2, h3)
            y0 = self.getHandles()[0].pos().y()
            h1.setPos(QPointF(h1.pos().x(), y0))
            h2.setPos(QPointF(h2.pos().x(), y0))
            h3.setPos(QPointF(h3.pos().x(), y0))
            self.wasModified.emit()
            self.sigRegionChangeFinished.emit(self)

    def setPoints(self, points, closed=None):
        self.wasInitialized = False
        QgsMessageLog.logMessage(
            "Iniciando pontos do diagrama de bruckner", "GeoRoad", level=0
        )
        if closed is not None:
            self.closed = closed
        self.clearPoints()

        first = True
        for p in points:
            self.addRotateHandle(p, p)
        #  self.addTranslateHandle(p)

        start = -1 if self.closed else 0

        self.handles[0]["item"].sigEditRequest.connect(lambda: self.HandleEditDialog(0))
        self.handles[0]["item"].fixedOnX = True
        self.handles[0]["item"].fixedOnY = True
        self.handles[0]["item"].edge = True

        for i in range(start, len(self.handles) - 1):
            self.addSegment(self.handles[i]["item"], self.handles[i + 1]["item"])
            j = i + 1
            self.handles[j]["item"].fixedOnY = True

        self.handles[j]["item"].fixedOnX = True
        self.handles[j]["item"].fixedOnY = True
        self.handles[j]["item"].edge = True

        self.wasInitialized = True
        self.updateHandles()

    def updateHandles(self):

        if self.wasInitialized:
            for i in range(0, len(self.handles) - 1):
                try:
                    self.handles[i]["item"].sigEditRequest.disconnect()
                except:
                    pass

            start = -1 if self.closed else 0
            for i in range(start, len(self.handles) - 1):
                j = i + 1
                self.handles[j]["item"].fixedOnY = True
                try:
                    diag = cvEditDialog(self, j)
                    diag.reset()
                except:
                    pass
            self.wasInitialized = True


class Ui_Perfil(QtWidgets.QDialog):

    save = QtCore.pyqtSignal(bool)
    reset = QtCore.pyqtSignal()

    def __init__(
        self,
        ref_estaca,
        tipo,
        classeProjeto,
        greide,
        cvList,
        wintitle="Perfil Longitudinal",
        iface=None,
    ):
        super(Ui_Perfil, self).__init__(None)
        self.iface = iface
        self.initVars(ref_estaca, tipo, classeProjeto, greide, cvList, wintitle)
        self.setupUi(self)

    def initVars(self, ref_estaca, tipo, classeProjeto, greide, cvList, wintitle):
        self.everPloted = False
        self.showDistances = False
        self.ref_estaca = ref_estaca
        self.tipo = tipo
        self.classeProjeto = classeProjeto
        self.estaca1txt = -1
        self.estaca2txt = -1
        self.greide = greide
        self.cvList = cvList
        self.vb = CustomViewBox()
        self.perfilPlot = pg.PlotWidget(
            viewBox=self.vb, enableMenu=False, title=wintitle
        )
        self.perfilPlot.curves = []
        self.saved = True
        self.isValid = False

    def showMaximized(self):
        if self.isValid:
            return super().showMaximized()
        else:
            return False

    def exec_(self):
        if self.isValid:
            return super().exec_()
        else:
            return messageDialog(
                message="Defina as cotas na tabela de horizontais primeiro!"
            )

    def __setAsNotSaved(self):
        self.lblTipo.setText("Modificado")
        self.saved = False

    def perfil_grafico(self):
        pontos = []
        k = 0
        while True:
            try:
                ponto = []
                # e = self.ref_estaca[k][0]
                # if e in [None,""]:
                #     break

                ponto.append(float(self.ref_estaca[k][1]))
                ponto.append(float(self.ref_estaca[k][2]))
                pontos.append(ponto)
                if ponto[1] != 0:
                    self.isValid = True
                # self.comboEstaca1.addItem(_fromUtf8(e))
            except:
                break
            k += 1

        x, y = list(zip(*pontos))
        x = list(x)
        y = list(y)
        self.V = y
        self.X = x
        self.ymed = np.average(y)
        self.perfilPlot.plot(x=x, y=y, symbol="o")
        self.perfilPlot.setWindowTitle("Perfil Vertical")
        # A = np.array([x,np.ones(len(x))])
        # w = np.linalg.lstsq(A.T,y)[0]
        if self.greide:
            # i=0
            lastHandleIndex = len(self.greide) - 1
            L = []
            for pt in self.greide:
                xh = pt[0]
                cota = pt[1]
                pos = (xh, cota)
                L.append(pos)
            if xh != x[-1]:
                final = (x[-1], cota)
                self.greide[-1] = final
                messageDialog(message="O último vértice foi ajustado ao novo traçado!")
                L[-1] = final
            self.roi = CustomPolyLineROI(L, plot=self.perfilPlot)
        else:
            # self.roi = CustomPolyLineROI([(x[0], w[0]*x[0]+w[1]), (x[len(x)-1],w[0]*x[len(x)-1]+w[1])], plot=self.perfilPlot)
            self.roi = CustomPolyLineROI(
                [(x[0], y[0]), (x[-1], y[-1])], plot=self.perfilPlot
            )
        self.roi.perfil = self
        self.roi.wasModified.connect(self.__setAsNotSaved)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.perfilPlot.addItem(self.roi)

        self.lastGreide = self.getVertices()
        self.lastCurvas = self.getCurvas()
        self.roi.setPlotWidget(self.perfilPlot)
        self.roi.addCvs(self.cvList)
        self.roi.sigRegionChangeFinished.connect(self.modifiedRoi)
        self.roi.sigRegionChangeFinished.connect(self.updater)

        # self.perfilPlot.plot(y,x)

    def updater(self):
        self.computingLabel.setText("Processando....")
        if not self.showDistances:
            for h in self.roi.getHandles():
                self.roi.removeRect(h)
            pg.QtGui.QGuiApplication.processEvents()
            self.computingLabel.clear()
            return
        if not self.roi.ismodifying:
            handles = [self.roi.getHandlePos(i) for i in range(self.roi.countHandles())]
            for j, handlePos in enumerate(handles[1:]):  # para cada segmento
                I = (handles[j + 1].y() - handles[j].y()) / (
                    handles[j + 1].x() - handles[j].x()
                )
                greideStart = [handles[j].x(), handles[j].y()]
                distsY = []
                Xs = []
                terreno = []
                greides = []
                endX = handlePos.x()
                lx = greideStart[0]
                i1 = max([i for i, ix in enumerate(self.X) if ix <= lx])
                i2 = min([i for i, ix in enumerate(self.X) if ix >= endX])
                # para cada estaca
                for i, pt in enumerate(zip(self.X[i1:i2], self.V[i1:i2])):
                    x = pt[0]
                    y = pt[1]
                    greideY = greideStart[1] + I * (x - greideStart[0])
                    distsY.append(y - greideY)
                    Xs.append(x)
                    terreno.append([x, y])
                    greides.append([x, greideY])
                ymax = max(distsY)
                ymin = min(distsY)
                if ymax > 0 and ymin > 0:
                    ymin = 0
                else:
                    indexMin = distsY.index(ymin)
                    xmin = Xs[indexMin]
                    tmin = terreno[indexMin][1]
                    gmin = greides[indexMin][1]
                if ymin < 0 and ymax < 0:
                    ymax = 0
                else:
                    indexMax = distsY.index(ymax)
                    xmax = Xs[indexMax]
                    tmax = terreno[indexMax][1]
                    gmax = greides[indexMax][1]

                #  Plotar cota
                handle = self.roi.handles[j + 1]["item"]
                self.roi.removeRect(handle)
                if ymin != 0:
                    handle.rect1 = pg.PlotCurveItem()
                    handle.rect1.setData(
                        [xmin, xmin],
                        [gmin, tmin],
                        pen=pg.mkPen("b", width=2, style=QtCore.Qt.SolidLine),
                    )
                    handle.leg1 = pg.TextItem(color=(200, 200, 200))
                    handle.leg1.setHtml("%s m" % (str(roundFloatShort(ymin))))
                    handle.leg1.setAnchor((0, 0))
                    handle.leg1.setPos(xmin, gmin + (ymin) / 2)
                    self.roi.plotWidget.addItem(handle.rect1)
                    self.roi.plotWidget.addItem(handle.leg1)

                if ymax != 0:
                    handle.rect2 = pg.PlotCurveItem()
                    handle.rect2.setData(
                        [xmax, xmax],
                        [gmax, tmax],
                        pen=pg.mkPen("b", width=2, style=QtCore.Qt.SolidLine),
                    )
                    handle.leg2 = pg.TextItem(color=(200, 200, 200))
                    handle.leg2.setHtml("%s m" % (str(roundFloatShort(ymax))))
                    handle.leg2.setAnchor((0, 0))
                    handle.leg2.setPos(xmax, gmax + (ymax) / 2)
                    self.roi.plotWidget.addItem(handle.rect2)
                    self.roi.plotWidget.addItem(handle.leg2)

                handle.sigRemoveRequested.connect(self.roi.removeRect)

            pg.QtGui.QGuiApplication.processEvents()
        self.computingLabel.clear()

    def calcularGreide(self):
        self.roi.getMenu()
        I = []
        handles = self.roi.getHandles()
        for i in range(0, len(self.roi.getHandles()) - 1):
            g1 = []
            g2 = []
            handle = handles[i]
            nextHandle = handles[i + 1]
            g1.append(handle.pos().x())
            g1.append(handle.pos().y())
            g2.append(nextHandle.pos().x())
            g2.append(nextHandle.pos().y())
            p1 = abs((g1[1] - g2[1]) / (g1[0] - g2[0])) * 100
            I.append(p1)
        A = []
        for x in I:
            A.append(x)
        A.sort()
        p1 = A[len(I) - 1]
        maxIndex = I.index(p1) + 1
        classeProjeto = Config.instance().CLASSE_INDEX - 1
        cfg = Config.instance()

        if p1 >= cfg.planoMin and p1 < cfg.planoMax:
            if classeProjeto <= 0:
                s = "120"
            elif classeProjeto < 4:
                s = "100"
            elif classeProjeto < 6:
                s = "80"
            else:
                s = "60"

            self.lblTipo.setText(
                "Plano %s KM/h, Rampa n° %d, Inclinação %s%%"
                % (s, maxIndex, roundFloat2str(I[maxIndex - 1])[:-2])
            )

        elif p1 >= cfg.onduladoMin and p1 < cfg.onduladoMax:
            if classeProjeto <= 0:
                s = "100"
            elif classeProjeto < 3:
                s = "80"
            elif classeProjeto < 4:
                s = "70"
            elif classeProjeto < 6:
                s = "60"
            else:
                s = "40"

            self.lblTipo.setText(
                "Ondulado %s KM/h, Rampa n° %d, Inclinação %s%%"
                % (s, maxIndex, roundFloat2str(I[maxIndex - 1])[:-2])
            )

        elif p1 <= cfg.montanhosoMax:
            if classeProjeto <= 0:
                s = "80"
            elif classeProjeto < 3:
                s = "60"
            elif classeProjeto < 4:
                s = "50"
            elif classeProjeto < 6:
                s = "40"
            else:
                s = "30"
            self.lblTipo.setText(
                "Montanhoso %s KM/h, Rampa n° %d, Inclinação %s%%"
                % (s, maxIndex, roundFloat2str(I[maxIndex - 1])[:-2])
            )

        else:
            s = "0"
            self.lblTipo.setText(
                "Indefinido %s KM/h, Rampa n° %d, Inclinação %s%%"
                % (s, maxIndex, roundFloat2str(I[maxIndex - 1])[:-2])
            )

        self.velProj = int(s)

        for a in A:
            maxIndex = I.index(a) + 1
            if a == p1:
                if hasattr(self, "maxInclinationIndicatorLine"):
                    self.perfilPlot.removeItem(self.maxInclinationIndicatorLine)
                    self.maxInclinationIndicatorLine.clear()
                    self.perfilPlot.update()
                self.maxInclinationIndicatorLine = pg.PlotCurveItem()
                self.maxInclinationIndicatorLine.setData(
                    [
                        self.roi.getHandlePos(maxIndex - 1).x(),
                        self.roi.getHandlePos(maxIndex).x(),
                    ],
                    [
                        self.roi.getHandlePos(maxIndex - 1).y(),
                        self.roi.getHandlePos(maxIndex).y(),
                    ],
                    pen=pg.mkPen("r", width=4),
                )
                self.perfilPlot.addItem(self.maxInclinationIndicatorLine)

    def modifiedRoiStarted(self):
        self.roi.updateHandles()
        try:
            self.perfilPlot.removeItem(self.maxInclinationIndicatorLine)
            self.maxInclinationIndicatorLine.clear()
            self.perfilPlot.update()
            self.vb.update()
        except Exception as e:
            import traceback

            msgLog("Falha ao remover linha!")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__)))

    def modifiedRoi(self):
        self.modifiedRoiStarted()
        pass

    def estaca1(self, ind):
        self.estaca1txt = ind - 1

    def estaca2(self, ind):
        self.estaca2txt = ind - 1

    def toggleDistances(self):
        self.showDistances = not self.showDistances
        self.updater()

    def setupUi(self, PerfilTrecho):
        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(590, 169)

        self.perfil_grafico()

        self.lblTipo = QtWidgets.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.calcularGreide)

        self.btnAutoRange = QtWidgets.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Escala")
        self.btnAutoRange.clicked.connect(self.showEscalaDialog)

        self.btnDistances = QtWidgets.QPushButton(PerfilTrecho)
        self.btnDistances.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnDistances.setText("Distâncias")
        self.btnDistances.clicked.connect(self.toggleDistances)

        self.btnSave = QtWidgets.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Aplicar")
        self.btnSave.clicked.connect(self.salvarPerfil)

        self.btnCancel = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCancel.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCancel.setText("Fechar")
        self.btnCancel.clicked.connect(self.close)

        self.btnReset = QtWidgets.QPushButton(PerfilTrecho)
        self.btnReset.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnReset.setText("Apagar")
        self.btnReset.clicked.connect(self.resetGeometry)

        self.computingLabel = QtWidgets.QLabel("Processando...")
        self.computingLabel.setAlignment(QtCore.Qt.AlignRight)
        self.computingLabel.clear()

        Hlayout = QtWidgets.QHBoxLayout()
        Hlayout2 = QtWidgets.QHBoxLayout()
        Vlayout = QtWidgets.QVBoxLayout()

        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)

        Hlayout.addWidget(self.btnCalcular)
        Hlayout.addWidget(self.btnAutoRange)
        Hlayout.addWidget(self.btnDistances)
        Hlayout.addWidget(self.btnSave)
        Hlayout.addWidget(self.btnReset)
        Hlayout.addWidget(self.btnCancel)
        Hlayout2.addWidget(self.computingLabel)
        Vlayout.addLayout(Hlayout)
        Vlayout.addLayout(Hlayout2)
        Vlayout.addWidget(self.lblTipo)
        Vlayout.addWidget(self.perfilPlot)

        self.setLayout(Vlayout)

        PerfilTrecho.setWindowTitle(
            _translate("PerfilTrecho", "Perfil do trecho", None)
        )
        self.calcularGreide()
        self.btnCalcular.setText("Calcular rampa máxima")

    def resetGeometry(self):
        reset = yesNoDialog(self, message="Realmente deseja excluir esse perfil?")
        if reset:
            self.reset.emit()

    def showEscalaDialog(self):
        dialog = setEscalaDialog(self)
        dialog.show()
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            pass
        else:
            pass

    def salvarPerfil(self, noreset=False):
        """exportar greide para o banco de dados
        sinal emitido para salvar"""

        self.save.emit(noreset)
        self.saved = True
        self.lastGreide = self.getVertices()
        self.lastCurvas = self.getCurvas()
        self.lblTipo.setText("Salvo!")

    def getCurvas(self):
        r = []
        for i in range(0, self.roi.countHandles()):
            x = []
            x.append(i)
            try:
                x.append(str(self.roi.handles[i]["item"].curve.L))

            except:
                x.append(str(None))
            r.append(x)

        return r

    def getVertices(self):
        r = []
        for handle in self.roi.getHandles():
            x = []
            x.append(str(handle.pos().x()))
            x.append(str(handle.pos().y()))
            r.append(x)

        return r

    def wasSaved(self):
        if (
            self.lastGreide == self.getVertices()
            and self.lastCurvas == self.getCurvas()
        ):
            return True
        else:
            return False

    def reject(self):
        if not self.wasSaved():
            closedialog = closeDialog(self)
            closedialog.setModal(True)
            closedialog.save.connect(self.__exitSave)
            #            closedialog.cancel.connect(closedialog.close)
            closedialog.dischart.connect(self.justClose)
            closedialog.exec_()
            return
        return super(Ui_Perfil, self).reject()

    def closeEvent(self, event):
        if not self.wasSaved():
            closedialog = closeDialog(self)
            closedialog.setModal(True)
            closedialog.save.connect(self.__exitSave)
            closedialog.cancel.connect(event.ignore)
            closedialog.dischart.connect(self.close)
            closedialog.exec_()
        else:
            event.accept()
            super(Ui_Perfil, self).closeEvent(event)

    def __exitSave(self):
        self.salvarPerfil(noreset=True)
        self.close()

    def justClose(self):
        self.wasSaved = lambda: True
        self.close()


class Ui_sessaoTipo(Ui_Perfil):

    save = QtCore.pyqtSignal(bool)
    plotar = QtCore.pyqtSignal(int)

    def __init__(
        self,
        iface,
        terreno,
        hor,
        ver=[],
        st=False,
        prism=None,
        estacanum=0,
        greide=[],
        title="Perfil Transversal",
    ):
        self.progressiva = []
        self.terreno = []
        self.iface = iface
        self.editMode = True
        self.intersecTable = hor

        if not st:
            msgLog("Creating new terrain")
            st = []
            self.terreno = terreno
            self.verticais = self.vGreideCurve(hor)
            defaultST = [
                [-9.549337802669857, -5.325013960480259],
                [-8.049337802669857, -5.370013960480259],
                [-4.299337802669858, -0.3700139604802599],
                [-4.099337802669858, -0.8700139604802597],
                [-3.699337802669858, -0.8700139604802597],
                [-3.499337802669858, -0.0700139604802598],
                [0.0006621973301417, -1.39604802598e-05],
                [3.500662197330141, -0.0700139604802598],
                [3.700662197330141, -0.8700139604802597],
                [4.100662197330142, -0.8700139604802597],
                [4.300662197330142, -0.3700139604802599],
                [6.800662197330142, 4.62998603951974],
                [8.300662197330142, 4.58498603951974],
            ]

            for item in hor:
                self.progressiva.append(float(item[2]))
                newST = []
                for pt in defaultST:
                    newST.append([pt[0], pt[1] + self.verticais.getY(float(item[2]))])
                st.append(newST)
            self.st = st

        else:
            msgLog("Using existing terrain")
            self.terreno = terreno
            self.progressiva = ver
            self.st = st
            self.verticais = self.vGreideCurve(hor)

        self.current = estacanum

        super(Ui_sessaoTipo, self).__init__(iface, 0, 0, st[self.current], [], title)

        if prism is None:
            try:
                self.prismoide
            except AttributeError:
                self.prismoide = Prismoide.QPrismoid(
                    self.terreno, self.st, self.progressiva
                )
                self.prismoide.generate(self.current)
        else:
            self.prismoide = Prismoide.QPrismoid(prism=prism, cti=7)

        if (
            not len(self.terreno)
            == len(self.st)
            == len(self.progressiva)
            == len(self.verticais.getPoints())
            == len(self.prismoide.progressiva)
        ):
            msgLog("Terreno: " + str(len(self.terreno)))
            msgLog("Progressiva: " + str(len(self.progressiva)))
            msgLog("Verticais: " + str(len(self.verticais.getPoints())))
            msgLog("Prismoide: " + str(len(self.prismoide.progressiva)))
            messageDialog(
                message="O traçado foi modificado! As edições não vão funcionar corretamente!"
            )

        self.roi.sigRegionChangeFinished.connect(self.updateData)
        self.updateAreaLabels()
        self.isValid = True

    def updater(self):
        pass

    def vGreideCurve(self, greide):
        ptList = []
        for item in greide:
            ptList.append(Figure.point(item[2], item[5]))
        greide = Figure.curve()
        greide.setPoints(ptList)
        return greide

    def createPrismoid(self, j):
        if not self.prismoide.generate(j) is None:
            messageDialog(
                title="Erro",
                message="Falha ao criar o talude na estaca: "
                + str(self.progressiva[j])
                + " estaca: "
                + prog2estacaStr(self.progressiva[j]),
            )
        self.updateAreaLabels()

    def createLabels(self):
        self.banquetaLbC = pg.TextItem(
            text="Banqueta em aterro", color=(200, 200, 200), anchor=(0.5, 0)
        )
        self.taludeLbC = pg.TextItem(text="Talude de aterro", anchor=(0.5, 0))
        self.pistaLb = pg.TextItem(text="Pista", anchor=(0.5, 0))
        self.banquetaLbA = pg.TextItem(
            text="Banqueta em corte", color=(200, 200, 200), anchor=(0.5, 0)
        )
        self.taludeLbA = pg.TextItem(text="Talude de corte", anchor=(0.5, 0))

    def perfil_grafico(self, reseting=False):
        if not reseting:
            self.perfilPlot.setWindowTitle("Seção Tipo")
            self.createLabels()

        if self.greide:
            lastHandleIndex = len(self.greide) - 1
            L = []
            for pt in self.greide:
                x = pt[0]
                cota = pt[1]
                pos = (x, cota)
                L.append(pos)

            self.roi = ssRoi(
                L, cota=self.verticais.getY(self.progressiva[self.current])
            )
            self.roi.wasModified.connect(self.setAsNotSaved)
            self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
            self.perfilPlot.addItem(self.roi)

        if reseting:
            self.st[self.current] = self.greide
            self.updateData()

        self.lastGreide = self.getVertices()
        self.lastCurvas = self.getCurvas()
        self.roi.setPlotWidget(self.perfilPlot)

        X = []
        Y = []
        for x, y in self.terreno[self.current]:
            X.append(x)
            Y.append(y)

        self.perfilPlot.plot(X, Y)
        self.updateLabels()

    def updateLabels(self):

        self.banquetaLbC.setPos(
            self.roi.getHandlePos(0).x(), self.roi.getHandlePos(0).y()
        )
        self.taludeLbC.setPos(
            (self.roi.getHandlePos(2).x() + self.roi.getHandlePos(1).x()) / 2,
            (self.roi.getHandlePos(1).y() + self.roi.getHandlePos(2).y()) / 2,
        )
        middle = float(self.st[self.current][int(len(self.st[self.current]) / 2)][1])
        self.pistaLb.setPos(0, middle)
        self.banquetaLbA.setPos(
            self.roi.getHandlePos(len(self.roi.handles) - 1).x(),
            self.roi.getHandlePos(len(self.roi.handles) - 1).y(),
        )
        self.taludeLbA.setPos(
            (
                self.roi.getHandlePos(len(self.roi.handles) - 3).x()
                + self.roi.getHandlePos(len(self.roi.handles) - 2).x()
            )
            / 2,
            (
                self.roi.getHandlePos(len(self.roi.handles) - 3).y()
                + self.roi.getHandlePos(len(self.roi.handles) - 2).y()
            )
            / 2,
        )

        self.perfilPlot.removeItem(self.banquetaLbA)
        self.perfilPlot.removeItem(self.taludeLbA)
        self.perfilPlot.removeItem(self.banquetaLbC)
        self.perfilPlot.removeItem(self.taludeLbC)
        self.perfilPlot.removeItem(self.pistaLb)

        self.perfilPlot.addItem(self.banquetaLbA)
        self.perfilPlot.addItem(self.taludeLbA)
        self.perfilPlot.addItem(self.banquetaLbC)
        self.perfilPlot.addItem(self.taludeLbC)
        self.perfilPlot.addItem(self.pistaLb)

    def updateData(self):
        self.updateLabels()
        if not self.editMode:
            self.plotTransCurve()

        #        if self.editMode:
        vt = self.getVertices()
        self.st[self.current] = vt
        self.prismoide.st = self.st
        self.createPrismoid(self.current)

        self.perfilPlot.scale(1, 1)

    def getMatrixVertices(self):

        r = []
        r.append([])
        r.append([])

        for i, _ in enumerate(self.progressiva):
            r[1].append(self.terreno[i])
            r[0].append(self.st[i])

        return r

    def getTerrenoVertices(self):
        return self.terreno

    def getxList(self):
        return self.progressiva

    def setAsNotSaved(self):
        self.lblTipo.setText("Modificado")
        self.saved = False

    def plotTrans(self):

        items = ["Plotar transversal atual", "Plotar todas transversais"]
        item, ok = QtWidgets.QInputDialog.getItem(
            None,
            "Plotar transversais",
            "Escolha uma opção para gerar as linhas:",
            items,
            0,
            False,
        )

        if ok:
            if item == items[0]:
                self.plotar.emit(self.current)
            elif item == items[1]:
                self.plotar.emit(-1)

    def exec_(self):
        self.salvarPerfil()
        return super().exec_()

    def calcularGreide(self):
        pass

    def setupUi(self, PerfilTrecho):

        PerfilTrecho.setObjectName(_fromUtf8("PerfilTrecho"))
        PerfilTrecho.resize(680, 320)

        self.perfil_grafico()

        self.lblTipo = QtWidgets.QLabel(PerfilTrecho)
        self.lblTipo.setGeometry(QtCore.QRect(220, 140, 181, 21))
        self.lblTipo.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTipo.setObjectName(_fromUtf8("lblTipo"))

        self.btnCalcular = QtWidgets.QPushButton(PerfilTrecho)
        self.btnCalcular.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnCalcular.setObjectName(_fromUtf8("btnCalcular"))
        self.btnCalcular.clicked.connect(self.plotTrans)
        self.btnCalcular.setText("Criar Layer")
        self.btnCalcular.setToolTip(
            "Plotar Layers com as tranversais sobre o traçado horizontal (Perpendiculares ao traçado)"
        )

        self.btnExportDxf = QtWidgets.QPushButton(PerfilTrecho)
        self.btnExportDxf.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnExportDxf.setObjectName(_fromUtf8("btnExportDxf"))
        self.btnExportDxf.setText("Exportar")
        self.btnExportDxf.setToolTip("Exporta DXF que pode ser modificado e importado")

        self.btnImportDxf = QtWidgets.QPushButton(PerfilTrecho)
        self.btnImportDxf.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnImportDxf.setObjectName(_fromUtf8("btnImportDxf"))
        self.btnImportDxf.setText("Importar")
        self.btnImportDxf.setToolTip("Importar DXF com a seção tipo")

        self.btnAutoRange = QtWidgets.QPushButton(PerfilTrecho)
        self.btnAutoRange.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnAutoRange.setText("Extender visão")
        self.btnAutoRange.clicked.connect(lambda: self.vb.autoRange())
        self.btnAutoRange.setToolTip("Ajusta o zoom e retorna para visualização padrão")

        self.btnSave = QtWidgets.QPushButton(PerfilTrecho)
        self.btnSave.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnSave.setText("Salvar")
        self.btnSave.clicked.connect(self.salvarPerfil)
        self.btnSave.setToolTip("Armazena edições")

        self.btnClean = QtWidgets.QPushButton(PerfilTrecho)
        self.btnClean.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnClean.setText("Recalcular")
        self.btnClean.setToolTip(
            "Apaga todas as modificações e retorna com o perfil padrão para todo o traçado"
        )

        self.btnReset = QtWidgets.QPushButton(PerfilTrecho)
        self.btnReset.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnReset.setText("Restaurar seção")
        self.btnReset.clicked.connect(self.resetSS)
        self.btnReset.setToolTip("Descarta as modificações na seção atual")

        self.btnVolume = QtWidgets.QPushButton(PerfilTrecho)
        self.btnVolume.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnVolume.setText("Volume")
        self.btnVolume.clicked.connect(self.volumeCalc)
        self.btnVolume.setToolTip("Calcular volumes de aterro e de corte")

        self.btnPrevious = QtWidgets.QPushButton(PerfilTrecho)
        self.btnPrevious.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnPrevious.setText("Anterior")
        self.btnPrevious.clicked.connect(self.previousEstaca)
        self.btnPrevious.setToolTip("Estaca anterior (seta esquerda)")

        self.btnNext = QtWidgets.QPushButton(PerfilTrecho)
        self.btnNext.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnNext.setText("Próxima")
        self.btnNext.clicked.connect(self.nextEstaca)
        self.btnNext.setToolTip("Proxima estaca (seta direita)")

        self.shortcut1 = QtWidgets.QShortcut(QtGui.QKeySequence.MoveToNextChar, self)
        self.shortcut2 = QtWidgets.QShortcut(
            QtGui.QKeySequence.MoveToPreviousChar, self
        )
        self.shortcut1.activated.connect(self.nextEstaca)
        self.shortcut2.activated.connect(self.previousEstaca)

        self.btnEditToggle = QtWidgets.QPushButton(PerfilTrecho)
        self.btnEditToggle.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.btnEditToggle.setText("Visualizar")
        self.btnEditToggle.clicked.connect(self.editToggle)

        self.selectEstacaComboBox = QtWidgets.QComboBox(PerfilTrecho)
        dist = Config.instance().DIST
        self.selectEstacaComboBox.addItems(
            list(map(lambda i: fastProg2EstacaStr(i, dist), self.progressiva))
        )
        self.selectEstacaComboBox.currentIndexChanged.connect(self.changeEstaca)
        self.selectEstacaComboBox.view().setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded
        )

        self.applyBtn = QtWidgets.QPushButton(PerfilTrecho)
        self.applyBtn.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.applyBtn.setText("Aplicar")
        self.applyBtn.clicked.connect(self.applyTrans)
        self.applyBtn.setToolTip("Aplica o desenho atual para um intervalo de estacas")

        self.ctatiBtn = QtWidgets.QPushButton(PerfilTrecho)
        self.ctatiBtn.setGeometry(QtCore.QRect(260, 80, 99, 27))
        self.ctatiBtn.setText("Laterais")
        self.ctatiBtn.clicked.connect(self.setAtCti)
        self.ctatiBtn.setToolTip(
            "Define os segmentos de reta que devem se repetir a partir das laterais de corte e aterro até a interseção com o terreno"
        )

        self.areaCtLb = QtWidgets.QLabel(PerfilTrecho)
        self.areaAtLb = QtWidgets.QLabel(PerfilTrecho)
        self.areaLb = QtWidgets.QLabel(PerfilTrecho)
        self.progressivaLb = QtWidgets.QLabel(PerfilTrecho)

        self.btnNext.setDisabled(self.current >= len(self.progressiva) - 1)
        self.btnPrevious.setDisabled(self.current == 0)
        QtCore.QMetaObject.connectSlotsByName(PerfilTrecho)

        self.layAllOut()

        PerfilTrecho.setWindowTitle(
            _translate("PerfilTrecho", "Perfil do trecho", None)
        )
        self.calcularGreide()

        self.changingEstaca = False

    def resetSS(self):
        self.perfilPlot.removeItem(self.roi)
        self.perfil_grafico(reseting=True)

    #        self.reset()

    def volumeCalc(self):
        try:
            diag = VolumeDialog(self)
            ct, at = self.prismoide.getVolumes(0)
            diag.set(ct, at)
            diag.exec_()
        except Exception as e:
            import traceback

            msgLog(str(traceback.format_exception(None, e, e.__traceback__)))
            messageDialog(message="Erro! Os taludes definidos não encontram o terreno!")

    def layAllOut(self):

        layout = self.layout()

        if layout is not None:
            index = layout.count() - 1
            while index >= 0:
                element = layout.itemAt(index).widget()
                if element is None:
                    element = layout.itemAt(index).layout()
                if element is not None:
                    element.setParent(None)

                index -= 1

        Hlayout = QtWidgets.QHBoxLayout()
        Hlayout2 = QtWidgets.QHBoxLayout()
        Hlayout3 = QtWidgets.QHBoxLayout()
        Vlayout = QtWidgets.QVBoxLayout()

        Hlayout.addWidget(self.btnCalcular)
        Hlayout.addWidget(self.btnExportDxf)
        Hlayout.addWidget(self.btnImportDxf)
        Hlayout.addWidget(self.applyBtn)
        Hlayout.addWidget(self.btnAutoRange)
        Hlayout.addWidget(self.btnReset)
        Hlayout.addWidget(self.btnClean)
        Hlayout.addWidget(self.btnSave)
        Hlayout.addWidget(self.btnVolume)

        Hlayout3.addWidget(self.areaLb)
        Hlayout3.addWidget(self.areaCtLb)
        Hlayout3.addWidget(self.areaAtLb)

        Hlayout3.addWidget(self.progressivaLb)

        Hlayout2.addWidget(self.btnEditToggle)
        Hlayout2.addWidget(self.ctatiBtn)
        Hlayout2.addWidget(self.selectEstacaComboBox)
        Hlayout2.addWidget(self.btnPrevious)
        Hlayout2.addWidget(self.btnNext)

        Vlayout.addLayout(Hlayout)
        Vlayout.addLayout(Hlayout3)
        Vlayout.addWidget(self.lblTipo)
        Vlayout.addWidget(self.perfilPlot)
        Vlayout.addLayout(Hlayout2)

        self.setLayout(Vlayout)
        self.Vlayout = Vlayout

    def disableArrowButtons(self, bool):
        self.btnEditToggle.setDisabled(bool)
        self.btnPrevious.setDisabled(bool)
        self.btnNext.setDisabled(bool)
        self.selectEstacaComboBox.setDisabled(bool)

    def nextEstaca(self):
        if self.current < len(self.progressiva) - 1 and not self.changingEstaca:
            self.current += 1
            self.changingEstaca = True
            self.reset()

    def previousEstaca(self):
        if self.current > 0 and not self.changingEstaca:
            self.current -= 1
            self.changingEstaca = True
            self.reset()

    def editToggle(self):
        if self.editMode:
            self.btnEditToggle.setText("Esconder")
            self.plotTransCurve()

        else:
            self.btnEditToggle.setText("Visualizar")
            self.curve.clear()
            self.perfilPlot.removeItem(self.curve)

        self.editMode = not self.editMode

    def changeEstaca(self):

        if not self.changingEstaca:
            self.current = int(
                self.progressiva.index(
                    estaca2progFloat(self.selectEstacaComboBox.currentText())
                )
            )
            self.reset()

    def reset(self):
        perfilPlot = self.perfilPlot
        self.disableArrowButtons(True)

        self.initVars(self.iface, 0, 0, self.st[self.current], [], "Perfil Transversal")
        self.perfil_grafico()
        self.roi.sigRegionChangeFinished.connect(self.updateData)

        self.btnNext.setDisabled(self.current == len(self.progressiva))
        self.btnPrevious.setDisabled(self.current == 0)
        self.selectEstacaComboBox.setCurrentIndex(self.current)
        self.Vlayout.replaceWidget(perfilPlot, self.perfilPlot)
        self.disableArrowButtons(False)

        if not self.editMode:
            self.plotTransCurve()

        if self.prismoide.lastGeneratedIndex < self.current:
            self.createPrismoid(self.current)

        self.btnNext.setDisabled(self.current >= len(self.progressiva) - 1)
        self.btnPrevious.setDisabled(self.current == 0)
        self.updateAreaLabels()
        pg.QtGui.QGuiApplication.processEvents()
        self.changingEstaca = False

    def updateAreaLabels(self):
        try:
            act, aat = self.prismoide.getFace(self.current).getAreas()
            area = self.prismoide.getFace(self.current).getArea()
        except Exception as e:
            import traceback

            msgLog(str(traceback.format_exception(None, e, e.__traceback__)))
            messageDialog(message="Erro! Os taludes definidos não encontram o terreno!")
            area = act = aat = 0
        self.areaLb.setText("Area: " + str(round(area, 3)) + "m²")
        dist = Config.instance().DIST
        self.progressivaLb.setText(
            "E: "
            + str(int(self.progressiva[self.current] / dist))
            + " + "
            + str(
                round(
                    (
                        self.progressiva[self.current] / dist
                        - int(self.progressiva[self.current] / dist)
                    )
                    * dist,
                    4,
                )
            )
            + "  "
            + str(self.intersecTable[self.current][1])
        )
        # act,aat = self.prismoide.getAreasCtAt(self.current)
        self.areaCtLb.setText("Corte: " + str(round(act, 3)) + "m²")
        self.areaAtLb.setText("Aterro: " + str(round(aat, 3)) + "m²")

    def plotTransCurve(self):

        if self.everPloted:
            self.curve.clear()
            self.perfilPlot.removeItem(self.curve)

        self.everPloted = True

        self.curve = pg.PlotCurveItem()

        X, Y = Figure.plotCurve(self.prismoide.getCurve(self.current))

        self.curve.clear()
        self.curve.setData(X, Y, pen=pg.mkPen("b", width=4, style=QtCore.Qt.SolidLine))
        self.perfilPlot.addItem(self.curve)

    def applyTrans(self):
        diag = ApplyTransDialog(self.iface, self.progressiva)
        diag.show()
        if diag.exec_() == QtWidgets.QDialog.Accepted:
            st = deepcopy(self.st[self.current])
            greide = self.verticais
            for estaca in range(diag.progressivas[0], diag.progressivas[1] + 1):
                progressiva = self.progressiva[estaca]
                newST = []
                for pt in st:
                    newST.append(
                        [
                            float(pt[0]),
                            float(pt[1])
                            + float(greide.getY(progressiva))
                            - float(greide.getY(self.progressiva[self.current])),
                        ]
                    )
                self.st[estaca] = newST

            self.prismoide.st = self.st
            erros = []
            for estaca in range(diag.progressivas[0], diag.progressivas[1] + 1):
                try:
                    if not self.prismoide.generate(estaca) is None:
                        erros.append(estaca)
                except Exception as e:
                    import traceback

                    msgLog(str(traceback.format_exception(None, e, e.__traceback__)))
                    erros.append(estaca)
            if erros:
                messageDialog(
                    message="Faha ao encontrar a interseção com o terreno nas estacas: \n"
                    + "; ".join([str(e) for e in erros])
                )

    def setAtCti(self):
        diag = SetCtAtiDialog(self.iface, self.roi.getVerticesList())
        diag.show()
        if diag.exec_() == QtWidgets.QDialog.Accepted:
            self.prismoide.ati = diag.ati
            self.prismoide.cti = diag.cti


class Ui_Bruckner(Ui_Perfil):

    save = QtCore.pyqtSignal()
    plotar = QtCore.pyqtSignal(int)

    def __init__(self, X, V, key="", bruck=[], bruckData=[], interval=[]):
        self.editMode = True
        self.X = X
        # self.V=[v/1000000 for v in V]
        self.V = V
        self.bruck = bruck
        self.key = key
        self.interval = interval
        self.bruckData = bruckData
        super(Ui_Bruckner, self).__init__(
            0, 0, 0, [], [], wintitle="Diagrama de Bruckner"
        )
        #        self.btnCalcular.setDisabled(True)
        self.btnDistances.hide()
        self.btnReset.clicked.disconnect()
        self.btnReset.clicked.connect(self.resetGeometry)
        self.btnReset.setText("Recalcular")
        self.btnReset.setToolTip(
            "Recalcular o diagrama de bruckner redefinindo o Fh com os novos dados de seção transversal"
        )
        self.setWindowTitle("Diagrama de Bruckner")
        self.btnSave.setText("Exportar")
        self.btnSave.setToolTip("Exportar planilha em formato csv")
        self.btnSave.clicked.connect(self.csvExport)
        self.btnCalcular.disconnect()
        self.btnCalcular.setText("Limpar Alterações")
        self.btnCalcular.setToolTip(
            "Apaga os dados relacionados à linha de terra para esse intervalo"
        )
        self.btnCalcular.clicked.connect(self.resetView)
        if not bruckData:
            self.setBruckData()
        else:
            # +self.roi.ymed))
            self.roi.setPos(QPointF(self.roi.pos().x(), float(bruckData[0][1])))
            self.updater()

    def setBruckData(self):
        r = []
        for handle in self.roi.getHandles():
            x = []
            x.append(str(handle.pos().x()))
            x.append(str(self.roi.ypos))
            r.append(x)
        self.bruckData = r
        #        self.bruckData = [[self.roi.getHandlePos(i).x(), self.roi.getHandlePos(i).y()] for i in range(self.roi.countHandles())]

    def resetView(self):
        for h in self.roi.getHandles()[1:-1]:
            h.sigRemoveRequested.emit(h)
        self.roi.removeRect(self.roi.getHandles()[-1])
        self.roi.removeRect(self.roi.getHandles()[0])
        self.setBruckData()

    def salvarPerfil(self):
        self.save.emit()

    def setAsNotSaved(self):
        pass

    def calcularGreide(self):
        pass

    def perfil_grafico(self):
        self.perfilPlot.setWindowTitle("Diagrama de Bruckner (m³)")
        #        self.createLabels()
        ymed = np.average(self.V)
        if self.bruckData:
            self.roi = brucknerRoi([[p[0], ymed] for p in self.bruckData])
        else:
            self.roi = brucknerRoi([[self.X[0], ymed], [self.X[-1], ymed]])
        self.roi.ymed = ymed
        self.roi.wasModified.connect(self.setAsNotSaved)
        self.roi.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.roi.sigRegionChangeFinished.connect(self.updater)
        self.perfilPlot.addItem(self.roi)
        self.roi.setPlotWidget(self.perfilPlot)
        self.perfilPlot.plot(self.X, self.V)
        #        self.updateLabels()
        self.isValid = True

    def updater(self):
        if not self.roi.ismodifying:
            handles = [
                self.roi.getHandlePos(i).x() for i in range(self.roi.countHandles())
            ]
            self.setBruckData()
            v0 = self.roi.pos().y() + self.roi.ymed
            dist = Config.instance().DIST
            for j, x in enumerate(handles[1:]):  # para cada segmento
                lx = handles[j]
                A = 0
                vmax = 0
                xmax = (lx + x) / 2
                i1 = max([i for i, ix in enumerate(self.X) if ix <= lx])
                i2 = min([i for i, ix in enumerate(self.X) if ix >= x])

                for i, v in enumerate(self.V[i1:i2]):  # para cada Volume
                    dx = self.X[i + 1 + i1] - self.X[i + i1]
                    A += dx * ((self.V[i + 1 + i1] + self.V[i + i1]) / 2 - v0)
                    if abs(vmax) <= abs(v - v0):
                        vmax = v - v0
                        xmax = (self.X[i + 1 + i1] + self.X[i + i1]) / 2

                lx = x
                # Distância média de transporte  vmax--> altura
                dm = abs(A / vmax)

                #  Plotar retangulo, associar com handle
                handle = self.roi.handles[j + 1]["item"]
                self.roi.removeRect(handle)
                handle.rect1 = pg.PlotCurveItem()
                handle.rect2 = pg.PlotCurveItem()
                handle.rect1.setData(
                    [xmax - dm / 2, xmax - dm / 2, xmax + dm / 2, xmax + dm / 2],
                    [v0, v0 + vmax, v0 + vmax, v0],
                    pen=pg.mkPen("b", width=4, style=QtCore.Qt.SolidLine),
                )
                handle.rect2.setData(
                    [xmax, xmax],
                    [v0, v0 + vmax],
                    pen=pg.mkPen("r", width=3, style=QtCore.Qt.SolidLine),
                )

                handle.leg = pg.TextItem(color=(200, 200, 200))
                handle.leg.setHtml(
                    "A = %s  \u33A1 <br>Vmax = %s m³<br>Dm = %s m"
                    % (
                        str(roundFloatShort(A * dist)),
                        str(roundFloatShort(vmax)),
                        str(roundFloatShort(dm * dist)),
                    )
                )
                handle.leg.setAnchor((0.5, abs(vmax) / vmax))
                handle.leg.setPos(xmax, v0 + vmax)
                handle.sigRemoveRequested.connect(self.roi.removeRect)
                self.roi.plotWidget.addItem(handle.rect1)
                self.roi.plotWidget.addItem(handle.rect2)
                self.roi.plotWidget.addItem(handle.leg)

            pg.QtGui.QGuiApplication.processEvents()

    def closeEvent(self, event):
        pass

    def wasSaved(self):
        pass

    def reject(self):
        pass

    def resetGeometry(self):
        reset = yesNoDialog(self, message="Realmente recalcular todo o Diagrama?")
        self.reseted = reset
        if reset:
            self.reset.emit()

    def csvExport(self):
        import csv

        filter = ".csv"
        filename = QtWidgets.QFileDialog.getSaveFileName(
            filter="Arquivo csv(*" + filter + " *" + filter.upper() + ")"
        )[0]
        if filename in ["", None]:
            return
        filename = (
            str(filename) if str(filename).endswith(filter) else str(filename) + filter
        )
        delimiter = str(Config.CSV_DELIMITER.strip()[0])
        table = self.bruck["table"]

        ei, ef = self.key.split("-")
        if not ei or not ef or not self.interval:
            msgLog(
                "Algo de errado com o intervalo de estacas: " + ei + "-" + ef + " !!!"
            )
            return
        ei, ef = self.interval
        table = table[ei : ef + 1]
        header = [
            "estaca",
            "corte",
            "aterro",
            "at.cor.",
            "soma",
            "semi-distancia",
            "vol.corte",
            "vol.aterro",
            "volume",
            "vol.acum",
        ]
        with open(filename, "w") as fo:
            writer = csv.writer(fo, delimiter=delimiter, dialect="excel")
            if type(header) == list:
                writer.writerow(header)
            for d in table:
                r = [d[k] for k in header]
                for i, c in enumerate(r):
                    try:
                        c = round(float(c), 4)
                        r[i] = str(c).replace(".", ",")
                    except:
                        r[i] = str(c)
                writer.writerow(r)
