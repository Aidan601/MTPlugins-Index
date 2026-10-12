# Visual Editor

**By SaintVertigo**

Visual Editor is a Radiant plugin for Call of Duty: Black Ops III. Version 1.0.2 rebuilds the plugin against the finalized MTPlugins camera LUT preview API so live camera LUT grading works with MTPlugins 1.1.0.

## Upgrade

The plugin keeps the `VisionEditor` install identifier and `VisionEditor.dll` filename. MTPlugins recognizes v1.0.2 as an in-place update from v1.0.0 or v1.0.1, so it does not create a duplicate plugin. `VisionEditor.ini` is marked as a user configuration file; the plugin manager keeps an existing settings file when updating.

MTPlugins 1.1.0 intentionally refuses the old v1.0.1 binary because its callback offsets do not match that host's table. Install Visual Editor 1.0.2 to use the camera LUT callbacks safely.

## Features

- Edit Bloom and Color `.lvi` grades with numeric controls, sliders, and reset buttons.
- Apply supported Bloom and Color LVI edits to worldspawn and preview them in Radiant's camera.
- Create a neutral LUT or import an existing image; grade it with Primary controls, Color Wheels, RGB Mixer, and Curves.
- Preview the real LUT texture transformation in Radiant's camera when the host provides the LUT preview API.
- Export a BO3-layout 16-bit TIFF, editable grading project, and matching GDT definitions.
- Create and edit `.vision` files, including a raw-text view that preserves unknown keys.
- Prepare Vision Set files for a map by copying them into the map's vision folder and adding the zone entry.
- Choose any LUT collection folder with the Windows folder picker; the last-used folder is remembered.

## Camera preview compatibility

With MTPlugins 1.1.0 or later, LUT edits are applied to the camera's in-memory LUT texture as you grade. This uses the host's real texture replacement callback; it does not use a colored overlay and does not rewrite the stock game LUT image. Vision Set camera color and transition previews use the same host callbacks.

Older hosts such as MTPlugins 1.0.0 do not have these callback slots. Visual Editor checks the host API table size and function pointers before use, so it loads safely and keeps its other editing and export features available; live camera LUT and Vision Set color/transition preview require the host update.

## Install

In Radiant, use Ctrl+Shift+P → Browse plugins and select Visual Editor. For a manual installation, extract the package under `<Black Ops III folder>\bin\plugins\`. The plugin DLL belongs at `bin\plugins\VisionEditor\VisionEditor.dll`; Radiant displays the name **Visual Editor**.

## LUT workflow

Choose New LUT for a neutral base or Open LUT image to import an existing image. Adjust Primary, Color Wheels, RGB Mixer, or Curves while looking through Radiant's camera. Export LUT creates a separate TIFF, editable project, and GDT assets; the stock BO3 LUT is not overwritten. Build the generated material in APE and include it in the map's zone before assigning it to worldspawn.

## Compatibility notes

- Windows 10 or 11, 64-bit, with the Black Ops III Mod Tools and MTPlugins installed.
- MTPlugins plugin API version 1; Radiant only.
- Real live camera LUT replacement requires MTPlugins 1.1.0 or later.
- LUT export uses the BO3 LUT texture layout and GDT template; APE must build the generated material.
- Some Bloom and Color LVI fields are undocumented by BO3; the editor preserves and writes their stored values rather than guessing their meaning.

## Troubleshooting

Open Ctrl+Shift+P → Plugins, select Visual Editor, and check its status for a load error. MTPlugins logs are normally in `<Black Ops III folder>\bin\plugins\RadiantPlugins.log`.