# Plugin list reference

The details behind [README.md](README.md): the submission file, the `index.json` format, how the builds run, and the plugins listed before source builds.

## How Browse installs a plugin

Browse reads `index.json`, downloads each file of a plugin over HTTPS, checks it against the SHA-256 listed there, and only then puts it in `<game>\bin\plugins\<Name>\` and loads it. A file that does not match its hash is never installed.

## The submission file

`tools/submit.py` writes it. To write it by hand, this is the public form (`sources/<Name>.json`):

```json
{
  "name": "MyTool",
  "displayName": "My Tool",
  "author": "you",
  "version": "1.0",
  "description": "One or two sentences.",
  "changes": "What is new in this version, one line.",
  "apps": ["radiant"],
  "apiVersion": 1,
  "source": {
    "repo": "https://github.com/you/MyTool",
    "commit": "0123456789abcdef0123456789abcdef01234567",
    "build": "MyTool.vcxproj"
  },
  "files": [
    { "path": "MyTool.dll", "from": "x64/Release/MyTool.dll" },
    { "path": "MyTool.ini", "from": "MyTool.ini", "config": true }
  ]
}
```

| `source` field | Meaning |
| -------------- | ------- |
| `repo` | `https://github.com/<owner>/<repo>` (public form only) |
| `sealed` | private form only (`private/<Name>.json`): the repo's address and the deploy key, sealed by `submit.py --private` so only the list can read them |
| `commit` | the full commit hash to build; submodules are fetched too (over https, so they must be public) |
| `build` | a `.vcxproj` or `.sln` (built with MSBuild), or a folder with `CMakeLists.txt` (built into `_build/` at the repo root, so `from` is `_build/Release/MyTool.dll`), relative to the repo |
| `configuration`, `platform` | optional, `Release` and `x64` by default |

- `files[].from` is the file's path in your repo after the build. File names may only use letters, digits, `_`, `-` and `.`, and must be unique (they become release asset names).
- A new commit always needs a higher `version`. A pull request that only changes text (description, changes, apps) is copied into `index.json` without a new build.
- Builds use Visual Studio 2026 (toolset v145, or `$(DefaultPlatformToolset)` as the SDK's template uses); VS 2026 has no v143.

## index.json entries

The list writes these after each build. Format:

```json
{
  "name": "MyTool",
  "displayName": "My Tool",
  "author": "you",
  "version": "1.0",
  "description": "One or two sentences.",
  "changes": "What is new in this version, one line.",
  "url": "https://github.com/you/MyTool",
  "apps": ["radiant"],
  "apiVersion": 1,
  "source": { "repo": "https://github.com/you/MyTool", "commit": "..." },
  "files": [
    { "path": "MyTool.dll", "url": "https://github.com/Aidan601/MTPlugins-Index/releases/download/MyTool-1.0/MyTool.dll", "sha256": "..." },
    { "path": "MyTool.ini", "url": "https://github.com/Aidan601/MTPlugins-Index/releases/download/MyTool-1.0/MyTool.ini", "sha256": "...", "config": true }
  ]
}
```

| Field | Meaning |
| ----- | ------- |
| `name` | the plugin's identifier: letters, digits, `_` or `-`; equal to the DLL name and to `api.name` in the plugin |
| `version` | numbers and dots (`1.0`, `1.2.3`), equal to `api.version` in the plugin. The editors compare it with the installed DLL's version: changed files without a newer version show as "Modified", never as an update |
| `changes` | optional: one line (200 characters at most), shown in the update question |
| `apps` | the editors it runs in: `"radiant"`, `"ape"`, `"launcher"` |
| `apiVersion` | the `MODTOOLS_PLUGIN_API_VERSION` the plugin was built with |
| `url` | optional: shown as "Website" in the Plugins window; a public source build uses its repo |
| `source` | `{repo, commit}` for a public build, `{private: true, commit}` for a private one; absent for the plugins listed before source builds |
| `files[].path` | where the file goes inside the plugin's folder, `/` for subfolders; must include `<name>.dll` |
| `files[].url` | an `https://` download URL; without it the file is taken from `plugins/<name>/<version>/<path>` in this repo |
| `files[].sha256` | the SHA-256 of that exact file, lowercase hex |
| `files[].config` | `true` for settings files: installed only when missing, so an update keeps the user's settings |

## Plugins listed before source builds

PhysX Placement, Spline Props, Visual Editor, Smart Props and Color Log were listed with their own built files before the list built from source. They stay, and may keep publishing updates this way; moving to a source build is welcome at any time (`tools/submit.py` with a higher version).

1. Build the plugin in Release.
2. Put the files where Browse can download them: in this repo (`python tools/make_entry.py <plugin folder> --version 1.1` copies them into `plugins/<Name>/1.1/` and removes the old version folder), or as assets of a new GitHub release of your own (`python tools/make_entry.py <plugin folder> https://github.com/<you>/<repo>/releases/download/<tag>`; never replace files in a release that is already listed).
3. Put the printed fields and hashes into your entry in `index.json`, raise `version`, and open a pull request. The check compares every file with its hash.

## Review

- The maintainer runs `python tools/review.py <pull request number>`: it fetches each submitted commit (a private one with its sealed key) into `~/.mtplugins-review/<Name>/`, lists the files changed since the listed version, the build files among them and every line with a risky call; `--build` also builds it (Windows).
- The review reads the build files too (`.vcxproj` build events, custom MSBuild targets, CMake `execute_process` and custom commands): whatever the build outputs is what users get.
- A submission changes only its own `sources/`, `private/` or `plugins/` files (and, for the plugins listed before, its `index.json` entry). Changes to `tools/` or `.github/` from a submission are not merged. The check refuses a new plugin written straight into `index.json` and hand edits of a built plugin's files.

## How the builds run

- `.github/workflows/check.yml`: on a pull request, checks the format and hashes and builds the public submissions (nothing built there is published).
- `.github/workflows/publish.yml`: after a merge, builds the public submissions in a job with a read-only token; a separate job that never runs plugin code creates the release `<Name>-<version>` and commits `index.json`. Private submissions are handed to the list's private builder, which fetches, builds and publishes them the same way without the code reaching this repo.
- An entry stays at its listed version until the new build is published, so a failed build never removes a plugin. Re-run "Publish plugins built from source" in Actions after a fix.
- Scripts: `build_source.py` (fetch exactly the pinned commit and build), `publish_source.py` (release and `index.json`), `check_index.py` (`--pending`, `--pending-private`), `seal.py` (seal and open private submissions; `list_key.txt` is the list's public key), `submit.py`, `review.py`, `make_entry.py`.
