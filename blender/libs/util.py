from mathutils import Vector


def gd_to_blender(vec) -> Vector:
    return Vector((-vec[0], vec[2], vec[1]))


def mp_to_blender(vec) -> Vector:
    #return Vector((vec[0], 0, -vec[1]))
    return Vector((vec[0], vec[2], -vec[1]))