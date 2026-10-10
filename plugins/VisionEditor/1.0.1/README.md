# Visual Editor

**By SaintVertigo**

Visual Editor is a Radiant plugin for Call of Duty: Black Ops III. Version 1.0.1 adds fixes and UI improvements for Bloom and Color LVI editing, LUT authoring, and Vision Set editing.

## Upgrade from v1.0.0

The public name is **Visual Editor**, while the MTPlugins install identifier remains VisionEditor. Keeping that identifier and the matching VisionEditor.dll lets MTPlugins recognize v1.0.1 as an update to v1.0.0. The update stays in the existing bin\plugins\VisionEditor folder instead of creating a second plugin.

VisionEditor.ini is included as a user configuration file. MTPlugins installs it only when it is missing, so the existing v1.0.0 settings file is kept during the update. LUT collections and exported assets are stored outside the plugin folder and are left where they are.

## Features

- Edit Bloom and Color .lvi grades with numeric controls, sliders, and reset buttons.
- Apply supported Bloom and Color LVI edits to worldspawn and preview them in Radiant's camera.
- Create a neutral LUT or import an existing image; grade it with Primary controls, Color Wheels, RGB Mixer, and Curves.
- Export a BO3-layout 16-bit TIFF, editable grading project, and matching GDT definitions.
- Create and edit .vision files, including a raw-text view that preserves unknown keys.
- Prepare Vision Set files for a map by copying them into the map's vision folder and adding the zone entry.
- Choose any LUT collection folder with the Windows folder picker; the last-used folder is remembered.

## Install and upgrade

Visual Editor requires the MTPlugins host and Radiant. In Radiant, use Ctrl+Shift+P → Browse plugins and select Visual Editor. MTPlugins will offer v1.0.1 as a normal update for existing v1.0.0 installations.

For a manual installation, extract the package under:
<Black Ops III folder>\bin\plugins\

The DLL path is <Black Ops III folder>\bin\plugins\VisionEditor\VisionEditor.dll. Radiant displays Visual Editor.

## Live preview compatibility

Bloom and Color LVI editing, their supported camera previews, LUT grading/export, and Vision Set editing remain available with the current public host.

Real LUT texture replacement in the camera requires the upcoming MTPlugins host update, which adds SetCameraLutPreview and CameraLutPreviewStatus. Version 1.0.1 checks the host API table before using those callbacks. On an older host, it reports that camera LUT preview needs a host update and skips that preview safely; it does not use a screen tint or overlay. After the host update is installed, the same plugin can use the real in-memory LUT preview.

Vision Set camera color and transition previews also require those host callbacks. Vision Set file editing, saving, raw-text editing, and map preparation remain usable on the current host.

## LUT workflow

Choose New LUT for a neutral base or Open LUT image to import an existing image. Adjust Primary, Color Wheels, RGB Mixer, or Curves. Export LUT creates a separate TIFF, editable project, and GDT assets; the stock BO3 LUT is not overwritten. Build the generated material in APE and include it in the map's zone before assigning it to worldspawn.

## Compatibility

- Windows 10 or 11, 64-bit, with the Black Ops III Mod Tools and MTPlugins installed.
- MTPlugins plugin API version 1; Radiant only.
- The current public host can load Visual Editor. The camera LUT replacement API is supplied by the upcoming host update.
- LUT export uses the BO3 LUT texture layout and GDT template; APE must build the generated material.
- Some Bloom and Color LVI fields are undocumented by BO3; the editor preserves and writes their stored values rather than guessing their meaning.

## Troubleshooting

Open Ctrl+Shift+P → Plugins, select Visual Editor, and check its status for a load error. MTPlugins logs are normally in <Black Ops III folder>\bin\plugins\RadiantPlugins.log.

For help, use MTPlugins' Report a problem command to collect the logs, then include the report and steps that led to the issue when contacting the maintainer.
