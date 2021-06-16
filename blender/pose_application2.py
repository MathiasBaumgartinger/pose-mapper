import bpy
import json
import numpy as np
from mathutils import Vector


NUM_ITERATIONS = 50

#data_path = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/output/asd.json"
data_path = "C:/Users/Mathias/Documents/tester/asd.json"
with open(data_path, "rt") as file:
    data_dict = json.loads(file.read())


def create_keyframe(current_frame, bone, vec0, vec1, bias=[0,0,0], side="r"):
    if vec0.any() == None:
        return
        
    if vec1.any() == None:
        return


def create_or_get_sphere(name):
    for ob in bpy.context.scene.objects:
        if ob.name == name:
            return ob

    bpy.ops.surface.primitive_nurbs_surface_sphere_add()

    ob = bpy.context.object
    ob.name = name

    return ob


def np_to_blender(vec):
    return Vector((vec[0], vec[2], vec[1]))


def prepare(identifier, bias: np.array = np.array([0,0,0])):
    bone = bpy.data.objects["Standard"].pose.bones[identifier]
    landmark = create_or_get_sphere(identifier)

    return bone, landmark

# Makehuman creates bones on each side with <id>.<R/L>, 
# points cannot be stored in json => add if required
def add_point_in_id(id: str):
    if id[len(id) - 1] == "R" or id[len(id) - 1] == "L":
        return id[:len(id) - 1] + "." + id[len(id) - 1:]
    return id


def do_single_frame():
    current_frame = 0

    head, head_landmark = prepare("neck03")

    l_shoulder, l_shoulder_landmark = prepare("shoulder01.L")
    l_elbow, l_elbow_landmark = prepare("lowerarm01.L")
    l_wrist, l_wrist_landmark = prepare("wrist.L")

    r_shoulder, r_shoulder_landmark = prepare("shoulder01.R")
    r_elbow, r_elbow_landmark = prepare("lowerarm01.R")
    r_wrist, r_wrist_landmark = prepare("wrist.R")

    entry = data_dict[0]
    
    head_pos = np_to_blender(np.array(entry["neck03"]))
    head_landmark.location = head_pos
    spine_pos05 = np_to_blender(np.array(entry["spine05"]))
    spine_pos01 = np_to_blender(np.array(entry["spine01"]))

    l_shoulder_pos = np_to_blender(np.array(entry["shoulder01L"]))
    l_shoulder_landmark.location = l_shoulder_pos 

    l_elbow_pos = np_to_blender(np.array(entry["lowerarm01L"]))
    l_elbow_landmark.location = l_elbow_pos
    l_wrist_pos = np_to_blender(np.array(entry["wristL"]))
    l_wrist_landmark.location = l_wrist_pos

    r_shoulder_pos = np_to_blender(np.array(entry["shoulder01R"]))
    r_shoulder_landmark.location = r_shoulder_pos 
    r_elbow_pos = np_to_blender(np.array(entry["lowerarm01R"]))
    r_elbow_landmark.location = r_elbow_pos
    r_wrist_pos = np_to_blender(np.array(entry["wristR"]))
    r_wrist_landmark.location = r_wrist_pos
    
    l_shoulder_constraint = l_shoulder.constraints.new("DAMPED_TRACK")
    l_shoulder_constraint.target = r_shoulder_landmark


    i = 0
    for entry in data_dict:
        for bone_id, pos in entry.items():
           current_bone, landmark = prepare(bone_id)
           

        current_frame += 1


def do_multiple_frames():
    current_frame = 0
    
    i += 1
    current_frame += 1

do_single_frame()