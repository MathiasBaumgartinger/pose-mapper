from mathutils import Vector


def gd_to_blender(vec) -> Vector:
    return Vector((-vec[0], vec[2], vec[1]))


# For some reason the z-axis (vec[2]) from mediapipe has way too much impact, thus dividing by 4
def mp_to_blender(vec) -> Vector:
    return Vector((vec[0], vec[2] / 4, -vec[1]))