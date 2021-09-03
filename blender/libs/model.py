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

        bpy.ops.object.empty_add()
        self.base = bpy.context.object
        self.base.name = "Base"
        self.model.parent = self.base

        bpy.ops.object.empty_add()
        self.landmark_rotation = bpy.context.object
        self.landmark_rotation.name = "LandmarkRotation"
        self.landmark_rotation.parent = self.base

        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.name = "Landmarks"
        self.landmark_parent.scale = Vector((10, 10, 10))
        self.landmark_parent.parent = self.landmark_rotation

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
                joint.connect(config[joint_id])

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
        # As the coordinate systems have different orders/signs of coordinates we need
        # to convert the data from our source
        convert_func: Function
        if MODE == self.Mode.GODOT.value:
            convert_func = util.gd_to_blender         
        elif MODE == self.Mode.OPENPOSE.value:
            convert_func = util.mp_to_blender

        for entry in data:
            shoulderR, shoulderL = np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"])
            upperlegR, upperlegL = np.array(entry["upperleg02.R"]), np.array(entry["upperleg02.L"])

            base = (self.find_base(
                shoulderR, shoulderL, upperlegR, upperlegL, convert_func
            ))
            self.base.location = self.find_translation(
                shoulderR, shoulderL, convert_func
            )
            body_center = self.get_body_center(
                shoulderR, shoulderL, upperlegR, upperlegL, convert_func
            )
            #body_center = self.model.matrix_world @ bpy.data.objects["Standard"].pose.bones["spine03"].tail

            base.resize_4x4()
            euler_angles: Euler = base.to_euler()
            euler_angles.x = 0
            self.model.rotation_euler = euler_angles
            # Only to adjust to the rotation of y-axis, otherwise the coordinates should stay true
            self.landmark_rotation.rotation_euler.y = euler_angles.y
            self.landmark_rotation.rotation_euler.x = euler_angles.x

            self.landmark_rotation.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)
            self.model.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)
            self.base.keyframe_insert(data_path="location", frame=self.current_frame)

            self.set_mode(self.BlenderMode.POSE)
            self.landmark_parent.matrix_world.translation = self.model.matrix_world @ bpy.data.objects["Standard"].pose.bones["spine03"].tail
            self.landmark_parent.keyframe_insert(data_path="location", frame=self.current_frame)
            
            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    landmark: Object = self.joints[bone_id].landmark

                    # Find location by the position (different system in blender) minus an adjustment
                    # to the origin
                    landmark.location = convert_func(pos) - body_center
                    landmark.location.normalize()                    
                    landmark.location *= (self.joints[bone_id].bone.head - self.armature.bones["spine03"].matrix_local.translation).length
                    landmark.location /= self.landmark_parent.scale[0]

                    landmark.keyframe_insert(data_path="location", frame=self.current_frame)

            self.current_frame += 1

        #self.last_position = self.base.matrix_world.translation
        #self.last_position.z = 0

