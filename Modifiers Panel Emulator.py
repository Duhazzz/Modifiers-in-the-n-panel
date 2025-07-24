bl_info = {
    "name": "Modifiers Panel Emulator",
    "author": "ChatGPT, deepseek, duhazzz",
    "version": (2, 4),
    "blender": (3, 0, 0),
    "location": "View3D > N-panel > Modifiers",
    "description": "Shows modifiers in N-panel with full settings, Geometry Nodes support, and optional popup",
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
        if mod.type != 'NODES':
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
            
            # Show node group inputs
            if mod.node_group:
                for input in mod.node_group.inputs:
                    if input.identifier not in mod:
                        continue
                    
                    # Skip certain internal sockets
                    if input.identifier in {'Input_1', 'Input_2', 'Input_3'}:
                        continue
                        
                    row = col.row()
                    if input.bl_socket_idname == 'NodeSocketFloat':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketVector':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketInt':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketBool':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name, toggle=True)
                    elif input.bl_socket_idname == 'NodeSocketColor':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    else:
                        row.label(text=f"{input.name}: {input.bl_socket_idname}")
            
            # Button to edit node group
            row = col.row()
            if mod.node_group:
                row.operator("object.geometry_nodes_tool", text="Edit Node Group", icon='NODETREE').node_group = mod.node_group.name
            else:
                row.operator("node.new_geometry_nodes_modifier", text="New Node Group", icon='ADD')
        
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

        # For other modifier types, show full settings in popup
        elif mod.type in {'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 'EDGE_SPLIT',
                         'SOLIDIFY', 'SUBSURF', 'SKIN', 'TRIANGULATE', 'WIREFRAME',
                         'ARMATURE', 'CAST', 'CURVE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE',
                         'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'WAVE',
                         'CLOTH', 'COLLISION', 'DYNAMIC_PAINT', 'EXPLODE', 'FLUID', 'OCEAN',
                         'PARTICLE_INSTANCE', 'PARTICLE_SYSTEM', 'SOFT_BODY'}:
            col.label(text=f"{mod.type} modifier")
            # Add specific properties for each modifier type as needed
            if hasattr(mod, "show_in_editmode"):
                col.prop(mod, "show_in_editmode")
            if hasattr(mod, "vertex_group"):
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups")


class OBJECT_OT_edit_geometry_nodes(bpy.types.Operator):
    bl_idname = "object.geometry_nodes_tool"
    bl_label = "Edit Geometry Nodes"
    bl_options = {'REGISTER', 'UNDO'}

    node_group: bpy.props.StringProperty()

    def execute(self, context):
        if not self.node_group:
            return {'CANCELLED'}
        
        # Switch to Node Editor
        area = None
        for a in context.screen.areas:
            if a.type == 'NODE_EDITOR':
                area = a
                break
        
        if not area:
            # If no node editor found, split current area
            area = context.area
            override = context.copy()
            with context.temp_override(**override):
                bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
                for a in context.screen.areas:
                    if a != area:
                        area = a
                        break
            area.type = 'NODE_EDITOR'
        
        # Set the node group
        node_group = bpy.data.node_groups.get(self.node_group)
        if node_group:
            area.spaces.active.node_tree = node_group
        
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
        
        # Modifier name and icon
        row.label(text=mod.name, icon=f'MOD_{mod.type}')
        
        # Visibility toggles
        toggles = row.row(align=True)
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
        col = layout.column()

        # GEOMETRY NODES
        if mod.type == 'NODES':
            col.prop(mod, "node_group", text="")
            
            # Quick access to edit node group
            row = col.row()
            if mod.node_group:
                row.operator("object.geometry_nodes_tool", text="Edit", icon='NODETREE').node_group = mod.node_group.name
            else:
                row.operator("node.new_geometry_nodes_modifier", text="New", icon='ADD')
            
            # Show first few important inputs
            if mod.node_group:
                inputs_shown = 0
                for input in mod.node_group.inputs:
                    if input.identifier not in mod:
                        continue
                        
                    # Skip certain internal sockets
                    if input.identifier in {'Input_1', 'Input_2', 'Input_3'}:
                        continue
                        
                    # Limit to 3 inputs in the panel
                    if inputs_shown >= 3:
                        break
                        
                    row = col.row()
                    if input.bl_socket_idname == 'NodeSocketFloat':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketVector':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketInt':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name)
                    elif input.bl_socket_idname == 'NodeSocketBool':
                        row.prop(mod, f'["{input.identifier}"]', text=input.name, toggle=True)
                    else:
                        row.label(text=input.name)
                    
                    inputs_shown += 1

        # MIRROR
        elif mod.type == 'MIRROR':
            col.prop(mod, "mirror_object", text="Mirror Object")
            row = col.row(heading="Axis")
            row.prop(mod, "use_axis", index=0, text="X", toggle=True)
            row.prop(mod, "use_axis", index=1, text="Y", toggle=True)
            row.prop(mod, "use_axis", index=2, text="Z", toggle=True)
            col.prop(mod, "use_clip", text="Clipping")
            if mod.use_mirror_merge:
                col.prop(mod, "merge_threshold", text="Merge Threshold")

        # MASK
        elif mod.type == 'MASK':
            col.prop(mod, "mode", expand=True)
            if mod.mode == 'VERTEX_GROUP':
                col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Group")
            col.prop(mod, "invert_vertex_group", text="Invert")

        # DISPLACE
        elif mod.type == 'DISPLACE':
            col.prop(mod, "direction")
            col.prop(mod, "strength")
            col.prop(mod, "mid_level")
            if mod.space == 'TEXTURE' and mod.texture_coords == 'UV':
                col.prop_search(mod, "uv_layer", mod.id_data.data, "uv_layers", text="UV Map")
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")

        # ARRAY
        elif mod.type == 'ARRAY':
            col.prop(mod, "fit_type")
            if mod.fit_type == 'FIXED_COUNT':
                col.prop(mod, "count")
            elif mod.fit_type == 'FIT_LENGTH':
                col.prop(mod, "fit_length")
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

        # BOOLEAN
        elif mod.type == 'BOOLEAN':
            col.prop(mod, "operation")
            col.prop(mod, "operand_type")
            if mod.operand_type == 'OBJECT':
                col.prop(mod, "object")
            elif mod.operand_type == 'COLLECTION':
                col.prop(mod, "collection")

        # Other modifiers - show key properties
        elif mod.type == 'SOLIDIFY':
            col.prop(mod, "thickness")
            col.prop(mod, "vertex_group")

        elif mod.type == 'SUBSURF':
            col.prop(mod, "levels")
            col.prop(mod, "render_levels")

        elif mod.type == 'ARMATURE':
            col.prop(mod, "object")
            col.prop(mod, "use_vertex_groups")

        elif mod.type == 'SHRINKWRAP':
            col.prop(mod, "target")
            col.prop(mod, "offset")
            col.prop(mod, "wrap_method")

        elif mod.type == 'SIMPLE_DEFORM':
            col.prop(mod, "deform_method")
            col.prop(mod, "factor")

        elif mod.type == 'LATTICE':
            col.prop(mod, "object")
            col.prop(mod, "strength")

        elif mod.type == 'CAST':
            col.prop(mod, "factor")
            row = col.row(heading="Axis")
            row.prop(mod, "use_x", text="X", toggle=True)
            row.prop(mod, "use_y", text="Y", toggle=True)
            row.prop(mod, "use_z", text="Z", toggle=True)

        elif mod.type == 'WAVE':
            col.prop(mod, "time_offset")
            col.prop(mod, "start_position_x")
            col.prop(mod, "start_position_y")

        # For other types, show at least vertex group if available
        elif hasattr(mod, "vertex_group"):
            col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups")


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
    OBJECT_OT_edit_geometry_nodes,
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
