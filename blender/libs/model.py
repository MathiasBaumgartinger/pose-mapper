from bpy.types import Armature, Function, Object, PoseBone
from mathutils import Euler, Matrix, Vector
from enum import Enum
import numpy as np
import bpy
import importlib

spec = importlib.util.spec_from_file_location("module.name", "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/blender/libs/util.py")
util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)


class Joint:
    #transform: np.array
    landmark: Object
    name: str
    bone: PoseBone
    constraint: Object
    has_landmark: bool


    def __init__(self, source_name: str, model: Object, create_landmark: bool = True) -> None:
        self.model = model
        self.name = source_name
        self.bone = model.model.pose.bones[source_name]
        self.has_landmark = create_landmark
        if create_landmark:
            self.landmark = self.create_landmark()
        self.constraint = self.bone.constraints.new("DAMPED_TRACK")


    def create_landmark(self) -> Object:
        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob

    
    def target(self, target_name: str):
        self.constraint.target = self.model.joints[target_name].landmark
    

    def connect(self, target_name: str):
        constraint = self.landmark.constraints.new("TRACK_TO")
        constraint.target = self.model.joints[target_name].landmark


class Model:
    model: Object
    landmark_parent: Object
    landmark_rotation: Object
    base: Object
    joints = dict() 
    current_frame: int
    last_position: Vector
    
    class Mode(Enum):
        GODOT = 0
        OPENPOSE = 1


    class BlenderMode(Enum):
        OBJECT = 0
        POSE = 1

    
    def __init__(self, config: dict, model: Object, armature: Armature) -> None:
        self.model: Object = model
        self.armature: Armature = armature
        self.current_frame: int = 0
        self.last_position = Vector((0,0,0))
        self.connections = config

        self.set_mode(self.BlenderMode.OBJECT)

        #bpy.ops.object.empty_add()
        #self.base = bpy.context.object
        #self.base.name = "Base"
        #self.model.parent = self.base
#
        #bpy.ops.object.empty_add()
        #self.landmark_rotation = bpy.context.object
        #self.landmark_rotation.name = "LandmarkRotation"
        #self.landmark_rotation.parent = self.base

        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.name = "Landmarks"
        self.landmark_parent.scale = Vector((10, 10, 10))
        #self.landmark_parent.parent = self.landmark_rotation

        self.set_connections(config["landmarked"], True)
        self.set_connections(config["rest"], False)

        for joint_id, joint in self.joints.items():
            if joint_id in config["landmarked"]:
                joint.target(config["landmarked"][joint_id])
                joint.connect(config["landmarked"][joint_id])
            elif joint_id in config["rest"]:
                joint.target(config["rest"][joint_id])
            

    def set_connections(self, config: dict, create_landmarks: bool):
        for bone_id, connection_id in config.items():
            if not bone_id in self.joints:
                self.joints[bone_id] = Joint(bone_id, self, create_landmarks)
                if create_landmarks:
                    self.joints[bone_id].landmark.parent = self.landmark_parent
            if not connection_id in self.joints:
                self.joints[connection_id] = Joint(connection_id, self, create_landmarks)
                if create_landmarks:
                    self.joints[connection_id].landmark.parent = self.landmark_parent
    

    def set_mode(self, b_mode: Enum):
        self.model.select_set(True)
        bpy.context.view_layer.objects.active = self.model
        if not bpy.context.object.mode == b_mode.name:
            bpy.ops.object.mode_set(mode=b_mode.name, toggle=False)


    def get_body_center(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector:
        adjustment_vec = ((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2
        return convert_func(adjustment_vec)


    def find_base(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array, convert_func) -> Matrix:
        base_x = ((shoulderL + hipL) / 2 - (shoulderR + hipR) / 2)
        base_z = ((shoulderR + shoulderL) / 2 - (hipR + hipL) / 2)
        base_y = np.cross(base_x, base_z)
        
        base = np.array([
            base_x, base_y, base_z
        ])
                
        return Matrix(base)
     
    
    def find_translation(self, shoulderR: np.array, shoulderL: np.array, convert_func) -> Vector:
        return convert_func((shoulderL + shoulderR) / 2) * 20


    def reset(self):
        self.current_frame = 0


    def apply_animation(self, data: dict, MODE: int) -> None:
        convert_func: Function
        if MODE == self.Mode.GODOT.value:
            convert_func = util.gd_to_blender         
        elif MODE == self.Mode.OPENPOSE.value:
            convert_func = util.mp_to_blender
        
        for entry in data:
            
            shoulderR, shoulderL = np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"])
            upperlegR, upperlegL = np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"])

            base = (self.find_base(
                shoulderR, shoulderL, upperlegR, upperlegL, convert_func
            ))
            current_location = self.find_translation(
                shoulderR, shoulderL, convert_func
            )

            base.resize_4x4()
            euler_angles: Euler = base.to_euler()
            euler_angles.x = 0
            self.model.rotation_euler = euler_angles
            self.model.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)

            self.model.location = current_location
            self.model.keyframe_insert(data_path="location", frame=self.current_frame)
            self.set_mode(self.BlenderMode.OBJECT)
            self.set_mode(self.BlenderMode.POSE)
            self.set_mode(self.BlenderMode.OBJECT)

            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    if self.joints[bone_id].has_landmark:
                        landmark: Object = self.joints[bone_id].landmark

                        # Find location by the position (different system in blender) minus an adjustment
                        # to the origin
                        keys_as_list = list(self.connections["landmarked"].keys())
                        vals_as_list = list(self.connections["landmarked"].values())
                        targeted_by_id = keys_as_list[vals_as_list.index(bone_id)] if bone_id in vals_as_list else None
                        
                        if targeted_by_id:
                            bone_head_targeted_by = self.model.matrix_world @ self.joints[targeted_by_id].bone.head
                            bone_head_current = self.model.matrix_world @ self.joints[bone_id].bone.head

                            direction = convert_func(np.array(pos) - np.array(entry[targeted_by_id]))
                            direction.normalize()

                            landmark.location = bone_head_targeted_by + direction * (bone_head_targeted_by - bone_head_current).length
                            landmark.location /= self.landmark_parent.scale[0]
                        else:
                            landmark.location = self.model.matrix_world @ self.joints[bone_id].bone.head
                            landmark.location /= self.landmark_parent.scale[0]

                        landmark.keyframe_insert(data_path="location", frame=self.current_frame)

            self.current_frame += 1