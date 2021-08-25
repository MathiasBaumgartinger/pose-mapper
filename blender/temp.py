import bpy


bpy.data.objects['Landmarks'].location = bpy.data.objects["Standard"].location + bpy.data.objects["Standard"].pose.bones["spine03"].tail

