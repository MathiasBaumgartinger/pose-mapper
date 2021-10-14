from bpy.types import Constraint, Object
from mathutils import Vector
from enum import Enum
import numpy as np
import bpy
import importlib


spec = importlib.util.spec_from_file_location("module.name", "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/blender/libs/util.py")
util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)


class Joint:
    landmark: Object
    constraint: Constraint
    name: str


    def __init__(self, source_name: str, model: Object) -> None:
        self.model = model
        self.name = source_name
        self.landmark = self.create_landmark()


    def create_landmark(self) -> Object:
        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob

    
    def connect(self, target_name: str):
        self.constraint = self.landmark.constraints.new("TRACK_TO")
        self.constraint.target = self.model.joints[target_name].landmark


class Plain:
    landmark_parent: Object
    joints = dict() 
    
    class Mode(Enum):
        GODOT = 0
        OPENPOSE = 1

    
    def __init__(self, config: dict) -> None:

        #bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.scale = Vector((10, 10, 10))

        for bone_id, connection_id in config.items():
            if not bone_id in self.joints:
                self.joints[bone_id] = Joint(bone_id, self)
                self.joints[bone_id].landmark.parent = self.landmark_parent
            if not connection_id in self.joints:
                self.joints[connection_id] = Joint(connection_id, self)
                self.joints[connection_id].landmark.parent = self.landmark_parent

        for joint_id, joint in self.joints.items():
            if joint_id in config:
                joint.connect(config[joint_id])


    def get_adjustment_vector(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector:
        adjustment_vec = ((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2
        return convert_func(adjustment_vec)


    def find_translation(self, shoulderR: np.array, shoulderL: np.array, convert_func) -> Vector:
        return convert_func((shoulderL + shoulderR) / 2) * 10


    def apply_animation(self, data: dict, MODE: int) -> None:
        current_frame = 0
        for entry in data:
            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    landmark = self.joints[bone_id].landmark
                    if MODE == self.Mode.GODOT.value:
                        landmark.location = util.gd_to_blender(pos) - self.get_adjustment_vector(
                            np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                            np.array(entry["upperleg02.R"]), np.array(entry["upperleg02.L"]),
                            util.gd_to_blender
                        )              
                    elif MODE == self.Mode.OPENPOSE.value:
                        # Find location by the position (different system in blender) minus an adjustment
                        # to the origin
                        adjustment_vec = self.get_adjustment_vector(
                            np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                            np.array(entry["upperleg02.R"]), np.array(entry["upperleg02.L"]),
                            util.mp_to_blender
                        )
                        self.landmark_parent.location = self.find_translation(
                            np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                            util.mp_to_blender
                        )
                        landmark.location = util.mp_to_blender(pos) - adjustment_vec
                        #landmark.location.normalize()
                    
                    self.landmark_parent.keyframe_insert(data_path="location", frame=current_frame)
                    landmark.keyframe_insert(data_path="location", frame=current_frame)                   
            
            current_frame += 1

