from typing import Type
from bpy.types import Armature, Function, Object, PoseBone
from mathutils import Euler, Matrix, Vector
from enum import Enum
import numpy as np
import bpy
import copy


class Joint:
    """
    A class used for referencing a PoseBone from Blender,
    it's landmark visualization which represents the estimated 
    position and the ("DAMPED-TRACK") bone-constraint which 
    targets the landmark

    ...

    Attributes
    ----------
    landmark: Object
        A plain blender sphere representing the estimated position,
        targeted by the constraint
    model: Object
        A reference to the model the bone belongs to
    name: str
        The name of the joint
    bone: PoseBone
        The according posebone inside the blender environment
    constraint: Object
        The ("DAMPED-TRACK") bone-constraint targeting the landmark
    has_landmark: bool
        Indicates whether this particular joint has a landmark, only 
        certain joints are landmarked

    Methods
    -------
    create_landmark(self) -> Object
        Creates a primitive_nurbs_surface_sphere visualizing the estimated position
    target(self, target_name: str) -> None
         Apply the ("DAMPED_TRACK") constraint to the wished target object
    connect(self, target_name: str) -> None
        Connects landmarks using the ("TRACK_TO")-constraint.
        Just a visual representation, such that the landmarks are accurately 
        connected with a blue line (easier debugging)
    """

    landmark: Object
    model: Object
    name: str
    bone: PoseBone
    constraint: Object
    has_landmark: bool


    def __init__(self, name: str, model: Object, create_landmark: bool = True) -> None:
        """
        Parameters
        ----------
        name: str
            The name of the joint
        model: Object
            A reference to the model the bone belongs to
        create_landmark: bool = True
            Indicates whether this particular joint has a landmark, only 
            certain joints are landmarked
        """
        self.model = model
        self.name = name
        self.bone = model.model.pose.bones[name]
        self.has_landmark = create_landmark
        if create_landmark:
            self.landmark = self.create_landmark()
        self.constraint = self.bone.constraints.new("DAMPED_TRACK")


    def create_landmark(self) -> Object:
        """
        Creates a primitive_nurbs_surface_sphere visualizing the estimated position
        """
        # If an animation has already been applied the objects will be here
        if self.name in bpy.data.objects:
            return bpy.data.objects[self.name]

        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob

    
    def target(self, target_name: str) -> None:
        """
        Apply the ("DAMPED_TRACK") constraint to the wished target object

        Parameters
        ----------
        target_name: str
            The name of the joint the constraint should be targeted at
        """
        self.constraint.target = self.model.joints[target_name].landmark
    

    def connect(self, target_name: str) -> None:
        """
        Connects landmarks using the ("TRACK_TO")-constraint.
        Just a visual representation, such that the landmarks are accurately 
        connected with a blue line (easier debugging)

        Parameters
        ----------
        target_name: str
            The name of the joint the constraint should be targeted at
        """
        constraint = self.landmark.constraints.new("TRACK_TO")
        constraint.target = self.model.joints[target_name].landmark


class Model:
    """
    A class used for referencing and applying/managing estimated animation to the Model
    inside the Blender environment.

    ...

    Attributes
    ----------
    model: Object
        A reference to the model the animations should be applied
    armature: Armature
        A reference to the armature the animations should be applied
    landmark_parent: Object
        All landmarks have a common parent which are inherently transformed by it
    joints: dict
        The dictionary containing all available joints of the model
    connections: dict
        All landmarked and non-landmarked key and value pairs where key->value represents
        bone->targeted-bone
    current_frame: int
        The current key_frame the animation is at
    current_starting_translation: Vector
        Since the application of successive sequences is possible, there needs to be a
        starting translation for the current sequence for a fluid transition
    previous_model_matrix: Matrix
        Since the application of successive sequences is possible, there needs to be a
        previous model matrix for the current sequence for a fluid transition
    DIST_FACTOR: float
        The factor the translation in the pose-estimated screen (0-1) is multiplied with

    Methods
    -------
    create_joints(self, config: dict, create_landmarks: bool) -> None
        Creates joints according to the config
    set_mode(self, b_mode: Enum) -> None
        Sets the current blender mode
    get_body_center(self, shoulderR, shoulderL, hipR, hipL, convert_func) -> Vector
        Get the center of the estimated body by an average of right/left shoulder/hip
    find_base(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array) -> Matrix
        Find the base of the estimated body by an average of right/left shoulder/hip as matrix
    find_relative_translation(self, total_translation: Vector, distance_factor: float) -> Vector
        Find the relative translation depending on the current_starting_translation
    reset(self) -> None
        Reset the animation of the model and reset the current_frame/previous_model_matrix 
    apply_animation(self, data: dict, convert_func, AVG_OVER_N: int) -> None
        Apply the estimated coordinates to the model
    """
    model: Object
    armature: Armature
    landmark_parent: Object
    joints = dict() 
    connections: dict
    current_frame: int
    current_starting_translation: Vector
    previous_model_matrix: Matrix
    DIST_FACTOR: float


    class BlenderMode(Enum):
        """
        Enum for identifying the current Blender Mode
        """
        OBJECT = 0
        POSE = 1

    
    def __init__(self, connections: dict, model: Object, armature: Armature, DIST_FACTOR: float) -> None:
        """
        Parameters
        ----------
        connections: dict
            All landmarked and non-landmarked key and value pairs where key->value represents
            bone->targeted-bone
        model: Object
            A reference to the model the animations should be applied
        armature: Armature
            A reference to the armature the animations should be applied
        DIST_FACTOR: float
            The factor the translation in the pose-estimated screen-space (0-1) is multiplied with
        """
        self.model: Object = model
        self.armature: Armature = armature
        self.current_frame: int = 0
        self.previous_model_matrix = Matrix.Identity(4)
        self.connections = connections
        self.DIST_FACTOR = DIST_FACTOR

        self.set_mode(self.BlenderMode.OBJECT)

        # If an animation has already been applied the objects will be here
        if "Landmarks" in bpy.data.objects:
            self.landmark_parent = bpy.data.objects["Landmarks"]
        else:
            bpy.ops.object.empty_add()
            self.landmark_parent = bpy.context.object
            self.landmark_parent.name = "Landmarks"
            self.landmark_parent.scale = Vector((10, 10, 10))

        # Only certain connections will be visualized with a landmark, others
        # just need the blender constraint
        self.create_joints(connections["landmarked"], True)
        self.create_joints(connections["rest"], False)

        for joint_id, joint in self.joints.items():
            if joint_id in connections["landmarked"]:
                joint.target(connections["landmarked"][joint_id])
                joint.connect(connections["landmarked"][joint_id])
            elif joint_id in connections["rest"]:
                joint.target(connections["rest"][joint_id])
            

    def create_joints(self, config: dict, create_landmarks: bool) -> None:
        """
        Creates joints according to the config

        Parameters
        ----------
        config: dict
            Key->value pairs (bone->targeted_bone)
        create_landmarks: bool
            Indicates whether landmarks should be created for the joints or not
        """
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
        """
        Sets the current blender mode

        Parameters
        ----------
        b_mode: Enum
            An enum for the mode
        """
        self.model.select_set(True)
        bpy.context.view_layer.objects.active = self.model
        if not bpy.context.object.mode == b_mode.name:
            bpy.ops.object.mode_set(mode=b_mode.name, toggle=False)

    
    def get_body_center(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array, convert_func) -> Vector:
        """
        Get the center of the estimated body by an average of right/left shoulder/hip

        Parameters
        ----------
        shoulderR: np.array
            Estimated position for the right shoulder
        shoulderL: np.array
            Estimated position for the left shoulder
        hipR: np.array
            Estimated position for the right hip
        hipL: np.array
            Estimated position for the left hip
        convert_func: function
            The XYZ-format of pose-estimators might be different than blender,
            provide a conversion function
        """
        return convert_func((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2


    def find_base(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array) -> Matrix:
        """
        Find the base of the estimated body by an average of right/left shoulder/hip as matrix

        Parameters
        ----------
        shoulderR: np.array
            Estimated position for the right shoulder
        shoulderL: np.array
            Estimated position for the left shoulder
        hipR: np.array
            Estimated position for the right hip
        hipL: np.array
            Estimated position for the left hip
        """
        base_x = ((shoulderL + hipL) / 2 - (shoulderR + hipR) / 2)
        base_z = ((shoulderR + shoulderL) / 2 - (hipR + hipL) / 2)
        base_y = np.cross(base_x, base_z)
        
        base = np.array([
            base_x, base_y, base_z
        ])
                
        return Matrix(base)
     
    
    def find_relative_translation(self, absolute_translation: Vector, distance_factor: float) -> Vector:
        """
        Find the relative translation depending on the current_starting_translation

        Parameters
        ----------
        absolute_translation: Vector
            The absoulute current translation
        distance_factor: float
            The factor the screen space of the estimator (0-1) is multiplied
        """
        return (absolute_translation - self.current_starting_translation) * distance_factor


    def reset(self) -> None:
        """
        Reset the animation of the model and reset the current_frame/previous_model_matrix 
        """
        self.current_frame = 0
        self.previous_model_matrix = Matrix.Identity(4)

        self.model.animation_data_clear()
        self.armature.animation_data_clear()
        for joint in self.joints.values():
            if joint.has_landmark:
                joint.landmark.animation_data_clear()


    def apply_animation(self, data: dict, convert_func, AVG_OVER_N: int) -> None: 
        """
        Apply the estimated coordinates to the model

        Parameters
        ----------
        data: dict
            The data preprocessed by the mp_pose_preprocess.py script
        convert_func: function
            The XYZ-format of pose-estimators might be different than blender,
            provide a conversion function
        AVG_OVER_N: int
            Identifies how many estimated frames are averaged over
        """         
        self.current_starting_translation = self.get_body_center(
            np.array(data[0]["shoulder01.R"]), np.array(data[0]["shoulder01.L"]),
            np.array(data[0]["upperleg01.R"]), np.array(data[0]["upperleg01.L"]),
            convert_func
        )
        
        average_over_n_entries = {}
        for i, entry in enumerate(data):
            shoulderR, shoulderL = np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"])
            upperlegR, upperlegL = np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"])

            # Find the "spine"-rotation and apply it to the whole model
            base = (self.find_base(
                shoulderR, shoulderL, upperlegR, upperlegL
            ))
            base.resize_4x4()
            euler_angles: Euler = base.to_euler()
            euler_angles.x = 0
            average_over_n_entries.setdefault("euler_angles",[]).append(euler_angles)

            # Find the location of the mid-point between shoulders and hips and apply it to the model
            translation = self.find_relative_translation(
                self.get_body_center(shoulderR, shoulderL, upperlegR, upperlegL, convert_func), self.DIST_FACTOR)
            average_over_n_entries.setdefault("model_location",[]).append(translation)

            for bone_id, pos in entry.items():
                # Not all bones as defined BODY_PARTS in the preprocessing steps are actually loaded joints
                if bone_id in self.joints:
                    if self.joints[bone_id].has_landmark:
                        average_over_n_entries.setdefault(bone_id,[]).append(pos)
            
            # After AVG_OVER_N iterations or the end of the data calculate the avgs and apply them to the model
            if i % AVG_OVER_N == 0 or i == len(data):
                for id, vecs in average_over_n_entries.items():
                    as_avg_array = np.array(list(map(lambda vec: np.array([vec[0] / AVG_OVER_N, vec[1] / AVG_OVER_N, vec[2] / AVG_OVER_N]), vecs)))
                    avg = np.sum(as_avg_array, axis=0) 

                    if id == "euler_angles":
                        self.model.rotation_euler = Euler((avg[0], avg[1], avg[2]))
                        self.model.keyframe_insert(data_path="rotation_euler", frame=self.current_frame)

                        # Application of changes (somehow this is necessary so the changes are actually committed,
                        # necessary for landmark-keyframes)
                        self.set_mode(self.BlenderMode.OBJECT)
                        self.set_mode(self.BlenderMode.POSE)
                        self.set_mode(self.BlenderMode.OBJECT)

                    elif id == "model_location":
                        self.model.location = self.previous_model_matrix.translation + Vector((avg[0], avg[1], avg[2]))
                        self.model.keyframe_insert(data_path="location", frame=self.current_frame)

                        # Application of changes (somehow this is necessary so the changes are actually committed, 
                        # necessary for landmark-keyframes)
                        self.set_mode(self.BlenderMode.OBJECT)
                        self.set_mode(self.BlenderMode.POSE)
                        self.set_mode(self.BlenderMode.OBJECT)

                    else:
                        landmark: Object = self.joints[id].landmark

                        # Find out whether the bone is targeted by another bone or not
                        keys_as_list = list(self.connections["landmarked"].keys())
                        vals_as_list = list(self.connections["landmarked"].values())
                        targeted_by_id = keys_as_list[vals_as_list.index(id)] if id in vals_as_list else None
                        
                        # If the bone is being targeted, set the landmark position of the landmark such that it is placed
                        # from the targeted (previous) bone to the current bone with the accurate length into the direction that 
                        # the pose-estimator found
                        if targeted_by_id:
                            bone_head_targeted_by = self.model.matrix_world @ self.joints[targeted_by_id].bone.head
                            bone_head_current = self.model.matrix_world @ self.joints[id].bone.head

                            targeted_avg_arr = np.array(list(map(
                                lambda vec: np.array([vec[0] / AVG_OVER_N, vec[1] / AVG_OVER_N, vec[2] / AVG_OVER_N]),
                                average_over_n_entries[targeted_by_id])))
                            direction = convert_func(avg - np.sum(targeted_avg_arr, axis=0))
                            direction.normalize()

                            landmark.location = bone_head_targeted_by + direction * (bone_head_targeted_by - bone_head_current).length
                            landmark.location /= self.landmark_parent.scale[0]
                        # Otherwise just set the landmark to the position of the current bone
                        else:
                            landmark.location = self.model.matrix_world @ self.joints[id].bone.head
                            landmark.location /= self.landmark_parent.scale[0]

                        landmark.keyframe_insert(data_path="location", frame=self.current_frame)
                
                average_over_n_entries = {}
            self.current_frame += 1
        
        # Shallow copy is necessary
        self.previous_model_matrix = copy.copy(self.model.matrix_local)