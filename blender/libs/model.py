from typing import Collection
from bpy.types import AdjustmentSequence, Armature, Object
from mathutils import Vector
from enum import Enum
import numpy as np
import bpy


class Joint:
    #transform: np.array
    landmark: Object
    name: str
    bone: Object
    constraint: Object


    def __init__(self, source_name: str, model: Object) -> None:
        self.model = model
        self.name = source_name
        self.bone = model.model.pose.bones[source_name]
        self.landmark = self.create_landmark()
        self.constraint = self.bone.constraints.new("DAMPED_TRACK")


    def create_landmark(self) -> Object:
        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.5, 0.5, 0.5))
        return ob

    
    def target(self, target_name: str):
        self.constraint.target = self.model.joints[target_name].landmark


class Model:
    model: Object
    landmark_parent: Object
    joints = dict() 
    
    class Mode(Enum):
        GODOT = 0
        OPENPOSE = 1

    
    def __init__(self, config: dict, model: Object, armature: Armature) -> None:
        self.model = model

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.location = Vector((0, 0, armature.bones['spine03'].matrix_local.translation.z))
        self.landmark_parent.parent = self.model

        for bone_id, connection_id in config.items():
            if not bone_id in self.joints:
                self.joints[bone_id] = Joint(bone_id, self)
                self.joints[bone_id].landmark.parent = self.landmark_parent
            if not connection_id in self.joints:
                self.joints[connection_id] = Joint(connection_id, self)
                self.joints[connection_id].landmark.parent = self.landmark_parent

        for joint_id, joint in self.joints.items():
            if joint_id in config:
                joint.target(config[joint_id])


    def gd_to_blender(self, vec) -> Vector:
        return Vector((-vec[0], vec[2], vec[1]))


    def op_to_blender(self, vec) -> Vector:
        return Vector((vec[0], vec[2] * 0.5, -vec[1]))


    def get_adjustment_vector(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector:
        adjustment_vec = ((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2
        return convert_func(adjustment_vec)


    def apply_animation(self, data: dict, MODE: int) -> None:
        current_frame = 0
        for entry in data:
            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    landmark = self.joints[bone_id].landmark
                    if MODE == self.Mode.GODOT.value:
                        landmark.location = self.gd_to_blender(pos) - self.get_adjustment_vector(
                            np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                            np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"]),
                            self.gd_to_blender
                        )              
                    elif MODE == self.Mode.OPENPOSE.value:
                        # Find location by the position (different system in blender) minus an adjustment
                        # to the origin
                        landmark.location = self.op_to_blender(pos) - self.get_adjustment_vector(
                            np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                            np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"]),
                            self.op_to_blender
                        )
                        landmark.location.normalize()
                    
                    landmark.keyframe_insert(data_path="location", frame=current_frame)                
            
            current_frame += 1

