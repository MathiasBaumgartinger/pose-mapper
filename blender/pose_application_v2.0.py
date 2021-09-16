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

spec2 = importlib.util.spec_from_file_location("module.name", "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/blender/libs/plain.py")
p = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(p)

class Mode(Enum):
    GODOT = 0
    OPENPOSE = 1

MODE = Mode.OPENPOSE
NUM_ITERATIONS = 10
data_paths = ["pose.json", "sit_down.json"]# ,
data_dicts = []
for path in data_paths:
    prefix = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/preprocess/output/" if MODE == Mode.OPENPOSE else "C:/Users/Mathias/Documents/tester/"
    with open(prefix+path, "rt") as file:
        data_dicts.append(json.loads(file.read()))


connections = {
    "landmarked": {
        "lowerarm01.L":	"wrist.L",
	    "lowerarm01.R": "wrist.R",

        "shoulder01.R": "lowerarm01.R",
        "shoulder01.L": "lowerarm01.L",
        
        "lowerleg01.R": "foot.R",
        "lowerleg01.L": "foot.L",

        "upperleg01.R": "lowerleg01.R", 
        "upperleg01.L": "lowerleg01.L", 
    },

    "rest": {
        "upperleg02.R": "lowerleg01.R",
        "upperleg02.L": "lowerleg01.L",

        "lowerleg02.R": "foot.R",
        "lowerleg02.L": "foot.L",

        "upperarm02.R": "lowerarm01.R",
        "upperarm01.R": "lowerarm01.R",
        "upperarm02.L": "lowerarm01.L",
        "upperarm01.L": "lowerarm01.L",

        "lowerarm02.L":	"wrist.L",
	    "lowerarm02.R": "wrist.R",
    }
}

model1 = m.Model(connections, bpy.data.objects["Standard"], bpy.data.armatures["Standard"])
for data_dict in data_dicts: 
    data = data_dict["poses"]

    model1.test(data, MODE.value)

    #plain = p.Plain(connections)
    #plain.apply_animation(data, MODE.value)