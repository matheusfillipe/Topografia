import bpy
from mathutils import Vector
from math import sqrt
import tempfile
import json
import sys
from pathlib import Path
from math import radians
argv = sys.argv
argv = argv[argv.index("--") + 1:] 

PREC=1.0

def find_by_name(name):
    for obj in bpy.data.objects:
        if name in obj.name:
            return obj
        
def distance(p1,p2):
    return sqrt((float(p1[0])-float(p2[0]))**2+(float(p1[1])-float(p2[1]))**2+(float(p1[2])-float(p2[2]))**2)

def  get_vertex(pos):
    o=bpy.context.active_object
    verts=[]
    for v in o.data.vertices:
        vec=v.undeformed_co
        dist=distance(vec, pos)
        if dist <= PREC:
            verts.append([v, dist])
    r=sorted(verts, key=lambda e: e[1])
    if len(r)==0:
        return False
    else:
        return r[0][0]

    
def toggle():
    if bpy.context.object.mode == "OBJECT":
        bpy.ops.object.mode_set(mode='EDIT') 
    else:
        bpy.ops.object.mode_set(mode='OBJECT') 
#start
print("script: Running Script...")
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[0]
filepath = argv[0]#"/home/matheus/tmp/testhighway.stl"
#dxf="/home/matheus/Downloads/Telegram Desktop/highway.dxf"
#start= [728352.9266,7787532.9365,484.0]
bpy.ops.preferences.addon_enable(module="io_import_dxf")
bpy.ops.preferences.addon_enable(module="io_export_dxf")
jsonfile = str(Path(tempfile.gettempdir()) / "georoadBlender.json")
with open(jsonfile, "r") as file:
    data = json.load(file)
start=data["start"]
points=data["points"]
print("script: json points loaded")

#mesh import
bpy.ops.import_mesh.stl(filepath=filepath)
mesh=bpy.context.object
bpy.data.scenes["Scene"].cursor.location=start
bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
mesh.location[2] = 0
mesh.location[1] = 0
mesh.location[0] = 0
bpy.ops.object.transform_apply(location = True, scale = False, rotation = False)
toggle()
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.tris_convert_to_quads()
bpy.ops.mesh.select_all(action='DESELECT')
toggle()
selverts=[]
for i,pt in enumerate(points):
    v=get_vertex(pt)
    if v:
        v.select = True
        selverts.append(v)
    else:
        print("No vertex at index: ", i)
toggle()
bpy.ops.mesh.select_mode(type="EDGE")
print("script: finished defining eixo!!")


#bpy.ops.import_scene.dxf(filepath=dxf)
#curve=find_by_name("curve")
#p=curve.data.splines[0].points[0].co
#v=curve.matrix_world @ p
#start=[v.x,v.y,v.z]

#apply materials
road=bpy.data.materials.get("Road")
eixo=bpy.data.materials.get("Eixo")
terreno=bpy.data.materials.get("Terreno")

bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_more()
bpy.ops.mesh.select_mode(type="FACE")
mesh.data.materials.append(road)
mesh.active_material_index = 0
bpy.ops.object.material_slot_assign()
bpy.ops.mesh.select_all(action='INVERT')
mesh.data.materials.append(terreno)
mesh.active_material_index = 1
bpy.ops.object.material_slot_assign()
bpy.ops.mesh.select_all(action='INVERT')
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
bpy.ops.mesh.select_less()
print("script: materials applied")

#create path for camera new obj
bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 10), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
#bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})

bpy.ops.mesh.separate(type="SELECTED")
toggle()
#bpy.ops.object.select_all(action='DESELECT')
#select path obj
for obj in bpy.context.selected_objects:
    if obj.type == 'MESH' and obj.name!=mesh.name:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        path=obj
bpy.context.view_layer.objects.active = path
path.select_set(True)
bpy.ops.object.convert(target='CURVE')
#bpy.context.object.hide_viewport = True
bpy.context.object.hide_set(True)
bpy.context.object.data.path_duration = int(data["frames"])
bpy.context.scene.frame_end = int(data["frames"])
print("script: animation path set")


#apply to camera
cam=bpy.data.objects["Camera"]
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cam
cam.select_set(True)
bpy.ops.object.rotation_clear(clear_delta=False)
bpy.ops.object.location_clear(clear_delta=False)
bpy.ops.object.constraint_add(type='FOLLOW_PATH')
bpy.context.object.constraints["Follow Path"].target = path
override={'constraint': cam.constraints["Follow Path"]}
bpy.ops.constraint.followpath_path_animate(override,constraint='Follow Path')
bpy.context.object.constraints["Follow Path"].use_curve_follow = True
bpy.ops.transform.rotate(value=1.48353, orient_axis='X', orient_type='LOCAL', orient_matrix=((0.926739, 0.375705, -5.16602e-09), (-0.373651, 0.921672, -0.104428), (-0.039234, 0.0967774, 0.994532)), orient_matrix_type='LOCAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
print("script: camera applied")


#add estaca labels
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
for pt, est, azi in zip(data["points"], data['estacas'], data['azi']):
    bpy.ops.object.text_add(enter_editmode=False, location=(pt[0], pt[1], pt[2]+15))
    bpy.context.object.data.body = est
    bpy.context.active_object.name = est
    bpy.context.object.data.size = 7.5
    bpy.ops.transform.rotate(value=1.5708, orient_axis='X', orient_type='GLOBAL',
                             orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                             constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False,
                             proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False,
                             use_proportional_projected=False)
    bpy.ops.transform.rotate(value=-radians(float(azi)), orient_axis='Z', orient_type='GLOBAL',
                             orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL',
                             constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False,
                             proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False,
                             use_proportional_projected=False)
print("script: labels added")


#select mesh
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[0]
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
print("script: mesh selected")


#yellow center
toggle()
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.select_all(action='DESELECT')
toggle()
#for v in selverts:
#    v.select = True
for i,pt in enumerate(points):
    v=get_vertex(pt)
    if v:
        v.select = True
        selverts.append(v)
    else:
        print("No vertex at index: ", i)

toggle()
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.bevel(offset=0.1, offset_pct=0, vertex_only=False)
mesh.data.materials.append(eixo)
mesh.active_material_index = 2
bpy.ops.object.material_slot_assign()
toggle()
print("script: eixo colored")


#rendered
my_areas = bpy.context.workspace.screens[0].areas
my_shading = 'RENDERED'  # 'WIREFRAME' 'SOLID' 'MATERIAL' 'RENDERED'
for area in my_areas:
    for space in area.spaces:
        if space.type == 'VIEW_3D':
            space.shading.type = my_shading

print("script: Finished Sucessfully!!")
