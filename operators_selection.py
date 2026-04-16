# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
from bpy.props import EnumProperty


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
    bl_property = "bone_name"

    def _bone_items(self, context):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return []
        pair = props.alignment_pairs[props.active_pair_index]

        arm_obj = None
        if pair.follower_obj and pair.follower_obj.type == 'ARMATURE':
            arm_obj = pair.follower_obj
        elif context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE':
            arm_obj = context.active_object

        if not arm_obj:
            return []

        return [(b.name, b.name, "") for b in arm_obj.pose.bones]

    bone_name: EnumProperty(name="Bone", items=_bone_items)
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return {'FINISHED'}

        pair = props.alignment_pairs[props.active_pair_index]

        # In Pose Mode, set both the armature and the bone (existing behavior).
        if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE' and context.active_pose_bone:
            pair.follower_obj = context.active_object
            pair.follower_bone = context.active_pose_bone.name
            return {'FINISHED'}

        # Otherwise, only set the bone if follower_obj is already an armature (existing behavior).
        if pair.follower_obj and pair.follower_obj.type == 'ARMATURE' and self.bone_name:
            pair.follower_bone = self.bone_name
        return {'FINISHED'}

    def invoke(self, context, event):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return {'CANCELLED'}

        pair = props.alignment_pairs[props.active_pair_index]

        # If the active pose bone is available, assign immediately (practical picker behavior).
        if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE' and context.active_pose_bone:
            pair.follower_obj = context.active_object
            pair.follower_bone = context.active_pose_bone.name
            return {'FINISHED'}

        if not (pair.follower_obj and pair.follower_obj.type == 'ARMATURE'):
            return {'CANCELLED'}

        if pair.follower_bone:
            self.bone_name = pair.follower_bone
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


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
    bl_property = "bone_name"

    def _bone_items(self, context):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return []
        pair = props.alignment_pairs[props.active_pair_index]

        arm_obj = None
        if pair.target_obj and pair.target_obj.type == 'ARMATURE':
            arm_obj = pair.target_obj
        elif context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE':
            arm_obj = context.active_object

        if not arm_obj:
            return []

        return [(b.name, b.name, "") for b in arm_obj.pose.bones]

    bone_name: EnumProperty(name="Bone", items=_bone_items)
    
    def execute(self, context):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return {'FINISHED'}

        pair = props.alignment_pairs[props.active_pair_index]

        # In Pose Mode, set both the armature and the bone (existing behavior).
        if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE' and context.active_pose_bone:
            pair.target_obj = context.active_object
            pair.target_bone = context.active_pose_bone.name
            return {'FINISHED'}

        # Otherwise, only set the bone if target_obj is already an armature (existing behavior).
        if pair.target_obj and pair.target_obj.type == 'ARMATURE' and self.bone_name:
            pair.target_bone = self.bone_name
        return {'FINISHED'}

    def invoke(self, context, event):
        props = context.scene.align_props
        if props.active_pair_index < 0:
            return {'CANCELLED'}

        pair = props.alignment_pairs[props.active_pair_index]

        # If the active pose bone is available, assign immediately (practical picker behavior).
        if context.mode == 'POSE' and context.active_object and context.active_object.type == 'ARMATURE' and context.active_pose_bone:
            pair.target_obj = context.active_object
            pair.target_bone = context.active_pose_bone.name
            return {'FINISHED'}

        if not (pair.target_obj and pair.target_obj.type == 'ARMATURE'):
            return {'CANCELLED'}

        if pair.target_bone:
            self.bone_name = pair.target_bone
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}


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

                # If target is an armature, auto-fill a default bone (closest to the follower object)
                # only when the bone field is currently empty (manual override remains possible).
                if (
                    pair.target_obj
                    and pair.target_obj.type == 'ARMATURE'
                    and not pair.target_bone
                    and pair.follower_obj
                ):
                    follower_loc = pair.follower_obj.matrix_world.translation
                    best_bone_name = None
                    best_dist_sq = None
                    for pose_bone in pair.target_obj.pose.bones:
                        bone_world_loc = pair.target_obj.matrix_world @ pose_bone.head
                        dist_sq = (bone_world_loc - follower_loc).length_squared
                        if best_dist_sq is None or dist_sq < best_dist_sq:
                            best_dist_sq = dist_sq
                            best_bone_name = pose_bone.name
                    if best_bone_name:
                        pair.target_bone = best_bone_name
        return {'FINISHED'}
