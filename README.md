# SIM Anialign Enhanced (Blender Add-on)

Blender add-on for aligning objects/bones with multiple alignment options and preset support.

## Install

1. Put the add-on in a folder (e.g. `sim_advanced_anialign/`) containing `__init__.py` and the module files.
2. Zip the folder (the folder itself must be at the root of the zip).
3. In Blender: **Edit → Preferences → Add-ons → Install…** and select the zip.
4. Enable the add-on.

## Where to find it

**View3D → Sidebar → SIM Tools → “SIM Anialign Enhanced”**

## What it includes

- Standard alignment (`Run Anialign`)
- Offset alignment (`Run with Offset`)
- “Like it’s linked!” helper workflow (`Run 'Like it's linked!'`) with optional helper deletion
- Presets save/load (`.json`)

## Project structure (package add-on)

- `__init__.py` — add-on entry point (`bl_info`, registration)
- `properties.py` — property groups
- `operators_presets.py` — preset operators
- `operators_align.py` — alignment operators
- `operators_selection.py` — selection/pick/toggle operators
- `operators_pairs.py` — add/remove pair operators
- `ui.py` — UI panel and UI list

## Notes

- This add-on depends on Blender’s bundled Python modules (`bpy`, `mathutils`, `bpy_extras`) and is intended to run inside Blender.

