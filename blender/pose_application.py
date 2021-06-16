import bpy
import json
import numpy as np
import os
import sys
from mathutils import Euler
from mathutils import Vector
from mathutils import Quaternion
from enum import Enum
import importlib

import angles as a
importlib.reload(a)

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

class Mode(Enum):
    QUAT = 0
    EULER_ANGLE_Z = 1
    EULER_ANGLES = 2
    
MODE = Mode.EULER_ANGLE_Z
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
    
    if MODE == Mode.EULER_ANGLES:
        bone.rotation_euler = a.angles(vec0, vec1, bias, side)
        bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
    elif MODE == Mode.EULER_ANGLE_Z:
        bone.rotation_euler = a.z_angles(vec0, vec1, bias, side)
        bone.keyframe_insert(data_path="rotation_euler", frame=current_frame)
    elif MODE == Mode.QUAT:
        bone.rotation_quaternion =  a.quaternion_angle(vec0, vec1, bias, side)
        bone.keyframe_insert(data_path="rotation_quaternion", frame=current_frame)


def prepare(identifier, bias: np.array = np.array([0,0,0])):
    bpy.data.objects["Standard"].data.bones[identifier].use_inherit_rotation = False
    bone = bpy.data.objects["Standard"].pose.bones[identifier]
    if MODE == Mode.EULER_ANGLES:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0 + bias[0], 0 + bias[1], 0 + bias[2]), "XYZ")
    elif MODE == Mode.EULER_ANGLE_Z:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler = Euler((0 + bias[0], 0 + bias[1], 0 + bias[2]), "XYZ")
    elif MODE == Mode.QUAT:
        bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = Quaternion((1,0,0,0))

    return bone


def do_single_frame():
    current_frame = 0

    head = prepare("neck03")

    l_shoulder = prepare("shoulder01.L",    np.array([0,0,-0.55]))
    l_elbow = prepare("lowerarm01.L",       np.array([-0.5,-0.3,-0.45]))
    l_wrist = prepare("wrist.L",            np.array([-0.5,-0.3,-0.45]))

    r_shoulder = prepare("shoulder01.R", np.array([0,0,0.55]))
    r_elbow = prepare("lowerarm01.R",    np.array([-0.5,0.3,0.45]))
    r_wrist = prepare("wrist.R",         np.array([-0.5,0.3,0.45]))

    head_vec = []

    l_shoulder_elbow_vec = []
    l_elbow_wrist_vec = []
    l_wrist_hand_vec = []

    r_shoulder_elbow_vec = []
    r_elbow_wrist_vec = []
    r_wrist_hand_vec = []


    i = 0
    for entry in data_dict:
        head_vec = np.array(entry["neck03"])
        
        spine_vec = np.array(entry["spine01"]) - np.array(entry["spine05"])
        
        l_spine_shoulder_vec = np.array(entry["shoulder01L"]) - np.array(entry["spine01"])
        l_shoulder_elbow_vec = (np.array(entry["shoulder01L"]) - np.array(entry["lowerarm01L"]))
        l_elbow_wrist_vec = (np.array(entry["lowerarm01L"]))
        
        r_spine_shoulder_vec = np.array(entry["shoulder01R"]) - np.array(entry["spine01"])
        r_shoulder_elbow_vec = (np.array(entry["shoulder01R"]) - np.array(entry["lowerarm01R"]))
        #r_shoulder_elbow_vec[0] = -r_shoulder_elbow_vec[0]
        r_elbow_wrist_vec = np.array(entry["lowerarm01R"]) - np.array(entry["wristR"])
        
        create_keyframe(current_frame, head, head_vec, spine_vec)
            
        create_keyframe(current_frame, l_shoulder, l_spine_shoulder_vec, l_shoulder_elbow_vec)#, np.array([0,0,-0.55]), "l")
        create_keyframe(current_frame, l_elbow, l_shoulder_elbow_vec, l_elbow_wrist_vec)#, np.array([-0.5,-0.3,-0.45]), "l")

        create_keyframe(current_frame, r_shoulder, r_shoulder_elbow_vec, r_spine_shoulder_vec, side="r")#, np.array([0,0,0.55]), "r")
        create_keyframe(current_frame, r_elbow, r_shoulder_elbow_vec, r_elbow_wrist_vec)#, np.array([-0.5,0.3,0.45]), "r")
        current_frame += 1

def do_multiple_frames():
    current_frame = 0

    head = prepare("neck03")

    l_shoulder = prepare("shoulder01.L",    np.array([0,0,-0.55]))
    l_elbow = prepare("lowerarm01.L",       np.array([-0.5,-0.3,-0.45]))
    l_wrist = prepare("wrist.L",            np.array([-0.5,-0.3,-0.45]))

    r_shoulder = prepare("shoulder01.R", np.array([0,0,0.55]))
    r_elbow = prepare("lowerarm01.R",    np.array([-0.5,0.3,0.45]))
    r_wrist = prepare("wrist.R",         np.array([-0.5,0.3,0.45]))

    head_vec = []

    l_shoulder_elbow_vec = []
    l_elbow_wrist_vec = []
    l_wrist_hand_vec = []

    r_shoulder_elbow_vec = []
    r_elbow_wrist_vec = []
    r_wrist_hand_vec = []


    i = 0
    for entry in data_dict:
        head_vec.append(np.array(entry["LeftEar"]) - np.array(entry["RightEar"]))
        
        spine_vec = np.array(entry["Nose"]) + np.array([0, 1, 0])
    
        l_shoulder_elbow_vec.append(np.array(entry["LeftShoulder"]) - np.array(entry["LeftElbow"]))
        l_elbow_wrist_vec.append(np.array(entry["LeftWrist"]) - np.array(entry["LeftElbow"]))
        l_wrist_hand_vec.append((np.array(entry["LeftIndex"]) + np.array(entry["LeftPinky"])) / 2 - np.array(entry["LeftWrist"]) )
    
        r_shoulder_elbow_vec.append(np.array(entry["RightElbow"]) - np.array(entry["RightShoulder"]))
        r_elbow_wrist_vec.append(np.array(entry["RightWrist"]) - np.array(entry["RightElbow"]))
        r_wrist_hand_vec.append((np.array(entry["RightIndex"]) + np.array(entry["RightPinky"])) / 2 - np.array(entry["RightWrist"]))

        if i == NUM_ITERATIONS:
            create_keyframe(head, np.mean(head_vec, axis=0), np.array([1,0,0]))
            
            create_keyframe(l_shoulder, -np.mean(l_shoulder_elbow_vec, axis=0), spine_vec, np.array([0,0,-0.55]))
            create_keyframe(l_elbow, np.mean(l_elbow_wrist_vec, axis=0), -np.mean(l_shoulder_elbow_vec, axis=0), np.array([-0.5,-0.3,-0.45]))
            create_keyframe(l_wrist, np.mean(l_wrist_hand_vec, axis=0), np.mean(l_elbow_wrist_vec, axis=0), [0, 0, 0])

            create_keyframe(r_shoulder, np.mean(r_shoulder_elbow_vec, axis=0), spine_vec,  [0, 0, 0.4])
            create_keyframe(r_elbow, np.mean(r_elbow_wrist_vec, axis=0), np.mean(r_shoulder_elbow_vec, axis=0), [0, 0, 0.2])
            create_keyframe(r_wrist, np.mean(r_wrist_hand_vec, axis=0), np.mean(r_elbow_wrist_vec, axis=0))

            l_shoulder_elbow_vec.clear()
            l_elbow_wrist_vec.clear()
            l_wrist_hand_vec.clear()
            r_shoulder_elbow_vec.clear()
            r_elbow_wrist_vec.clear()
            r_wrist_hand_vec.clear()

            i = 0
        
        i += 1
        current_frame += 1
        test = Vector((5,0,6))

do_single_frame()