from bpy.types import Armature, Function, Object
from mathutils import Matrix, Vector
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
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob

    
    def target(self, target_name: str):
        self.constraint.target = self.model.joints[target_name].landmark


class Model:
    model: Object
    landmark_parent: Object
    base: Object
    joints = dict() 
    
    class Mode(Enum):
        GODOT = 0
        OPENPOSE = 1

    
    def __init__(self, config: dict, model: Object, armature: Armature) -> None:
        self.model = model

        #bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.empty_add()
        self.base = bpy.context.object
        self.base.name = "Base"
        self.model.parent = self.base

        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.name = "Landmarks"
        self.landmark_parent.location = Vector((0, 0, armature.bones['spine03'].matrix_local.translation.z))
        self.landmark_parent.scale = Vector((10, 10, 10))
        self.landmark_parent.parent = self.base

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


    def get_adjustment_vector(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector:
        adjustment_vec = ((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2
        return convert_func(adjustment_vec)


    def find_basis(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array, convert_func) -> Matrix:
        base_x = (shoulderL - shoulderR)
        base_z = ((shoulderR + shoulderL) / 2 - (hipR + hipL) / 2)
        base_y = np.cross(base_x, base_z)
        
        base = np.array([
            base_x, base_y, base_z
        ])
                
        #base = Matrix((convert_func(base[0]), convert_func(base[1]), convert_func(base[2])))
        #base.resize_4x4()
        return base
    
    
    def find_translation(self, shoulderR: np.array, shoulderL: np.array, convert_func) -> Vector:
        return convert_func((shoulderL + shoulderR) / 2) * 20


    def apply_animation(self, data: dict, MODE: int) -> None:
        current_frame = 0

        convert_func: Function
        if MODE == self.Mode.GODOT.value:
                        convert_func = util.gd_to_blender         
        elif MODE == self.Mode.OPENPOSE.value:
            convert_func = util.mp_to_blender

        for entry in data:
            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    landmark: Object = self.joints[bone_id].landmark

                    all_bases = []
                    # Find location by the position (different system in blender) minus an adjustment
                    # to the origin
                    all_bases.append(self.find_basis(
                        np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                        np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"]),
                        convert_func
                    ))
                    self.base.location = self.find_translation(
                        np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                        convert_func
                    )
                    landmark.location = convert_func(pos) - self.get_adjustment_vector(
                        np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                        np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"]),
                        convert_func
                    )
                    landmark.location.normalize()
                    
                    #self.model.keyframe_insert(data_path="rotation_euler", frame=current_frame)
                    landmark.keyframe_insert(data_path="location", frame=current_frame)
                    self.base.keyframe_insert(data_path="location", frame=current_frame)

            avg_base = np.sum(all_bases, axis=0) / (len(data) * len(data[0]))
            print(avg_base)
            avg_base = Matrix((convert_func(avg_base[0]), convert_func(avg_base[1]), convert_func(avg_base[2])))
            avg_base.resize_4x4()
            self.model.rotation_euler = avg_base.to_euler()

            current_frame += 1

