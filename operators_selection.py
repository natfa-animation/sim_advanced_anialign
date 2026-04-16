# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy


class SIM_OT_ToggleDirection(bpy.types.Operator):
    bl_idname = "object.sim_toggle_direction"
    bl_label = ""
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.align_props
        props.reverse_direction = not props.reverse_direction
        return {'FINISHED'}

    @classmethod
    def description(cls, context, properties):
        props = context.scene.align_props
        return "Backward" if props.reverse_direction else "Forward"


class SIM_OT_PickFollower(bpy.types.Operator):
    bl_idname = "object.sim_pick_follower"
    bl_label = "Pick Follower"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0:
            pair = props.alignment_pairs[props.active_pair_index]
            pair.follower_obj = context.active_object
            if pair.follower_obj and pair.follower_obj.type != 'ARMATURE':
                pair.follower_bone = ""
        return {'FINISHED'}


class SIM_OT_PickFollowerBone(bpy.types.Operator):
    bl_idname = "object.sim_pick_follower_bone"
    bl_label = "Pick Follower Bone"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0 and context.active_pose_bone:
            pair = props.alignment_pairs[props.active_pair_index]
            # In Pose Mode, set both the armature and the bone
            if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE':
                pair.follower_obj = context.active_object
                pair.follower_bone = context.active_pose_bone.name
            else:
                # Otherwise, only set the bone if follower_obj is already an armature
                if pair.follower_obj and pair.follower_obj.type == 'ARMATURE':
                    pair.follower_bone = context.active_pose_bone.name
        return {'FINISHED'}


class SIM_OT_PickTarget(bpy.types.Operator):
    bl_idname = "object.sim_pick_target"
    bl_label = "Pick Target"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0:
            pair = props.alignment_pairs[props.active_pair_index]
            pair.target_obj = context.active_object
            if pair.target_obj and pair.target_obj.type != 'ARMATURE':
                pair.target_bone = ""
        return {'FINISHED'}


class SIM_OT_PickTargetBone(bpy.types.Operator):
    bl_idname = "object.sim_pick_target_bone"
    bl_label = "Pick Target Bone"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0 and context.active_pose_bone:
            pair = props.alignment_pairs[props.active_pair_index]
            # In Pose Mode, set both the armature and the bone
            if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE':
                pair.target_obj = context.active_object
                pair.target_bone = context.active_pose_bone.name
            else:
                # Otherwise, only set the bone if target_obj is already an armature
                if pair.target_obj and pair.target_obj.type == 'ARMATURE':
                    pair.target_bone = context.active_pose_bone.name
        return {'FINISHED'}


class SIM_OT_GetFollowerSelection(bpy.types.Operator):
    bl_idname = "object.sim_get_follower_selection"
    bl_label = "Get Sel."
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0:
            pair = props.alignment_pairs[props.active_pair_index]
            if context.active_object:
                pair.follower_obj = context.active_object
                if context.active_pose_bone and pair.follower_obj.type == 'ARMATURE':
                    pair.follower_bone = context.active_pose_bone.name
                else:
                    pair.follower_bone = ""
        return {'FINISHED'}


class SIM_OT_GetTargetSelection(bpy.types.Operator):
    bl_idname = "object.sim_get_target_selection"
    bl_label = "Get Sel."
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index >= 0:
            pair = props.alignment_pairs[props.active_pair_index]
            if context.active_object:
                pair.target_obj = context.active_object
                if context.active_pose_bone and pair.target_obj.type == 'ARMATURE':
                    pair.target_bone = context.active_pose_bone.name
                else:
                    pair.target_bone = ""
        return {'FINISHED'}

