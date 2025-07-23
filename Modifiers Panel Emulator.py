bl_info = {
    "name": "Modifiers Panel Emulator (Complete)",
    "author": "ChatGPT",
    "version": (2, 1),
    "blender": (3, 0, 0),
    "location": "View3D > N-panel > Modifiers",
    "description": "Emulates the complete Modifiers panel from Properties inside the 3D Viewport N-panel with collapse support",
    "category": "3D View",
}

import bpy


def get_collapse_data(obj):
    return obj.get("_modifiers_collapsed", {})


class OBJECT_OT_toggle_modifier_collapse(bpy.types.Operator):
    bl_idname = "object.toggle_modifier_collapse"
    bl_label = "Toggle Modifier Collapse"
    bl_options = {'INTERNAL'}

    modifier_name: bpy.props.StringProperty()

    def invoke(self, context, event):
        obj = context.object
        if not obj:
            return {'CANCELLED'}

        collapsed = dict(get_collapse_data(obj))
        current_state = collapsed.get(self.modifier_name, False)

        if event.ctrl:
            new_state = not current_state
            for mod in obj.modifiers:
                collapsed[mod.name] = new_state
        elif event.shift:
            for mod in obj.modifiers:
                collapsed[mod.name] = False
            collapsed[self.modifier_name] = True
        else:
            collapsed[self.modifier_name] = not current_state

        obj["_modifiers_collapsed"] = collapsed
        return {'FINISHED'}


class VIEW3D_PT_modifiers_emulator(bpy.types.Panel):
    bl_label = "Modifiers"
    bl_idname = "VIEW3D_PT_modifiers_emulator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Modifiers'

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj and hasattr(obj, "modifiers")

    def draw_modifier_header(self, layout, mod):
        row = layout.row(align=True)
        
        # Collapse toggle
        collapsed = get_collapse_data(mod.id_data)
        is_collapsed = collapsed.get(mod.name, False)
        icon = 'TRIA_RIGHT' if is_collapsed else 'TRIA_DOWN'
        collapse_op = row.operator(
            OBJECT_OT_toggle_modifier_collapse.bl_idname,
            text="",
            icon=icon,
            emboss=False
        )
        collapse_op.modifier_name = mod.name
        
        # Modifier name and icon
        row.label(text=mod.name, icon=f'MOD_{mod.type}')
        
        # Visibility toggles
        toggles = row.row(align=True)
        toggles.prop(mod, "show_on_cage", text="", icon='MESH_DATA')
        toggles.prop(mod, "show_in_editmode", text="", icon='EDITMODE_HLT')
        toggles.prop(mod, "show_viewport", text="", icon='HIDE_OFF' if mod.show_viewport else 'HIDE_ON')
        toggles.prop(mod, "show_render", text="", icon='RESTRICT_RENDER_OFF' if mod.show_render else 'RESTRICT_RENDER_ON')
        
        # Spacer
        row.separator()
        
        # Control buttons
        controls = row.row(align=True)
        move_up = controls.operator("object.modifier_move_custom", text="", icon='TRIA_UP')
        move_up.modifier = mod.name
        move_up.direction = 'UP'
        
        move_down = controls.operator("object.modifier_move_custom", text="", icon='TRIA_DOWN')
        move_down.modifier = mod.name
        move_down.direction = 'DOWN'
        
        remove = controls.operator("object.modifier_remove_custom", text="", icon='X')
        remove.modifier = mod.name

    def draw_modifier_content(self, layout, mod):
        collapsed = get_collapse_data(mod.id_data)
        if collapsed.get(mod.name, False):
            return
            
        col = layout.column()

        # DATA_TRANSFER
        if mod.type == 'DATA_TRANSFER':
            col.prop(mod, "object")
            col.prop(mod, "use_object_transform")
            col.separator()
            col.prop(mod, "vert_mapping")
            col.prop(mod, "data_types", text="")
            col.separator()
            col.prop(mod, "mix_mode")
            col.prop(mod, "mix_factor")

        # MESH_CACHE
        elif mod.type == 'MESH_CACHE':
            col.prop(mod, "filepath")
            col.prop(mod, "object_path")
            col.prop(mod, "factor")
            col.prop(mod, "deform_mode")
            col.prop(mod, "flip_axis")

        # MESH_SEQUENCE_CACHE
        elif mod.type == 'MESH_SEQUENCE_CACHE':
            col.prop(mod, "cache_file")
            col.prop(mod, "object_path")
            col.prop(mod, "read_data")

        # NORMAL_EDIT
        elif mod.type == 'NORMAL_EDIT':
            col.prop(mod, "target")
            col.prop(mod, "mode")
            col.prop(mod, "offset")
            col.prop(mod, "mix_mode")
            col.prop(mod, "mix_factor")
            col.prop(mod, "vertex_group")

        # WEIGHTED_NORMAL
        elif mod.type == 'WEIGHTED_NORMAL':
            col.prop(mod, "weight")
            col.prop(mod, "keep_sharp")
            col.prop(mod, "vertex_group")
            col.prop(mod, "thresh")
            col.prop(mod, "mode")

        # UV_PROJECT
        elif mod.type == 'UV_PROJECT':
            col.prop(mod, "projector_count")
            for projector in mod.projectors:
                col.prop(projector, "object")
            col.prop(mod, "aspect_x")
            col.prop(mod, "aspect_y")
            col.prop(mod, "scale_x")
            col.prop(mod, "scale_y")

        # UV_WARP
        elif mod.type == 'UV_WARP':
            col.prop(mod, "object_from")
            col.prop(mod, "object_to")
            col.prop(mod, "vertex_group")
            col.prop(mod, "uv_layer")
            col.separator()
            col.prop(mod, "axis_u")
            col.prop(mod, "axis_v")

        # VERTEX_WEIGHT_EDIT
        elif mod.type == 'VERTEX_WEIGHT_EDIT':
            col.prop(mod, "vertex_group")
            col.prop(mod, "falloff_type")
            col.prop(mod, "map_curve")
            col.prop(mod, "add_threshold")
            col.prop(mod, "remove_threshold")

        # VERTEX_WEIGHT_MIX
        elif mod.type == 'VERTEX_WEIGHT_MIX':
            col.prop(mod, "vertex_group_a")
            col.prop(mod, "vertex_group_b")
            col.prop(mod, "default_weight_a")
            col.prop(mod, "default_weight_b")
            col.prop(mod, "mix_mode")
            col.prop(mod, "mix_set")

        # VERTEX_WEIGHT_PROXIMITY
        elif mod.type == 'VERTEX_WEIGHT_PROXIMITY':
            col.prop(mod, "vertex_group")
            col.prop(mod, "target")
            col.prop(mod, "proximity_mode")
            col.prop(mod, "proximity_geometry")
            col.prop(mod, "min_dist")
            col.prop(mod, "max_dist")
            col.prop(mod, "falloff_type")

        # ARRAY
        elif mod.type == 'ARRAY':
            col.prop(mod, "fit_type")
            if mod.fit_type == 'FIXED_COUNT':
                col.prop(mod, "count")
            elif mod.fit_type == 'FIT_LENGTH':
                col.prop(mod, "fit_length")
            elif mod.fit_type == 'FIT_CURVE':
                col.prop(mod, "curve")
            col.prop(mod, "relative_offset_displace")
            col.prop(mod, "constant_offset_displace")
            col.prop(mod, "use_merge_vertices")
            col.prop(mod, "merge_threshold")

        # BEVEL
        elif mod.type == 'BEVEL':
            col.prop(mod, "width")
            col.prop(mod, "segments")
            col.prop(mod, "limit_method")
            if mod.limit_method == 'ANGLE':
                col.prop(mod, "angle_limit")
            elif mod.limit_method == 'VGROUP':
                col.prop(mod, "vertex_group")
            col.prop(mod, "offset_type")
            col.prop(mod, "use_clamp_overlap")
            col.prop(mod, "loop_slide")

        # BOOLEAN
        elif mod.type == 'BOOLEAN':
            col.prop(mod, "operation")
            col.prop(mod, "operand_type")
            if mod.operand_type == 'OBJECT':
                col.prop(mod, "object")
            elif mod.operand_type == 'COLLECTION':
                col.prop(mod, "collection")
            col.prop(mod, "solver")
            if mod.solver == 'FAST':
                col.prop(mod, "double_threshold")
            col.prop(mod, "use_self")

        # BUILD
        elif mod.type == 'BUILD':
            col.prop(mod, "frame_start")
            col.prop(mod, "frame_duration")
            col.prop(mod, "use_reverse")

        # DECIMATE
        elif mod.type == 'DECIMATE':
            col.prop(mod, "decimate_type")
            if mod.decimate_type == 'COLLAPSE':
                col.prop(mod, "ratio")
                col.prop(mod, "use_collapse_triangulate")
            elif mod.decimate_type == 'UNSUBDIV':
                col.prop(mod, "iterations")
            elif mod.decimate_type == 'DISSOLVE':
                col.prop(mod, "angle_limit")
            col.prop(mod, "vertex_group")
            col.prop(mod, "invert_vertex_group")

        # EDGE_SPLIT
        elif mod.type == 'EDGE_SPLIT':
            col.prop(mod, "use_edge_angle")
            col.prop(mod, "split_angle")
            col.prop(mod, "use_edge_sharp")

        # MASK
        elif mod.type == 'MASK':
            col.prop(mod, "mode", expand=True)
            if mod.mode == 'VERTEX_GROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")
            elif mod.mode == 'ARMATURE':
                col.prop(mod, "armature", text="Armature")
                col.prop(mod, "threshold", text="Threshold")
            col.prop(mod, "invert_vertex_group", text="Invert")

        # MIRROR
        elif mod.type == 'MIRROR':
            col.prop(mod, "mirror_object", text="Mirror Object")
            row = col.row(heading="Axis")
            row.prop(mod, "use_axis", index=0, text="X", toggle=True)
            row.prop(mod, "use_axis", index=1, text="Y", toggle=True)
            row.prop(mod, "use_axis", index=2, text="Z", toggle=True)
            row = col.row(heading="Bisect")
            row.prop(mod, "use_bisect_axis", index=0, text="X", toggle=True)
            row.prop(mod, "use_bisect_axis", index=1, text="Y", toggle=True)
            row.prop(mod, "use_bisect_axis", index=2, text="Z", toggle=True)   
            if mod.use_bisect_axis:
                row = col.row(heading="Flip")
                row.prop(mod, "use_bisect_flip_axis", index=0, text="X", toggle=True)
                row.prop(mod, "use_bisect_flip_axis", index=1, text="Y", toggle=True)
                row.prop(mod, "use_bisect_flip_axis", index=2, text="Z", toggle=True)

            col.prop(mod, "use_clip", text="Clipping")
            col.prop(mod, "use_mirror_merge", text="Merge")
            if mod.use_mirror_merge:
                col.prop(mod, "merge_threshold", text="Threshold")
            col.separator()

        # MULTIRES
        elif mod.type == 'MULTIRES':
            col.prop(mod, "levels")
            col.prop(mod, "sculpt_levels")
            col.prop(mod, "render_levels")
            col.prop(mod, "subdivision_type")
            col.prop(mod, "use_subsurf_uv")
            col.prop(mod, "show_only_control_edges")

        # REMESH
        elif mod.type == 'REMESH':
            col.prop(mod, "mode")
            if mod.mode == 'VOXEL':
                col.prop(mod, "voxel_size")
                col.prop(mod, "adaptivity")
            elif mod.mode == 'QUAD':
                col.prop(mod, "octree_depth")
                col.prop(mod, "scale")
                col.prop(mod, "sharpness")
            col.prop(mod, "use_remove_disconnected")
            col.prop(mod, "threshold")

        # SCREW
        elif mod.type == 'SCREW':
            col.prop(mod, "angle")
            col.prop(mod, "steps")
            col.prop(mod, "render_steps")
            col.prop(mod, "use_smooth_shade")
            col.prop(mod, "use_normal_calculate")
            col.prop(mod, "use_normal_flip")
            col.prop(mod, "iterations")
            col.prop(mod, "use_stretch_u")
            col.prop(mod, "use_stretch_v")

        # SKIN
        elif mod.type == 'SKIN':
            col.prop(mod, "branch_smoothing")
            col.prop(mod, "use_smooth_shade")
            col.prop(mod, "use_x_symmetry")
            col.prop(mod, "use_y_symmetry")
            col.prop(mod, "use_z_symmetry")

        # SOLIDIFY
        elif mod.type == 'SOLIDIFY':
            col.prop(mod, "thickness")
            col.prop(mod, "thickness_clamp")
            col.prop(mod, "offset")
            col.prop(mod, "use_rim")
            col.prop(mod, "use_rim_only")
            col.prop(mod, "edge_crease_inner")
            col.prop(mod, "edge_crease_outer")
            col.prop(mod, "vertex_group")
            col.prop(mod, "invert_vertex_group")

        # SUBSURF
        elif mod.type == 'SUBSURF':
            col.prop(mod, "levels")
            col.prop(mod, "render_levels")
            col.prop(mod, "subdivision_type")
            col.prop(mod, "use_subsurf_uv")
            col.prop(mod, "show_only_control_edges")

        # TRIANGULATE
        elif mod.type == 'TRIANGULATE':
            col.prop(mod, "quad_method")
            col.prop(mod, "ngon_method")
            col.prop(mod, "min_vertices")
            col.prop(mod, "keep_custom_normals")

        # WELD
        elif mod.type == 'WELD':
            col.prop(mod, "merge_threshold")
            col.prop(mod, "vertex_group")

        # WIREFRAME
        elif mod.type == 'WIREFRAME':
            col.prop(mod, "thickness")
            col.prop(mod, "offset")
            col.prop(mod, "use_replace")
            col.prop(mod, "use_boundary")
            col.prop(mod, "use_even_offset")
            col.prop(mod, "use_relative_offset")
            col.prop(mod, "use_crease")
            col.prop(mod, "crease_weight")
            col.prop(mod, "vertex_group")
            col.prop(mod, "material_offset")

        # ARMATURE
        elif mod.type == 'ARMATURE':
            col.prop(mod, "object")
            col.prop(mod, "use_vertex_groups")
            col.prop(mod, "use_deform_preserve_volume")
            col.prop(mod, "use_multi_modifier")

        # CAST
        elif mod.type == 'CAST':
            col.prop(mod, "cast_type")
            col.prop(mod, "factor")
            col.prop(mod, "radius")
            col.prop(mod, "size")
            row = col.row(heading="Axis")
            row.prop(mod, "use_x", text="X", toggle=True)
            row.prop(mod, "use_y", text="Y", toggle=True)
            row.prop(mod, "use_z", text="Z", toggle=True)
            col.prop(mod, "vertex_group")
            col.prop(mod, "direction")

        # CURVE
        elif mod.type == 'CURVE':
            col.prop(mod, "object")
            col.prop(mod, "deform_axis")

        # DISPLACE
        elif mod.type == 'DISPLACE':
            col.prop(mod, "direction")
            col.prop(mod, "strength")
            col.prop(mod, "mid_level")
            row = col.row()
            row.prop(mod, "space", expand=True)
            if mod.space == 'TEXTURE':
                col.prop(mod, "texture_coords", text="Coordinates")
                if mod.texture_coords == 'OBJECT':
                    col.prop(mod, "texture_coords_object", text="Object")
                elif mod.texture_coords == 'UV':
                    col.prop_search(mod, "uv_layer", mod.id_data.data, "uv_layers", text="UV Map")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")

        # HOOK
        elif mod.type == 'HOOK':
            col.prop(mod, "object")
            col.prop(mod, "subtarget")
            col.prop(mod, "vertex_group")
            col.prop(mod, "strength")
            col.prop(mod, "falloff_radius")
            col.prop(mod, "falloff_type")

        # LAPLACIANDEFORM
        elif mod.type == 'LAPLACIANDEFORM':
            col.prop(mod, "vertex_group")
            col.prop(mod, "iterations")
            col.prop(mod, "anchor_grp")
            col.prop(mod, "use_volume_preserve")

        # LATTICE
        elif mod.type == 'LATTICE':
            col.prop(mod, "object")
            col.prop(mod, "strength")
            col.prop(mod, "vertex_group")

        # MESH_DEFORM
        elif mod.type == 'MESH_DEFORM':
            col.prop(mod, "object")
            col.prop(mod, "precision")
            col.prop(mod, "use_dynamic_bind")
            col.prop(mod, "vertex_group")

        # SHRINKWRAP
        elif mod.type == 'SHRINKWRAP':
            col.prop(mod, "target")
            col.prop(mod, "offset")
            col.prop(mod, "vertex_group")
            col.prop(mod, "wrap_method")
            if mod.wrap_method == 'PROJECT':
                row = col.row(heading="Project")
                row.prop(mod, "use_project_x", text="X", toggle=True)
                row.prop(mod, "use_project_y", text="Y", toggle=True)
                row.prop(mod, "use_project_z", text="Z", toggle=True)
                row = col.row(heading="Direction")
                row.prop(mod, "use_negative_direction", text="Negative", toggle=True)
                row.prop(mod, "use_positive_direction", text="Positive", toggle=True)
                col.prop(mod, "cull_face")
                col.prop(mod, "auxiliary_target")
            elif mod.wrap_method == 'NEAREST_SURFACEPOINT':
                col.prop(mod, "use_track_normal")
            col.prop(mod, "wrap_mode")

        # SIMPLE_DEFORM
        elif mod.type == 'SIMPLE_DEFORM':
            col.prop(mod, "deform_method")
            col.prop(mod, "vertex_group")
            col.prop(mod, "origin")
            col.prop(mod, "deform_axis")
            col.prop(mod, "factor")
            row = col.row(heading="Lock")
            row.prop(mod, "lock_x", text="X", toggle=True)
            row.prop(mod, "lock_y", text="Y", toggle=True)

        # SMOOTH
        elif mod.type == 'SMOOTH':
            col.prop(mod, "factor")
            col.prop(mod, "iterations")
            col.prop(mod, "vertex_group")
            row = col.row(heading="Axis")
            row.prop(mod, "use_x", text="X", toggle=True)
            row.prop(mod, "use_y", text="Y", toggle=True)
            row.prop(mod, "use_z", text="Z", toggle=True)

        # CORRECTIVE_SMOOTH
        elif mod.type == 'CORRECTIVE_SMOOTH':
            col.prop(mod, "factor")
            col.prop(mod, "iterations")
            col.prop(mod, "scale")
            col.prop(mod, "vertex_group")
            col.prop(mod, "use_only_smooth")
            col.prop(mod, "use_pin_boundary")

        # LAPLACIANSMOOTH
        elif mod.type == 'LAPLACIANSMOOTH':
            col.prop(mod, "lambda_factor")
            col.prop(mod, "lambda_border")
            row = col.row(heading="Axis")
            row.prop(mod, "use_x", text="X", toggle=True)
            row.prop(mod, "use_y", text="Y", toggle=True)
            row.prop(mod, "use_z", text="Z", toggle=True)
            col.prop(mod, "use_normalized")
            col.prop(mod, "vertex_group")

        # SURFACE_DEFORM
        elif mod.type == 'SURFACE_DEFORM':
            col.prop(mod, "target")
            col.prop(mod, "falloff")
            col.prop(mod, "vertex_group")

        # WARP
        elif mod.type == 'WARP':
            col.prop(mod, "object_from")
            col.prop(mod, "object_to")
            col.prop(mod, "strength")
            col.prop(mod, "falloff_radius")
            col.prop(mod, "falloff_type")
            col.prop(mod, "vertex_group")
            col.prop(mod, "texture_coords")
            if mod.texture_coords == 'OBJECT':
                col.prop(mod, "texture_coords_object", text="Object")
            elif mod.texture_coords == 'UV':
                col.prop_search(mod, "uv_layer", mod.id_data.data, "uv_layers", text="UV Map")

        # WAVE
        elif mod.type == 'WAVE':
            col.prop(mod, "time_offset")
            col.prop(mod, "lifetime")
            col.prop(mod, "damping_time")
            col.prop(mod, "start_position_x")
            col.prop(mod, "start_position_y")
            col.prop(mod, "falloff_radius")
            row = col.row(heading="Axis")
            row.prop(mod, "use_x", text="X", toggle=True)
            row.prop(mod, "use_y", text="Y", toggle=True)
            col.prop(mod, "use_cyclic")
            col.prop(mod, "use_normal")
            col.prop(mod, "vertex_group")

        # PHYSICS MODIFIERS (simplified)
        elif mod.type in {'CLOTH', 'COLLISION', 'DYNAMIC_PAINT', 'FLUID', 'SOFT_BODY', 'PARTICLE_SYSTEM'}:
            col.label(text="Use Properties editor for full settings")
        
        # OCEAN
        elif mod.type == 'OCEAN':
            col.prop(mod, "geometry_mode")
            col.prop(mod, "repeat_x")
            col.prop(mod, "repeat_y")
            col.prop(mod, "time")
            col.prop(mod, "depth")
            col.prop(mod, "random_seed")
            col.prop(mod, "resolution")
            col.prop(mod, "size")
            col.prop(mod, "spatial_size")
            col.prop(mod, "choppiness")
            col.prop(mod, "wave_scale")
            col.prop(mod, "wave_scale_min")
            col.prop(mod, "wind_velocity")
            col.prop(mod, "damping")

        # PARTICLE_INSTANCE
        elif mod.type == 'PARTICLE_INSTANCE':
            col.prop(mod, "object")
            col.prop(mod, "particle_system_index")
            col.prop(mod, "use_normal")
            col.prop(mod, "use_children")
            col.prop(mod, "use_size")
            col.prop(mod, "show_alive")
            col.prop(mod, "show_unborn")
            col.prop(mod, "show_dead")
            col.prop(mod, "axis")

        # EXPLODE
        elif mod.type == 'EXPLODE':
            col.prop(mod, "vertex_group")
            col.prop(mod, "protect")
            col.prop(mod, "use_edge_cut")
            col.prop(mod, "show_unborn")
            col.prop(mod, "show_alive")
            col.prop(mod, "show_dead")
            col.prop(mod, "use_size")

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj.modifiers:
            layout.label(text="No modifiers", icon='INFO')
            return

        for mod in obj.modifiers:
            box = layout.box()
            self.draw_modifier_header(box, mod)
            self.draw_modifier_content(box, mod)


class OBJECT_OT_modifier_remove_custom(bpy.types.Operator):
    bl_idname = "object.modifier_remove_custom"
    bl_label = "Remove Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    modifier: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.object
        if obj and self.modifier in obj.modifiers:
            obj.modifiers.remove(obj.modifiers[self.modifier])
            self.report({'INFO'}, f"Modifier {self.modifier} removed")
        else:
            self.report({'WARNING'}, "Modifier not found")
            return {'CANCELLED'}
        return {'FINISHED'}


class OBJECT_OT_modifier_move_custom(bpy.types.Operator):
    bl_idname = "object.modifier_move_custom"
    bl_label = "Move Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    modifier: bpy.props.StringProperty()
    direction: bpy.props.EnumProperty(items=[
        ('UP', 'Up', 'Move modifier up'),
        ('DOWN', 'Down', 'Move modifier down')
    ])

    def execute(self, context):
        obj = context.object
        if not obj:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}

        mods = obj.modifiers
        index = mods.find(self.modifier)
        if index == -1:
            self.report({'WARNING'}, "Modifier not found")
            return {'CANCELLED'}

        if self.direction == 'UP' and index > 0:
            mods.move(index, index - 1)
        elif self.direction == 'DOWN' and index < len(mods) - 1:
            mods.move(index, index + 1)
        else:
            return {'CANCELLED'}

        return {'FINISHED'}


classes = (
    VIEW3D_PT_modifiers_emulator,
    OBJECT_OT_modifier_remove_custom,
    OBJECT_OT_modifier_move_custom,
    OBJECT_OT_toggle_modifier_collapse,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    try:
        unregister()
    except Exception:
        pass
    register()
