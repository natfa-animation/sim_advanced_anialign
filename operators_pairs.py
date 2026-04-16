# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy


# -------------------------- #
# Additional Operators       #
# -------------------------- #

class SIM_OT_AddPair(bpy.types.Operator):
    bl_idname = "object.sim_add_pair"
    bl_label = "Add Pair"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        props.alignment_pairs.add()
        props.active_pair_index = len(props.alignment_pairs) - 1
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        return {'FINISHED'}


class SIM_OT_RemovePair(bpy.types.Operator):
    bl_idname = "object.sim_remove_pair"
    bl_label = "Remove Pair"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0:
            props.alignment_pairs.remove(props.active_pair_index)
            props.active_pair_index = min(props.active_pair_index, len(props.alignment_pairs) - 1)
        return {'FINISHED'}

