# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setEscala.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(328, 181)
        Dialog.setMaximumSize(QtCore.QSize(480, 300))
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.x = QtWidgets.QDoubleSpinBox(Dialog)
        self.x.setMinimum(0.01)
        self.x.setMaximum(9999.99)
        self.x.setSingleStep(0.1)
        self.x.setProperty("value", 1.0)
        self.x.setObjectName("x")
        self.verticalLayout.addWidget(self.x)
        self.horizontalLayout.addLayout(self.verticalLayout)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.y = QtWidgets.QDoubleSpinBox(Dialog)
        self.y.setMinimum(0.01)
        self.y.setMaximum(9999.99)
        self.y.setSingleStep(0.1)
        self.y.setProperty("value", 1.0)
        self.y.setObjectName("y")
        self.verticalLayout_2.addWidget(self.y)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.zoomBtn = QtWidgets.QPushButton(Dialog)
        self.zoomBtn.setObjectName("zoomBtn")
        self.verticalLayout_3.addWidget(self.zoomBtn)
        self.gridLayout.addLayout(self.verticalLayout_3, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Escala"))
        self.label.setText(_translate("Dialog", "Eixo X"))
        self.label_2.setText(_translate("Dialog", "Eixo Y"))
        self.zoomBtn.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Enquadra o desenho em toda área disponível</p></body></html>"))
        self.zoomBtn.setText(_translate("Dialog", "Restaurar Zoom"))


