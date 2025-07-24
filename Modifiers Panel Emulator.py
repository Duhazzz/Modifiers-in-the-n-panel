bl_info = {
    "name": "Modifiers Panel Emulator",
    "author": "ChatGPT, deepseek, duhazzz",
    "version": (2, 6),
    "blender": (3, 0, 0),
    "location": "View3D > N-panel > Modifiers",
    "description": "Complete modifiers panel with consistent settings between N-panel and popup",
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


class OBJECT_OT_open_modifiers_popup(bpy.types.Operator):
    bl_idname = "object.open_modifiers_popup"
    bl_label = "Modifiers Popup"
    bl_description = "Open modifiers in a popup window"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=400)

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
        if mod.type not in {'NODES', 'PARTICLE_SYSTEM'}:
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

        # GEOMETRY NODES
        if mod.type == 'NODES':
            col.prop(mod, "node_group", text="Node Group")
            if mod.node_group:
                col.label(text="Use Properties editor for full settings")
            return

        # PARTICLE SYSTEM
        elif mod.type == 'PARTICLE_SYSTEM':
            col.prop_search(mod, "particle_system", obj, "particle_systems", text="System")
            col.label(text="Use Properties editor for full settings")
            return

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

        # MASK
        elif mod.type == 'MASK':
            col.prop(mod, "mode", expand=True)
            if mod.mode == 'VERTEX_GROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")
            elif mod.mode == 'ARMATURE':
                col.prop(mod, "armature", text="Armature")
                col.prop(mod, "threshold", text="Threshold")
            col.prop(mod, "invert_vertex_group", text="Invert")

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

        # ARRAY
        elif mod.type == 'ARRAY':
            col.prop(mod, "fit_type")
            if mod.fit_type == 'FIXED_COUNT':
                col.prop(mod, "count")
            elif mod.fit_type == 'FIT_LENGTH':
                col.prop(mod, "fit_length")
            elif mod.fit_type == 'FIT_CURVE':
                col.prop(mod, "curve")
            col.prop(mod, "relative_offset_displace", text="Relative Offset")
            col.prop(mod, "constant_offset_displace", text="Constant Offset")
            col.prop(mod, "use_merge_vertices", text="Merge")
            if mod.use_merge_vertices:
                col.prop(mod, "merge_threshold", text="Threshold")

        # BEVEL
        elif mod.type == 'BEVEL':
            col.prop(mod, "width")
            col.prop(mod, "segments")
            col.prop(mod, "limit_method")
            if mod.limit_method == 'ANGLE':
                col.prop(mod, "angle_limit")
            elif mod.limit_method == 'VGROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups")
            col.prop(mod, "offset_type")
            col.prop(mod, "use_clamp_overlap", text="Clamp Overlap")
            col.prop(mod, "loop_slide", text="Loop Slide")

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
                col.prop(mod, "double_threshold", text="Threshold")
            col.prop(mod, "use_self", text="Self")

        # SOLIDIFY
        elif mod.type == 'SOLIDIFY':
            col.prop(mod, "thickness")
            col.prop(mod, "thickness_clamp")
            col.prop(mod, "offset")
            col.prop(mod, "use_rim", text="Rim")
            col.prop(mod, "use_rim_only", text="Rim Only")
            col.prop(mod, "edge_crease_inner", text="Inner Crease")
            col.prop(mod, "edge_crease_outer", text="Outer Crease")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")
            col.prop(mod, "invert_vertex_group", text="Invert")

        # SUBSURF
        elif mod.type == 'SUBSURF':
            col.prop(mod, "levels")
            col.prop(mod, "render_levels")
            col.prop(mod, "subdivision_type", text="Subdivision Type")
            col.prop(mod, "use_subsurf_uv", text="Optimal Display")
            col.prop(mod, "show_only_control_edges", text="Simple")

        # ARMATURE
        elif mod.type == 'ARMATURE':
            col.prop(mod, "object")
            col.prop(mod, "use_vertex_groups", text="Vertex Groups")
            col.prop(mod, "use_deform_preserve_volume", text="Preserve Volume")
            col.prop(mod, "use_multi_modifier", text="Multi Modifier")

        # SHRINKWRAP
        elif mod.type == 'SHRINKWRAP':
            col.prop(mod, "target")
            col.prop(mod, "offset")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")
            col.prop(mod, "wrap_method", text="Mode")
            if mod.wrap_method == 'PROJECT':
                row = col.row(heading="Project")
                row.prop(mod, "use_project_x", text="X", toggle=True)
                row.prop(mod, "use_project_y", text="Y", toggle=True)
                row.prop(mod, "use_project_z", text="Z", toggle=True)
                row = col.row(heading="Direction")
                row.prop(mod, "use_negative_direction", text="Negative", toggle=True)
                row.prop(mod, "use_positive_direction", text="Positive", toggle=True)
                col.prop(mod, "cull_face", text="Cull Faces")
                col.prop(mod, "auxiliary_target", text="Auxiliary Target")
            elif mod.wrap_method == 'NEAREST_SURFACEPOINT':
                col.prop(mod, "use_track_normal", text="Track Normal")
            col.prop(mod, "wrap_mode", text="Wrap Mode")

        # For other types with vertex groups
        elif hasattr(mod, "vertex_group"):
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")
            if hasattr(mod, "invert_vertex_group"):
                col.prop(mod, "invert_vertex_group", text="Invert")


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

    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        # Add button to open the popup
        row = layout.row()
        row.operator("object.open_modifiers_popup", text="Open Full Modifiers", icon='FULLSCREEN_ENTER')
        
        if not obj.modifiers:
            layout.label(text="No modifiers", icon='INFO')
            return
            
        for mod in obj.modifiers:
            box = layout.box()
            self.draw_modifier_header(box, mod)
            self.draw_modifier_content(box, mod)

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
        if mod.type not in {'NODES', 'PARTICLE_SYSTEM'}:
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

        # GEOMETRY NODES
        if mod.type == 'NODES':
            col.prop(mod, "node_group", text="")
            return

        # PARTICLE SYSTEM
        elif mod.type == 'PARTICLE_SYSTEM':
            col.prop_search(mod, "particle_system", mod.id_data, "particle_systems", text="")
            return

        # MIRROR
        elif mod.type == 'MIRROR':
            col.prop(mod, "mirror_object", text="Mirror")
            row = col.row(heading="Axis")
            row.prop(mod, "use_axis", index=0, text="X", toggle=True)
            row.prop(mod, "use_axis", index=1, text="Y", toggle=True)
            row.prop(mod, "use_axis", index=2, text="Z", toggle=True)
            col.prop(mod, "use_clip", text="Clipping")

        # MASK
        elif mod.type == 'MASK':
            col.prop(mod, "mode", expand=True)
            if mod.mode == 'VERTEX_GROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")

        # DISPLACE
        elif mod.type == 'DISPLACE':
            col.prop(mod, "direction")
            col.prop(mod, "strength")
            if mod.space == 'TEXTURE' and mod.texture_coords == 'UV':
                col.prop_search(mod, "uv_layer", mod.id_data.data, "uv_layers", text="UV Map")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")

        # ARRAY
        elif mod.type == 'ARRAY':
            col.prop(mod, "fit_type")
            if mod.fit_type == 'FIXED_COUNT':
                col.prop(mod, "count")
            elif mod.fit_type == 'FIT_LENGTH':
                col.prop(mod, "fit_length")
            col.prop(mod, "use_merge_vertices", text="Merge")

        # BEVEL
        elif mod.type == 'BEVEL':
            col.prop(mod, "width")
            col.prop(mod, "segments")
            col.prop(mod, "limit_method")
            if mod.limit_method == 'ANGLE':
                col.prop(mod, "angle_limit")
            elif mod.limit_method == 'VGROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups")

        # BOOLEAN
        elif mod.type == 'BOOLEAN':
            col.prop(mod, "operation")
            col.prop(mod, "operand_type")
            if mod.operand_type == 'OBJECT':
                col.prop(mod, "object")
            elif mod.operand_type == 'COLLECTION':
                col.prop(mod, "collection")

        # SOLIDIFY
        elif mod.type == 'SOLIDIFY':
            col.prop(mod, "thickness")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")

        # SUBSURF
        elif mod.type == 'SUBSURF':
            col.prop(mod, "levels")
            col.prop(mod, "render_levels")

        # ARMATURE
        elif mod.type == 'ARMATURE':
            col.prop(mod, "object")
            col.prop(mod, "use_vertex_groups", text="Vertex Groups")

        # SHRINKWRAP
        elif mod.type == 'SHRINKWRAP':
            col.prop(mod, "target")
            col.prop(mod, "offset")
            col.prop(mod, "wrap_method", text="Mode")

        # For other types with vertex groups
        elif hasattr(mod, "vertex_group"):
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")


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
    OBJECT_OT_open_modifiers_popup,
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
