"""Shared helpers for plugins built from source: sources/<Name>.json (public repo) and private/<Name>.json (private repo,
its address and deploy key sealed for the list) are read, checked and compared with index.json here."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(ROOT, "sources")
PRIVATE = os.path.join(ROOT, "private")
SEALED = re.compile(r"^[A-Za-z0-9+/=]{100,20000}$")
NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ASSET = re.compile(r"^[A-Za-z0-9_.-]+$")
# filled in by publish_source.py, never written by hand in a sources file
GENERATED = ("url", "sha256")

def version_key(v):
    parts = [int(x) for x in v.split(".")] if re.match(r"^[0-9]+(\.[0-9]+){0,3}$", v) else [0]
    return parts + [0] * (4 - len(parts))

def tag(entry):
    return f"{entry['name']}-{entry['version']}"

def load_all(folder=SOURCES):
    """Every <folder>/*.json as {name: entry}, in file name order."""
    out = {}
    if os.path.isdir(folder):
        for fn in sorted(os.listdir(folder)):
            if fn.endswith(".json"):
                out[fn[:-5]] = json.load(open(os.path.join(folder, fn), encoding="utf-8"))
    return out

def load_private():
    return load_all(PRIVATE)

def is_private(e):
    return isinstance(e.get("source"), dict) and "sealed" in e["source"]

def check(fn_name, e):
    """Errors in one sources or private file (the plain entry fields are checked by check_index.py)."""
    private = is_private(e)
    where, errors = f"{'private' if private else 'sources'}/{fn_name}.json", []
    if e.get("name") != fn_name:
        errors.append(f"{where}: 'name' must equal the file name ({fn_name})")
    s = e.get("source")
    if not isinstance(s, dict):
        return errors + [f"{where}: needs a 'source' object (repo, commit, build)"]
    if private:
        if "repo" in s:
            errors.append(f"{where}: a private submission keeps its repo inside 'sealed' (tools/submit.py --private writes it)")
        if not isinstance(s.get("sealed"), str) or not SEALED.match(s["sealed"]):
            errors.append(f"{where}: source.sealed is not a sealed box from tools/submit.py")
    elif not REPO.match(s.get("repo", "")):
        errors.append(f"{where}: source.repo must be https://github.com/<owner>/<repo>")
    if not COMMIT.match(s.get("commit", "")):
        errors.append(f"{where}: source.commit must be a full 40 digit commit hash (a tag or branch can move)")
    b = s.get("build", "")
    if not isinstance(b, str) or not b or ".." in b.replace("\\", "/").split("/") or b.startswith(("/", "\\")) or ":" in b:
        errors.append(f"{where}: source.build must be a .vcxproj, a .sln or a folder with CMakeLists.txt, relative to the repo")
    for k in ("configuration", "platform"):
        if k in s and not re.match(r"^[A-Za-z0-9_ ]{1,32}$", str(s[k])):
            errors.append(f"{where}: source.{k} has odd characters")
    for f in e.get("files", []):
        p = f.get("path", "")
        if any(k in f for k in GENERATED):
            errors.append(f"{where}: {p}: leave out url and sha256, they are filled in when the plugin is built")
        frm = f.get("from", "")
        if not isinstance(frm, str) or not frm or ".." in frm.split("/") or frm.startswith("/") or "\\" in frm or ":" in frm:
            errors.append(f"{where}: {p}: 'from' must be the file's path in the repo after the build, with / separators")
        a = os.path.basename(p)
        if not ASSET.match(a):
            errors.append(f"{where}: {p}: file names may only use letters, digits, '_', '-' and '.'")
    return errors

def pending(index, sources):
    """Names whose sources file is not yet published: no entry, or another version or commit."""
    listed = {e.get("name"): e for e in index.get("plugins", [])}
    out = []
    for n, s in sources.items():
        if not NAME.match(n):
            continue
        e = listed.get(n)
        if not e or e.get("version") != s.get("version") or (e.get("source") or {}).get("commit") != (s.get("source") or {}).get("commit"):
            out.append(n)
    return out
