import bpy, os

from .addon_prefs import get_addon_preferences

class STORYBOARD_EXPORTER_OT_test_export(bpy.types.Operator):
    bl_idname = "storyboard_exporter.test_export"
    bl_label = "Export"
    bl_options = {'REGISTER'}
 
    export_name : bpy.props.StringProperty(default = "export name")

    @classmethod
    def poll(cls, context):
        return True
 
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
 
    def draw(self, context):
        
        layout = self.layout

        layout.prop(self, "export_name")           

    def execute(self, context):
        scn = context.scene

        old_frame = scn.frame_current
        old_filepath = scn.render.filepath

        export_folder = os.path.dirname(old_filepath)

        n = 0
        for m in scn.timeline_markers:
            if m.name == get_addon_preferences().marker_pattern:
                scn.frame_current = m.frame
                scn.render.filepath = os.path.join(export_folder, self.export_name + str(n).zfill(3))
                bpy.ops.render.opengl(sequencer = True, write_still = True)
                n += 1

        scn.frame_current = old_frame
        scn.render.filepath = old_filepath

        return {'FINISHED'}