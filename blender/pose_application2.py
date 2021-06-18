import bpy
import json
import numpy as np
import math
from mathutils import Vector
from enum import Enum

class Mode(Enum):
    GODOT = 0
    OPENPOSE = 1

MODE = Mode.OPENPOSE
NUM_ITERATIONS = 10
data_path = "pose.json"

prefix = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/output/" if MODE == Mode.OPENPOSE else "C:/Users/Mathias/Documents/tester/"
with open(prefix+data_path, "rt") as file:
    data_dict = json.loads(file.read())


connections = {	
    "upperleg01.R": "lowerleg01.R", 
    "upperleg01.L": "lowerleg01.L",
    
    "lowerleg01.R": "foot.R",
    "upperleg01.L": "foot.L",

	"shoulder01.R": "lowerarm01.R",
	"shoulder01.L": "lowerarm01.L",
	
	"lowerarm01.L":	"wrist.L",
	"lowerarm01.R": "wrist.R"
}


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
    return Vector((vec[0], vec[2] * 0.5, -vec[1]))


def prepare(identifier, bias: np.array = np.array([0,0,0])):
    if not identifier in bpy.data.objects["Standard"].pose.bones:
        return None, None
    
    bone = bpy.data.objects["Standard"].pose.bones[identifier]
    landmark = create_or_get_sphere(identifier)
    #landmark.animation_data_clear()
    
    return bone, landmark


# Makehuman creates bones on each side with <id>.<R/L>, 
# points cannot be stored in json => add if required
def add_point_in_id(id: str):
    if id[len(id) - 1] == "R" or id[len(id) - 1] == "L":
        return id[:len(id) - 1] + "." + id[len(id) - 1:]
    return id

landmarks = {}

def do_multiple():
    if MODE == Mode.OPENPOSE:
        bpy.data.objects["Standard"].location = Vector((0.65, 0.04, -0.93))
        bpy.data.objects["Standard"].rotation_euler = Vector((0, math.radians(-17.9), 0))
        bpy.data.objects["Standard"].scale = Vector((0.04, 0.04, 0.04))
    elif MODE == Mode.GODOT:
        bpy.data.objects["Standard"].location = Vector((0, 0, 0.15))
        bpy.data.objects["Standard"].scale = Vector((0.072, 0.072, 0.072))
    
    for landmark in landmarks:
        landmark.animation_data_clear()

    for bone_id in data_dict["bones"]:
        if "spine" in bone_id or "neck" in bone_id: continue
        current_bone, landmark = prepare(add_point_in_id(bone_id))

        if current_bone == None: continue

        landmark.scale = Vector((0.02, 0.02, 0.02))
        landmarks[add_point_in_id(bone_id)] = landmark
    
    # Store multiple frames and take average -> smoother
    keyframe_arrays = {}
    for bone_id, connection_id in connections.items():
        bone = bpy.data.objects["Standard"].pose.bones[bone_id]
        bone_constraint = bone.constraints.new("DAMPED_TRACK")
        bone_constraint.target = landmarks[connection_id]
        # Init
        keyframe_arrays[bone_id] = np.zeros((1, 3))

    current_frame = 0
    i = 0
    for entry in data_dict["poses"]:
        for bone_id, pos in entry.items():
            bone_id = add_point_in_id(bone_id)
            if not bone_id in keyframe_arrays: continue
        
            keyframe_arrays[bone_id] = np.vstack((keyframe_arrays[bone_id], np.array(pos)))

            if i == NUM_ITERATIONS:
                keyframe_arrays[bone_id] = keyframe_arrays[bone_id][1:,:]
                landmark = get_sphere(bone_id)
                if landmark != None:
                    if MODE == Mode.GODOT:
                        landmark.location = gd_to_blender(np.mean(keyframe_arrays[bone_id]),axis=0)                  
                    elif MODE == Mode.OPENPOSE:
                        landmark.location = op_to_blender(np.mean(keyframe_arrays[bone_id], axis=0))                  
                    
                    landmark.keyframe_insert(data_path="location", frame=current_frame)
                    keyframe_arrays[bone_id] = np.zeros((1, 3))
                
                i = 0
        
            i += 1
            current_frame += 1


def do():
    if MODE == Mode.OPENPOSE:
        bpy.data.objects["Standard"].location = Vector((0.65, 0.04, -0.93))
        bpy.data.objects["Standard"].rotation_euler = Vector((0, math.radians(-17.9), 0))
        bpy.data.objects["Standard"].scale = Vector((0.04, 0.04, 0.04))
    elif MODE == Mode.GODOT:
        bpy.data.objects["Standard"].location = Vector((0, 0, 0.15))
        bpy.data.objects["Standard"].scale = Vector((0.072, 0.072, 0.072))

    for landmark in landmarks:
        landmark.animation_data_clear()

    for bone_id in data_dict["bones"]:
        if "spine" in bone_id or "neck" in bone_id: continue
        current_bone, landmark = prepare(add_point_in_id(bone_id))

        if current_bone == None: continue

        landmark.scale = Vector((0.02, 0.02, 0.02))
        landmarks[add_point_in_id(bone_id)] = landmark

    for bone_id, connection_id in connections.items():
        bone = bpy.data.objects["Standard"].pose.bones[bone_id]
        bone_constraint = bone.constraints.new("DAMPED_TRACK")
        bone_constraint.target = landmarks[connection_id]

    current_frame = 0
    for entry in data_dict["poses"]:
        for bone_id, pos in entry.items():
            bone_id = add_point_in_id(bone_id)
        
            landmark = get_sphere(bone_id)
            if landmark != None:
                if MODE == Mode.GODOT:
                    landmark.location = gd_to_blender(pos)                  
                elif MODE == Mode.OPENPOSE:
                    landmark.location = op_to_blender(pos)                  
                
                landmark.keyframe_insert(data_path="location", frame=current_frame)                
        
            current_frame += 1


do()