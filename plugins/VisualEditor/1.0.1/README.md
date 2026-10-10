# Visual Editor

**By SaintVertigo**

Visual Editor edits BO3 Bloom and Color LVI grades, authors LUT textures, and creates Vision Sets inside Radiant.

## Features

- Edit Bloom and Color `.lvi` grades with numeric controls, sliders, and reset buttons.
- Create a neutral LUT or import an existing image; grade with Primary, Color Wheels, RGB Mixer, and Curves.
- Export a BO3-layout 16-bit TIFF, editable grading project, and matching GDT definitions.
- Create and edit `.vision` files, including a raw-text view that preserves unknown keys.
- Use the Windows Explorer folder picker to choose any LUT collection directory.

## Install

Visual Editor requires the MTPlugins host. For a manual install, extract the release ZIP under:

```text
<Black Ops III folder>\bin\plugins\
```

The installed plugin is `VisualEditor\VisualEditor.dll`; its internal identifier, folder, DLL, and INI names all match. Radiant displays **Visual Editor**.

### Upgrade from the old VisionEditor plugin

The published v1.0.0 used the old `VisionEditor` identifier. Before enabling Visual Editor, disable the old plugin in Radiant's Plugins window and restart Radiant. If both versions are loaded, Visual Editor disables its own pane and requests a restart. The new plugin copies `VisionEditor.ini` to `VisualEditor.ini` only when the new settings file is absent. It keeps the old DLL, folder, and settings untouched; remove the old installation manually only after verifying the new one.

Existing LUT collections are not moved or deleted. The default collection for new projects is `texture_assets\visualedit_luts`; the previous `VisionEditor LUTs` folder remains discoverable. The last-used custom folder is retained in plugin settings.

## Use it in Radiant

Open the **Visual Editor** pane from the **Visual Editor** menu. It has **Bloom**, **Color**, **LUT**, and **Vision Sets** tabs.

### Bloom and Color

Open or create an `.lvi` grade. Use **Apply to worldspawn** and **Live preview** to preview supported edits in Radiant's camera. Changes save after editing pauses; **Save** and **Save As** are also available.

### LUT authoring

Choose **New LUT** for a neutral base or **Open LUT image** to import one. Grade it in **Primary**, **Color Wheels**, **RGB Mixer**, or **Curves**. **Export LUT** writes a separate TIFF, editable project, and GDT assets; the stock BO3 LUT is not overwritten. Build the material in APE and include it in the map's zone before assigning it to worldspawn.

**Public host limitation:** the installed public RadiantPlugins host does not expose the camera LUT texture replacement callbacks required for a real live preview. The editor reports this limitation and does not simulate the result with a screen tint. A separate host update is required before camera LUT preview can be advertised as supported. See `UPSTREAM_HOST_LUT_PREVIEW.md` in the prepared release folder for the exact host changes.

### Vision Sets

Create or open a `.vision` file and edit its supported controls or raw text. Camera color and transition previews also require the host's camera LUT callbacks and are unavailable in the currently installed public host. **Prepare for Map** copies the file into the map and adds its zone entry.

## Compatibility

- Windows 10 or 11, 64-bit, with the Black Ops III Mod Tools and MTPlugins installed.
- MTPlugins plugin API version 1; Radiant only.
- Bloom/Color `.lvi` editing and LUT TIFF/GDT export do not require the camera LUT preview callbacks.
- Camera LUT and Vision Set color previews require a host exposing `SetCameraLutPreview` and `CameraLutPreviewStatus`. The current public installation lacks them, so the complete public release is blocked pending a host update.
- Some Bloom and Color LVI fields are undocumented by BO3; stored values are preserved rather than guessed.

## Troubleshooting

Open **Ctrl+Shift+P → Plugins** and select Visual Editor to see its status. MTPlugins logs are normally in `<Black Ops III folder>\bin\plugins\RadiantPlugins.log`. Plugin crash dumps are saved beside the plugin.

For help, use MTPlugins' **Report a problem** command to collect the logs, then include the report and steps that led to the issue when contacting the maintainer.
