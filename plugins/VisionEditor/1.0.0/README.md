# Visual Editor

**By SaintVertigo**

Visual Editor is a plugin for Call of Duty: Black Ops III Radiant. It brings map-grade editing, LUT authoring, and Vision Set editing into Radiant so you can work while viewing the map camera.

## Features

- Edit Bloom and Color values in BO3 `.lvi` grade files, with numeric fields, sliders, row resets, and reset-all controls.
- Preview worldspawn-linked Bloom and Color edits in Radiant's camera.
- Create a neutral BO3 LUT or open an existing LUT image and grade it with primary controls, color wheels, an RGB mixer, and custom RGB and secondary curves.
- Preview the actual LUT transform in Radiant's camera and export a BO3-layout 16-bit TIFF, editable project JSON, and GDT material/image definitions.
- Save and reopen editable LUT projects and grading presets.
- Create and edit `.vision` files with structured controls and a raw-text editor that preserves unknown keys and comments.
- Preview supported Vision Set color changes and transitions through Radiant's camera LUT.
- Prepare a `.vision` file for a map by copying it into the map's vision folder and adding its zone rawfile entry.

## Install

Visual Editor requires the MTPlugins host. Install MTPlugins for Black Ops III Mod Tools first.

When Visual Editor is available in the MTPlugins catalog, open Radiant, press **Ctrl+Shift+P**, choose **Browse plugins**, and install **Visual Editor**.

For manual installation, extract the release ZIP into:

```text
<Black Ops III folder>\bin\plugins\
```

The result should be `<Black Ops III folder>\bin\plugins\VisionEditor\VisionEditor.dll`. The folder and DLL keep the plugin's established `VisionEditor` identifier because MTPlugins requires them to match `api.name`; Radiant displays the public name **Visual Editor**. Start Radiant and enable Visual Editor in the Plugins window if needed.

## Use it in Radiant

Open the **Visual Editor** pane from the **Visual Editor** menu. The pane has **Bloom**, **Color**, **LUT**, and **Vision Sets** tabs.

### Bloom and Color LVI grades

Open an existing `.lvi` file or create a new grade. Adjust its values with the sliders or numeric fields. Use **Apply to worldspawn** and **Live preview** to preview the grade in the camera. Changes are saved to the `.lvi` after you stop editing; use **Save** or **Save As** to manage the file directly.

### LUT authoring

Choose **New LUT** for a neutral starting image or **Open LUT image** to import an existing image. Adjust the grade in **Primary**, **Color Wheels**, **RGB Mixer**, or **Curves** while **Live LUT preview** is enabled. The camera preview and exported TIFF use the same LUT transformation.

Use **Export LUT** to create the TIFF, editable JSON project, and GDT definitions in the selected collection. Visual Editor also prepares an APE-visible texture/GDT copy under the BO3 project folders. Build the material in APE and include the asset in the map's zone before assigning it to worldspawn. The stock BO3 LUT image and GDT are not export destinations.

### Vision Sets

Create or open a `.vision` file, edit supported color controls under **Controls**, or edit the full text under **Raw .vision**. **Preview Transition** interpolates supported color values in the Radiant camera. **Prepare for Map** copies the file into the map and adds the zone entry; add the displayed activation call to the map's gameplay script to activate it in game.

## Compatibility and limitations

- Windows 10 or 11, 64-bit, with the Black Ops III Mod Tools and Radiant.
- MTPlugins plugin API version 1, with the Visual Editor plugin enabled in Radiant.
- Live LUT and Vision camera previews require a RadiantPlugins host build that exposes the SDK's `SetCameraLutPreview` callback. Older host builds may load Visual Editor but cannot apply those camera previews.
- Visual Editor targets Radiant only; it does not run in APE or the Mod Tools Launcher.
- LUT export uses the BO3 LUT texture layout and GDT template. APE must build the generated material and the map must include it in its zone.
- Radiant's camera preview for Vision Sets approximates supported color fields through its LUT. It does not reproduce the game's complete vision pipeline: non-color vision effects are not previewed, and some temperature/ramp behavior is approximate.
- Some Bloom and Color LVI fields are undocumented by BO3. The editor preserves and writes their stored values rather than guessing their meaning.

The plugin is built as a 64-bit Release DLL and uses Windows system components and the MTPlugins host; it does not bundle Qt, game files, or third-party runtime DLLs.

## Troubleshooting

Open **Ctrl+Shift+P → Plugins**, select Visual Editor, and check its status for a load error. MTPlugins logs are normally in `<Black Ops III folder>\bin\plugins\RadiantPlugins.log`. A plugin crash dump, when one is written, is saved beside the plugin.

For help, use MTPlugins' **Report a problem** command to collect the logs, then include the report and the steps that led to the problem when contacting the maintainer.
