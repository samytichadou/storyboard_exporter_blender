import bpy
import os

addon_name = os.path.basename(os.path.dirname(__file__))

# addon preferences
class STORYBOARD_EXPORTER_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = addon_name

    marker_pattern : bpy.props.StringProperty(
        name = "Marker pattern",
        default = "_storyboard",
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "marker_pattern")


# get addon preferences
def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(addon_name)
    return getattr(addon, "preferences", None)