# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
from bpy.props import (
    PointerProperty,
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    IntVectorProperty,
)


# -------------------------- #
# Property and Data Classes  #
# -------------------------- #

class AlignmentPair(bpy.types.PropertyGroup):
    custom_name: StringProperty(name="Name", default="")
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
