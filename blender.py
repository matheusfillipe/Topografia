# Blender script to generate the road mesh from stl model

import json
import sys
import tempfile
from math import radians, sqrt, pi
from pathlib import Path

import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:]

PREC = 1.0


def find_by_name(name):
    for obj in bpy.data.objects:
        if name in obj.name:
            return obj


def distance(p1, p2):
    return sqrt(
        (float(p1[0]) - float(p2[0])) ** 2
        + (float(p1[1]) - float(p2[1])) ** 2
        + (float(p1[2]) - float(p2[2])) ** 2
    )


def get_vertex(pos):
    o = bpy.context.active_object
    verts = []
    for v in o.data.vertices:
        vec = v.undeformed_co
        dist = distance(vec, pos)
        if dist <= PREC:
            verts.append([v, dist])
    r = sorted(verts, key=lambda e: e[1])
    if len(r) == 0:
        return False
    else:
        return r[0][0]


def toggle():
    if bpy.context.object.mode == "OBJECT":
        bpy.ops.object.mode_set(mode="EDIT")
    else:
        bpy.ops.object.mode_set(mode="OBJECT")


# start
print("script: Running Script...")
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[0]
)

# .stl trimesh filepath
filepath = argv[0]

bpy.ops.preferences.addon_enable(module="io_import_dxf")
bpy.ops.preferences.addon_enable(module="io_export_dxf")
jsonfile = str(Path(tempfile.gettempdir()) / "georoadBlender.json")
with open(jsonfile, "r") as file:
    data = json.load(file)

start = data["start"]
points = data["points"]
print("script: json points loaded")

# mesh import
bpy.ops.import_mesh.stl(filepath=filepath)
mesh = bpy.context.object
bpy.data.scenes["Scene"].cursor.location = start
bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
mesh.location[2] = 0
mesh.location[1] = 0
mesh.location[0] = 0
bpy.ops.object.transform_apply(location=True, scale=False, rotation=False)
toggle()
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.tris_convert_to_quads()
bpy.ops.mesh.select_all(action="DESELECT")
toggle()
selverts = []
for i, pt in enumerate(points):
    v = get_vertex(pt)
    if v:
        v.select = True
        selverts.append(v)
    else:
        print("No vertex at index: ", i)
toggle()
bpy.ops.mesh.select_mode(type="EDGE")
print("script: finished defining main axis!!")

# apply materials
road = bpy.data.materials.get("Road")
eixo = bpy.data.materials.get("Eixo")
terreno = bpy.data.materials.get("Terreno")

bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_mode(type="FACE")
mesh.data.materials.append(road)
mesh.active_material_index = 0
bpy.ops.object.material_slot_assign()
bpy.ops.mesh.select_all(action="INVERT")
mesh.data.materials.append(terreno)
mesh.active_material_index = 1
bpy.ops.object.material_slot_assign()
bpy.ops.mesh.select_all(action="INVERT")
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
print("script: materials applied")
toggle()
bpy.ops.object.select_all(action="DESELECT")

# create path for camera new obj
coords = [pt for i, pt in enumerate(points)]
curveData = bpy.data.curves.new("myCurve", type="CURVE")
curveData.dimensions = "3D"
curveData.resolution_u = 2

# map coords to spline
polyline = curveData.splines.new("NURBS")
polyline.points.add(len(coords))
for i, coord in enumerate(coords):
    x, y, z = coord
    polyline.points[i].co = (x, y, z + 10, 1)

# create Object
curveOB = bpy.data.objects.new("myCurve", curveData)

# attach to scene and validate context
# scn = bpy.context.scene
# scn.objects.link(curveOB)
bpy.context.collection.objects.link(curveOB)
# scn.objects.active = curveOB
# curveOB.select = True
path = curveOB
path.select_set(True)

# select path obj
bpy.context.view_layer.objects.active = path
path.select_set(True)
bpy.ops.object.convert(target="CURVE")
# bpy.context.object.hide_viewport = True
bpy.context.object.hide_set(True)
bpy.context.object.data.path_duration = int(data["frames"])
bpy.context.scene.frame_end = int(data["frames"])
print("script: animation path set")


# apply to camera
cam = bpy.data.objects["Camera"]
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = cam
cam.select_set(True)
bpy.ops.object.rotation_clear(clear_delta=False)
bpy.ops.object.location_clear(clear_delta=False)
bpy.ops.object.constraint_add(type="FOLLOW_PATH")
bpy.context.object.constraints["Follow Path"].target = path
override = {"constraint": cam.constraints["Follow Path"]}
area = next((a for a in bpy.context.screen.areas if a.type == "VIEW_3D"), None)
if area is not None:
    bpy.ops.constraint.followpath_path_animate(override, constraint="Follow Path")
    bpy.context.object.constraints["Follow Path"].use_curve_follow = True

bpy.data.objects["Camera"].rotation_euler[0] = 1.309
bpy.data.objects["Camera"].rotation_euler[1] = 0
bpy.data.objects["Camera"].rotation_euler[2] = 0
print("script: camera applied")


# add estaca labels
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[-1]
)
for pt, est, azi in zip(data["points"], data["estacas"], data["azi"]):
    ## Print only 10th's
    # if not est.strip().endswith("0"):
    #     continue
    bpy.ops.object.text_add(enter_editmode=False, location=(pt[0], pt[1], pt[2] + 15))
    bpy.context.object.data.materials.append(bpy.data.materials.get("Label"))
    bpy.context.object.data.body = est
    bpy.context.active_object.name = est
    bpy.context.object.data.size = 7.5

    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
    bpy.context.object.rotation_euler[0] = pi / 2
    bpy.context.object.rotation_euler[2] = -radians(float(azi))

print("script: labels added")


# select mesh
bpy.context.view_layer.active_layer_collection = (
    bpy.context.view_layer.layer_collection.children[0]
)
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
print("script: mesh selected")


# yellow centerline
toggle()
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.select_all(action="DESELECT")
toggle()
# for v in selverts:
#    v.select = True
for i, pt in enumerate(points):
    v = get_vertex(pt)
    if v:
        v.select = True
        selverts.append(v)
    else:
        print("No vertex at index: ", i)

toggle()
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.bevel(offset=0.1, offset_pct=0)
mesh.data.materials.append(eixo)
mesh.active_material_index = 2
bpy.ops.object.material_slot_assign()
toggle()
print("script: colors applied to main axis")


# set rendered
my_areas = bpy.context.workspace.screens[0].areas
my_shading = "RENDERED"  # 'WIREFRAME' 'SOLID' 'MATERIAL' 'RENDERED'
for area in my_areas:
    for space in area.spaces:
        if space.type == "VIEW_3D":
            space.shading.type = my_shading

print("script: Finished Sucessfully!!")
