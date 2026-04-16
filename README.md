# SIM Anialign Enhanced (Blender Add-on)

Aligns a "follower" object/bone to a "target" object/bone over a frame range, keyframing location and rotation on each processed frame. Includes preset save/load and an optional helper-based workflow ("Like it's linked!").

## Install

1. Put the add-on in a folder (e.g. `sim_advanced_anialign/`) containing `__init__.py` and the module files.
2. Zip the folder (the folder itself must be at the root of the zip).
3. In Blender: **Edit -> Preferences -> Add-ons -> Install...** and select the zip.
4. Enable the add-on.

## Where to find it

**View3D -> Sidebar -> SIM Tools -> "SIM Anialign Enhanced"**

## Core concepts

The UI manages a list of alignment pairs. Each pair has:

- `Active`: enables/disables the pair for runs.
- `Follower`: an object, and optionally a bone name (only valid when the follower object is an Armature).
- `Target`: an object, and optionally a bone name (only valid when the target object is an Armature).

## Controls

- `Start Frame`, `End Frame`, `Frame Step`: the processed frame range.
- `Forward` / `Backward`: toggles whether the range is processed from `Start -> End` or `End -> Start`.
- `Delete Helper`: only affects the "Like it's linked!" operator (deletes the helper spheres it creates).

## Operators (exact behavior)

### Run Anialign

- For each active pair and each frame in the chosen range:
  - Reads the target transform (target object world matrix, or armature world * pose bone matrix if a target bone is set).
  - Applies that transform to the follower:
    - If a follower bone is set: writes to `pose_bone.matrix` using `follower_armature.matrix_world.inverted() @ target_matrix`.
    - Otherwise: writes to `follower_object.matrix_world`.
  - Sets rotation mode to `XYZ` and inserts keyframes for:
    - `location`
    - `rotation_euler`

### Run with Offset

- At the time you run the operator, it computes (per active pair) an initial translation offset and Euler rotation difference between follower and target.
- For each processed frame, it applies the target transform plus that saved offset/difference, then keyframes the follower the same way as `Run Anialign`.

### Run 'Like it's linked!'

- At a single reference frame (`Start Frame` when Forward, `End Frame` when Backward):
  - Creates a UV sphere at each follower's position and orientation.
  - Adds a `CHILD_OF` constraint targeting the target object/bone and sets `inverse_matrix` based on the target matrix at that reference frame.
- Then for each processed frame:
  - Uses each sphere's world matrix as the "target matrix" and applies it to the follower (same keyframing behavior as `Run Anialign`).
- If `Delete Helper` is enabled, the created spheres are removed at the end.

## Presets (`.json`)

Save/Load stores:

- The pair list (by object name + bone name + active flag)
- `Start Frame`, `End Frame`, `Frame Step`
- `Delete Helper`
- `Forward/Backward` direction toggle

## Constraints and messages

- Requires a visible `VIEW_3D` area in the current screen layout; otherwise the operators cancel with an error.
- If a bone name is provided but the corresponding object is not an Armature, the operators cancel with an error.
- If a specified bone name is not found, that pair is skipped for that frame (warning is reported).

## Project structure (package add-on)

- `__init__.py` - add-on entry point (`bl_info`, registration)
- `properties.py` - property groups
- `operators_presets.py` - preset operators
- `operators_align.py` - alignment operators
- `operators_selection.py` - selection/pick/toggle operators
- `operators_pairs.py` - add/remove pair operators
- `ui.py` - UI panel and UI list

## Notes

- This add-on depends on Blender's bundled Python modules (`bpy`, `mathutils`, `bpy_extras`) and is intended to run inside Blender.

