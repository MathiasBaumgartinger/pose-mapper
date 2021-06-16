import math
import numpy as np
from mathutils import Euler
from mathutils import Quaternion


def angleZ(vec0, vec1, bias=0):
    dividend = (vec0[0] * vec1[0] + vec0[1] * vec1[1])
    divisor = np.linalg.norm(vec0[:2]) * np.linalg.norm(vec1[:2])
    return math.acos((dividend + 0.00001) / (divisor + 0.00001)) + bias


def angleY(vec0, vec1, bias=0):
    dividend = (vec0[0] * vec1[0] + vec0[2] * vec1[2])
    divisor = np.linalg.norm(np.array([vec0[0], vec0[2]])) * np.linalg.norm(np.array([vec1[0], vec1[2]]))
    return math.acos((dividend + 0.00001) / (divisor + 0.00001)) + bias


def angleX(vec0, vec1, bias=0):
    dividend = (vec0[1] * vec1[1] + vec0[2] * vec1[2])
    divisor = np.linalg.norm(vec0[1:]) * np.linalg.norm(vec1[1:])
    return math.acos((dividend + 0.00001) / (divisor + 0.00001)) + bias


def z_angles(vec0, vec1, bias: np.array = np.array([0,0,0]), side: chr = "r") -> Euler:
    if side=="r":
        return Euler((0, 0, math.pi + angleZ(vec0, vec1, bias[2])))
    else:
        return Euler((0, 0, angleZ(vec0, vec1, bias[2])))


def angles(vec0, vec1, bias: np.array = np.array([0,0,0]), side: chr = "r") -> Euler:
    if side=="r":
        return Euler((0, 0, -angleZ(vec0, vec1, bias[2])))
    else:
        return Euler((0, 0, angleZ(vec0, vec1, bias[2])))


def orthogonal(vec):
    x = abs(vec[0])
    y = abs(vec[1])
    z = abs(vec[2])

    other = np.array(
        ([1,0,0] if x < z else [0,0,1]) if x < y else ([0,1,0] if y < z else [0,0,1])  
    )
    return np.cross(vec, other)


def normalized(vec):
    return  vec / np.sqrt(np.sum(vec**2)) 


def quaternion_angle(vec0, vec1, bias, side):
    k_cos_theta = np.dot(vec0, vec1)
    k = math.sqrt(np.linalg.norm(vec0) ** 2 * np.linalg.norm(vec1) ** 2)

    if k_cos_theta / k == -1:
        return Quaternion((np.insert(normalized(orthogonal(vec0)), 0, 0)))

    return Quaternion((np.insert(np.cross(vec0, vec1), 0, k_cos_theta + k))) + Euler((bias)).to_quaternion()