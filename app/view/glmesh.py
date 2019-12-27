# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from ... import PyQtGraph as pg
from ...PyQtGraph import opengl as gl
from ..model.utils import msgLog
from ..model.config import Config

import numpy as np


shaders=[
    'balloon',
    'viewNormalColor',
    'normalColor',
    'shaded',
    'edgeHilight',
    'heightColor',
    'pointSprite']


class view3D_Ui(QtWidgets.QDialog):
    def __init__(self, intersect=[], vertices=None, faces=None):
        super().__init__()
        self.w=gl.GLViewWidget()
        self.intersect=intersect
        self.vertices=np.array(vertices)
        self.faces=np.array(faces)
        self.setWindowTitle('Modelo tridimensional')
        self.w.setCameraPosition(distance=40)
       # self.g = gl.GLGridItem()
       # self.g.scale(2, 2, 1)
       # self.g.setSize(1000000, 1000000)
       # self.w.addItem(self.g)
        self.meshList = []
        self.setupUi()

        if intersect:
            colors=[]
            msgLog("Colorindo pista...")
            terreno=[0.1,1,0.2,.85]
            pista=[.4,.15,.15,1]
            eixo=[np.array([float(intersect[j][4]), float(intersect[j][3]), float(intersect[j][5])])
                  for j in range(len(intersect))]
            n=0
            for f in faces:
                ca=terreno
#                for i in f:
#                    for j, e in enumerate(eixo[n:n+3]):
#                        d=np.linalg.norm(np.array(vertices[i]) - e)
#                        if d < 5:
#                            ca=pista
#                            if j>1:
#                                n+=1
#                            break
#                    if ca==pista:
#                        msgLog("debug: " + str(f))
#                        break
                colors.append(ca)
            msgLog("last: "+str(f))
            self.addMesh(vertices, faces, np.array(colors))
        else:
            self.addMesh(vertices, faces)

    def setupUi(self):
        self.vl=QtWidgets.QVBoxLayout()
        self.hl=QtWidgets.QHBoxLayout()
        self.vl.addWidget(self.w)
        self.comboBox=QtWidgets.QComboBox()
        self.comboBox.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.comboBox.addItems([est[0] for est in self.intersect])
        self.comboBox.currentIndexChanged.connect(self.changeEstaca)
        label=QtWidgets.QLabel("Estaca: ")
        self.hl.addWidget(label)
        self.hl.addWidget(self.comboBox)
        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.hl.addItem(spacer)
        label2=QtWidgets.QLabel("Shader: ")
        self.hl.addWidget(label2)
        cbsh=QtWidgets.QComboBox()
        cbsh.addItems(shaders)
        cbsh.currentTextChanged.connect(self.changeShader)
        cbsh.setCurrentIndex(3)
        self.hl.addWidget(cbsh)
        spacer5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.hl.addItem(spacer5)
        col1 = QtWidgets.QPushButton("Cor")
        col1.clicked.connect(self.meshColorChanged)
        self.hl.addWidget(col1)
        spacer3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.hl.addItem(spacer3)
        col=QtWidgets.QPushButton("Cor de Fundo")
        col.clicked.connect(self.colorChanged)
        self.hl.addWidget(col)
        spacer4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.hl.addItem(spacer4)
        btn = QtWidgets.QCheckBox("Wireframe")
        btn.setChecked(True)
        btn.stateChanged.connect(self.wireframeToggle)
        self.hl.addWidget(btn)
        spacer2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hl.addItem(spacer2)
        self.vl.addLayout(self.hl)
        self.setLayout(self.vl)

        self.changeEstaca(0)


    def colorChanged(self):
       color = QtWidgets.QColorDialog.getColor()
       if color.isValid():
           self.w.setBackgroundColor(color)
           self.w.update()

    def meshColorChanged(self):
        color = QtWidgets.QColorDialog.getColor()
        colorC=[color.redF(), color.greenF(), color.blueF(), color.alphaF()]
        if color.isValid():
            mesh = self.meshList[-1]
            colors=np.array([colorC for c in mesh.opts['faceColors']])
            msgLog('Debug: Color lengh is '+str(len(colors)))
            mesh.setMeshData(vertexes=self.vertices, faces=self.faces, faceColors=colors, smooth=False, drawEdges=mesh.opts['drawEdges'], edgeColor=(0, 0, 0, 1), shader=mesh.opts['shader'])
#            mesh.parseMeshData()
 #           mesh.paint()
            self.w.update()

    def wireframeToggle(self, state):
        mesh=self.meshList[-1]
        mesh.opts["drawEdges"]=True if state else False
        mesh.parseMeshData()
        mesh.paint()
        self.w.update()
        #mesh.meshDataChanged()

    def changeShader(self, shader):
        for mesh in self.meshList:
            mesh.setShader(shader)

    def changeEstaca(self, index):
        intersect = self.intersect
        self.w.setWindowTitle("Estaca "+str(intersect[index][0]))
        campos=self.w.cameraPosition()
        self.w.pan(float(intersect[index][4])-campos.x(), float(intersect[index][3])-campos.y(),
                   float(intersect[index][5])-campos.z()+40)
      #  az = float(intersect[index][7])
       # self.w.orbit(az, 20)

    def addMesh(self, verts, faces, colors=[]):
        m1 = gl.GLMeshItem(vertexes=verts, faces=faces, faceColors=colors, smooth=False, drawEdges=True, edgeColor=(0, 0, 0, 1), shader='shaded')
        #m1.translate(5, 5, 0)
        m1.setGLOptions('translucent')
        m1.setDepthValue(0)
        self.w.addItem(m1)
        self.meshList.append(m1)



## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    app = QtGui.QApplication([])
    w=view3D_Ui()
    w.show()

    ## Example 1:
    ## Array of vertex positions and array of vertex indexes defining faces
    ## Colors are specified per-face

    verts = np.array([
        [0, 0, 0],
        [2, 0, 0],
        [1, 2, 0],
        [1, 1, 1],
    ])
    faces = np.array([
        [0, 1, 2],
        [0, 1, 3],
        [0, 2, 3],
        [1, 2, 3]
    ])
    colors = np.array([
        [1, 0, 0, 0.3],
        [0, 1, 0, 0.3],
        [0, 0, 1, 0.3],
        [1, 1, 0, 0.3]
    ])
    w.addMesh(verts, faces, colors)
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
