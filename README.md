<p align="center"><img src="assets/logo-wide.png" alt="MTPlugins" width="640"></p>

# MTPlugins plugin list

This is the list of plugins people can install from **Browse plugins** in the MTPlugins Plugins window (Ctrl+Shift+P in Radiant or APE). Anyone can add their plugin.

The list builds every plugin itself from its source code, after the code has been read. So the DLL people install is always made from code that was checked.

## Before you start

- Your plugin is made with the MTPlugins SDK, and its DLL is named after the plugin (`MyTool.dll` for a plugin called `MyTool`).
- Its code is in a GitHub repo, public or private, with the SDK headers inside it.
- It builds in Visual Studio 2026 (Release, x64) or with CMake.
- You have [Python](https://www.python.org/downloads/) and [Git](https://git-scm.com/) installed.

## Submit your plugin

1. **Push** the version you want to release to your plugin's GitHub repo.
2. **Fork** this repo on GitHub and clone your fork.
3. **Run** this from the clone, pointing it at your plugin's folder:

   ```
   python tools/submit.py C:\path\to\MyTool
   ```

   It asks a few questions (name, description, which editors it runs in) and writes one file, `sources/MyTool.json`. Add `--test-build` to build it on your PC first and catch errors early.
4. **Open a pull request** with that one file. The script prints the commands.

That's all. Once your pull request is reviewed and merged, the list builds your plugin and it shows up in Browse plugins.

### If your repo is private

Run it with `--private` instead (first time only: `python -m pip install pynacl`):

```
python tools/submit.py C:\path\to\MyTool --private
```

It adds a read-only key to your repo so the list can build it, then writes `private/MyTool.json`. Only the list's maintainer reads your code. Your repo's address is never shown anywhere public. The key can only read that one repo, and you can delete it any time (your repo's Settings > Deploy keys).

If you have the [GitHub CLI](https://cli.github.com/) logged in, it adds the key for you. Otherwise it shows you the key and where to paste it.

## Release an update

1. Push the new version to your plugin's repo.
2. Run `python tools/submit.py C:\path\to\MyTool` again. It remembers everything and only asks for the new version number and one line on what changed.
3. Open a pull request with the updated file.

Use a higher version number every time, and set the same number as `api.version` in your plugin. People who have your plugin then see "Update available".

## Rules

- No downloading and running other code, and no changing files outside your plugin's own folder without asking the user.
- Your pull request changes only your plugin's own file.
- Plugins run inside the editor with the user's full rights, so code that cannot be checked is not listed.

## Questions

**Do I need to upload a DLL?** No. The list builds it from your code. Built DLLs without their source are not accepted for new plugins.

**What if the build fails?** The pull request shows the error (with `--test-build` you see it on your PC first). Fix it, push, run `submit.py` again and update your pull request.

**Where do settings go?** An `.ini` named after your plugin is picked up by `submit.py` and installed only when the user has none, so updates keep their settings.

**MTPlugins' own plugins?** They are not in this list: they come with the MTPlugins installer.

Technical details (the file format, how the builds run, plugins listed before source builds): [REFERENCE.md](REFERENCE.md).
