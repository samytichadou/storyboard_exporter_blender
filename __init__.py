'''
Copyright (C) 2018 Samy Tichadou (tonton)
samytichadou@gmail.com

Created by Samy Tichadou (tonton)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {  
 "name": "Storyboard Exporter",  
 "author": "Samy Tichadou (tonton)",  
 "version": (0, 1),  
 "blender": (2, 91, 2), 
 "location": "",  
 "description": "",  
 "wiki_url": "https://github.com/samytichadou/storyboard_exporter_blender",  
 "tracker_url": "https://github.com/samytichadou/storyboard_exporter_blender/issues/new",  
 "category": "Import-Export",
 "warning": "Alpha version, use at your own risks"
 }


import bpy


# IMPORT SPECIFICS
##################################

from .op_export import *
from .addon_prefs import *


# register
##################################

classes = (
            STORYBOARD_EXPORTER_OT_test_export,
            STORYBOARD_EXPORTER_addon_prefs,
            )

def register():

    ### OPERATORS ###
    from bpy.utils import register_class
    for cls in classes :
        register_class(cls)


def unregister():
    
    ### OPERATORS ###
    from bpy.utils import unregister_class
    for cls in reversed(classes) :
        unregister_class(cls)