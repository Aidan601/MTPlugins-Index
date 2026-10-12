#!/usr/bin/env python3
"""Check index.json format, file hashes (downloads unless --offline, files in plugins/ always) and, with --base, that changed files raise the version, and that plugins/ holds only the listed versions.
Also checks sources/*.json and private/*.json (plugins built from source). --pending and --pending-private print the
names waiting to be built as a JSON list.
Usage: python tools/check_index.py [--offline] [--base <file>] [--pending | --pending-private]"""
import hashlib, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources

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

def check_fields(e, where, errors):
    """The fields every entry needs, listed or in sources/."""
    n = e.get("name", "")
    for k in ("displayName", "author", "version", "description"):
        if not isinstance(e.get(k), str) or not e[k].strip():
            errors.append(f"{where}: '{k}' is empty")
    v = e.get("version", "")
    if isinstance(v, str) and v.strip() and not VERSION.match(v):
        errors.append(f"{where}: 'version' must be numbers and dots (1.0, 1.2.3), so the editors can tell which is newer")
    if "changes" in e and (not isinstance(e["changes"], str) or len(e["changes"]) > 200 or "\n" in e["changes"]):
        errors.append(f"{where}: 'changes' must be one line of at most 200 characters")
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
        if not valid_path(f.get("path", "")):
            errors.append(f"{where}: bad path '{f.get('path', '')}'")

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
    srcs, privs = sources.load_all(), sources.load_private()
    if "--pending" in sys.argv:
        print(json.dumps(sources.pending(idx, srcs)))
        return
    if "--pending-private" in sys.argv:
        print(json.dumps(sources.pending(idx, privs)))
        return
    pend = set(sources.pending(idx, srcs)) | set(sources.pending(idx, privs))
    names = set()
    for e in idx["plugins"]:
        n = e.get("name", "")
        where = f"entry '{n}'"
        if not NAME.match(n) or n.lower() == "radiantplugins":
            errors.append(f"{where}: bad name"); continue
        if n.lower() in names:
            errors.append(f"{where}: listed twice")
        names.add(n.lower())
        src_pin = e.get("source")
        if src_pin is not None and (not isinstance(src_pin, dict) or not sources.COMMIT.match(str(src_pin.get("commit", "")))):
            errors.append(f"{where}: 'source' needs a full 40 digit 'commit'")
        elif src_pin and src_pin.get("private") is True:
            if "repo" in src_pin:
                errors.append(f"{where}: a privately reviewed plugin lists no source repo")
            elif n not in privs:
                errors.append(f"{where}: privately built but no private/{n}.json")
        elif src_pin is not None and n not in srcs:
            errors.append(f"{where}: has a 'source' but no sources/{n}.json")
        check_fields(e, where, errors)
        v = e.get("version", "")
        old = base.get(n.lower())
        # new plugins come in only as source builds, the plugins listed before keep their own files
        if base and not old:
            errors.append(f"{where}: a new plugin is submitted as sources/{n}.json or private/{n}.json (tools/submit.py), "
                          "the list then writes its index.json entry")
        if base and old and ("source" in e or "source" in old) and e.get("files") != old.get("files"):
            errors.append(f"{where}: built by the list, its files in index.json are only written by the list's build")
        if old and isinstance(v, str) and VERSION.match(v) and VERSION.match(old.get("version", "")):
            hashes = lambda x: sorted((f.get("path", ""), f.get("sha256", "")) for f in x.get("files", []) if not f.get("config"))
            if hashes(e) != hashes(old) and version_key(v) <= version_key(old["version"]):
                errors.append(f"{where}: the files changed but 'version' did not go up (was {old['version']})")
        files = e.get("files", [])
        for f in files:
            p, u, h = f.get("path", ""), f.get("url", ""), f.get("sha256", "")
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
    listed = {e.get("name", ""): e for e in idx["plugins"]}
    for n in sorted(set(srcs) & set(privs)):
        errors.append(f"private/{n}.json: sources/{n}.json exists too, keep one")
    for n, src in list(srcs.items()) + list(privs.items()):
        where = f"{'private' if n in privs and src is privs[n] else 'sources'}/{n}.json"
        if not NAME.match(n) or n.lower() == "radiantplugins":
            errors.append(f"{where}: bad name"); continue
        check_fields(src, where, errors)
        errors += sources.check(n, src)
        v, e = src.get("version", ""), listed.get(n)
        if n in pend and e and VERSION.match(str(v)) and VERSION.match(e.get("version", "")) and version_key(v) <= version_key(e["version"]):
            errors.append(f"{where}: a new commit needs a higher 'version' than the listed {e['version']}")
        if os.path.isdir(os.path.join("plugins", n)) and not (e and any(not f.get("url") for f in e.get("files", []))):
            errors.append(f"plugins/{n}: built from source, only the list's build writes this folder, delete it")
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
    print(f"{len(idx['plugins'])} plugin(s), {len(srcs) + len(privs)} built from source ({len(pend)} waiting for a build), {len(errors)} error(s)")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
