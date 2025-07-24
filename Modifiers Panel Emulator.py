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

# Modifier name and icon
MODIFIER_ICONS = {
    'NODES': 'GEOMETRY_NODES',
    'PARTICLE_SYSTEM': 'PARTICLES',
    'NORMAL_EDIT': 'MODIFIER',
    'DATA_TRANSFER': 'MOD_DATA_TRANSFER',
    'VERTEX_WEIGHT_EDIT': 'MOD_VERTEX_WEIGHT',
    'VERTEX_WEIGHT_MIX': 'MOD_VERTEX_WEIGHT',
    'VERTEX_WEIGHT_PROXIMITY': 'MOD_VERTEX_WEIGHT',
}


def get_collapse_data(obj):
    return obj.get("_modifiers_collapsed", {})


def draw_modifier_content_full(layout, mod):
    collapsed = get_collapse_data(mod.id_data)
    if collapsed.get(mod.name, False):
        return

    col = layout.column()

    if mod.type == 'NODES':
        col.prop(mod, "node_group", text="Node Group")
        if mod.node_group:
            col.label(text="Use Properties editor for full settings")
        return

    elif mod.type == 'PARTICLE_SYSTEM':
        col.prop_search(mod, "particle_system", mod.id_data, "particle_systems", text="System")
        col.label(text="Use Properties editor for full settings")
        return

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
        if any(mod.use_bisect_axis):
            row = col.row(heading="Flip")
            row.prop(mod, "use_bisect_flip_axis", index=0, text="X", toggle=True)
            row.prop(mod, "use_bisect_flip_axis", index=1, text="Y", toggle=True)
            row.prop(mod, "use_bisect_flip_axis", index=2, text="Z", toggle=True)
        col.prop(mod, "use_clip", text="Clipping")
        col.prop(mod, "use_mirror_merge", text="Merge")
        if mod.use_mirror_merge:
            col.prop(mod, "merge_threshold", text="Threshold")

    elif hasattr(mod, "vertex_group"):
        col.prop_search(mod, "vertex_group", mod.id_data, "vertex_groups", text="Vertex Group")
        if hasattr(mod, "invert_vertex_group"):
            col.prop(mod, "invert_vertex_group", text="Invert")


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

        mod_icon = MODIFIER_ICONS.get(mod.type, 'MODIFIER')
        row.label(text=mod.name, icon=mod_icon)

        toggles = row.row(align=True)
        if mod.type not in {'NODES', 'PARTICLE_SYSTEM'}:
            toggles.prop(mod, "show_on_cage", text="", icon='MESH_DATA')
            toggles.prop(mod, "show_in_editmode", text="", icon='EDITMODE_HLT')
        toggles.prop(mod, "show_viewport", text="", icon='HIDE_OFF' if mod.show_viewport else 'HIDE_ON')
        toggles.prop(mod, "show_render", text="", icon='RESTRICT_RENDER_OFF' if mod.show_render else 'RESTRICT_RENDER_ON')

        row.separator()

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
        draw_modifier_content_full(layout, mod)


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

        mod_icon = MODIFIER_ICONS.get(mod.type, 'MODIFIER')
        row.label(text=mod.name, icon=mod_icon)

        toggles = row.row(align=True)
        if mod.type not in {'NODES', 'PARTICLE_SYSTEM'}:
            toggles.prop(mod, "show_on_cage", text="", icon='MESH_DATA')
            toggles.prop(mod, "show_in_editmode", text="", icon='EDITMODE_HLT')
        toggles.prop(mod, "show_viewport", text="", icon='HIDE_OFF' if mod.show_viewport else 'HIDE_ON')
        toggles.prop(mod, "show_render", text="", icon='RESTRICT_RENDER_OFF' if mod.show_render else 'RESTRICT_RENDER_ON')

        row.separator()

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
        draw_modifier_content_full(layout, mod)


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
