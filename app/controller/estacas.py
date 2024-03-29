from __future__ import print_function

# -*- coding: utf-8 -*-
import webbrowser
from copy import deepcopy

from PyQt5.QtCore import QFile, QVariant
from PyQt5.QtWidgets import QTableWidgetSelectionRange
from qgis.core import QgsDxfExport

from ..controller.Geometria.Prismoide import QPrismoid
from ..controller.perfil import Ui_Bruckner, Ui_Perfil, Ui_sessaoTipo
from ..controller.perfil import cv as CV
from ..controller.threading import nongui
from ..model.curvas import Curvas
from ..model.estacas import Estacas as EstacasModel
from ..model.knn import KNN
from ..model.utils import *
from ..view.curvas import Curvas as CurvasView
from ..view.curvas import refreshCanvas
from ..view.estacas import CorteExport, EstacaRangeSelect
from ..view.estacas import Estacas as EstacasView
from ..view.estacas import EstacasCv, EstacasUI, ProgressDialog
from ..view.glmesh import view3D_Ui

DEBUG = True

try:
    import dxfgrabber
except:
    pass


DIALOGS_TO_CLOSE_ON_LOOP = ["curvaView"]


class Estacas(object):
    def __init__(self, iface):

        self.iface = iface

        self.estacasVerticalList = []
        self.estacasHorizontalList = []

        self.model = EstacasModel()
        self.model.iface = iface
        self.preview = EstacasUI(iface)
        self.view = EstacasView(iface, self)
        self.viewCv = EstacasCv(iface, self)
        self.progressDialog = ProgressDialog(iface)

        self.events()
        self.elemento = -1
        self.click = False
        self.edit = False
        self.points = []

        self.nextView = self.view
        msgLog("RELOADED")

    def mudancaCelula(self, item):
        if item.column() > 1:
            campo = float(
                self.view.tableWidget.item(item.row(), item.column())
                .text()
                .replace(",", ".")
            )
            self.view.tableWidget.setItem(
                item.row(), item.column(), QtWidgets.QTableWidgetItem("%s" % campo)
            )

    def linkGoogle(self, item):
        if item.column() == 0:
            este = float(self.view.tableWidget.item(item.row(), 4).text())
            north = float(self.view.tableWidget.item(item.row(), 3).text())
            crs = int(self.model.getCRS())
            point = QgsPointXY(este, north)
            epsg4326 = QgsCoordinateReferenceSystem(
                4326, QgsCoordinateReferenceSystem.EpsgCrsId
            )
            mycrs = QgsCoordinateReferenceSystem(int(crs), 0)
            reprojectgeographic = QgsCoordinateTransform(
                mycrs, epsg4326, QgsProject.instance()
            )
            pt = reprojectgeographic.transform(point)

            webbrowser.open(
                "https://www.google.com.br/maps/@%f,%f,15z?hl=pt-BR" % (pt.y(), pt.x())
            )

    def events(self):
        self.preview.tableEstacas: QtWidgets.QTableWidget
        self.preview.btnNovo.clicked.connect(self.new)
        self.preview.btnOpen.clicked.connect(lambda: self.openEstaca(True))
        self.preview.tableEstacas.doubleClicked.connect(lambda: self.openEstaca(True))
        self.preview.btnOpenCSV.clicked.connect(self.openEstacaCSV)
        self.preview.btnApagar.clicked.connect(self.deleteEstaca)
        self.preview.btnGerarTracado.clicked.connect(self.geraTracado)
        self.preview.tableEstacas.itemClicked.connect(self.itemClickTableEstacas)
        self.preview.tableEstacas.itemActivated.connect(self.itemClickTableEstacas)
        self.preview.tableEstacas.itemSelectionChanged.connect(
            self.itemClickTableEstacas
        )
        self.preview.btnOpenCv.clicked.connect(self.openCv)
        self.preview.deleted.connect(self.deleteEstaca)
        self.preview.btnDuplicar.clicked.connect(lambda: self.duplicarEstaca(True))
        self.preview.btnGerarCurvas.clicked.connect(self.geraCurvas)

        """
            ------------------------------------------------
        """

        self.view.btns = [
            self.view.btnSave,
            self.view.btnSaveCSV,
            self.view.btnLayer,
            self.view.btnEstacas,
            self.view.btnPerfil,
            self.view.btnCurva,
            self.view.btnCotaTIFF,
            self.view.btnCotaPC,
            self.view.btnCota,
        ]

        for btn in self.view.btns:
            btn.clicked.connect(self.view.clearLayers)

        self.view.btnSave.clicked.connect(self.saveEstacas)
        self.view.btnSaveCSV.clicked.connect(self.saveEstacasCSV)
        self.view.btnLayer.clicked.connect(self.plotar)
        self.view.btnEstacas.clicked.connect(self.recalcular)
        self.view.btnCurva.clicked.connect(self.curva)
        self.view.btnCotaTIFF.clicked.connect(self.obterCotasTIFF)
        self.view.btnCotaPC.clicked.connect(self.obterCotasPC)
        self.view.btnCota.clicked.connect(self.obterCotas)
        self.view.btnCota.hide()  # TODO Add google Elevation API ?
        self.view.tableWidget.itemDoubleClicked.connect(self.linkGoogle)
        self.view.tableWidget.itemDoubleClicked.connect(self.mudancaCelula)
        self.view.btnDuplicar.clicked.connect(self.duplicarEstacaHorizontal)
        #        self.view.layerUpdated.connect(self.joinFeatures)
        self.view.btnPerfil.clicked.connect(self.perfilView)

        """
            ------------------------------------------------
        """

        self.viewCv.btnGen.clicked.connect(self.generateIntersec)
        self.viewCv.btnTrans.clicked.connect(self.generateTrans)
        self.viewCv.btnBruck.clicked.connect(self.bruckner)
        self.viewCv.btnCrossSectionExport.clicked.connect(self.exportCS)
        self.viewCv.btnCsv.clicked.connect(self.exportCSV)
        # self.viewCv.btnClean.clicked.connect(self.cleanTrans)
        self.viewCv.btnRecalcular.clicked.connect(self.recalcularVerticais)
        self.viewCv.btn3D.clicked.connect(lambda: self.export3D())
        self.viewCv.btnCorte.clicked.connect(lambda: self.exportCorte())
        self.viewCv.btn3DView.clicked.connect(lambda: self.view3DView())

    def view3DView(self):
        msgLog("Iniciando visão 3D")
        intersect, vertices, faces = self.export3D(pointsOnly=True)
        msgLog("Pontos da malha carregados")
        view3d = view3D_Ui(intersect, vertices, faces)
        view3d.showMaximized()
        view3d.exec_()

    def createMesh(self, tipo="H"):
        import tempfile
        from pathlib import Path

        if hasattr(self, "ctExpDiag"):
            tipo = self.ctExpDiag.getType()
        file = str(Path(tempfile.gettempdir()) / "GeoRoadTempMesh.stl")
        table = self.export3D(filename=file, tipo=tipo)
        self.tableCorte = table
        self.fileCorte = file
        return table, file

    def exportCorte(self):
        if self.viewCv.mode == "CV":
            self.exportDXF()
        else:
            table, file = self.createMesh()
            if not table:
                return
            self.generateCorte()
            self.ctExpDiag = diag = CorteExport(None, float(table[-1][2]))
            diag.btnPreview.clicked.connect(lambda: self.corteExport(True))
            diag.btnSave.clicked.connect(lambda: self.corteExport(False))
            diag.comboBox.currentIndexChanged.connect(lambda: self.createMesh())
            diag.label_4.hide()
            diag.inicialSb.hide()
            diag.finalSb.hide()
            diag.label_3.hide()
            diag.buttonBox.hide()
            diag.line.hide()
            diag.comboBox.hide()
            diag.label_8.hide()
            diag.btnSave.clicked.connect(diag.accept)
            diag.exec_()

    def corteExport(self, preview=False):
        self.generateCorte()
        if not hasattr(self.combined, "show"):
            messageDialog(
                message="Seção vazia! Nada foi encontrado, tente aumentar a profundidade!"
            )
        else:
            if preview:
                self.combined.show()
            else:
                self.saveDxfCorte()

    def generateCorte(self, step=1, depth=20, tipo="H"):
        import numpy as np

        file = self.fileCorte
        if hasattr(self, "ctExpDiag"):
            tipo = self.ctExpDiag.getType()
            step = self.ctExpDiag.intSp.value()
            depth = self.ctExpDiag.espSb.value()
            e1 = self.ctExpDiag.inicialSb.value()
            e2 = self.ctExpDiag.finalSb.value()
            offset = self.ctExpDiag.offsetSb.value()
        else:
            e2 = float(self.tableCorte[-1][2])
            e1 = 0
            offset = 0

        if tipo == "T":
            plane_normal = [1, 0, 0]
            self.progressDialog.show()
            self.progressDialog.setLoop(100, (e1 - e2) / Config.instance().DIST, 0)
            for e in self.tableCorte:
                if estaca2progFloat(e[0]) > e2:
                    break
                if estaca2progFloat(e[0]) >= e1:
                    self.progressDialog.increment()
                    offset = estaca2progFloat(e[0]) - e1
                    sections = self.sliceCorte(
                        file, tipo, step, depth, plane_normal, offset
                    )
            self.progressDialog.close()
        elif tipo == "H":
            plane_normal = [0, 0, 1]
            sections = self.sliceCorte(
                file,
                tipo,
                step,
                depth,
                plane_normal,
                offset,
                float(self.tableCorte[0][5]),
            )
        else:  # V
            plane_normal = [0, 1, 0]
            sections = self.sliceCorte(file, tipo, step, depth, plane_normal, offset)
        self.combined = np.sum(sections)

        if hasattr(self, "ctExpDiag") and self.ctExpDiag.isEstaca():  # printar estacas
            from ... import trimesh

            textHeight = 5
            if tipo == "T":
                self.progressDialog.show()
                self.progressDialog.setLoop(100, (e1 - e2) / Config.instance().DIST)
                for e in self.tableCorte:
                    if estaca2progFloat(e[1]) > e2:
                        break
                    if estaca2progFloat(e[1]) >= e1:
                        self.progressDialog.increment()
                        text = trimesh.path.entities.Text(
                            origin=len(self.combined.vertices),
                            text=str(e[0]) + "  " + str(e[1]),
                            height=textHeight,
                        )
                        self.combined.vertices = np.vstack(
                            (self.combined.vertices, self.combined.bounds.mean(axis=0))
                        )
                        self.combined.entities = np.append(self.combined.entities, text)

                self.progressDialog.close()

            elif tipo == "H":
                for e in self.tableCorte:
                    azi = np.deg2rad(float(e[7]) + 90)
                    l = 50
                    text = trimesh.path.entities.Text(
                        origin=len(self.combined.vertices),
                        text=str(e[0]) + "  " + str(e[1]),
                        height=textHeight,
                    )
                    self.combined.vertices = np.vstack(
                        (self.combined.vertices, np.array([float(e[4]), float(e[3])]))
                    )
                    self.combined.entities = np.append(self.combined.entities, text)
                    line = trimesh.path.entities.Line(
                        np.array(
                            [
                                len(self.combined.vertices),
                                len(self.combined.vertices) + 1,
                            ]
                        )
                    )
                    self.combined.vertices = np.vstack(
                        (
                            self.combined.vertices,
                            np.array(
                                [
                                    float(e[4]) + l * np.sin(azi),
                                    float(e[3]) + l * np.cos(azi),
                                ]
                            ),
                        )
                    )
                    self.combined.vertices = np.vstack(
                        (
                            self.combined.vertices,
                            np.array(
                                [
                                    float(e[4]) - l * np.sin(azi),
                                    float(e[3]) - l * np.cos(azi),
                                ]
                            ),
                        )
                    )
                    self.combined.entities = np.append(self.combined.entities, line)
            else:  # V
                for e in self.tableCorte:
                    text = trimesh.path.entities.Text(
                        origin=len(self.combined.vertices),
                        text=str(e[0]) + "  " + str(e[1]),
                        height=textHeight,
                    )
                    self.combined.vertices = np.vstack(
                        (self.combined.vertices, np.array([float(e[2]), float(e[5])]))
                    )
                    self.combined.entities = np.append(self.combined.entities, text)
                    line = trimesh.path.entities.Line(
                        np.array(
                            [
                                len(self.combined.vertices),
                                len(self.combined.vertices) + 1,
                            ]
                        )
                    )
                    self.combined.vertices = np.vstack(
                        (
                            self.combined.vertices,
                            np.array([float(e[2]), float(e[5]) - 5]),
                        )
                    )
                    self.combined.vertices = np.vstack(
                        (
                            self.combined.vertices,
                            np.array([float(e[2]), float(e[5]) + 5]),
                        )
                    )
                    self.combined.entities = np.append(self.combined.entities, line)

            msgLog(
                "Foram adicionados "
                + str(len(self.combined.entities))
                + " elementos para o tipo "
                + tipo
            )

    def sliceCorte(self, file, tipo, step, depth, plane_normal, offset=0, cota=0.0):
        import numpy as np

        from ... import trimesh

        mesh = trimesh.load_mesh(file)
        if tipo == "T":
            n = 0
            plane_origin = [0, 0, mesh.bounds[0][2]]
        elif tipo == "V":
            n = 1
            plane_origin = [0, 0, -2 * mesh.bounds[0][1]]
        else:
            n = 2
            plane_origin = [0, 0, mesh.bounds[0][2]]
        z_extents = mesh.bounds[:, n]
        depth = min(z_extents[1] - z_extents[0], depth)
        # z_levels = np.arange(*z_extents, step=step)[int(offset/step):int(depth/step)]
        # [int(offset/step):]#int(depth/step)]
        z_levels = np.linspace(offset, depth, num=int(depth / step))
        sections = mesh.section_multiplane(
            plane_origin=plane_origin, plane_normal=plane_normal, heights=z_levels
        )
        # sections=[s for s in sections if not s is None]
        labeled_sections = []
        textHeight = 2
        for s in sections:
            if s is None:
                cota += step
                continue
            for vi, v in enumerate(s.vertices):
                if vi % 30 == 0:
                    text = trimesh.path.entities.Text(
                        origin=vi, text=cota, height=textHeight
                    )
                    s.entities = np.append(s.entities, text)
            labeled_sections.append(s)
            cota += step

        return labeled_sections

    def saveDxfCorte(self):
        filter = ".dxf"
        filename = QtWidgets.QFileDialog.getSaveFileName(
            filter="Arquivo dxf(*" + filter + " *" + filter.upper() + ")"
        )[0]
        if filename in ["", None]:
            return
        filename = (
            str(filename) if str(filename).endswith(filter) else str(filename) + filter
        )
        self.combined.export(filename)

    def export3D(
        self, filename=None, terrain=True, tipo="3D", pointsOnly=False
    ):  # H, V, T
        self.progressDialog.show()
        self.progressDialog.setValue(0)

        Z = 0 if tipo in "HT" else None
        reto = True if tipo in "VT" else None

        filter = ".stl"
        X, table, prismoide = self.model.getTrans(self.model.id_filename)
        self.progressDialog.setValue(5)
        intersect = self.model.load_intersect()
        self.progressDialog.setValue(10)
        prismoide: QPrismoid
        if not X or not prismoide:
            messageDialog(message="Seção Transversal não definida!")
            self.progressDialog.close()
            return

        import numpy as np
        from scipy import spatial

        from ...stl import mesh

        self.progressDialog.setValue(25)

        # Define the terrain vertices
        verticesg = []
        vertices = []
        errors = []

        for i, est in enumerate(X):
            self.progressDialog.setValue(25 + 70 * i / len(X))
            norte = float(intersect[i][3])
            este = float(intersect[i][4])
            greide = float(intersect[i][5])
            az = float(intersect[i][7])
            st = prismoide.faces[i].superior
            stpts = st.getPoints()
            points = []
            try:
                if terrain:
                    for pt in table[1][i]:
                        if pt[0] > stpts[0][0]:
                            break
                        else:
                            points.append(pt)

                points += [[pt.x(), pt.y()] for pt in stpts]

                if terrain:
                    for pt in table[1][i]:
                        if pt[0] > stpts[-1][0]:
                            points.append(pt)

            except Exception as e:
                import traceback

                msgLog(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
                errors.append(est)
                continue

            perp = az + 90
            if perp > 360:
                perp = perp - 360
            nsign = 1
            esign = 1
            if perp < 90:
                nsign = 1
                esign = 1
            elif perp < 180:
                nsign = -1
                esign = 1
            elif perp < 270:
                nsign = -1
                esign = -1
            elif perp < 360:
                nsign = 1
                esign = -1

            for j, pt in enumerate(points):
                x, y, z = est, pt[0], pt[1]
                z = z if Z is None else z - greide + Z
                if reto is None:
                    yangleE = esign * y * abs(math.sin(perp * math.pi / 180))
                    yangleN = nsign * y * abs(math.cos(perp * math.pi / 180))
                    xPoint = float(este + yangleE)
                    yPoint = float(norte + yangleN)
                    verticesg.append([xPoint, yPoint, z])
                else:
                    verticesg.append([x, y, z])
                vertices.append([x, y, z])

        if errors:
            messageDialog(
                title="Erro",
                message="Erro nas estacas: "
                + ";  ".join([prog2estacaStr(p) for p in errors]),
            )

        verticesg = np.array(verticesg)
        vertices = np.array(vertices)
        tri = spatial.Delaunay(vertices[:, :2])
        facesg = tri.simplices

        if pointsOnly:
            self.progressDialog.close()
            return intersect, verticesg, facesg

        # Create the meshes
        greide = mesh.Mesh(np.zeros(facesg.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(facesg):
            for j in range(3):
                greide.vectors[i][j] = verticesg[f[j], :]
        self.progressDialog.setValue(98)

        # combined = mesh.Mesh(np.concatenate([terrain.data, greide.data]))
        combined = greide
        self.progressDialog.close()

        if filename is None:
            filename = QtWidgets.QFileDialog.getSaveFileName(
                filter="Arquivo stl(*" + filter + " *" + filter.upper() + ")"
            )[0]
        if filename in ["", None]:
            return
        filename = (
            str(filename) if str(filename).endswith(filter) else str(filename) + filter
        )
        combined.save(filename)

        if tipo == "3D":
            import shutil

            # maybe this works on windows someday?
            exe = shutil.which("blender")

            from pathlib import Path

            p = Path(r"C:\Program Files\Blender Foundation\\").rglob(
                "*/*.exe"
            )  # blender's default path on windows
            for file in p:
                if file.name == "blender.exe":
                    exe = str(file)
            if exe:

                def resolve(name, basepath=None):
                    if not basepath:
                        basepath = str(Path(__file__).parents[2])
                    return os.path.join(basepath, name)

                if yesNoDialog(
                    message="O blender foi detectado no sistem. Deseja abrir o modelo?"
                ):
                    # move template blend to tmp
                    from tempfile import gettempdir

                    blend = str(Path(gettempdir()) / "georoadBlender.blend")
                    shutil.copy(resolve("layout.blend"), blend)

                    # start=?, create dxf starting from 0,0,10
                    import json

                    table = intersect
                    jsonfile = str(Path(gettempdir()) / "georoadBlender.json")
                    init = table[0]
                    data = {}  # x,y,z --> 0,0,0
                    init = data["start"] = [
                        float(init[4]),
                        float(init[3]),
                        float(init[5]),
                    ]
                    data["points"] = [
                        [
                            float(e[4]) - init[0],
                            float(e[3]) - init[1],
                            float(e[5]) - init[2],
                        ]
                        for e in table
                    ]
                    data["estacas"] = [e[0] for e in table]
                    data["azi"] = [e[7] for e in table]
                    data["frames"] = float(table[-1][2]) / 200 * 24
                    with open(jsonfile, "w") as outfile:
                        json.dump(data, outfile)

                    # launch exe -P with the script and arguments
                    import subprocess

                    script = resolve("blender.py")
                    cmd = [exe, blend, "--python", script, "--", filename]
                    msgLog("Running Command:  " + " ".join(cmd))
                    subprocess.Popen(cmd)
                else:
                    # self.showModelo3D(filename)
                    pass
            else:
                msgLog("Blender não foi encontrado!")
            # self.showModelo3D(filename)
        else:
            return intersect

    def showModelo3D(self, filename):
        if yesNoDialog(message="Deseja visualizar o modelo gerado?"):
            try:
                import trimesh

                mesh = trimesh.load(filename)
                mesh.show()
            except Exception as e:
                import traceback

                msgLog(
                    "Erro: "
                    + str(traceback.format_exception(None, e, e.__traceback__))[1:-1]
                )

    def exportTrans(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save dxf", filter="Arquivo DXF (*.dxf)"
        )
        if filename in ["", None]:
            return
        if not filename.endswith(".dxf"):
            filename += ".dxf"
        v = self.trans.verticais.getY(self.trans.progressiva[self.trans.current])
        self.saveDXF(
            filename[0],
            [
                [
                    p2QgsPoint(float(x), float(y) - float(v))
                    for x, y in self.trans.st[self.trans.current]
                ]
            ],
        )

    def importTrans(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(
            caption="Open dxf", filter="Arquivo DXF (*.dxf)"
        )
        if filename[0] in ["", None]:
            return
        uri = filename[0] + "|layername=entities|geometrytype=Line"
        vlayer = QgsVectorLayer(uri, "Seção tipo", "ogr")
        features = [f for f in vlayer.getFeatures()]
        v = self.trans.verticais.getY(self.trans.progressiva[self.trans.current])
        pl = featureToPolyline(features[0])
        from collections import OrderedDict

        pl = list(OrderedDict.fromkeys(pl))
        msgLog("Seção :" + str([[p.x(), p.y()] for p in pl]))
        self.trans.st[self.trans.current] = [[pt.x(), pt.y() + v] for pt in pl]
        self.trans.prismoide.st = self.trans.st
        try:
            self.trans.prismoide.generate(self.trans.current)
        except:
            msgLog("Falha ao achar interseção com o terreno!")
        self.trans.reset()

    def bruckner(self):
        self.progressDialog.show()
        self.progressDialog.setValue(0)
        table = self.model.load_bruckner()
        bruck = self.model.load_bruck()
        # if non existent, compute
        if not table or not ("table" in bruck and bruck["table"]):
            X, est, prismoide = self.loadTrans()
            msgLog(str(len(X)) + " Estacas na transversal")
            if not X:
                messageDialog(message="Seção Transversal não definida!")
                self.progressDialog.close()
                return
            fh, ok = QtWidgets.QInputDialog.getDouble(
                None,
                "Fator de Homogeneização",
                "Defina o Fh:",
                value=1.05,
                min=0,
                max=10,
                decimals=4,
            )
            if not ok:
                return
            self.progressDialog.setValue(10)
            X, V = self.brucknerThread(X, est, prismoide, 0, len(X), fh)
        else:
            X, V = zip(*table)
            X = [float(x) for x in X]
            V = [float(v) for v in V]
        self.progressDialog.setValue(90)
        Xests = X
        Vests = V
        dialog = EstacaRangeSelect(None, Xests, bruck=bruck)
        self.progressDialog.close()
        while dialog.exec_():
            self.bruck = dialog.bruck
            ei = dialog.inicial.currentIndex()
            ef = dialog.final_2.currentIndex()
            key = (
                str(dialog.inicial.itemText(ei))
                + "-"
                + str(dialog.final_2.itemText(ef))
            )
            X = Xests[ei : ef + 1]
            V = Vests[ei : ef + 1]
            dist = Config.instance().DIST
            X = [x * dist for x in X]

            if key in self.bruck:
                bruckD = Ui_Bruckner(
                    X,
                    V,
                    key=key,
                    bruck=self.bruck,
                    bruckData=self.bruck[key],
                    interval=[ei, ef],
                )
            else:
                size = min(len(X), len(V))
                bruckD = Ui_Bruckner(
                    X[:size], V[:size], key=key, bruck=self.bruck, interval=[ei, ef]
                )

            msgLog("Abrindo intervalo: " + key)
            bruckD.showMaximized()
            # bruckD.save.connect(lambda: self.bruckner2DXF(bruckD.X, bruckD.V))
            bruckD.reset.connect(self.brucknerReset)
            self.brucknerView = bruckD
            bruckD.exec_()
            bruckD.setBruckData()
            if hasattr(self, "bruckReseted") and self.bruckReseted:  # loop do reset
                self.bruckReseted = False
            elif (hasattr(self, "bruckReseted") and not self.bruckReseted) or (
                hasattr(bruckD, "reseted") and bruckD.reseted
            ):  # primeiro loop
                self.bruckReseted = False
                del self.bruckReseted
                return
            self.bruck[key] = bruckD.bruckData
            self.model.save_bruck(self.bruck)
            dialog = EstacaRangeSelect(None, Xests, bruck=self.bruck)

        self.model.save_bruck(dialog.bruck)
        msgLog("Edição bruckner finalizada")

    def brucknerReset(self):
        self.brucknerView.close()
        self.bruckReseted = True
        self.model.cleanBruckner(
            keepLines=yesNoDialog(message="Deseja manter as linhas de terra?")
        )
        self.bruck = self.model.load_bruck()
        self.bruckner()

    def matplot(
        self, X, V, title="Diagrama de Bruckner", xlabel="Estacas", ylabel="Volume m³"
    ):
        import matplotlib.pyplot as plt

        (line,) = plt.plot(X, V, lw=2)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.show()

    @nongui
    def brucknerThread(self, X, est, prismoide, ei, ef, fh):
        self.progressDialog.setText("Calculando Volumes acumulados")
        msgLog("Calculando tabela de volumes acumulados")
        X = [float(x) for x in X]
        x1 = X[ei]
        X = X[ei : ef + 1]
        V = []
        vAcumulado = 0
        face = prismoide.faces[ei]
        ct, at = face.getAreas()
        self.progressDialog.setLoop(30, len(X))
        bruck = [
            {
                "estaca": prog2estacaStr(x1),
                "corte": abs(ct),
                "aterro": abs(at),
                "at.cor.": abs(at * fh),
                "soma": "",
                "semi-distancia": "",
                "vol.corte": "",
                "vol.aterro": "",
                "volume": "",
                "vol.acum": "",
            }
        ]
        for x in range(1, len(X)):
            data = prismoide.getBruckVols(ei + x - 1, ei + x, fh=fh)[0]
            data["estaca"] = prog2estacaStr(X[x])
            if data["volume"] == 0 and data["semi-distancia"] == 0:
                msgLog("Erro na estaca " + data["estaca"])
            vAcumulado += data["volume"]
            data["vol.acum"] = vAcumulado
            V.append(vAcumulado)
            bruck.append(data)
            self.progressDialog.increment()
        self.model.save_bruck({"table": bruck})
        V = [v + abs(min(V)) + 1000 for v in V]
        X = [x / Config.instance().DIST for x in X]
        self.progressDialog.setValue(80)
        self.model.saveBruckner(list(zip(X, V)))
        return X, V

    def bruckner2DXF(self, X, Y):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save dxf", filter="Arquivo DXF (*.dxf)"
        )
        if filename in ["", None]:
            return
        if not filename.endswith(".dxf"):
            filename += ".dxf"
        dist = Config.instance().DIST
        self.saveDXF(
            filename, [[p2QgsPoint(x * dist, y / 1000000) for x, y in (zip(X, Y))]]
        )

    def exportDXF(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save dxf", filter="Arquivo DXF (*.dxf)"
        )
        if filename in ["", None]:
            return
        if not filename.endswith(".dxf"):
            filename += ".dxf"
        estacas = self.viewCv.get_estacas()
        terreno = self.model.load_terreno_long()
        Lpoints = []
        if self.viewCv.mode == "CV":
            points = []
            for e in estacas:
                points.append(p2QgsPoint(float(e[-2]), float(e[-1])))
            Lpoints.append(points)
            prog = float(e[-2])
            points = [p2QgsPoint(float(e[-2]) - prog, float(e[-1])) for e in terreno]
            Lpoints.append(points)
        elif self.viewCv.mode == "T":
            points = []
            for e in estacas:
                points.append(p2QgsPoint([float(e[4]), float(e[3]), float(e[-3])]))
            Lpoints.append(points)

        self.saveDXF(filename, Lpoints)

        if self.viewCv.mode == "CV":
            self.addVerticalEstacas(filename, estacas)

    def exportCS(self):
        #        if yesNoDialog(title="Plotar Transversais?", message="Deseja exportar os perfis transversais? (Se ainda não foram definidos não serão salvos)"):
        self.progressDialog.show()

        X, table, prismoide = self.loadTrans()

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            caption="Save dxf", filter="Arquivo DXF (*.dxf)"
        )
        if filename in ["", None]:
            return
        if not filename.endswith(".dxf"):
            filename += ".dxf"
        LPoints = []
        for i, face in enumerate(prismoide.getFaces()):
            st = face.superior
            stpts = st.getPoints()
            points = []
            for pt in table[1][i]:
                if pt[0] > stpts[0][0]:
                    break
                else:
                    points.append(p2QgsPoint([float(pt[0]), float(pt[1])]))
            points += [p2QgsPoint([pt.x(), pt.y()]) for pt in stpts]
            for pt in table[1][i]:
                if pt[0] > stpts[-1][0]:
                    points.append(p2QgsPoint([float(pt[0]), float(pt[1])]))
            #                for line in face.superior.lines:
            #                    points.append(p2QgsPoint(line.point1.x(), line.point1.y()))
            #                for line in face.inferior.lines:
            #                    points.append(p2QgsPoint(line.point1.x(), line.point1.y()))
            LPoints.append(points)

        self.addTransEstacas(
            filename, self.model.load_intersect(), self.saveDXF(filename, LPoints)
        )
        self.progressDialog.close()

    def addVerticalEstacas(self, filename, estacas):
        import numpy as np

        from ... import trimesh

        combined = trimesh.load(filename)
        textHeight = 5
        l = 20
        for e in estacas:
            p = np.array([float(e[-2]), float(e[-1])])
            text = trimesh.path.entities.Text(
                origin=len(combined.vertices),
                text=str(e[0]) + "  " + str(e[1]),
                height=textHeight,
            )
            combined.vertices = np.vstack((combined.vertices, p))
            combined.entities = np.append(combined.entities, text)
            line = trimesh.path.entities.Line(
                np.array([len(combined.vertices), len(combined.vertices) + 1])
            )
            combined.vertices = np.vstack(
                (combined.vertices, np.array([p[0], p[1] + l]))
            )
            combined.vertices = np.vstack(
                (combined.vertices, np.array([p[0], p[1] - l]))
            )
            combined.entities = np.append(combined.entities, line)

        combined.export(filename)

    def addTransEstacas(self, filename, estacas, coords):
        import numpy as np

        from ... import trimesh

        combined = trimesh.load(filename)
        textHeight = 5
        for e, c in zip(estacas, coords):
            text = trimesh.path.entities.Text(
                origin=len(combined.vertices),
                text=str(e[0]) + "  " + str(e[1]),
                height=textHeight,
            )
            combined.vertices = np.vstack((combined.vertices, c))
            combined.entities = np.append(combined.entities, text)
        combined.export(filename)

    # [ [ p2QgsPoint[ x,y], [x,y] ...] , [ [ x,y] , [x,y] ...] ....] Each list is a feature
    def saveDXF(self, filename, listOfListOfPoints):
        import numpy as np

        coords = []
        layer = QgsVectorLayer(
            "LineStringZ?crs=%s" % (QgsProject.instance().crs().authid()),
            "Perfil: "
            if self.viewCv.mode == "CV"
            else "Traçado Horizontal: "
            + self.model.getNameFromId(self.model.id_filename),
            "memory",
        )
        layer.setCrs(QgsCoordinateReferenceSystem(QgsProject.instance().crs()))
        DX = 0
        DY = 0
        MAX_COLUMNS = 10
        ncolumns = 1
        for points in listOfListOfPoints:
            feat = QgsFeature()
            g = QgsGeometry.fromPolyline(points)
            g.translate(DX, DY)
            feat.setGeometry(g)
            # features.append(QgsFeature(feat))
            layer.dataProvider().addFeatures([feat])
            layer.updateExtents()

            # TODO this rectangle is not really being added around
            feat = QgsFeature()
            rect = g.boundingBox()
            feat.setGeometry(QgsGeometry.fromRect(rect))

            layer.dataProvider().addFeatures([feat])
            layer.updateExtents()

            # features.append(QgsFeature(feat))
            coords.append(
                np.array([np.average(rect.center().x()), rect.center().y() + 5])
            )

            if ncolumns < MAX_COLUMNS:
                DX += abs(rect.xMaximum() - rect.xMinimum())
                ncolumns += 1
            else:
                ncolumns = 0
                DY -= DX / MAX_COLUMNS
                DX = 0

        # QgsProject.instance().addMapLayer(layer)

        dxfExport = QgsDxfExport()
        dxfExport.setMapSettings(self.iface.mapCanvas().mapSettings())
        dxfExport.addLayers([QgsDxfExport.DxfLayer(layer)])
        dxfExport.setSymbologyScale(1)
        dxfExport.setSymbologyExport(QgsDxfExport.SymbolLayerSymbology)
        dxfExport.setLayerTitleAsName(True)
        dxfExport.setDestinationCrs(layer.crs())
        dxfExport.setForce2d(False)
        dxfExport.setExtent(layer.dataProvider().extent())

        error = dxfExport.writeToFile(QFile(filename), "UTF-8")
        if error != QgsDxfExport.ExportResult.Success:
            msgLog(str(error))
            messageDialog(
                title="Erro!",
                message="Não foi possível realizar a conversão para DXF ou salvar o arquivo!",
            )

        return coords

    def exportCSV(self):
        filename = self.view.saveEstacasCSV()
        if filename[0] in ["", None]:
            return
        estacas = self.viewCv.get_estacas()
        self.model.table = estacas
        header = [
            self.viewCv.tableWidget.horizontalHeaderItem(i).text()
            for i in range(self.viewCv.tableWidget.columnCount())
        ]
        if self.viewCv.mode == "CV":
            self.model.saveCSV(filename, noWGS=True, header=header)
        else:
            self.model.saveCSV(filename, header=header)

    @nongui
    def loadTrans(self):
        self.progressDialog.setValue(0)
        self.progressDialog.setText("Carregando Transversais")
        X, est, prism = self.model.getTrans(self.model.id_filename)
        self.progressDialog.setValue(50)
        if X:
            # Database Trans
            self.trans = Ui_sessaoTipo(
                self.iface,
                est[1],
                self.model.load_intersect(),
                X,
                est[0],
                prism=prism,
                greide=self.model.getGreide(self.model.id_filename),
                title="Transversal: "
                + str(self.model.getNameFromId(self.model.id_filename)),
            )
        else:
            self.progressDialog.close()
            msgLog("Não há seção transversal!")
            return False, False, False
        self.progressDialog.setValue(100)
        prismoide: QPrismoid
        prismoide = self.trans.prismoide
        return X, est, prismoide

    def geraCurvas(self, arquivo_id=None, recalcular=False):
        table = self.preview.tableEstacas
        table: QtWidgets.QTableWidget
        #
        if recalcular:
            self.saveEstacasLayer(
                self.view.get_estacas(), name=self.model.getNameFromId(arquivo_id)
            )
            return
        if not arquivo_id:
            l = len(table.selectionModel().selectedRows())
        else:  # curva para traçado
            self.newEstacasLayer(name=self.model.getNameFromId(arquivo_id))
            self.view.openLayers()
            return

        if l > 1:
            self.preview.error("Selecione um único arquivo!")
        elif l < 1:  # criar traçado, iniciar edição
            name = self.fileName("Traçado " + str(len(self.model.listTables()) + 1))
            if not name:
                return
            self.new(
                dados=(
                    name,
                    self.newEstacasLayer(name=name),
                    Config.instance().DIST,
                    [],
                )
            )
        else:
            self.openEstaca()
            self.view.btnCurva.click()

    def joinFeatures(self):
        layer = self.view.curvaLayers[0]
        layer.layerModified.disconnect()
        layer.commitChanges()
        id = [f for f in layer.getFeatures()][-1].id()
        if id > 1:
            moveLine(layer, id, getLastPoint(layer, id))
        self.iface.mapCanvas().refresh()
        layer.startEditing()
        layer.layerModified.connect(lambda: self.view.add_row(layer))

    #        self.updateTables()

    def fillView(self, table):
        self.estacasHorizontalList = []
        empty = True
        self.view.clear()
        for item in table:
            self.view.fill_table(tuple(item))
            self.estacasHorizontalList.append(tuple(item))
            empty = False
        self.view.empty = empty
        self.model.save(self.model.id_filename)

    def fileName(self, suggestion=False):
        filename = ""
        names = [
            self.preview.tableEstacas.item(i, 1).text()
            for i in range(self.preview.tableEstacas.rowCount())
        ]
        first = True
        while filename == "" or filename in names:
            if not first:
                from ..model.utils import messageDialog

                messageDialog(
                    None, title="Erro", message="Já existe um arquivo com esse nome"
                )

            filename, ok = QtWidgets.QInputDialog.getText(
                None,
                "Nome do arquivo",
                "Nome do arquivo:",
                text=suggestion
                if suggestion
                else "Traçado " + str(len(self.model.listTables() + 1)),
            )
            if not ok:
                return False
            first = False
        return filename

    def finishEdit(self):
        l = self.view.curvaLayers[0]
        l.commitChanges()
        l.endEditCommand()
        QgsProject.instance().removeMapLayer(l.id())

    def duplicarEstacaHorizontal(self):
        self.duplicarEstaca(False)

    def duplicarEstaca(self, trans=True):
        msgLog("---------Iniciando cópia--------")
        import traceback

        if self.model.id_filename == -1:
            return
        filename = self.fileName(
            suggestion="Cópia de " + self.model.getNameFromId(self.model.id_filename)
        )
        if not filename:
            return None
        self.progressDialog.show()
        self.openEstaca()
        self.progressDialog.setValue(10)
        estacas = self.view.get_estacas()
        bruck = self.model.load_bruck()
        id_filename = deepcopy(self.model.id_filename)
        self.model = self.model.saveEstacas(filename, estacas)
        if trans:
            try:
                msgLog("Carregando Transversais: ")
                prog, est, prism = self.model.getTrans(id_filename)
                if prog:
                    self.trans = Ui_sessaoTipo(
                        self.iface,
                        est[1],
                        self.model.load_intersect(id_filename),
                        prog,
                        est[0],
                        prism=prism,
                        greide=self.model.getGreide(id_filename),
                        title="Transversal: "
                        + str(self.model.getNameFromId(id_filename)),
                    )
                    self.model.id_filename = self.model.ultimo
                    self.saveTrans()
                    msgLog("Tranversais Salvas!")
            except Exception as e:
                msgLog("Falha ao duplicar Transversais: ")
                msgLog(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])

        self.model.id_filename = self.model.ultimo
        self.progressDialog.setValue(40)
        if bruck:
            self.model.save_bruck(bruck)
        try:
            self.view.openLayers()
            l = self.view.curvaLayers[0]
            source = self.view.curvaLayers[0].source()
            curvaModel = Curvas(id_filename)
            l.commitChanges()
            l.endEditCommand()
            QgsProject.instance().removeMapLayer(l.id())
            curvaModel.duplicate(filename, self.model.ultimo, source)
        except Exception as e:
            msgLog("---------------------------------\n\nFalha ao duplicar curvas: ")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
        self.progressDialog.setValue(60)
        try:
            tipo, class_project = self.model.tipo()
            estacas = self.model.load_terreno_long()
            self.perfil = Ui_Perfil(
                estacas,
                tipo,
                class_project,
                self.model.getGreide(id_filename),
                self.model.getCv(id_filename),
                iface=self,
            )
            table = deepcopy(self.perfil.getVertices())
            cvData = deepcopy(self.perfil.getCurvas())
            self.model.table = table
            self.model.cvData = cvData
            self.model.saveGreide(self.model.ultimo)
        except Exception as e:
            msgLog("Falha ao duplicar Greide: ")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
        self.progressDialog.setValue(80)
        # self.geraCurvas(self.model.id_filename)

        self.update()
        self.view.clear()
        estacas = self.model.loadFilename()
        self.estacasHorizontalList = []
        for e in estacas:
            self.view.fill_table(tuple(e), True)
            self.estacasHorizontalList.append(tuple(e))
        self.progressDialog.setValue(99)
        self.nextView = self.view
        self.view.setCopy()
        self.updateTables()
        try:
            self.view.closeLayers()
            self.viewCv.closeLayers()
        except:
            msgLog("Failed to close layers!")
        self.progressDialog.close()

    def cleanTrans(self):
        if yesNoDialog(
            None, message="Tem certeza que quer excluir os dados transversais?"
        ):
            self.trans.close()
            self.model.cleanTrans(idEstacaTable=self.model.id_filename)
            self.generateTrans()

    def recalcularVerticais(self):
        if self.viewCv.mode == "CV":
            self.openCv(True)
        elif self.viewCv.mode == "T":
            self.generateIntersec(True)

    def generateIntersec(self, recalcular=False):
        table = self.model.load_intersect()

        if recalcular or not table:
            self.progressDialog.show()
            table = self.generateintersecThread()
            self.progressDialog.close()
            if not table:
                return

        self.viewCv.clear()
        self.viewCv.setIntersect()
        s = 0
        for e, e2 in zip(table[:-1], table[1:]):
            self.viewCv.fill_table(tuple(e), True)
            e1 = [float(e[2]), float(e[-3])]
            e2 = [float(e2[2]), float(e2[-3])]
            s += ((e2[0] - e1[0]) ** 2 + (e2[1] - e1[1]) ** 2) ** 0.5
        self.viewCv.fill_table(tuple(table[-1]), True)

        self.viewCv.setWindowTitle(
            self.model.getNameFromId(self.model.id_filename) + ": Estacas"
        )
        try:
            self.viewCv.btnGen.clicked.disconnect()
        except:
            pass
        self.viewCv.btnGen.clicked.connect(self.openCv)
        self.viewCv.comprimento.setText(
            roundFloat2str(s) + " " + Config.instance().UNITS
        )
        self.nextView = self.viewCv

    @nongui
    def generateintersecThread(self):
        self.progressDialog.setValue(0)
        self.progressDialog.setText("Montando matrix de conflito...")
        import time

        self.openEstaca(False)
        horizontais = self.view.get_estacas()  # x = 4, y =3
        startTime = time.time()
        points = []
        progs = []
        LH = len(horizontais)
        self.progressDialog.setLoop(100, LH)
        for i, h in enumerate(horizontais):
            points.append(p2QgsPoint(float(h[4]), float(h[3])))
            progs.append(float(h[2]))
            self.progressDialog.increment()

        road = QgsGeometry.fromPolyline(points)

        QgsMessageLog.logMessage("Iniciando comparação", "GeoRoad", level=0)
        msgLog("Organizando: " + str(time.time() - startTime) + " seconds")

        verticais = []
        lastH = deepcopy(h)
        self.openCv()
        vprogs = []
        estacas = self.viewCv.getEstacas()

        LH = 500
        self.progressDialog.setLoop(60, LH)
        try:
            for i, v in enumerate(estacas):  # prog=2 em ambos
                prog = float(v[2])
                if prog in progs:
                    h = horizontais[progs.index(float(v[2]))]
                    if h[1]:
                        desc = "" if h[1] == "" and v[1] == "" else h[1] + " + " + v[1]
                    else:
                        desc = v[1]
                    verticais.append([v[0], desc, v[2], h[3], h[4], v[3], h[5], h[6]])
                else:
                    pt = road.interpolate(prog - 0.1).asPoint()
                    pt2 = road.interpolate(prog).asPoint()
                    verticais.append(
                        [v[0], v[1], v[2], pt.y(), pt.x(), v[3], None, azimuth(pt, pt2)]
                    )  # Não sei a cota 6
                self.progressDialog.increment()
                vprogs.append(prog)
        except Exception as e:
            import traceback

            msgLog("Erro ao gerar pontos!!!!!! ")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__)))
            msgLog("Road: ")
            msgLog(str(road))
            msgLog("Na Progressiva: ")
            msgLog(str(prog))
            messageDialog(
                message="As estacas finais do perfil vertical e horizontal não estão alinhadas",
                info="Tente criar seu perfil vertical novamente e recalcular a tabela vertical!",
            )
            return False

        if v[2] != lastH[2]:
            messageDialog(
                message="As estacas finais do perfil vertical e horizontal não estão alinhadas",
                info="Tente criar seu perfil vertical novamente e recalcular a tabela vertical!",
            )
            return False

        table = verticais
        msgLog("Horizontais: " + str(time.time() - startTime) + " seconds")

        for h in horizontais:
            if float(h[2]) not in vprogs:
                # Não sei o greide 5
                table.append([h[0], h[1], h[2], h[3], h[4], None, h[5], h[6]])

        # Organizar em ordem da progressiva
        table = sorted(table, key=lambda x: float(x[2]))
        msgLog("Organizar: " + str(time.time() - startTime) + " seconds")
        self.progressDialog.setValue(90)

        progAnt = float(table[0][2])
        anterior = [table[0][-2], table[0][-3]]  # cota, greide
        cfg = Config.instance()
        DIST = cfg.DIST
        PREC = cfg.PREC
        for i, t in enumerate(table):  # Interpolar greides e cotas desconhecidos
            atual = [t[-2], t[-3]]  # cota, greide
            if None in atual:
                if i == 0:
                    distAnt = 1000000
                else:
                    distAnt = float(t[2]) - progAnt
                j = 1
                while i + j < len(table) - 1:  # Próxima estaca inteira
                    if float(table[i + j][2]) % DIST == 0:
                        # cota, greide
                        proxima = [table[i + j][-2], table[i + j][-3]]
                        distProx = float(table[i + j][2]) - float(t[2])
                        break
                    j += 1
                else:
                    proxima = anterior
                    distProx = 1000000

                try:
                    # Interpola os valores de greide e cota desconhecidos em pontos críticos
                    from numpy import interp

                    table[i][-2] = interp(
                        0, [-distAnt, distProx], [float(anterior[0]), float(proxima[0])]
                    )
                    table[i][-3] = interp(
                        0, [-distAnt, distProx], [float(anterior[1]), float(proxima[1])]
                    )
                except Exception as e:
                    msgLog(str(e))
                    table[i][-2] = 0
                    table[i][-3] = 0

            if float(t[2]) % DIST == 0:  # se é uma estaca inteira se torna a anterior
                anterior = atual
                progAnt = float(t[2])

        # unir estacas muito próximas
        intersec = []
        e = table[0]
        for e1, e2 in zip(table[:-1], table[1:]):
            dist = float(e2[2]) - float(e1[2])
            if dist <= PREC:
                e1[1] = e[1] + " + " + e2[1]
                e = e1
            else:
                intersec.append(e)
                e = e2
        intersec.append(e2)

        self.model.saveIntersect(intersec)

        msgLog("Verticais: " + str(time.time() - startTime) + " seconds")
        QgsMessageLog.logMessage("Fim comparação", "GeoRoad", level=0)
        return intersec

    def new(self, layer=None, dados=None):
        self.view.clear()

        isGeopckg = True if dados else False
        dados = (
            dados
            if dados
            else self.preview.new(lastIndex=len(self.model.listTables()) + 1)
        )
        self.model.iface = self.iface
        if not dados is None:
            filename, lyr, dist, estaca = dados
            id_estaca, table = (
                self.model.new(dist, estaca, lyr, filename)
                if not isGeopckg
                else self.model.newEmpty(Config.instance().DIST, filename)
            )
            self.elemento = id_estaca
            self.model.id_filename = id_estaca
            self.estacasHorizontalList = []

            empty = True
            for item in table:
                self.view.fill_table(tuple(item))
                self.estacasHorizontalList.append(tuple(item))
                empty = False

            self.view.empty = empty
            self.model.save(id_estaca)
            self.updateTables()
            Config.instance().store("DIST", dados[-2])

            return self.model.getNewId()

        return False

    def perfilView(self):
        tipo, class_project = self.model.tipo()
        estacas = self.model.load_terreno_long()
        self.perfil = Ui_Perfil(
            estacas,
            tipo,
            class_project,
            self.model.getGreide(self.model.id_filename),
            self.model.getCv(self.model.id_filename),
            iface=self,
        )
        self.perfil.save.connect(self.saveGreide)
        self.perfil.reset.connect(self.cleanGreide)
        self.perfil.showMaximized()
        self.perfil.exec_()

    def saveGreide(self, noreset=False):
        if self.model.id_filename == -1:
            return
        self.model.table = self.perfil.getVertices()
        self.model.cvData = self.perfil.getCurvas()
        self.model.saveGreide(self.model.id_filename)
        if not noreset:
            self.perfil.justClose()
            self.perfilView()

    def cleanGreide(self):
        if self.model.id_filename == -1:
            return
        self.model.cleanGreide(self.model.id_filename)
        self.perfil.justClose()
        self.perfilView()

    @nongui
    def generateTransThread(self):
        self.progressDialog.setText("Carregando dados.")
        self.progressDialog.setValue(0)
        prog, est, prism = self.model.getTrans(self.model.id_filename)
        if prog:
            # Database Trans
            self.progressDialog.setValue(1)
            self.trans = Ui_sessaoTipo(
                self.iface,
                est[1],
                self.model.load_intersect(),
                prog,
                est[0],
                prism=prism,
                greide=self.model.getGreide(self.model.id_filename),
                title="Transversal: "
                + str(self.model.getNameFromId(self.model.id_filename)),
            )
        else:
            # New trans
            self.progressDialog.setValue(1)
            self.openEstaca(False)
            terreno = self.obterTerrenoTIFF()
            if not terreno:
                return False, False, False
            else:
                prog = True
            self.progressDialog.setValue(91)
            intersect = self.model.load_intersect()
            self.progressDialog.setValue(92)
            if len(intersect) <= 1:
                self.generateIntersec(True)
                self.progressDialog.setValue(93)
                intersect = self.model.load_intersect()
                self.progressDialog.setValue(95)
            self.trans = Ui_sessaoTipo(
                self.iface,
                terreno,
                intersect,
                self.estacasVerticalList,
                greide=self.model.getGreide(self.model.id_filename),
                title="Transversal: "
                + str(self.model.getNameFromId(self.model.id_filename)),
            )

        return prog, est, prism

    def generateTrans(self):
        self.progressDialog.show()
        prog, est, prism = self.generateTransThread()
        if not prog:
            self.progressDialog.close()
            return
        self.trans.save.connect(self.saveTrans)
        self.trans.btnClean.clicked.connect(self.cleanTrans)
        self.trans.plotar.connect(self.plotTransLayer)
        self.progressDialog.close()
        self.trans.btnExportDxf.clicked.connect(self.exportTrans)
        self.trans.btnImportDxf.clicked.connect(self.importTrans)
        self.trans.showMaximized()
        self.trans.exec_()
        self.raiseWindow(self.viewCv)

    def saveTrans(self):
        if self.model.id_filename == -1:
            return
        self.model.table = self.trans.getMatrixVertices()
        self.model.xList = self.trans.getxList()
        self.model.saveTrans(
            self.model.id_filename, self.trans.prismoide.getPrismoide()
        )

    def recalcular(self, curva=False):
        msgLog("Recalculando")
        self.view.comboBox.clear()
        id = self.model.id_filename
        if not curva:
            dados = self.preview.new(True)
        else:
            dados = self.preview.new(
                True, layerName=self.view.curvaLayers[0].name(), ask=False
            )

        if dados is None:
            return
        _, layer, dist, estaca = dados
        layer = layer if not curva else self.view.curvaLayers[0]
        msgLog("Usando Layer " + layer.name())
        table = self.model.recalcular(dist, estaca, layer, ask=not curva)
        self.view.clear()
        for item in table:
            self.view.fill_table(tuple(item))
        self.model.id_filename = id
        self.model.save(id)
        if not curva:
            self.geraCurvas(self.model.id_filename, recalcular=True)
            msgLog("Calculando traçado para o Desenho")

        if (
            not curva
            and len(self.view.curvaLayers) > 0
            and yesNoDialog(
                message="Foram detectadas curvas horizontais no traçado, deseja sobreescrever?"
            )
        ):
            msgLog("Removendo layer e curvas")
            curvas = Curvas(id_filename=self.model.id_filename)
            curvas.erase()
            self.model.removeGeoPackage(
                self.model.getNameFromId(self.model.id_filename)
            )

    def saveEstacas(self):
        if self.model.id_filename == -1:
            return
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.save(self.model.id_filename)

    def saveEstacasCSV(self):
        filename = self.view.saveEstacasCSV()
        if filename[0] in ["", None]:
            return
        self.saveEstacas()
        estacas = self.view.get_estacas()
        self.model.table = estacas
        self.model.saveCSV(filename)

    def deleteEstaca(self):
        table = self.preview.tableEstacas
        table: QtWidgets.QTableWidget
        if len(table.selectionModel().selectedRows(0)) == 0:
            return
        if not yesNoDialog(
            self.preview,
            title="Atenção",
            message="Tem certeza que deseja remover o arquivo?",
        ):
            return
        indexes = [i.row() for i in table.selectionModel().selectedRows(0)]
        if len(indexes) > 1:
            for i in indexes:
                id = table.item(i, 0).text()
                self.model.deleteEstaca(id)
        else:
            self.model.deleteEstaca(self.model.id_filename)
        curvaModel = Curvas(id_filename=self.model.id_filename)
        curvaModel.erase()
        self.update()
        self.model.id_filename = -1
        self.click = False

    def curva(self):
        curvas = self.model.getCurvas(self.model.id_filename)
        vertices = [
            [v[1], p2QgsPoint(float(v[4]), float(v[3]))]
            for v in self.model.loadFilename()
            if v[1] != ""
        ]
        if len(self.view.curvaLayers) == 0:
            self.geraCurvas(self.model.id_filename)
        if len(vertices) == 0:
            messageDialog(
                "Erro!", msg="Você deve calcular uma tabela de tangentes primeiro!"
            )
            return
        else:
            curvaView = CurvasView(
                self.view,
                self.iface,
                self.model.id_filename,
                curvas,
                vertices,
                self.model.tipo(),
            )
            curvaView.setWindowFlags(
                QtCore.Qt.Dialog
                | QtCore.Qt.WindowSystemMenuHint
                | QtCore.Qt.WindowMinimizeButtonHint
                | QtCore.Qt.WindowCloseButtonHint
            )
            curvaView.accepted.connect(self.raiseView)
            curvaView.rejected.connect(self.raiseView)
            curvaView.btnRecalcular.clicked.connect(self.recalcularCurvas)
            curvaView.btnTable.clicked.connect(self.viewCurvaZoom)
            self.curvaView = curvaView
            self.view.showMinimized()
            self.view.chview = curvaView
            self.curvaView.show()
            self.raiseWindow(self.curvaView)

    def recalcularCurvas(self):
        self.recalcular(True)
        self.curvaView.layer = self.view.curvaLayers[0]

    def viewCurvaZoom(self):
        desc = "TS" if self.curvaView.comboElemento.currentIndex() > 0 else "TC"
        items = [
            self.view.comboBox.itemText(i) for i in range(self.view.comboBox.count())
        ]
        desc += "".join(
            [str(c) for c in self.curvaView.comboCurva.currentText() if c.isdigit()]
        )
        self.raiseView()
        if desc in items:
            row = 0
            self.view.tableWidget.setRangeSelected(
                QTableWidgetSelectionRange(row, 1, row, 1), True
            )
            self.view.tableWidget.setCurrentCell(row, 1)
            self.view.comboBox.setCurrentIndex(items.index(desc))

    def raiseView(self):
        self.raiseWindow(self.view)
        if hasattr(self.curvaView, "c"):
            self.curvaView.c.rejected.emit()

    def raiseWindow(self, view):
        view.setWindowState(
            view.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive
        )
        view.activateWindow()

    def plotTransLayer(self, index):
        self.progressDialog.show()
        self.obterTerrenoTIFF(True, index)
        self.progressDialog.close()

    def obterTerrenoTIFF(self, plotTrans=False, index=-1):
        if not plotTrans:
            filename = self.view.openTIFF()
            if filename in ["", None]:
                return
        terreno = []

        # progressBar=ProgressDialog(None)
        # progressBar.show()

        try:
            layer = None
            if not plotTrans:
                for l in self.iface.mapCanvas().layers():
                    if l.source() == filename:
                        layer = l
                if layer is None:
                    msgLog("Layer não encontrada")
                    return []
                msgLog("Interpolando Layer: " + str(layer.name()))

            estacas = self.estacas = self.model.load_intersect()
            if not estacas:
                if yesNoDialog(
                    message="Você ainda não calculou a interseção das estacas! Quer que a seção transversal contenha somente estacas do perfil Horizontal?"
                ):
                    estacas = self.estacas = self.view.get_estacas()
                else:
                    return
            # fazer multithreading ?
            self.progressDialog.setValue(0)
            self.progressDialog.setLoop(90, len(estacas))
            ri = RasterInterpolator()
            for i, _ in enumerate(estacas):
                if plotTrans and index != -1:
                    i = index

                v = []
                az = float(estacas[i][7])
                perp = az + 90

                if perp > 360:
                    perp = perp - 360

                nsign = 1
                esign = 1
                if perp < 90:
                    nsign = 1
                    esign = 1
                elif perp < 180:
                    nsign = -1
                    esign = 1
                elif perp < 270:
                    nsign = -1
                    esign = -1
                elif perp < 360:
                    nsign = 1
                    esign = -1

                pointsList = []

                NPONTOS = Config.instance().T_OFFSET
                T_SPACING = Config.instance().T_SPACING
                SPACING = T_SPACING / (NPONTOS - 1)
                interpol = Config.instance().interpol
                for yi in range(int(-NPONTOS + 1), int(NPONTOS)):
                    y = yi * SPACING

                    yangleE = esign * y * abs(math.sin(perp * math.pi / 180))
                    yangleN = nsign * y * abs(math.cos(perp * math.pi / 180))
                    msgLog("Computando azimute transversal: " + str(perp))
                    try:
                        xPoint = float(float(estacas[i][4]) + yangleE)
                        yPoint = float(float(estacas[i][3]) + yangleN)

                        if not plotTrans:
                            cota = ri.cotaFromTiff(
                                layer, QgsPointXY(xPoint, yPoint), interpol
                            )
                        else:
                            cota = 0
                        v.append([y, float(cota)])
                        pointsList.append([xPoint, yPoint])

                    except ValueError as e:
                        self.preview.error("GeoTIFF não compativel com a coordenada!!!")
                        msgLog(str(e))
                        return False
                    except IndexError as e:
                        continue

                self.progressDialog.increment()
                terreno.append(v)

                if plotTrans:
                    if index == -1:
                        self.drawPoints(pointsList, str(i + 1))
                    # for ind in range(len(pointsList)):
                    #     self.drawPoint(pointsList[ind], str(i+1))
                    if index == i:
                        self.drawPoints(pointsList, str(i + 1))
                        for ind in range(len(pointsList)):
                            self.drawPoint(pointsList[ind], str(i + 1))
                        return

        except e:
            msgLog("Interpolação Falhou: " + str(e))
            terreno = []

        return terreno

    def drawPoint(self, point, name):
        layer = QgsVectorLayer("Point", name, "memory")
        pr = layer.dataProvider()
        ft = QgsFeature()
        ft.setAttributes([1])
        ft.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(point[0], point[1])))
        pr.addFeatures([ft])
        layer.setCrs(QgsProject.instance().crs())
        QgsProject.instance().addMapLayer(layer)

    def drawPoints(self, pointsList, name):
        layer = QgsVectorLayer("LineString", name, "memory")
        pr = layer.dataProvider()
        poly = QgsFeature()

        points = []

        for i, _ in enumerate(pointsList):

            point = QgsPointXY(float(pointsList[i][0]), float(pointsList[i][1]))
            points.append(point)

        poly.setGeometry(QgsGeometry.fromPolylineXY(points))
        pr.addFeatures([poly])
        layer.updateExtents()
        layer.setCrs(QgsProject.instance().crs())
        QgsProject.instance().addMapLayers([layer])

    def newEstacasLayer(self, name):
        fields = layerFields()
        self.model.saveGeoPackage(name, [], fields, QgsWkbTypes.MultiCurveZ, "GPKG")

    def saveEstacasLayer(self, estacas, name=None):
        name = (
            str(self.model.getNameFromId(self.model.id_filename))
            if name == None
            else name
        )
        # path = QtWidgets.QFileDialog.getSaveFileName(self.iface.mainWindow(), "Caminho para salvar o traçado com as curvas", filter="Geopackage (*.gpkg)")[0]
        # if not path: return None

        fields = layerFields()
        points = []
        features = []
        j = 0
        desc = "T"
        for i, _ in enumerate(estacas):
            point = QgsPointXY(float(estacas[i][4]), float(estacas[i][3]))
            ed = estacas[i][1]
            if ed.startswith("P") or ed.startswith("CT") or ed.startswith("ST"):
                desc = "T"
            elif ed.startswith("TS") or ed.startswith("CS"):
                desc = "S"
            elif ed.startswith("SC") or ed.startswith("TC"):
                desc = "C"
            if i == 0:
                points.append(point)
            else:
                if float(estacas[i][6]) != lastAz or i == len(estacas) - 1:
                    points.append(point)
                    feat = QgsFeature(fields)
                    feat.setAttributes([desc, "Recalculado"])
                    feat.setGeometry(QgsGeometry.fromPolylineXY(points))
                    features.append(feat)
                    j += 1
                    points = [point]
            lastAz = float(estacas[i][6])

        path = self.model.saveGeoPackage(
            name, features, fields, QgsWkbTypes.MultiCurveZ, "GPKG"
        )
        self.view.openLayers()
        refreshCanvas(self.iface)

        # CARREGAR NOVA LAYER:

    # layer=self.iface.addVectorLayer(path,name,"ogr")
    # self.iface.digitizeToolBar().show()
    # self.iface.shapeDigitizeToolBar().show()

    # addLineAction = self.iface.digitizeToolBar().actions()[8]
    # toggleEditAction = self.iface.digitizeToolBar().actions()[1]
    # if not addLineAction.isChecked():
    #     toggleEditAction.trigger()
    # addLineAction.setChecked(True)
    # addLineAction.trigger()

    #  return layer

    def drawEstacas(self, estacas):
        layer = QgsVectorLayer(
            "LineString?crs=%s" % (QgsProject.instance().crs().authid()),
            str(self.model.getNameFromId(self.model.id_filename)),
            "memory",
        )
        layer.setCrs(QgsCoordinateReferenceSystem(QgsProject.instance().crs()))
        pr = layer.dataProvider()
        poly = QgsFeature()

        points = []
        for i, _ in enumerate(estacas):

            point = QgsPointXY(float(estacas[i][4]), float(estacas[i][3]))
            points.append(point)

        poly.setGeometry(QgsGeometry.fromPolylineXY(points))
        pr.addFeatures([poly])
        layer.updateExtents()
        QgsProject.instance().addMapLayers([layer], False)
        QgsProject.instance().layerTreeRoot().insertLayer(0, layer)
        return layer

    def obterCotasTIFF(self):

        filename = self.view.openTIFF()
        if filename in ["", None]:
            return
        self.progressDialog.setText("Carregando cotas")
        self.progressDialog.show()

        try:
            l = False
            for l in self.iface.mapCanvas().layers():
                if l.source() == filename:
                    layer = l
                    break
            if not l:
                self.preview.error("Salve a layer antes de usa-lá!")
                return
            from ..model.utils import RasterInterpolator

            ri = RasterInterpolator()
            self.estacas = self.view.get_estacas()
            estacas = self.estacas
            self.progressDialog.setLoop(100, len(estacas))

            for i, _ in enumerate(estacas):
                cota = ri.cotaFromTiff(
                    layer,
                    QgsPointXY(float(estacas[i][4]), float(estacas[i][3])),
                    interpolate=Config.instance().interpol,
                )
                if cota >= 0:
                    estacas[i][5] = roundFloat2str(cota)
                else:
                    self.preview.error(
                        "Pontos do traçado estão fora do raster selecionado!!!"
                    )
                    break
                self.progressDialog.increment()

        except Exception as e:
            msgLog("TasterInterpolator failed with " + str(e))
            from osgeo import gdal

            dataset = gdal.Open(filename, gdal.GA_ReadOnly)
            for x in range(1, dataset.RasterCount + 1):
                band = dataset.GetRasterBand(x)
                img = band.ReadAsArray()
            self.img_origem = dataset.GetGeoTransform()[0], dataset.GetGeoTransform()[3]
            self.tamanho_pixel = abs(dataset.GetGeoTransform()[1]), abs(
                dataset.GetGeoTransform()[5]
            )
            self.estacas = self.view.get_estacas()
            estacas = self.estacas

            self.progressDialog.setValue(0)
            self.progressDialog.setLoop(100, len(estacas))

            for i, _ in enumerate(estacas):
                self.progressDialog.increment()
                try:
                    pixel = (
                        int(
                            abs(float(estacas[i][4]) - self.img_origem[0])
                            / self.tamanho_pixel[0]
                        ),
                        int(
                            abs(float(estacas[i][3]) - self.img_origem[1])
                            / self.tamanho_pixel[1]
                        ),
                    )
                    estacas[i][5] = "%f" % img[pixel]
                except Exception as e:
                    # self.drawEstacas(estacas)
                    self.preview.error("GeoTIFF não compativel com a coordenada!!!")
                    msgLog("Erro: " + str(e))
                    break

        self.progressDialog.close()
        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca(False)
        self.progressDialog.close()

    def obterCotasPC3(self):

        filename = self.view.openTIFF()
        if filename in ["", None] or not filename.endswith("dxf"):
            return
        self.estacas = self.view.get_estacas()
        estacas = self.estacas
        points = []
        # fazer multithreading
        for i, _ in enumerate(estacas):
            points.append(
                (int("%d" % float(estacas[i][4])), int("%d" % float(estacas[i][3])))
            )

        dwg = dxfgrabber.readfile(filename, options={"assure_3d_coords": True})
        dxfversion = dwg.header["$ACADVER"]
        all_points = []
        for entity in dwg.entities:
            if entity.dxftype == "POINT":
                pe = "%d" % entity.point[0]
                pn = "%d" % entity.point[1]
                p = (int(pe), int(pn))
                if p in points:
                    all_points.append(p)

        for p in all_points:
            ponto = points.index((int(p[0]), int(p[1])))
            estacas[ponto][5] = p[2]
            # fix_print_with_import
            print(estacas[ponto])
        # fix_print_with_import
        print("terminou")
        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca()

    def elevate(self):
        import ctypes

        import win32com.shell.shell
        import win32event
        import win32process

        outpath = r"%s\%s.out" % (os.environ["TEMP"], os.path.basename(__file__))
        if ctypes.windll.shell32.IsUserAnAdmin():
            if os.path.isfile(outpath):
                sys.stderr = sys.stdout = open(outpath, "w", 0)
                return
        with open(outpath, "w+", 0) as outfile:
            hProc = win32com.shell.shell.ShellExecuteEx(
                lpFile=sys.executable,
                lpVerb="runas",
                lpParameters=" ".join(sys.argv),
                fMask=64,
                nShow=0,
            )["hProcess"]
            while True:
                hr = win32event.WaitForSingleObject(hProc, 40)
                while True:
                    line = outfile.readline()
                    if not line:
                        break
                    sys.stdout.write(line)
                if hr != 0x102:
                    break
        os.remove(outpath)
        sys.stderr = ""
        sys.exit(win32process.GetExitCodeProcess(hProc))

    def obterCotasPC(self):
        try:
            import dxfgrabber
            from sklearn import linear_model
            from sklearn.neighbors import KNeighborsRegressor
            from sklearn.svm import SVR
        except:
            import os
            import re

            if not re.match("win{1}.*", os.sys.platform) is None:
                saida = os.system(
                    "C:\\Users\\%%USERNAME%%\\.qgis2\\python\\plugins\\TopoGrafia\\app\\controller\\install.bat"
                )
            else:
                saida = os.system(
                    "sudo apt install python-pip&&pip install scikit-learn&&pip install dxfgrabber"
                )
            if saida != 0:
                self.preview.error(
                    "Para usar este recurso você deve instalar os pacotes abaixo:\nSKLearn e dxfgrabber: (Linux) 'sudo pip install scikit-learn&&pip install dxfgrabber' (Windows) Deve seguir o tutorial https://github.com/lennepkade/dzetsaka#installation-of-scikit-learn"
                )
            return
        filename, _ = self.view.openDXF()
        if filename in ["", None] or not (
            filename.endswith("dxf") or filename.endswith("DXF")
        ):
            return
        estacas = self.view.get_estacas()
        dwg = dxfgrabber.readfile(filename, options={"assure_3d_coords": True})
        all_points = []
        all_points_Y = []
        inicial = (float(estacas[0][4]), float(estacas[0][3]))
        az_inicial = float(estacas[0][6])
        for entity in dwg.entities:
            if entity.dxftype == "POINT":
                dist = math.sqrt(
                    (inicial[0] - entity.point[0]) ** 2
                    + (inicial[1] - entity.point[1]) ** 2
                )
                az = float(
                    azimuth(
                        p2QgsPoint(inicial[0], inicial[1]),
                        p2QgsPoint(entity.point[0], entity.point[1]),
                    )
                )
                all_points.append([entity.point[0], entity.point[1]])
                all_points_Y.append([entity.point[2]])

        points = []
        for i, _ in enumerate(estacas):
            points.append([float(estacas[i][4]), float(estacas[i][3])])
        X = all_points
        y = all_points_Y
        # clf = SVR(C=1.0, epsilon=0.2)
        # clf = KNeighborsRegressor(n_neighbors=3)
        itens = [
            "KNN Regressão (Classico)",
            "KNN Regressão (K Inteligente)",
            "SVM",
            "Regressão Linear",
        ]
        itens_func = [KNeighborsRegressor, KNN, SVR, linear_model.ARDRegression]
        item, ok = QtWidgets.QInputDialog.getItem(
            None, "Selecione:", "Selecione o método de predição:", itens, 0, False
        )
        if not (ok) or not (item):
            return None

        clf = itens_func[item.index(item)](5)
        if itens.index(item) < 2:
            k, ok = QtWidgets.QInputDialog.getInteger(
                None, "Escolha o valor de K", "Valor de K:", 3, 2, 10000, 2
            )
            if k < 1 or not (ok):
                return None
            clf = itens_func[itens.index(item)](k)
        # clf = KNN(5)
        # clf = linear_model.LinearRegression()
        # clf = linear_model.ARDRegression()
        modelo = clf.fit(X, y)
        pred = modelo.predict(points)
        for i, predito in enumerate(pred):
            estacas[i][5] = "%f" % predito
        self.model.table = estacas
        self.model.save(self.model.id_filename)
        self.openEstaca()

    def obterCotas(self):
        self.model.table = self.view.get_estacas()
        crs = int(self.model.getCRS())
        for i, _ in enumerate(self.model.table):
            try:
                self.model.table[i][5] = "%d" % getElevation(
                    crs,
                    p2QgsPoint(
                        float(self.model.table[i][4]), float(self.model.table[i][3])
                    ),
                )
                if self.model.table[i][5] == 0:
                    return
            except Exception as e:
                # fix_print_with_import
                print(e.message)
                break
        self.model.save(self.model.id_filename)
        self.openEstaca()

    """
        Metodos responsaveis por gerar o traçado de acordo com cliques na tela.
    """

    def geraTracado(self, parte=0, pontos=None):
        crs = self.model.getCRS()
        self.preview.drawShapeFileAndLoad(crs)

    def get_click(self, point, mouse):

        if not self.edit:
            return
        self.edit = False
        # if mouse == 2: return
        if mouse == 1:
            self.preview.create_point(p2QgsPoint(point), "vertice")
            self.points.append(p2QgsPoint(point))

        self.edit = True

    def get_click_coordenate(self, point, mouse):

        if not self.edit:
            return
        self.edit = False
        # if mouse == 2: return
        if mouse == 1:
            self.preview.create_point(p2QgsPoint(point), "vertice")
            self.points.append(p2QgsPoint(point))

        self.edit = True

    def exit_dialog(self):
        self.points.append(p2QgsPoint(self.points_end))
        self.iface.mapCanvas().setMapTool(QgsMapToolEmitPoint(self.iface.mapCanvas()))
        self.edit = False
        self.preview.exit_dialog(self.points, self.crs)
        self.new()
        self.view.show()
        self.view.exec_()

    def gera_tracado_vertices(self, p1, p2, crs):
        self.crs = crs
        self.points = [p1]
        self.edit = True
        self.points_end = p2
        self.pointerEmitter = QgsMapToolEmitPoint(self.iface.mapCanvas())

        self.pointerEmitter.canvasClicked.connect(self.get_click)
        name_tracado = self.preview.gera_tracado_vertices(self.pointerEmitter)
        self.preview.dialog.btnClose.clicked.connect(self.exit_dialog)
        return name_tracado

    """
        --------------------------------------------------
    """

    def openEstaca(self, display=True):
        if self.model.id_filename == -1:
            return
        self.view.clear()
        estacas = self.model.loadFilename()
        self.estacasHorizontalList = []
        for e in estacas:
            self.view.fill_table(tuple(e), True)
            self.estacasHorizontalList.append(tuple(e))
        if display:
            self.nextView = self.view
            self.view.setCopy()
        self.updateTables()

    def openCv(self, recalcular=False):
        estacas = self.model.load_verticais()
        if recalcular or not estacas:
            self.progressDialog.show()
            estacas = self.generateVerticaisThread()
            self.progressDialog.close()

        if not estacas:
            return
        self.estacasVerticalList = estacas
        self.viewCv.clear()
        self.viewCv.setCv()

        for e in estacas:
            self.viewCv.fill_table(tuple(e), True)
        try:
            self.viewCv.btnGen.clicked.disconnect()
        except:
            pass
        self.viewCv.btnGen.clicked.connect(self.generateIntersec)
        self.nextView = self.viewCv

    @nongui
    def generateVerticaisThread(self):
        self.progressDialog.setText("Calculando estacas do greide no perfil vertical")
        self.openEstaca()
        self.viewCv.clear()
        self.viewCv.setWindowTitle(
            str(self.model.getNameFromId(self.model.id_filename)) + ": Verticais"
        )
        try:
            tipo, class_project = self.model.tipo()
            estacas = self.model.load_terreno_long()
            self.perfil = Ui_Perfil(
                estacas,
                tipo,
                class_project,
                self.model.getGreide(self.model.id_filename),
                self.model.getCv(self.model.id_filename),
                iface=self,
            )
        except Exception as e:
            import traceback

            messageDialog(
                None, title="Erro!", message="Perfil Vertical ainda não foi definido!"
            )
            msgLog("Falha ao identificar Greide")
            msgLog(str(traceback.format_exception(None, e, e.__traceback__))[1:-1])
            return
            # self.perfilView()
            # self.perfil = Ui_Perfil(self.view, tipo, class_project, self.model.getGreide(self.model.id_filename), self.model.getCv(self.model.id_filename))

        estacas = []
        (estaca, descricao, progressiva, cota) = (
            0,
            "V0",
            0,
            self.perfil.getVertices()[0][1],
        )
        estacas.append((estaca, descricao, progressiva, cota))
        missingCurveDialog = []
        y = float(cota)
        points = []

        LH = len(self.perfil.roi.handles) - 1
        self.progressDialog.setLoop(30, LH)
        for i in range(1, LH):
            self.progressDialog.increment()
            i1 = self.perfil.roi.getSegIncl(i - 1, i)
            i2 = self.perfil.roi.getSegIncl(i, i + 1)
            L = 0
            if self.perfil.cvList[i][1] != "None":
                L = float(self.perfil.cvList[i][1])

            pontosCv = CV(
                i1,
                i2,
                L,
                self.perfil.roi.getHandlePos(i),
                self.perfil.roi.getHandlePos(i - 1),
            )
            points.append(
                {"cv": pontosCv, "i1": i1 / 100, "i2": i2 / 100, "L": L, "i": i}
            )

        if len(points) == 0:
            self.progressDialog.close()
            messageDialog(
                None, title="Erro!", message="Perfil Vertical ainda não foi definido!"
            )
            msgLog("len(points)==0")
            return None

        x = 0
        i = points[0]["i1"]
        s = 0
        c = 1
        fpcv = 0
        fptv = 0
        est = 1
        dist = Config.instance().DIST
        LH = int(
            self.perfil.roi.getHandlePos(self.perfil.roi.countHandles() - 1).x() / dist
        )
        skip = False
        self.progressDialog.setLoop(80, LH)
        while est <= LH:
            self.progressDialog.increment()
            if fptv:
                dx = dist - dx
                dy = point["i2"] * dx
                fptv = 0

            elif fpcv:
                dx = dist - dx
                dy = point["i1"] * dx
                fpcv = 0
            else:
                dx = dist
                dy = i * dx

            desc = ""

            if len(points) > 0:
                point = points[0]

                try:
                    pt = x + dx >= point["cv"].xptv
                    pv = x + dx >= point["cv"].xpcv and not pt and not s

                except AttributeError:
                    point["cv"].xptv = point["cv"].handlePos.x()
                    point["cv"].xpcv = point["cv"].handlePos.x()
                    point["cv"].ypcv = point["cv"].handlePos.y()
                    point["cv"].yptv = point["cv"].handlePos.y()

                    missingCurveDialog.append(c)

                    pt = x + dx >= point["cv"].xptv
                    pv = x + dx >= point["cv"].xpcv and not pt and not s

                i = points[0]["i1"]
            else:
                pt = False
                pv = False
                i = point["cv"].i2 / 100

            if pv:
                # estacas.append(("debug",point["i"],point["i1"],point["cv"].ypcv))
                dx = point["cv"].xpcv - x
                desc = "PCV" + str(c)
                s = 1
                dy = point["cv"].ypcv - y
                est -= 1
                fpcv = 1

            elif pt:
                dx = point["cv"].xptv - x

                if point["cv"].xptv == point["cv"].handlePos.x():
                    desc = "PV" + str(c)
                else:
                    desc = "PTV" + str(c)

                s = 0
                dy = point["cv"].yptv - y
                est -= 1
                points.pop(0)
                fptv = 1
                c += 1

            x += dx
            if s and not (pv or pt):
                dy = point["cv"].getCota(x) - y
            y += dy

            if skip:
                skip = False
                est += 1
                continue

            if dx == dist and (pv or pt):
                (estaca, descricao, progressiva, cota) = (str(est + 1), desc, x, y)
                skip = True
            else:
                (estaca, descricao, progressiva, cota) = (
                    est if not (pv or pt) else str(est) + " + " + roundFloat2str(dx),
                    desc,
                    x,
                    y,
                )

            estacas.append((estaca, descricao, progressiva, cota))
            est += 1

        if len(missingCurveDialog) > 0:
            messageDialog(
                self.viewCv,
                "Atenção!",
                message="Nenhum comprimento de curva foi definido no perfil vertical para os vértices: "
                + str(missingCurveDialog)[1:-1],
            )
        dx = float(self.perfil.getVertices()[-1:][0][0]) - x
        x += dx
        dy = float(self.perfil.getVertices()[-1:][0][1]) - y
        y += dy

        (estaca, descricao, progressiva, cota) = (
            str(est - 1) + " + " + str(dx),
            "V" + str(c + 1),
            x,
            y,
        )
        estacas.append((estaca, descricao, progressiva, cota))

        self.model.saveVerticais(estacas)
        return estacas

    def itemClickTableEstacas(self, item=None):
        self.click = True
        if item is None:
            self.preview.tableEstacas: QtWidgets.QTableWidget
            item = self.preview.tableEstacas.currentItem()
        try:
            ident = int(self.preview.tableEstacas.item(item.row(), 0).text())
            self.model.id_filename = ident
        except:
            pass

    def openEstacaCSV(self):
        self.view.clear()
        res = self.preview.openCSV()
        if not res:
            return
        file = res[0]
        if (
            file[0] in ["", None]
            or res[1] in ["", None]
            or not (file[0].endswith("csv"))
        ):
            return
        filename, fileDB = file[0], res[1]
        estacas = self.model.openCSV(filename, fileDB)
        self.model.table = estacas
        self.elemento = self.model.ultimo
        for estaca in estacas:
            self.view.fill_table(tuple(estaca), True)
        self.view.setCopy()
        self.model.save(self.elemento)

    def plotar(self):
        self.drawEstacas(self.view.get_estacas())
        # self.view.plotar()

    def update(self):
        files = self.model.listTables()
        self.preview.fill_table_index(files)
        self.preview.checkButtons()
        self.view.clear()
        self.view.clearLayers()
        refreshCanvas(self.iface)

    def updateTables(self):
        try:
            self.view.setWindowTitle(
                self.model.getNameFromId(self.model.id_filename) + ": Horizontal"
            )
        except:
            pass

    def run(self):
        # from ..view.estacas import SelectFeatureDialog
        # s=SelectFeatureDialog(self.iface,self.iface.mapCanvas().layer(0).getFeatures())
        # s.exec_()
        self.update()
        self.click = False
        self.preview.setWindowTitle(Config.instance().FILE_PATH)
        self.preview.show()

        finalResult = False
        result = True

        lastFinalResult = True
        lastResult = False

        while finalResult > 0 or result > 0:
            self.update()
            result = self.preview.exec_()
            self.nextView.resize(self.nextView.width(), self.nextView.height() + 1)
            if result:
                self.preview.close()
                self.nextView.show()
                finalResult = self.nextView.exec_()

            if lastResult == result:
                lastResult = not result

            elif lastFinalResult == finalResult:
                lastFinalResult = not finalResult

            else:
                lastFinalResult = finalResult
                lastResult = result

            for d in DIALOGS_TO_CLOSE_ON_LOOP:
                if hasattr(self, d):
                    getattr(self, d).close()
