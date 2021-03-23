from collections import namedtuple
from functools import reduce
import os
from shlex import split
from subprocess import check_output
import bpy
import re

bl_info = {
    'name': 'Generate Sequence from Markers',
    'author': 'gabriel montagné, gabriel@tibas.london',
    'version': (0, 1, 0),
    'blender': (2, 80, 0),
    'description': 'Render all the frames with markers in them, add the images to the VSE Edit scene as Image strips and export FCPXML',
    "location": "Sequencer > Marker > Generate Sequence from Markers",
    'tracker_url': 'https://github.com/gabrielmontagne/blender-addon-marker-preview-video/issues',
    'category': 'Render'
}

version_file = 'VERSION.txt'

def slugify(name):
    return re.sub(r'[\W_]+', '-', name)

Span = namedtuple('Span', 'frame name length', defaults=[1])

class RENDER_MARKER_OT_preview(bpy.types.Operator):
    """Render a image for each marker and insert them as Image strips in a new Scene, 'Edit', and export a FCPXML file"""
    bl_idname = "sequencer.preview_from_markers"
    bl_label = "Generate Sequence from Markers"
    bl_options = {"REGISTER", "UNDO"}

    render_from_sequencer: bpy.props.BoolProperty(name="Render from Sequencer", default=False)
    override_images: bpy.props.BoolProperty(name="Overwrite Images", default=False)
    save_fcpxml: bpy.props.BoolProperty(name="Save FCPXML", default=True)
    clear_vse_channel: bpy.props.BoolProperty(name="Clean VSE Channel", default=True)
    vse_channel_id: bpy.props.IntProperty(name='Insert in Channel', default=1)

    def execute(self, context):

        filepath = bpy.data.filepath
        base_dir = os.path.dirname(filepath)
        version_path = os.path.join(base_dir, version_file)
        version = None
        if os.path.isfile(os.path.join(base_dir, version_path)):
            version = open(version_path, 'r').read().strip()

        branch = None
        try:
            branch = check_output(split('git branch --show-current')).decode('utf8').strip()
        except:
            branch = ''

        print('version_path', version_path, version)
        print('git branch', branch)

        scene = context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end

        def to_spans(acc, next):
            frame = next.frame

            if frame < frame_start: return acc
            if frame > frame_end: return acc

            if not len(acc) and frame > frame_start:
                acc =[ Span(frame_start, 'start') ]

            acc.append(Span(next.frame, next.name))
            return acc

        def assign_lengths(spans):
            def calculate_length(acc, next):
                i, (c, n) = next
                is_last = i == len(spans) - 2

                acc.append(c._replace(length=n.frame - c.frame))
                if is_last:
                    acc.append(n._replace(length=frame_end - n.frame))
                return acc

            return reduce(calculate_length, enumerate(zip(spans[:-1], spans[1:])), [])

        def to_frame(maker):
            return maker.frame

        spans = assign_lengths(reduce(to_spans, sorted(scene.timeline_markers, key=to_frame), []))

        edit_scene = bpy.data.scenes.get('Edit') or bpy.data.scenes.get('edit') or bpy.data.scenes.get('__ Edit')
        if edit_scene is None:
            edit_scene = bpy.data.scenes.new(name='Edit')

        print('we have an edit scene, try to mount on VSE')
        print('... on channel', self.vse_channel_id)
        print(f'should {self.clear_vse_channel} clear channel.')

        edit_scene.sequence_editor_create()
        sequence_editor = edit_scene.sequence_editor

        if self.clear_vse_channel:
            for s in list(sequence_editor.sequences):
                if s.channel == self.vse_channel_id:
                    print('Removing sequence', s)
                    sequence_editor.sequences.remove(s)

        original_out = scene.render.filepath
        original_format = scene.render.image_settings.file_format
        context.window_manager.progress_begin(0, len(spans))

        files = []

        for i, span in enumerate(spans):

            if version:
                out_path = f'//marker-frames/{branch}/{version}/mark-{i:03d}-frame-{span.frame:06d}-{slugify(span.name)}.jpg'
            else:
                out_path = f'//marker-frames/{branch}/mark-{i:03d}-frame-{span.frame:06d}-{slugify(span.name)}.jpg'

            scene.render.filepath = out_path
            scene.render.image_settings.file_format = 'JPEG'
            scene.frame_current = span.frame

            if os.path.exists(bpy.path.abspath(out_path)):
                print(f'File {out_path} already exists.')
                if self.override_images:
                    print('Override images, render')
                    if self.render_from_sequencer:
                        bpy.ops.render.opengl(sequencer = True, write_still = True)
                    else:
                        bpy.ops.render.render(write_still=True, scene=scene.name)
                else:
                    print('Skip rerender')
            else:
                bpy.ops.render.render(write_still=True, scene=scene.name)


            if edit_scene is not None:
                new_sequence = sequence_editor.sequences.new_image(
                    name=span.name,
                    filepath=bpy.path.relpath(out_path),
                    frame_start=span.frame,
                    channel=self.vse_channel_id
                )
                new_sequence.frame_final_duration = span.length
                print('sequence', new_sequence)

            files.append([os.path.basename(os.path.realpath(out_path)), bpy.path.relpath(out_path), span.frame, span.length])

            context.window_manager.progress_update(i)

        scene.render.filepath = original_out
        scene.render.image_settings.file_format = original_format

        message = f'Done! renderered {len(spans)} marker images'

        self.report({'INFO'}, message)

        if not self.save_fcpxml:
            return {'FINISHED'}

        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        out_path = base_dir + '\\Blender_Storyboards.fcpxml'

        file = open(out_path, 'w')
        file.write('<?xml version='+chr(34)+'1.0'+chr(34)+' encoding='+chr(34)+'UTF-8'+chr(34)+'?>\n')
        file.write('<!DOCTYPE fcpxml>\n')
        file.write('<fcpxml version='+chr(34)+'1.6'+chr(34)+'>\n')
        file.write('\t<resources>\n')
        frame_duration = chr(34)+str(int(100*render.fps_base))+'/'+str(int(100*render.fps))+'s'+chr(34)
        x = chr(34)+str(bpy.context.scene.render.resolution_x)+chr(34)
        y = chr(34)+str(bpy.context.scene.render.resolution_y)+chr(34)
        file.write('\t\t<format id='+chr(34)+'r1'+chr(34)+' frameDuration='+frame_duration+' width='+x+' height='+y+'/>\n')
        file.write('\t\t<format id='+chr(34)+'r2'+chr(34)+' name='+chr(34)+'FFVideoFormatRateUndefined'+chr(34)+' width='+x+' height='+y+'/>\n')
        file.write('\t\t<format id='+chr(34)+'r3'+chr(34)+' name='+chr(34)+'FFVideoFormatRateUndefined'+chr(34)+' />\n')
        for n, f in enumerate(files):
            name = chr(34)+f[0]+chr(34)
            path = chr(34)+base_dir+f[1]+chr(34)
            id = chr(34)+'r'+str(n+4)+chr(34)
            file.write('\t\t<asset id='+id+' name='+name+' src='+path+' start='+chr(34)+'0s'+chr(34)+' duration='+chr(34)+'0s'+chr(34)+' hasVideo='+chr(34)+'1'+chr(34)+' format='+chr(34)+'r2'+chr(34)+' />\n')
        file.write('\t</resources>\n')
        file.write('\t<library>\n')
        file.write('\t\t<event name='+chr(34)+'Blender Storyboards'+chr(34)+'>\n')
        file.write('\t\t\t<project name='+chr(34)+'text'+chr(34)+'>\n')
        file.write('\t\t\t\t<sequence format='+chr(34)+'r1'+chr(34)+' renderColorSpace='+chr(34)+'Rec. 709'+chr(34)+'>\n')
        file.write('\t\t\t\t\t<spine>\n')
        for n, f in enumerate(files):
            offset = chr(34)+str(100*int(render.fps_base)*f[2])+'/'+str(100*render.fps)+'s'+chr(34)
            duration = chr(34)+str(100*int(render.fps_base)*f[3])+'/'+str(100*render.fps)+'s'+chr(34)
            file.write('\t\t\t\t\t\t<video name='+chr(34)+str(n+1)+'A'+chr(34)+' offset='+offset+' ref='+chr(34)+'r'+str(4+n)+chr(34)+' duration='+duration+' start='+chr(34)+'0s'+chr(34)+'></video>\n')
        file.write('\t\t\t\t\t</spine>\n')
        file.write('\t\t\t\t</sequence>\n')
        file.write('\t\t\t</project>\n')
        file.write('\t\t</event>\n')
        file.write('\t</library>\n')
        file.write('</fcpxml>\n')
        file.close()

        message = f'Done! renderered {len(spans)} marker images and {out_path} saved'

        self.report({'INFO'}, message)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def menu_render_markers(self, context):
    self.layout.separator()
    self.layout.operator("sequencer.preview_from_markers")

def register():
    bpy.utils.register_class(RENDER_MARKER_OT_preview)
    bpy.types.SEQUENCER_MT_marker.append(menu_render_markers)

def unregister():
    bpy.utils.unregister_class(RENDER_MARKER_OT_preview)
    bpy.types.SEQUENCER_MT_marker.remove(menu_render_markers)

if __name__ == "__main__":
    register()
