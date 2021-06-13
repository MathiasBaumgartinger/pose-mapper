import bpy
import json
import math
import numpy as np
from mathutils import Euler

#print(bpy.data.objects["Standard"].name)
#for child in bpy.data.objects["Standard"].pose.bones:
#    print(child.name)


BODY_PARTS = {
    # Head
    "Head": "neck03",

    # Left arm + hand
    "LeftShoulder": "shoulder01.L", "LeftElbow": "lowerarm01.L", "LeftWrist": "wrist.L",
    "LeftPinky": "finger5-1.L", "LeftIndex": "finger2-1.L", "LeftThumb": "finger1-1.L",
    # Right arm + hand
    "RightShoulder": "shoulder01.R", "RightElbow": "lowerarm01.R", "RightWrist": "wrist.R",
    "RightPinky": "finger5-1.R", "RightIndex": "finger2-1.R", "RightThumb": "finger1-1.R",

    # Left foot
    "LeftHip": "upperleg01.L", "LeftKnee": "lowerleg01.L", "LeftAnkle": "foot.L",
    # Right foot
    "RightHip": "upperleg01.R", "RightKnee": "lowerleg01.R", "RightAnkle": "foot.R"
}


with open("C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/output/hal_poses.json", "rt") as file:
    data_dict = json.loads(file.read())


def angleZ(vec0, vec1, bias=0):
    dividend = (vec0[0] * vec1[0] + vec0[1] * vec1[1])
    divisor = np.linalg.norm(vec0[:2]) * np.linalg.norm(vec1[:2])
    return math.acos((dividend + 0.0001) / (divisor + 0.0001)) + bias

def angleY(vec0, vec1, bias=0):
    dividend = (vec0[0] * vec1[0] + vec0[2] * vec1[2])
    divisor = np.linalg.norm(np.array([vec0[0], vec0[2]])) * np.linalg.norm(np.array([vec1[0], vec1[2]]))
    return math.acos((dividend + 0.0001) / (divisor + 0.0001)) + bias


def angleX(vec0, vec1, bias=0):
    dividend = (vec0[1] * vec1[1] + vec0[2] * vec1[2])
    divisor = np.linalg.norm(vec0[1:]) * np.linalg.norm(vec1[1:])
    return math.acos((dividend + 0.0001) / (divisor + 0.0001)) + bias


def angles(vec0, vec1, bias: np.array, side: chr):
    if side=="r":
        return Euler((angleX(vec0, vec1), angleY(vec0, vec1), angleZ(vec0, vec1, bias[2])))
    else:
        return Euler((angleX(vec0, vec1), angleY(vec0, vec1), -angleZ(vec0, vec1, bias[2])))


def create_keyframe(bone, vec0, vec1, bias=[0,0,0], side="r"):
    if vec0.any() == None:
        vec0 = np.array([0,0,1])
        
    if vec1.any() == None:
        vec1 = np.array([0,0,1])
        
    bone.rotation_euler = angles(vec0, vec1, bias, side)
    bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)


def prepare(identifier):
    bpy.data.objects["Standard"].data.bones[identifier].use_inherit_rotation = False
    bone = bpy.data.objects["Standard"].pose.bones[identifier]
    bone.rotation_mode = "XZY"
    bone.rotation_euler = Euler((0, 0, 0), "XZY")
    return bone



current_frame = 0

spine_vec = np.array([0, 1, 0])

head = prepare("neck03")

l_shoulder = prepare("shoulder01.L")
l_elbow = prepare("lowerarm01.L")
l_wrist = prepare("wrist.L")

r_shoulder = prepare("shoulder01.R")
r_elbow = prepare("lowerarm01.R")
r_wrist = prepare("wrist.R")

for entry in data_dict:
    create_keyframe(head,  np.array(entry["LeftEar"]) - np.array(entry["RightEar"]), np.array([1,0,0]))
    
    l_shoulder_elbow_vec = np.array(entry["LeftElbow"]) - np.array(entry["LeftShoulder"])
    create_keyframe(l_shoulder, l_shoulder_elbow_vec, spine_vec, [0, 0, 0], "l")
    l_elbow_wrist_vec = np.array(entry["LeftWrist"]) - np.array(entry["LeftElbow"])
    create_keyframe(l_elbow, l_elbow_wrist_vec, l_shoulder_elbow_vec, [0, 0, 0], "l")
    l_wrist_hand_vec = (np.array(entry["LeftIndex"]) + np.array(entry["LeftPinky"])) / 2 - np.array(entry["LeftWrist"]) 
    create_keyframe(l_wrist, l_wrist_hand_vec, l_elbow_wrist_vec, [0, 0, 0], "l")
    
    r_shoulder_elbow_vec = np.array(entry["RightElbow"]) - np.array(entry["RightShoulder"])
    create_keyframe(r_shoulder, r_shoulder_elbow_vec, spine_vec,  [0, 0, 0])
    r_elbow_wrist_vec = np.array(entry["RightWrist"]) - np.array(entry["RightElbow"])
    create_keyframe(r_elbow, r_elbow_wrist_vec, r_shoulder_elbow_vec, [0, 0, 0])
    r_wrist_hand_vec = (np.array(entry["RightIndex"]) + np.array(entry["RightPinky"])) / 2 - np.array(entry["RightWrist"])
    create_keyframe(r_wrist, r_wrist_hand_vec, r_elbow_wrist_vec)

    current_frame += 2