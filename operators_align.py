# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
from mathutils import Matrix, Euler


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

