import bpy
import json
from mathutils import Vector
import importlib.util

PATH_PREFIX = "C:/Users/Mathias/Sync/Master/sem2/P1/implementations/pose-estimation/"
DISTANCE_FACTOR = 20
MODEL_NAME = "Standard"
DATA_PATHS = [
            PATH_PREFIX + "preprocess/output/walking.json",
            PATH_PREFIX + "preprocess/output/sit_down_fixed.json", 
            PATH_PREFIX + "preprocess/output/pose.json",
            ]
FRAMES_BETWEEN = [20, 5]
CONNECTIONS = {
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

spec = importlib.util.spec_from_file_location("module.name", PATH_PREFIX + "blender/libs/model.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

spec2 = importlib.util.spec_from_file_location("module.name", PATH_PREFIX + "blender/libs/plain.py")
p = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(p)

spec = importlib.util.spec_from_file_location("module.name", PATH_PREFIX + "blender/libs/util.py")
util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(util)

data_dicts = []
for path in DATA_PATHS:
    with open(path, "rt") as file:
        data_dicts.append(json.loads(file.read()))


model1 = m.Model(CONNECTIONS, bpy.data.objects[MODEL_NAME], bpy.data.armatures[MODEL_NAME], DISTANCE_FACTOR)
model1.reset()
for (i, data_dict) in enumerate(data_dicts): 
    data = data_dict["poses"]

    model1.apply_animation(data, util.mp_to_blender, 10)
    
    if not len(FRAMES_BETWEEN) - 1 < i:
        model1.current_frame += FRAMES_BETWEEN[i]

    #plain = p.Plain(connections)
    #plain.apply_animation(data, MODE.value)