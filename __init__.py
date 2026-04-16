# pyright: reportMissingImports=false, reportInvalidTypeForm=false

import bpy
from bpy.props import PointerProperty

from .properties import AlignmentPair, SIMAnialignProperties
from .operators_presets import SIM_OT_SavePreset, SIM_OT_LoadPreset
from .operators_align import (
    SIMAnialignOperator,
    SIMAnialignOffsetOperator,
    SIMCreateZeObjectOperator,
)
from .operators_selection import (
    SIM_OT_ToggleDirection,
    SIM_OT_PickFollower,
    SIM_OT_PickFollowerBone,
    SIM_OT_PickTarget,
    SIM_OT_PickTargetBone,
    SIM_OT_GetFollowerSelection,
    SIM_OT_GetTargetSelection,
)
from .operators_pairs import SIM_OT_AddPair, SIM_OT_RemovePair
from .ui import SIM_UL_AlignmentPairs, SIMAnialignPanel

bl_info = {
    "name": "SIM Anialign Enhanced",
    "author": "Sim Sokerov",
    "version": (1, 3, 9),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > SIM Tools",
    "description": "Aligns objects/bones with multiple alignment options and preset support",
    "category": "Animation",
}

classes = (
    AlignmentPair,
    SIMAnialignProperties,
    SIM_OT_SavePreset,
    SIM_OT_LoadPreset,
    SIM_UL_AlignmentPairs,
    SIM_OT_AddPair,
    SIM_OT_RemovePair,
    SIMAnialignOperator,
    SIMAnialignOffsetOperator,
    SIMCreateZeObjectOperator,
    SIM_OT_ToggleDirection,
    SIM_OT_PickFollower,
    SIM_OT_PickFollowerBone,
    SIM_OT_PickTarget,
    SIM_OT_PickTargetBone,
    SIM_OT_GetFollowerSelection,
    SIM_OT_GetTargetSelection,
    SIMAnialignPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.align_props = PointerProperty(type=SIMAnialignProperties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.align_props


if __name__ == "__main__":
    register()

