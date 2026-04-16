# Agent Instructions (sim_advanced_anialign)

This repository contains a Blender add-on implemented as a Python package (folder add-on) with the entry point in `__init__.py`.

## Non-negotiables

- Do **not** change add-on behavior unless explicitly requested.
- Preserve all Blender identifiers and user-facing strings exactly (e.g. `bl_idname`, `bl_label`, panel ids, property names).
- Keep `classes` registration order stable (registration/unregistration must continue to work exactly as before).
- Avoid refactors that “clean up” logic, rename things, or alter UI layout/flow.

## Structure

- `__init__.py`: `bl_info`, `classes`, `register()` / `unregister()`
- `properties.py`: `PropertyGroup` definitions
- `operators_*.py`: operator classes split by function
- `ui.py`: `Panel`/`UIList` classes

## Local development tips

- Blender runs its own Python; type-checking in a normal Python environment is optional.
- If you see editor warnings for Blender-only modules (`bpy`, `mathutils`, `bpy_extras`), prefer local tooling/stubs rather than code changes that affect runtime.

## Quick manual test (Blender)

1. Install the add-on by zipping the folder (must include `__init__.py` at the zip root folder).
2. Enable it in **Edit → Preferences → Add-ons**.
3. Verify the panel appears at **View3D → Sidebar → SIM Tools**.
4. Run each operator and confirm outputs match the prior behavior.

