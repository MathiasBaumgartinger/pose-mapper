from typing import Type
from bpy.types import Armature, Function, Object, PoseBone
from mathutils import Euler, Matrix, Vector
from enum import Enum
import numpy as np
import bpy
import copy


class Joint:
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
        if self.name in bpy.data.objects:
            return bpy.data.objects[self.name]

        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob

    
    def target(self, target_name: str) -> None:
        self.constraint.target = self.model.joints[target_name].landmark
    

    def connect(self, target_name: str) -> None:
        constraint = self.landmark.constraints.new("TRACK_TO")
        constraint.target = self.model.joints[target_name].landmark


class Model:
    model: Object
    landmark_parent: Object
    base: Object
    joints = dict() 
    current_frame: int
    current_starting_translation: Vector
    previous_model_matrix: Matrix
    DIST_FACTOR = 20
    FRAMES_BETWEEN_CUT = 5
    
    class Mode(Enum):
        GODOT = 0
        OPENPOSE = 1


    class BlenderMode(Enum):
        OBJECT = 0
        POSE = 1

    
    def __init__(self, config: dict, model: Object, armature: Armature, DIST_FACTOR: float) -> None:
        self.model: Object = model
        self.armature: Armature = armature
        self.current_frame: int = 0
        self.previous_model_matrix = Matrix.Identity(4)
        self.connections = config
        self.DIST_FACTOR = DIST_FACTOR

        self.set_mode(self.BlenderMode.OBJECT)

        if "Landmarks" in bpy.data.objects:
            self.landmark_parent = bpy.data.objects["Landmarks"]
        else:
            bpy.ops.object.empty_add()
            self.landmark_parent = bpy.context.object
            self.landmark_parent.name = "Landmarks"
            self.landmark_parent.scale = Vector((10, 10, 10))

        self.set_connections(config["landmarked"], True)
        self.set_connections(config["rest"], False)

        for joint_id, joint in self.joints.items():
            if joint_id in config["landmarked"]:
                joint.target(config["landmarked"][joint_id])
                joint.connect(config["landmarked"][joint_id])
            elif joint_id in config["rest"]:
                joint.target(config["rest"][joint_id])
            

    def set_connections(self, config: dict, create_landmarks: bool) -> None:
        for bone_id, connection_id in config.items():
            if not bone_id in self.joints:
                self.joints[bone_id] = Joint(bone_id, self, create_landmarks)
                if create_landmarks:
                    self.joints[bone_id].landmark.parent = self.landmark_parent
            if not connection_id in self.joints:
                self.joints[connection_id] = Joint(connection_id, self, create_landmarks)
                if create_landmarks:
                    self.joints[connection_id].landmark.parent = self.landmark_parent
    

    def set_mode(self, b_mode: Enum) -> None:
        self.model.select_set(True)
        bpy.context.view_layer.objects.active = self.model
        if not bpy.context.object.mode == b_mode.name:
            bpy.ops.object.mode_set(mode=b_mode.name, toggle=False)


    def get_body_center(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector:
        return convert_func((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2


    def find_base(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array, convert_func) -> Matrix:
        base_x = ((shoulderL + hipL) / 2 - (shoulderR + hipR) / 2)
        base_z = ((shoulderR + shoulderL) / 2 - (hipR + hipL) / 2)
        base_y = np.cross(base_x, base_z)
        
        base = np.array([
            base_x, base_y, base_z
        ])
                
        return Matrix(base)
     
    
    def find_relative_translation(self, total_translation: Vector, distance_factor: float) -> Vector:
        assert(self.current_starting_translation != None)

        return (total_translation - self.current_starting_translation) * distance_factor


    def reset(self) -> None:
        self.current_frame = 0
        self.previous_model_matrix = Matrix.Identity(4)

        self.model.animation_data_clear()
        self.armature.animation_data_clear()
        for joint in self.joints.values():
            if joint.has_landmark:
                joint.landmark.animation_data_clear()


    def create_or_append_dict(self, dict: dict, key, value) -> None:
        if key in dict:
            dict[key].append(value)
        else:
            dict[key] = []
            dict[key].append(value)


    def apply_animation(self, data: dict, convert_func, AVG_OVER_N: int) -> None:          
        self.current_starting_translation = self.get_body_center(
            np.array(data[0]["shoulder01.R"]), np.array(data[0]["shoulder01.L"]),
            np.array(data[0]["upperleg01.R"]), np.array(data[0]["upperleg01.L"]),
            convert_func
        )
        
        average_over_n_entries = {}
        for i, entry in enumerate(data):
            temp_model: Object = self.model.copy()
            shoulderR, shoulderL = np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"])
            upperlegR, upperlegL = np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"])

            # Find the "spine"-rotation and apply it to the whole model
            base = (self.find_base(
                shoulderR, shoulderL, upperlegR, upperlegL, convert_func
            ))
            base.resize_4x4()
            euler_angles: Euler = base.to_euler()
            euler_angles.x = 0
            self.create_or_append_dict(average_over_n_entries, "euler_angles", euler_angles)
            temp_model.rotation_euler = euler_angles
            #self.model.rotation_euler = euler_angles
            #self.model.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)

            # Find the location of the mid-point between shoulders and hips and apply it to the model
            translation = self.previous_model_matrix.translation + self.find_relative_translation(
                self.get_body_center(shoulderR, shoulderL, upperlegR, upperlegL, convert_func), self.DIST_FACTOR)
            self.create_or_append_dict(average_over_n_entries, "model_location", translation)
            temp_model.location = translation
            #self.model.location = self.previous_model_matrix.translation + self.find_relative_translation(
            #    self.get_body_center(shoulderR, shoulderL, upperlegR, upperlegL, convert_func), self.DIST_FACTOR)
            #self.model.keyframe_insert(data_path="location", frame=self.current_frame)

            # Application of changes (somehow this is necessary so the changes are actually committed)
            self.set_mode(self.BlenderMode.OBJECT)
            self.set_mode(self.BlenderMode.POSE)
            self.set_mode(self.BlenderMode.OBJECT)


            for bone_id, pos in entry.items():
                # Not all bones as defined BODY_PARTS in the preprocessing steps are actually loaded joints
                if bone_id in self.joints:
                    if self.joints[bone_id].has_landmark:
                        landmark: Object = self.joints[bone_id].landmark

                        # Find out whether the bone is targeted by another bone or not
                        keys_as_list = list(self.connections["landmarked"].keys())
                        vals_as_list = list(self.connections["landmarked"].values())
                        targeted_by_id = keys_as_list[vals_as_list.index(bone_id)] if bone_id in vals_as_list else None
                        
                        # If the bone is being targeted, set the landmark position of the landmark such that it is placed
                        # from the targeted (previous) bone to the current bone with the accurate length into the direction that 
                        # the pose-estimator found
                        if targeted_by_id:
                            bone_head_targeted_by = temp_model.matrix_world @ self.joints[targeted_by_id].bone.head
                            bone_head_current = temp_model.matrix_world @ self.joints[bone_id].bone.head

                            direction = convert_func(np.array(pos) - np.array(entry[targeted_by_id]))
                            direction.normalize()

                            #landmark.location = bone_head_targeted_by + direction * (bone_head_targeted_by - bone_head_current).length
                            #landmark.location /= self.landmark_parent.scale[0]
                            self.create_or_append_dict(average_over_n_entries, bone_id, 
                                (bone_head_targeted_by + direction * (bone_head_targeted_by - bone_head_current).length) / self.landmark_parent.scale[0])
                        # Otherwise just set the landmark to the position of the current bone
                        else:
                            #landmark.location = self.model.matrix_world @ self.joints[bone_id].bone.head
                            #landmark.location /= self.landmark_parent.scale[0]
                            self.create_or_append_dict(average_over_n_entries, bone_id, 
                                temp_model.matrix_world @ self.joints[bone_id].bone.head / self.landmark_parent.scale[0])

                        #landmark.keyframe_insert(data_path="location", frame=self.current_frame)
            
            if i % AVG_OVER_N == 0:
                for id, vecs in average_over_n_entries.items():
                    as_array = np.array(list(map(lambda vec: np.array([vec.x / AVG_OVER_N, vec.y / AVG_OVER_N, vec.z / AVG_OVER_N]), vecs)))
                    avg = np.sum(as_array, axis=0) 
                    if id == "euler_angles":
                        self.model.rotation_euler = Euler((avg[0], avg[1], avg[2]))
                        self.model.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)
                    elif id == "model_location":
                        self.model.location = Vector((avg[0], avg[1], avg[2]))
                        self.model.keyframe_insert(data_path="location", frame=self.current_frame)
                    else:
                        landmark: Object = self.joints[id].landmark
                        landmark.location = Vector((avg[0], avg[1], avg[2]))
                        landmark.keyframe_insert(data_path="location", frame=self.current_frame)
                
                average_over_n_entries = {}


            self.current_frame += 1
        
        self.previous_model_matrix = copy.copy(temp_model.matrix_local)