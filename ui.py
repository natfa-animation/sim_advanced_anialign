# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy


# -------------------------- #
# UI Elements                #
# -------------------------- #

class SIM_UL_AlignmentPairs(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "active", text="")
            display_name = (item.custom_name or "").strip()
            if not display_name:
                follower_name = item.follower_obj.name if item.follower_obj else "None"
                target_name = item.target_obj.name if item.target_obj else "None"
                display_name = f"{follower_name} follows {target_name}"
            row.label(text=display_name)


class SIMAnialignPanel(bpy.types.Panel):
    bl_label = "SIM Anialign Enhanced"
    bl_idname = "OBJECT_PT_sim_anialign"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SIM Tools"

    def draw_header(self, context):
        self.layout.label(text="Author: Sim Sokerov")

    def draw(self, context):
        props = context.scene.align_props
        layout = self.layout
        
        # Preset buttons
        row = layout.row()
        row.operator("object.sim_save_preset", icon='FILE_TICK')
        row.operator("object.sim_load_preset", icon='FILE_FOLDER')
        
        # Pairs list
        row = layout.row()
        row.template_list(
            "SIM_UL_AlignmentPairs",
            "",
            props, "alignment_pairs",
            props, "active_pair_index",
            rows=4,
            type='DEFAULT'
        )
        
        col = row.column(align=True)
        col.operator("object.sim_add_pair", icon='ADD', text="")
        col.operator("object.sim_remove_pair", icon='REMOVE', text="")
        
        # Current pair settings
        if props.active_pair_index >= 0 and len(props.alignment_pairs) > props.active_pair_index:
            pair = props.alignment_pairs[props.active_pair_index]
            box = layout.box()
            
            row = box.row(align=True)
            row.prop(pair, "custom_name", text="Name")
            
            # Follower
            row = box.row(align=True)
            row.label(text="Follower:")
            row.prop(pair, "follower_obj", text="")
            row.operator("object.sim_get_follower_selection", text="Get Sel.")
            
            if pair.follower_obj and pair.follower_obj.type == 'ARMATURE':
                row = box.row(align=True)
                row.prop_search(pair, "follower_bone", pair.follower_obj.pose, "bones", text="Bone")
            
            # Target
            row = box.row(align=True)
            row.label(text="Target:")
            row.prop(pair, "target_obj", text="")
            row.operator("object.sim_get_target_selection", text="Get Sel.")
            
            if pair.target_obj and pair.target_obj.type == 'ARMATURE':
                row = box.row(align=True)
                row.prop_search(pair, "target_bone", pair.target_obj.pose, "bones", text="Bone")
        
        # Animation settings
        row = layout.row(align=True)
        row.label(text="Start:")
        row.prop(props, "start_frame", text="")
        row.label(text="End:")
        row.prop(props, "end_frame", text="")
        row.label(text="Step:")
        row.prop(props, "frame_step", text="")
        row.operator("object.sim_toggle_direction", text="Backward" if props.reverse_direction else "Forward")
        
        # Operators
        layout.operator("object.sim_anialign", text="Run Anialign")
        layout.operator("object.sim_anialign_offset", text="Run with Offset")
        row = layout.row(align=True)
        row.operator("object.sim_create_ze_object", text="Run 'Like it's linked!'")
        row.prop(props, "delete_helper", text="Delete Helper")
