#!/usr/bin/env python3
"""Check index.json format, file hashes (downloads unless --offline, files in plugins/ always) and, with --base, that changed files raise the version, and that plugins/ holds only the listed versions.
Usage: python tools/check_index.py [--offline] [--base <file>]"""
import hashlib, json, os, re, sys, urllib.request

NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SEG = re.compile(r"^[A-Za-z0-9_. -]+$")
HASH = re.compile(r"^[0-9a-f]{64}$")
VERSION = re.compile(r"^[0-9]+(\.[0-9]+){0,3}$")

def version_key(v):
    parts = [int(x) for x in v.split(".")]
    return parts + [0] * (4 - len(parts))

def valid_path(p):
    if not p or len(p) > 200:
        return False
    return all(s and s not in (".", "..") and SEG.match(s) and not s.endswith((".", " ")) for s in p.split("/"))

def valid_url(u):
    return u.lower().startswith("https://") and len(u) <= 2000 and all(" " < c <= "~" and c != '"' for c in u)

def main():
    offline = "--offline" in sys.argv
    base = {}
    if "--base" in sys.argv:
        old = json.load(open(sys.argv[sys.argv.index("--base") + 1], encoding="utf-8"))
        base = {e.get("name", "").lower(): e for e in old.get("plugins", [])}
    errors = []
    idx = json.load(open("index.json", encoding="utf-8"))
    if idx.get("format") != 1 or not isinstance(idx.get("plugins"), list):
        sys.exit('index.json needs "format": 1 and a "plugins" array')
    names = set()
    for e in idx["plugins"]:
        n = e.get("name", "")
        where = f"entry '{n}'"
        if not NAME.match(n) or n.lower() == "radiantplugins":
            errors.append(f"{where}: bad name"); continue
        if n.lower() in names:
            errors.append(f"{where}: listed twice")
        names.add(n.lower())
        for k in ("displayName", "author", "version", "description"):
            if not isinstance(e.get(k), str) or not e[k].strip():
                errors.append(f"{where}: '{k}' is empty")
        v = e.get("version", "")
        if isinstance(v, str) and v.strip() and not VERSION.match(v):
            errors.append(f"{where}: 'version' must be numbers and dots (1.0, 1.2.3), so the editors can tell which is newer")
        if "changes" in e and (not isinstance(e["changes"], str) or len(e["changes"]) > 200 or "\n" in e["changes"]):
            errors.append(f"{where}: 'changes' must be one line of at most 200 characters")
        old = base.get(n.lower())
        if old and isinstance(v, str) and VERSION.match(v) and VERSION.match(old.get("version", "")):
            hashes = lambda x: sorted((f.get("path", ""), f.get("sha256", "")) for f in x.get("files", []) if not f.get("config"))
            if hashes(e) != hashes(old) and version_key(v) <= version_key(old["version"]):
                errors.append(f"{where}: the files changed but 'version' did not go up (was {old['version']})")
        u = e.get("url", "")
        if not isinstance(u, str) or (u and not valid_url(u)):
            errors.append(f"{where}: 'url' must be empty or the https:// source or project page")
        if not set(e.get("apps", [])) or not set(e.get("apps", [])) <= {"radiant", "ape", "launcher"}:
            errors.append(f"{where}: 'apps' must list radiant, ape and/or launcher")
        if not isinstance(e.get("apiVersion"), int):
            errors.append(f"{where}: 'apiVersion' must be a number")
        files = e.get("files", [])
        if not any(f.get("path", "").lower() == f"{n.lower()}.dll" for f in files):
            errors.append(f"{where}: 'files' must include {n}.dll")
        for f in files:
            p, u, h = f.get("path", ""), f.get("url", ""), f.get("sha256", "")
            if not valid_path(p): errors.append(f"{where}: bad path '{p}'")
            if not HASH.match(h): errors.append(f"{where}: {p}: sha256 must be 64 lowercase hex digits")
            if not u:
                if not (isinstance(v, str) and VERSION.match(v)) or not valid_path(p):
                    continue
                local = os.path.join("plugins", n, v, *p.split("/"))
                if not os.path.isfile(local):
                    errors.append(f"{where}: {p}: no url and no file at {local.replace(os.sep, '/')}")
                elif HASH.match(h) and hashlib.sha256(open(local, "rb").read()).hexdigest() != h:
                    errors.append(f"{where}: {p}: {local.replace(os.sep, '/')} does not match its sha256")
                continue
            if not valid_url(u): errors.append(f"{where}: {p}: url must be empty or https://")
            if offline or not valid_url(u) or not HASH.match(h):
                continue
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "MTPlugins-Index-check"})
                data = urllib.request.urlopen(req, timeout=60).read()
                if hashlib.sha256(data).hexdigest() != h:
                    errors.append(f"{where}: {p}: the downloaded file does not match its sha256")
            except Exception as ex:
                errors.append(f"{where}: {p}: download failed ({ex})")
    if os.path.isdir("plugins"):
        listed = {e.get("name", ""): e for e in idx["plugins"]}
        for d in sorted(os.listdir("plugins")):
            if d not in listed:
                errors.append(f"plugins/{d}: no entry named '{d}' in index.json"); continue
            # only the listed version is ever downloaded, older folders must go
            e = listed[d]
            keep = {e.get("version")} if any(not f.get("url") for f in e.get("files", [])) else set()
            for sub in sorted(os.listdir(os.path.join("plugins", d))):
                if sub not in keep:
                    errors.append(f"plugins/{d}/{sub}: not the listed version ({e.get('version')}), delete it")
    for err in errors:
        print("ERROR", err)
    print(f"{len(idx['plugins'])} plugin(s), {len(errors)} error(s)")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
