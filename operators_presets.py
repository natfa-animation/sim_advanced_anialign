# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
import json


# -------------------------- #
# Preset Operators           #
# -------------------------- #

class SIM_OT_SavePreset(bpy.types.Operator, ExportHelper):
    bl_idname = "object.sim_save_preset"
    bl_label = "Save Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    
    def execute(self, context):
        props = context.scene.align_props
        pairs_data = []
        
        for pair in props.alignment_pairs:
            pair_data = {
                'follower': pair.follower_obj.name if pair.follower_obj else "",
                'follower_bone': pair.follower_bone,
                'target': pair.target_obj.name if pair.target_obj else "",
                'target_bone': pair.target_bone,
                'active': pair.active
            }
            pairs_data.append(pair_data)
        
        preset_data = {
            'pairs': pairs_data,
            'start_frame': props.start_frame,
            'end_frame': props.end_frame,
            'frame_step': props.frame_step,
            'delete_helper': props.delete_helper,
            'reverse_direction': props.reverse_direction
        }
        
        with open(self.filepath, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        self.report({'INFO'}, f"Preset saved to {self.filepath}")
        return {'FINISHED'}


class SIM_OT_LoadPreset(bpy.types.Operator, ImportHelper):
    bl_idname = "object.sim_load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    
    def execute(self, context):
        props = context.scene.align_props
        
        with open(self.filepath, 'r') as f:
            preset_data = json.load(f)
        
        props.alignment_pairs.clear()
        
        for pair_data in preset_data.get('pairs', []):
            new_pair = props.alignment_pairs.add()
            if pair_data['follower']:
                new_pair.follower_obj = bpy.data.objects.get(pair_data['follower'])
            if pair_data['target']:
                new_pair.target_obj = bpy.data.objects.get(pair_data['target'])
            new_pair.follower_bone = pair_data.get('follower_bone', "")
            new_pair.target_bone = pair_data.get('target_bone', "")
            new_pair.active = pair_data.get('active', True)
        
        props.start_frame = preset_data.get('start_frame', 1)
        props.end_frame = preset_data.get('end_frame', 100)
        props.frame_step = preset_data.get('frame_step', 1)
        props.delete_helper = preset_data.get('delete_helper', False)
        props.reverse_direction = preset_data.get('reverse_direction', False)
        
        self.report({'INFO'}, f"Preset loaded from {self.filepath}")
        return {'FINISHED'}

