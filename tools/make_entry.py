#!/usr/bin/env python3
"""Print an index.json entry for a plugin folder with every file's SHA-256 (*.ini marked config).
Usage: python tools/make_entry.py <plugin folder> <release download base URL>
       python tools/make_entry.py <plugin folder> --version <version>   (copies the files into plugins/<name>/<version>/, no urls)"""
import hashlib, json, os, shutil, sys

def main():
    if len(sys.argv) == 4 and sys.argv[2] == "--version":
        base, version = None, sys.argv[3]
    elif len(sys.argv) == 3 and not sys.argv[2].startswith("--"):
        base, version = sys.argv[2].rstrip("/"), ""
    else:
        sys.exit(__doc__)
    folder = os.path.abspath(sys.argv[1])
    name = os.path.basename(folder)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dest = os.path.join(repo, "plugins", name, version) if base is None else None
    files, seen = [], set()
    for root, _, names in os.walk(folder):
        for n in sorted(names):
            if n.lower().endswith((".pdb", ".lib", ".exp", ".ilk", ".log", ".dmp")):
                continue
            full = os.path.join(root, n)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            entry = {"path": rel, "sha256": hashlib.sha256(open(full, "rb").read()).hexdigest()}
            if base is not None:
                if n.lower() in seen:
                    sys.exit(f"two files are named {n}: release asset names are flat, rename one")
                seen.add(n.lower())
                entry["url"] = f"{base}/{n}"
            if n.lower().endswith(".ini"):
                entry["config"] = True
            files.append((full, entry))
    if not any(e["path"].lower() == f"{name.lower()}.dll" for _, e in files):
        sys.exit(f"{folder} has no {name}.dll (the folder must be named after the plugin)")
    if dest is not None:
        if os.path.exists(dest):
            sys.exit(f"{dest} already exists: a listed version is never changed, raise the version")
        for full, e in files:
            out = os.path.join(dest, *e["path"].split("/"))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(full, out)
        print(f"copied {len(files)} file(s) to {os.path.relpath(dest, repo)}", file=sys.stderr)
    print(json.dumps({"name": name, "displayName": "", "author": "", "version": version, "description": "", "url": "",
                      "apps": ["radiant"], "apiVersion": 1, "files": [e for _, e in files]}, indent=2))

if __name__ == "__main__":
    main()
