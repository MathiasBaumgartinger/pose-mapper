from bpy.types import Object
from mathutils import Vector
import numpy as np
import bpy


class Joint:
    """
    A class used for referencing a PoseBone from Blender,
    it's landmark visualization which represents the estimated 
    position and the ("TRACK-TO") bone-constraint which 
    targets the landmark. This is a light version of the Joint 
    class in "model.py"

    ...

    Attributes
    ----------
    landmark: Object
        A plain blender sphere representing the estimated position,
        targeted by the constraint
    name: str
        The name of the joint
    constraint: Object
        The ("DAMPED-TRACK") bone-constraint targeting the landmark
    has_landmark: bool
        Indicates whether this particular joint has a landmark, only 
        certain joints are landmarked

    Methods
    -------
    create_landmark(self) -> Object
        Creates a primitive_nurbs_surface_sphere visualizing the estimated position
    connect(self, target_name: str) -> None
        Connects landmarks using the ("TRACK_TO")-constraint.
        Just a visual representation, such that the landmarks are accurately 
        connected with a blue line (easier debugging)
    """
    landmark: Object
    name: str
    constraint: Object

    def __init__(self, name: str) -> None:
        """
        Parameters
        ----------
        name: str
            The name of the joint
        create_landmark: bool = True
            Indicates whether this particular joint has a landmark, only 
            certain joints are landmarked
        """
        self.name = name
        self.landmark = self.create_landmark()

    def create_landmark(self) -> Object:
        """
        Creates a primitive_nurbs_surface_sphere visualizing the estimated position
        """
        bpy.ops.surface.primitive_nurbs_surface_sphere_add()
        ob = bpy.context.object
        ob.name = self.name
        ob.scale = Vector((0.02, 0.02, 0.02))
        return ob
    

    def connect(self, joints, target_name: str) -> None:
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
        constraint.target = joints[target_name].landmark


class Plain:
    """
    A class used for simple visualizations of the actual data from the pose-estimator

    ...

    Attributes
    ----------
    landmark_parent: Object
        All landmarks have a common parent which are inherently transformed by it
    joints: dict
        The dictionary containing all available joints of the model

    Methods
    -------
    create_joints(self, config: dict, create_landmarks: bool) -> None
        Creates joints according to the config
    get_body_center(self, shoulderR: np.array, shoulderL: np.array, hipR: np.array, hipL: np.array, convert_func) -> Vector
        Get the center of the estimated body by an average of right/left shoulder/hip
    find_translation(self, shoulderR: np.array, shoulderL: np.array, convert_func) -> Vector
        Find the absolute translation depending on the shoulders
    apply_animation(self, data: dict, convert_func, AVG_OVER_N: int) -> None
        Apply the estimated coordinates to the model
    """
    landmark_parent: Object
    joints = dict() 

    
    def __init__(self, connections: dict) -> None:
        bpy.ops.object.empty_add()
        self.landmark_parent = bpy.context.object
        self.landmark_parent.scale = Vector((10, 10, 10))

        # Only certain connections will be visualized with a landmark
        self.create_joints(connections["landmarked"])

        for joint_id, joint in self.joints.items():
            if joint_id in connections["landmarked"]:
                joint.connect(self.joints, connections["landmarked"][joint_id])
            

    def create_joints(self, config: dict) -> None:
        """
        Creates joints according to the config

        Parameters
        ----------
        config: dict
            Key->value pairs (bone->targeted_bone)
        """
        for bone_id, connection_id in config.items():
            if not bone_id in self.joints:
                self.joints[bone_id] = Joint(bone_id)
                self.joints[bone_id].landmark.parent = self.landmark_parent
            if not connection_id in self.joints:
                self.joints[connection_id] = Joint(connection_id)
                self.joints[connection_id].landmark.parent = self.landmark_parent


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
        adjustment_vec = ((shoulderR + shoulderL) / 2 + (hipR + hipL) / 2) / 2
        return convert_func(adjustment_vec)


    def find_translation(self, shoulderR: np.array, shoulderL: np.array, convert_func) -> Vector:
        """
        Find the absolute translation depending on the shoulders

        Parameters
        ----------
        shoulderR: np.array
            Estimated position for the right shoulder
        shoulderL: np.array
            Estimated position for the left shoulder
        convert_func: function
            The XYZ-format of pose-estimators might be different than blender,
            provide a conversion function
        """
        return convert_func((shoulderL + shoulderR) / 2)


    def apply_animation(self, data: dict, convert_func) -> None:
        """
        Apply the estimated coordinates to the model

        Parameters
        ----------
        data: dict
            The data preprocessed by the mp_pose_preprocess.py script
        convert_func: function
            The XYZ-format of pose-estimators might be different than blender,
            provide a conversion function
        """   
        current_frame = 0
        for entry in data:
            for bone_id, pos in entry.items():
                if bone_id in self.joints:
                    landmark = self.joints[bone_id].landmark

                    # Find location by the position (different system in blender) minus an adjustment
                    # to the origin
                    adjustment_vec = self.get_body_center(
                        np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                        np.array(entry["upperleg01.R"]), np.array(entry["upperleg01.L"]),
                        convert_func
                    )
                    self.landmark_parent.location = self.find_translation(
                        np.array(entry["shoulder01.R"]), np.array(entry["shoulder01.L"]),
                        convert_func
                    )
                    landmark.location = convert_func(pos) - adjustment_vec
                    #landmark.location.normalize()
                    
                    self.landmark_parent.keyframe_insert(data_path="location", frame=current_frame)
                    landmark.keyframe_insert(data_path="location", frame=current_frame)                   
            
            current_frame += 1

