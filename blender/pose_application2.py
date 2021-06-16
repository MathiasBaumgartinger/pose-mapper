import bpy
import json
import numpy as np
from mathutils import Vector
from enum import Enum

class Mode(Enum):
    GODOT = 0
    OPENPOSE = 1

MODE = Mode.OPENPOSE
NUM_ITERATIONS = 50

prefix = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/output/" if MODE == Mode.OPENPOSE else "C:/Users/Mathias/Documents/tester/"
data_path = "flex.json"

with open(prefix+data_path, "rt") as file:
    data_dict = json.loads(file.read())


def create_keyframe(current_frame, bone, vec0, vec1, bias=[0,0,0], side="r"):
    if vec0.any() == None:
        return
        
    if vec1.any() == None:
        return


def get_sphere(name):
    for ob in bpy.context.scene.objects:
        if ob.name == name:
            return ob


def create_or_get_sphere(name):
    for ob in bpy.context.scene.objects:
        if ob.name == name:
            return ob

    bpy.ops.surface.primitive_nurbs_surface_sphere_add()

    ob = bpy.context.object
    ob.name = name

    return ob


def gd_to_blender(vec):
    return Vector((-vec[0], vec[2], vec[1]))


def op_to_blender(vec):
    return Vector((vec[0], vec[1], -vec[2]))


def prepare(identifier, bias: np.array = np.array([0,0,0])):
    if not identifier in bpy.data.objects["Standard"].pose.bones:
        return None, None
    
    bone = bpy.data.objects["Standard"].pose.bones[identifier]
    landmark = create_or_get_sphere(identifier)
    #landmark.animation_data_clear()
    print(landmark)
    
    return bone, landmark


# Makehuman creates bones on each side with <id>.<R/L>, 
# points cannot be stored in json => add if required
def add_point_in_id(id: str):
    if id[len(id) - 1] == "R" or id[len(id) - 1] == "L":
        return id[:len(id) - 1] + "." + id[len(id) - 1:]
    return id


def do_single_frame():
    for bone_id in data_dict["bones"]:
        if "spine" in bone_id or "neck" in bone_id: continue
        current_bone, landmark = prepare(add_point_in_id(bone_id))

        if current_bone == None: continue

        landmark.scale = Vector((0.05, 0.05, 0.05))
        bone_constraint = current_bone.constraints.new("DAMPED_TRACK")
        bone_constraint.target = landmark

    current_frame = 0
    for entry in data_dict["poses"]:
        for bone_id, pos in entry.items():
            if "spine" in bone_id or "neck" in bone_id: continue
            
            landmark = get_sphere(add_point_in_id(bone_id))
            if landmark != None:
                if MODE == Mode.GODOT:
                    landmark.location = gd_to_blender(pos)
                elif MODE == Mode.OPENPOSE:
                    landmark.location = op_to_blender(pos)
                
                landmark.keyframe_insert(data_path="location", frame=current_frame)

        current_frame += 1


def do_multiple_frames():
    current_frame = 0
    
    i += 1
    current_frame += 1

do_single_frame()