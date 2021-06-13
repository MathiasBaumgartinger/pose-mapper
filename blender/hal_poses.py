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


with open("C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/blender/hal_poses.json", "rt") as file:
    data_dict = json.loads(file.read())


def angleZ(vec0, vec1):
    dividend = (vec0[0] * vec1[0] + vec0[1] * vec1[1])
    divisor = (np.linalg.norm(vec0[:2]) * np.linalg.norm(vec1[:2]))
    return math.acos(dividend / divisor)

def angleY(vec0, vec1):
    dividend = (vec0[0] * vec1[0] + vec0[2] * vec1[2])
    divisor = (np.linalg.norm(vec0[1,2]) * np.linalg.norm(vec1[1,2]))
    return math.acos(dividend / divisor)

def angleX(vec0, vec1):
    dividend = (vec0[2] * vec1[2] + vec0[1] * vec1[1])
    divisor = (np.linalg.norm(vec0[1:3]) * np.linalg.norm(vec1[1:3]))
    return math.acos(dividend / divisor)

def angle(vec0, vec1):
    return Euler(angleX(vec0, vec1), angleY(vec0, vec1), angleZ(vec0, vec1))

def prepare(bone):
    bone.rotation_mode = "XZY"
    bone.rotation_euler = Euler((0, 0, 0), "XZY")
    return bone


bones = bpy.data.objects["Standard"].pose.bones
current_frame = 0

spine_vec = np.array([0, 1, 0])

head = prepare(bones["neck03"])

l_shoulder = prepare(bones["shoulder01.L"])
l_elbow = prepare(bones["lowerarm01.L"])
l_wrist = prepare(bones["wrist.L"])

r_shoulder = prepare(bones["shoulder01.R"])
r_elbow = prepare(bones["lowerarm01.R"])
r_wrist = prepare(bones["wrist.R"])

for entry in data_dict:
    head_vec = np.array(entry["LeftEar"]) - np.array(entry["RightEar"])
    head_angle = angleZ(head_vec, np.array([1,0,0]))
    head.rotation_euler = Euler((0, 0, head_angle))
    head.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    l_shoulder_elbow_vec = np.array(entry["LeftElbow"]) - np.array(entry["LeftShoulder"])
    l_shoulder_angle = angleZ(l_shoulder_elbow_vec, spine_vec) 
    l_shoulder.rotation_euler = Euler((0, 0, -l_shoulder_angle))
    l_shoulder.keyframe_insert(data_path="rotation_euler", frame=current_frame)
    
    l_elbow_wrist_vec = np.array(entry["LeftWrist"]) - np.array(entry["LeftElbow"])
    l_elbow_angle = angleZ(l_elbow_wrist_vec, l_shoulder_elbow_vec) 
    l_elbow.rotation_euler = Euler((0, 0, -l_elbow_angle))
    l_elbow.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    l_wrist_hand_vec = (np.array(entry["LeftIndex"]) + np.array(entry["LeftPinky"])) / 2 - np.array(entry["LeftWrist"]) 
    l_wrist_angle = angleZ(l_wrist_hand_vec, l_elbow_wrist_vec)
    l_wrist.rotation_euler = Euler((0, 0, l_wrist_angle))
    l_wrist.keyframe_insert(data_path="rotation_euler", frame=current_frame)  
    
    r_shoulder_elbow_vec = np.array(entry["RightElbow"]) - np.array(entry["RightShoulder"])
    r_shoulder_angle = angleZ(r_shoulder_elbow_vec, spine_vec)
    r_shoulder.rotation_euler = Euler((0, 0, r_shoulder_angle))
    r_shoulder.keyframe_insert(data_path="rotation_euler", frame=current_frame)
    
    r_elbow_wrist_vec = np.array(entry["RightWrist"]) - np.array(entry["RightElbow"])
    r_elbow_angle = angleZ(r_elbow_wrist_vec, r_shoulder_elbow_vec)
    r_elbow.rotation_euler = Euler((0, 0, r_elbow_angle))
    r_elbow.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    r_wrist_hand_vec = (np.array(entry["RightIndex"]) + np.array(entry["RightPinky"])) / 2 - np.array(entry["RightWrist"])
    r_wrist_angle = angleZ(r_wrist_hand_vec, r_elbow_wrist_vec)
    r_wrist.rotation_euler = Euler((0, 0, r_wrist_angle))
    r_wrist.keyframe_insert(data_path="rotation_euler", frame=current_frame)

    current_frame += 2