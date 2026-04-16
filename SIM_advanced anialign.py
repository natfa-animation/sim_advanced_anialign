# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
import os
from bpy.props import (PointerProperty, StringProperty, BoolProperty, CollectionProperty,
                      IntProperty, IntVectorProperty)
from mathutils import Matrix, Euler
from bpy_extras.io_utils import ImportHelper, ExportHelper
import json

bl_info = {
    "name": "SIM Anialign Enhanced",
    "author": "Sim Sokerov",
    "version": (1, 3, 9),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > SIM Tools",
    "description": "Aligns objects/bones with multiple alignment options and preset support",
    "category": "Animation",
}

# -------------------------- #
# Property and Data Classes  #
# -------------------------- #

class AlignmentPair(bpy.types.PropertyGroup):
    follower_obj: PointerProperty(type=bpy.types.Object)
    follower_bone: StringProperty()
    target_obj: PointerProperty(type=bpy.types.Object)
    target_bone: StringProperty()
    active: BoolProperty(name="Active", default=True, description="Enable or disable this alignment pair")

class SIMAnialignProperties(bpy.types.PropertyGroup):
    alignment_pairs: CollectionProperty(type=AlignmentPair)
    active_pair_index: IntProperty(default=0)
    start_frame: IntProperty(name="Start Frame", default=1, min=1)
    end_frame: IntProperty(name="End Frame", default=100, min=1)
    frame_step: IntProperty(name="Frame Step", default=1, min=1)
    delete_helper: BoolProperty(name="Delete Helper", default=False)
    reverse_direction: BoolProperty(name="Direction", default=False, description="Forward (False) or Backward (True)")

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

# -------------------------- #
# Alignment Operators        #
# -------------------------- #

class SIMAnialignOperator(bpy.types.Operator):
    bl_idname = "object.sim_anialign"
    bl_label = "Run Anialign"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.align_props
        scene = context.scene
        
        # Find a 3D Viewport area for context override (needed for mesh creation)
        view_3d_area = next((area for area in context.screen.areas if area.type == 'VIEW_3D'), None)
        if not view_3d_area:
            self.report({'ERROR'}, "No 3D Viewport found in current screen layout!")
            return {'CANCELLED'}
        
        region = next((region for region in view_3d_area.regions if region.type == 'WINDOW'), None)
        if not region:
            self.report({'ERROR'}, "No valid region found in 3D Viewport!")
            return {'CANCELLED'}
        
        override = context.copy()
        override['area'] = view_3d_area
        override['region'] = region
        override['space_data'] = view_3d_area.spaces.active
        override['scene'] = scene
        override['screen'] = context.screen
        override['window'] = context.window
        override['view_layer'] = context.view_layer

        for pair in props.alignment_pairs:
            if not pair.active:
                continue
            fol_obj = pair.follower_obj
            target_obj = pair.target_obj
            fol_bone = pair.follower_bone
            target_bone = pair.target_bone
            
            if not fol_obj or not target_obj:
                self.report({'ERROR'}, f"Missing follower or target object in pair! Follower: {fol_obj.name if fol_obj else 'None'}, Target: {target_obj.name if target_obj else 'None'}")
                return {'CANCELLED'}
            
            # Deselect all objects without bpy.ops
            for obj in context.view_layer.objects:
                obj.select_set(False)
            fol_obj.select_set(True)
            context.view_layer.objects.active = fol_obj
            
            # Ensure object mode
            if context.mode != 'OBJECT':
                with context.temp_override(**override):
                    bpy.ops.object.mode_set(mode='OBJECT')
            
            # Determine frame range based on direction
            frame_range = range(props.end_frame, props.start_frame - 1, -props.frame_step) if props.reverse_direction else range(props.start_frame, props.end_frame + 1, props.frame_step)
            
            for frame in frame_range:
                scene.frame_set(frame)
                context.view_layer.update()
                
                # Get target matrix
                if target_bone:
                    if target_obj.type != 'ARMATURE':
                        self.report({'ERROR'}, f"Target object '{target_obj.name}' is not an armature but a bone is specified!")
                        return {'CANCELLED'}
                    target = target_obj.pose.bones.get(target_bone)
                    if not target:
                        self.report({'WARNING'}, f"Target bone '{target_bone}' not found in '{target_obj.name}'!")
                        continue
                    target_matrix = target_obj.matrix_world @ target.matrix
                else:
                    target_matrix = target_obj.matrix_world
                
                # Get follower
                if fol_bone:
                    if fol_obj.type != 'ARMATURE':
                        self.report({'ERROR'}, f"Follower object '{fol_obj.name}' is not an armature but a bone is specified!")
                        return {'CANCELLED'}
                    follower = fol_obj.pose.bones.get(fol_bone)
                    if not follower:
                        self.report({'WARNING'}, f"Follower bone '{fol_bone}' not found in '{fol_obj.name}'!")
                        continue
                    follower_matrix = fol_obj.matrix_world.inverted() @ target_matrix
                    follower.matrix = follower_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
                else:
                    follower = fol_obj
                    follower.matrix_world = target_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        self.report({'INFO'}, f"Standard alignment completed for {len([p for p in props.alignment_pairs if p.active])} pairs!")
        return {'FINISHED'}

class SIMAnialignOffsetOperator(bpy.types.Operator):
    bl_idname = "object.sim_anialign_offset"
    bl_label = "Run with Offset"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.align_props
        scene = context.scene
        
        # Find a 3D Viewport area for context override (needed for mesh creation)
        view_3d_area = next((area for area in context.screen.areas if area.type == 'VIEW_3D'), None)
        if not view_3d_area:
            self.report({'ERROR'}, "No 3D Viewport found in current screen layout!")
            return {'CANCELLED'}
        
        region = next((region for region in view_3d_area.regions if region.type == 'WINDOW'), None)
        if not region:
            self.report({'ERROR'}, "No valid region found in 3D Viewport!")
            return {'CANCELLED'}
        
        override = context.copy()
        override['area'] = view_3d_area
        override['region'] = region
        override['space_data'] = view_3d_area.spaces.active
        override['scene'] = scene
        override['screen'] = context.screen
        override['window'] = context.window
        override['view_layer'] = context.view_layer

        # Calculate initial offsets
        initial_offsets = {}
        initial_rot_diffs = {}
        for pair in props.alignment_pairs:
            if not pair.active:
                continue
            fol_obj = pair.follower_obj
            target_obj = pair.target_obj
            fol_bone = pair.follower_bone
            target_bone = pair.target_bone
            
            if not fol_obj or not target_obj:
                self.report({'WARNING'}, f"Skipping pair with missing follower or target! Follower: {fol_obj.name if fol_obj else 'None'}, Target: {target_obj.name if target_obj else 'None'}")
                continue
                
            # Get follower matrix
            if fol_bone:
                if fol_obj.type != 'ARMATURE':
                    self.report({'WARNING'}, f"Follower object '{fol_obj.name}' is not an armature but a bone is specified!")
                    continue
                follower = fol_obj.pose.bones.get(fol_bone)
                if not follower:
                    self.report({'WARNING'}, f"Follower bone '{fol_bone}' not found in '{fol_obj.name}'!")
                    continue
                follower_matrix = fol_obj.matrix_world @ follower.matrix
            else:
                follower_matrix = fol_obj.matrix_world
            
            # Get target matrix
            if target_bone:
                if target_obj.type != 'ARMATURE':
                    self.report({'WARNING'}, f"Target object '{target_obj.name}' is not an armature but a bone is specified!")
                    continue
                target = target_obj.pose.bones.get(target_bone)
                if not target:
                    self.report({'WARNING'}, f"Target bone '{target_bone}' not found in '{target_obj.name}'!")
                    continue
                target_matrix = target_obj.matrix_world @ target.matrix
            else:
                target_matrix = target_obj.matrix_world
            
            # Calculate offsets
            initial_offsets[pair] = follower_matrix.translation - target_matrix.translation
            follower_rot = follower_matrix.to_euler('XYZ')
            target_rot = target_matrix.to_euler('XYZ')
            initial_rot_diffs[pair] = Euler((
                follower_rot.x - target_rot.x,
                follower_rot.y - target_rot.y,
                follower_rot.z - target_rot.z
            ), 'XYZ')
        
        for pair in props.alignment_pairs:
            if not pair.active:
                continue
            fol_obj = pair.follower_obj
            target_obj = pair.target_obj
            fol_bone = pair.follower_bone
            target_bone = pair.target_bone
            
            if not fol_obj or not target_obj:
                self.report({'ERROR'}, f"Missing follower or target object in pair! Follower: {fol_obj.name if fol_obj else 'None'}, Target: {target_obj.name if target_obj else 'None'}")
                return {'CANCELLED'}
            
            # Deselect all objects without bpy.ops
            for obj in context.view_layer.objects:
                obj.select_set(False)
            fol_obj.select_set(True)
            context.view_layer.objects.active = fol_obj
            
            # Ensure object mode
            if context.mode != 'OBJECT':
                with context.temp_override(**override):
                    bpy.ops.object.mode_set(mode='OBJECT')
            
            # Determine frame range based on direction
            frame_range = range(props.end_frame, props.start_frame - 1, -props.frame_step) if props.reverse_direction else range(props.start_frame, props.end_frame + 1, props.frame_step)
            
            for frame in frame_range:
                scene.frame_set(frame)
                context.view_layer.update()
                
                # Get target matrix
                if target_bone:
                    if target_obj.type != 'ARMATURE':
                        self.report({'ERROR'}, f"Target object '{target_obj.name}' is not an armature but a bone is specified!")
                        return {'CANCELLED'}
                    target = target_obj.pose.bones.get(target_bone)
                    if not target:
                        self.report({'WARNING'}, f"Target bone '{target_bone}' not found in '{target_obj.name}'!")
                        continue
                    target_matrix = target_obj.matrix_world @ target.matrix
                else:
                    target_matrix = target_obj.matrix_world
                
                # Apply offset
                offset = initial_offsets.get(pair, None)
                rot_diff = initial_rot_diffs.get(pair, None)
                if offset and rot_diff:
                    target_pos = target_matrix.translation
                    target_rot = target_matrix.to_euler('XYZ')
                    target_matrix = Matrix.Translation(target_pos + offset) @ Euler((
                        target_rot.x + rot_diff.x,
                        target_rot.y + rot_diff.y,
                        target_rot.z + rot_diff.z
                    ), 'XYZ').to_matrix().to_4x4()
                
                # Get follower
                if fol_bone:
                    if fol_obj.type != 'ARMATURE':
                        self.report({'ERROR'}, f"Follower object '{fol_obj.name}' is not an armature but a bone is specified!")
                        return {'CANCELLED'}
                    follower = fol_obj.pose.bones.get(fol_bone)
                    if not follower:
                        self.report({'WARNING'}, f"Follower bone '{fol_bone}' not found in '{fol_obj.name}'!")
                        continue
                    follower_matrix = fol_obj.matrix_world.inverted() @ target_matrix
                    follower.matrix = follower_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
                else:
                    follower = fol_obj
                    follower.matrix_world = target_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        self.report({'INFO'}, f"Offset alignment completed for {len([p for p in props.alignment_pairs if p.active])} pairs!")
        return {'FINISHED'}

class SIMCreateZeObjectOperator(bpy.types.Operator):
    bl_idname = "object.sim_create_ze_object"
    bl_label = "Run 'Like it's linked!'"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.align_props
        scene = context.scene
        
        # Set scene to start_frame or end_frame based on direction
        frame_for_sphere = props.end_frame if props.reverse_direction else props.start_frame
        scene.frame_set(frame_for_sphere)
        context.view_layer.update()
        
        # Find a 3D Viewport area for context override (needed for mesh creation)
        view_3d_area = next((area for area in context.screen.areas if area.type == 'VIEW_3D'), None)
        if not view_3d_area:
            self.report({'ERROR'}, "No 3D Viewport found in current screen layout!")
            return {'CANCELLED'}
        
        region = next((region for region in view_3d_area.regions if region.type == 'WINDOW'), None)
        if not region:
            self.report({'ERROR'}, "No valid region found in 3D Viewport!")
            return {'CANCELLED'}
        
        override = context.copy()
        override['area'] = view_3d_area
        override['region'] = region
        override['space_data'] = view_3d_area.spaces.active
        override['scene'] = scene
        override['screen'] = context.screen
        override['window'] = context.window
        override['view_layer'] = context.view_layer
        
        spheres = {}
        for pair in props.alignment_pairs:
            if not pair.active:
                continue
            fol_obj = pair.follower_obj
            target_obj = pair.target_obj
            fol_bone = pair.follower_bone
            target_bone = pair.target_bone
            
            if not fol_obj or not target_obj:
                self.report({'ERROR'}, f"Missing follower or target object in pair! Follower: {fol_obj.name if fol_obj else 'None'}, Target: {target_obj.name if target_obj else 'None'}")
                return {'CANCELLED'}
            
            # Get follower matrix for position and orientation
            if fol_bone:
                if fol_obj.type != 'ARMATURE':
                    self.report({'ERROR'}, f"Follower object '{fol_obj.name}' is not an armature but a bone is specified!")
                    return {'CANCELLED'}
                follower = fol_obj.pose.bones.get(fol_bone)
                if not follower:
                    self.report({'WARNING'}, f"Follower bone '{fol_bone}' not found in '{fol_obj.name}'!")
                    continue
                follower_matrix = fol_obj.matrix_world @ follower.matrix
            else:
                follower_matrix = fol_obj.matrix_world
            
            # Get target matrix for constraint
            if target_bone:
                if target_obj.type != 'ARMATURE':
                    self.report({'ERROR'}, f"Target object '{target_obj.name}' is not an armature but a bone is specified!")
                    return {'CANCELLED'}
                target = target_obj.pose.bones.get(target_bone)
                if not target:
                    self.report({'WARNING'}, f"Target bone '{target_bone}' not found in '{target_obj.name}'!")
                    continue
                target_matrix = target_obj.matrix_world @ target.matrix
            else:
                target_matrix = target_obj.matrix_world
            
            # Create sphere at follower position with follower orientation
            with context.temp_override(**override):
                if context.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=follower_matrix.translation)
            sphere_obj = context.active_object
            sphere_obj.name = f"{fol_obj.name}_sphere"
            
            # Set sphere orientation to match follower
            sphere_obj.matrix_world = Matrix.Translation(follower_matrix.translation) @ follower_matrix.to_3x3().to_4x4()
            sphere_obj.rotation_mode = 'XYZ'
            
            # Link sphere to target at frame_for_sphere
            child_constraint = sphere_obj.constraints.new(type='CHILD_OF')
            child_constraint.target = target_obj
            if target_bone:
                child_constraint.subtarget = target_bone
            # Set inverse matrix at frame_for_sphere
            child_constraint.inverse_matrix = target_matrix.inverted()
            spheres[pair] = sphere_obj
        
        for pair in props.alignment_pairs:
            if not pair.active:
                continue
            fol_obj = pair.follower_obj
            fol_bone = pair.follower_bone
            
            if not fol_obj:
                self.report({'ERROR'}, f"Missing follower object in pair!")
                return {'CANCELLED'}
            
            # Deselect all objects without bpy.ops
            for obj in context.view_layer.objects:
                obj.select_set(False)
            fol_obj.select_set(True)
            context.view_layer.objects.active = fol_obj
            
            # Ensure object mode
            if context.mode != 'OBJECT':
                with context.temp_override(**override):
                    bpy.ops.object.mode_set(mode='OBJECT')
            
            # Determine frame range based on direction
            frame_range = range(props.end_frame, props.start_frame - 1, -props.frame_step) if props.reverse_direction else range(props.start_frame, props.end_frame + 1, props.frame_step)
            
            for frame in frame_range:
                scene.frame_set(frame)
                context.view_layer.update()
                
                # Get sphere matrix
                sphere = spheres.get(pair)
                if not sphere:
                    continue
                target_matrix = sphere.matrix_world
                
                # Get follower
                if fol_bone:
                    if fol_obj.type != 'ARMATURE':
                        self.report({'ERROR'}, f"Follower object '{fol_obj.name}' is not an armature but a bone is specified!")
                        return {'CANCELLED'}
                    follower = fol_obj.pose.bones.get(fol_bone)
                    if not follower:
                        self.report({'WARNING'}, f"Follower bone '{fol_bone}' not found in '{fol_obj.name}'!")
                        continue
                    follower_matrix = fol_obj.matrix_world.inverted() @ target_matrix
                    follower.matrix = follower_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
                else:
                    follower = fol_obj
                    follower.matrix_world = target_matrix
                    follower.rotation_mode = 'XYZ'
                    follower.keyframe_insert(data_path="location", frame=frame)
                    follower.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Delete helper spheres if requested
        if props.delete_helper:
            for sphere in spheres.values():
                bpy.data.objects.remove(sphere, do_unlink=True)
        
        self.report({'INFO'}, f"Sphere alignment completed for {len([p for p in props.alignment_pairs if p.active])} pairs!")
        return {'FINISHED'}

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

# -------------------------- #
# UI Elements                #
# -------------------------- #

class SIM_UL_AlignmentPairs(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "active", text="")
            left = row.row(align=True)
            left.alignment = 'LEFT'
            left.label(text=f"{item.follower_obj.name if item.follower_obj else 'None'}")
            left.label(text="→")
            left.label(text=f"{item.target_obj.name if item.target_obj else 'None'}")

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
            
            # Follower
            row = box.row(align=True)
            row.label(text="Follower:")
            row.prop(pair, "follower_obj", text="")
            row.operator("object.sim_pick_follower", icon='EYEDROPPER', text="")
            row.operator("object.sim_get_follower_selection", icon='EYEDROPPER', text="")
            
            if pair.follower_obj and pair.follower_obj.type == 'ARMATURE':
                row = box.row(align=True)
                row.prop_search(pair, "follower_bone", pair.follower_obj.pose, "bones", text="Bone")
                row.operator("object.sim_pick_follower_bone", icon='EYEDROPPER', text="")
            
            # Target
            row = box.row(align=True)
            row.label(text="Target:")
            row.prop(pair, "target_obj", text="")
            row.operator("object.sim_pick_target", icon='EYEDROPPER', text="")
            row.operator("object.sim_get_target_selection", icon='EYEDROPPER', text="")
            
            if pair.target_obj and pair.target_obj.type == 'ARMATURE':
                row = box.row(align=True)
                row.prop_search(pair, "target_bone", pair.target_obj.pose, "bones", text="Bone")
                row.operator("object.sim_pick_target_bone", icon='EYEDROPPER', text="")
        
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

# -------------------------- #
# Registration               #
# -------------------------- #

classes = (
    AlignmentPair,
    SIMAnialignProperties,
    SIM_OT_SavePreset,
    SIM_OT_LoadPreset,
    SIM_UL_AlignmentPairs,
    SIM_OT_AddPair,
    SIM_OT_RemovePair,
    SIMAnialignOperator,
    SIMAnialignOffsetOperator,
    SIMCreateZeObjectOperator,
    SIM_OT_ToggleDirection,
    SIM_OT_PickFollower,
    SIM_OT_PickFollowerBone,
    SIM_OT_PickTarget,
    SIM_OT_PickTargetBone,
    SIM_OT_GetFollowerSelection,
    SIM_OT_GetTargetSelection,
    SIMAnialignPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.align_props = PointerProperty(type=SIMAnialignProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.align_props

if __name__ == "__main__":
    register()
