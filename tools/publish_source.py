#!/usr/bin/env python3
"""Publish plugins built by build_source.py: the built files go to plugins/<Name>/<version>/ in this repo (older
versions removed), then index.json gets the entry from sources/<Name>.json with each file's sha256. Also copies text-only edits of the
sources files (description, changes, ...) into already published entries. Never runs any of the plugin's code.
Usage: python tools/publish_source.py [--repo <owner/repo>] [--dry-run] [<build folder> ...]
       python tools/publish_source.py [--repo <owner/repo>] [--dry-run] --private <Name> <build folder>
       (private/<Name>.json, run by the private builder: its repo stays out of index.json)
       --repo is accepted for the private builder and unused."""
import hashlib, json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources

INDEX = os.path.join(sources.ROOT, "index.json")
BUILD_ONLY = ("source", "files")

def entry_from(src, files=None, old=None, private=False):
    """The index.json entry for a sources file: its fields, the source pin, and the files (kept from old when not rebuilt)."""
    e = {k: v for k, v in src.items() if k not in BUILD_ONLY}
    if private:
        e["source"] = {"private": True, "commit": src["source"]["commit"]}
    else:
        if not e.get("url"):
            e["url"] = src["source"]["repo"]
        e["source"] = {"repo": src["source"]["repo"], "commit": src["source"]["commit"]}
    e["files"] = files if files is not None else old["files"]
    return e

def publish(build_dir, src, dry, private=False):
    info = json.load(open(os.path.join(build_dir, "build.json"), encoding="utf-8"))
    n, s = src["name"], src["source"]
    if (info["name"], info["version"], info["commit"]) != (n, src["version"], s["commit"]):
        sys.exit(f"{build_dir}: built {info['name']} {info['version']} at {info['commit']}, sources/{n}.json now says {src['version']} at {s['commit']}")
    files, copies = [], []
    for f, b in zip(src["files"], info["files"]):
        local = os.path.join(build_dir, "files", *f["path"].split("/"))
        if b["path"] != f["path"] or hashlib.sha256(open(local, "rb").read()).hexdigest() != b["sha256"]:
            sys.exit(f"{build_dir}: {f['path']} does not match build.json")
        out = {"path": f["path"], "sha256": b["sha256"]}
        if f.get("config"):
            out["config"] = True
        files.append(out)
        copies.append((local, f["path"]))
    # only the listed version is kept in plugins/<Name>/
    folder = os.path.join(sources.ROOT, "plugins", n)
    print(f"> plugins/{n}/{src['version']}/: " + ", ".join(p for _, p in copies), flush=True)
    if not dry:
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        for local, p in copies:
            dest = os.path.join(folder, src["version"], *p.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(local, dest)
    return files

def main():
    args, dry = sys.argv[1:], False
    if "--dry-run" in args:
        args.remove("--dry-run"); dry = True
    if "--repo" in args:
        i = args.index("--repo"); del args[i:i + 2]
    private = None
    if "--private" in args:
        i = args.index("--private"); private = args[i + 1]; del args[i:i + 2]
        if len(args) != 1:
            sys.exit(__doc__)
    srcs, privs = sources.load_all(), sources.load_private()
    for n, s in list(srcs.items()) + list(privs.items()):
        errors = sources.check(n, s)
        if errors:
            sys.exit("\n".join(errors))
    index = json.load(open(INDEX, encoding="utf-8"))
    plugins = index["plugins"]
    pos = {e.get("name"): i for i, e in enumerate(plugins)}
    pend = set(sources.pending(index, srcs)) | set(sources.pending(index, privs))
    if private is not None and private not in privs:
        sys.exit(f"no private/{private}.json")
    built = {}
    for d in args:
        n = json.load(open(os.path.join(d, "build.json"), encoding="utf-8"))["name"]
        if n not in pend:
            sys.exit(f"{n} is not waiting to be published")
        if (n in privs) != (private is not None) or (private is not None and n != private):
            sys.exit(f"{d}: a private build is published with --private <Name>, a public one without")
        if n in pos and sources.version_key(privs.get(n, srcs.get(n))["version"]) <= sources.version_key(plugins[pos[n]].get("version", "0")):
            sys.exit(f"{n}: the version must be higher than the listed {plugins[pos[n]].get('version')}")
        built[n] = publish(d, privs.get(n) or srcs[n], dry, private=n in privs)
    changed = []
    for n, s in list(srcs.items()) + list(privs.items()):
        priv = sources.is_private(s)
        if n in built:
            e = entry_from(s, files=built[n], private=priv)
        elif n in pend:
            print(f"{n}: waiting for its build, index.json keeps the listed version")
            continue
        else:
            e = entry_from(s, old=plugins[pos[n]], private=priv)
        if n in pos:
            if plugins[pos[n]] != e:
                plugins[pos[n]] = e; changed.append(n)
        else:
            pos[n] = len(plugins); plugins.append(e); changed.append(n)
    if changed:
        with open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print("updated in index.json: " + (", ".join(changed) if changed else "nothing"))

if __name__ == "__main__":
    main()
