import bpy
import json
import numpy as np
import math
from mathutils import Vector
from enum import Enum
import importlib.util

spec = importlib.util.spec_from_file_location("module.name", "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/blender/libs/model.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Mode(Enum):
    GODOT = 0
    OPENPOSE = 1

MODE = Mode.OPENPOSE
NUM_ITERATIONS = 10
data_path = "pose.json"

prefix = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/output/" if MODE == Mode.OPENPOSE else "C:/Users/Mathias/Documents/tester/"
with open(prefix+data_path, "rt") as file:
    data_dict = json.loads(file.read())


connections = {	
    "upperleg01.R": "lowerleg01.R", 
    "upperleg01.L": "lowerleg01.L",
    
    "lowerleg01.R": "foot.R",
    "upperleg01.L": "foot.L",

	"shoulder01.R": "lowerarm01.R",
	"shoulder01.L": "lowerarm01.L",
	
	"lowerarm01.L":	"wrist.L",
	"lowerarm01.R": "wrist.R"
}

data = data_dict["poses"]

model1 = m.Model(connections, bpy.data.objects["Standard"])
model1.apply_animation(data, MODE.value)