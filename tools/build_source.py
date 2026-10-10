#!/usr/bin/env python3
"""Build one plugin from sources/<Name>.json on Windows: fetch the pinned commit, run MSBuild or CMake, copy the listed files.
Writes <out>/files/<path> for every file and <out>/build.json (name, version, commit, hashes).
Usage: python tools/build_source.py <Name> <out folder> [--work <folder>] [--file <sources json>]
       python tools/build_source.py <Name> --fetch-only --ssh-key <key file> --repo-url <url> --work <folder> --file <json>   (private repo: fetch only)
       python tools/build_source.py <Name> <out folder> --no-fetch --work <folder> --file <json>   (build a tree fetched before)"""
import hashlib, json, os, shutil, stat, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources

def run(*cmd, cwd=None):
    print(">", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)

# GitHub's published SSH host key, so a private fetch never trusts an unknown host
GITHUB_HOST_KEY = "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"

def remove(path):
    # git marks its object files read-only, which stops rmtree on Windows
    def writable(func, p, _):
        os.chmod(p, stat.S_IWRITE); func(p)
    shutil.rmtree(path, onerror=writable)

def msbuild():
    vswhere = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), r"Microsoft Visual Studio\Installer\vswhere.exe")
    out = subprocess.run([vswhere, "-latest", "-products", "*", "-requires", "Microsoft.Component.MSBuild",
                          "-find", r"MSBuild\**\Bin\MSBuild.exe"], capture_output=True, text=True, check=True).stdout.splitlines()
    out = [l.strip() for l in out if l.strip()]
    if not out:
        sys.exit("MSBuild not found (vswhere found no Visual Studio with MSBuild)")
    return out[0]

def is_x64_dll(path):
    with open(path, "rb") as f:
        head = f.read(4096)
    if head[:2] != b"MZ" or len(head) < 64:
        return False
    pe = struct.unpack_from("<I", head, 0x3C)[0]
    if pe + 24 > len(head) or head[pe:pe + 4] != b"PE\0\0":
        return False
    machine, chars = struct.unpack_from("<H", head, pe + 4)[0], struct.unpack_from("<H", head, pe + 22)[0]
    return machine == 0x8664 and bool(chars & 0x2000)

def option(args, flag, value=True):
    if flag not in args:
        return None
    i = args.index(flag)
    if not value:
        del args[i]; return True
    v = args[i + 1]; del args[i:i + 2]
    return v

def fetch(s, repo, work, ssh_key, repo_url):
    """Exactly the pinned commit into <repo>, nothing from a moving branch or tag."""
    if os.path.exists(repo):
        remove(repo)
    os.makedirs(repo)
    url = repo_url + ".git"
    if ssh_key:
        known = os.path.join(work, "known_hosts")
        open(known, "w").write(GITHUB_HOST_KEY + "\n")
        os.chmod(ssh_key, 0o600)
        os.environ["GIT_SSH_COMMAND"] = (f'ssh -i "{os.path.abspath(ssh_key)}" -o IdentitiesOnly=yes '
                                         f'-o UserKnownHostsFile="{known}" -o StrictHostKeyChecking=yes')
        url = "git@github.com:" + repo_url[len("https://github.com/"):] + ".git"
    run("git", "init", "-q", repo)
    # the repo's exact bytes on every machine, Windows git would turn LF into CRLF
    run("git", "-C", repo, "config", "core.autocrlf", "false")
    run("git", "-C", repo, "fetch", "-q", "--depth", "1", url, s["commit"])
    run("git", "-C", repo, "checkout", "-q", "--detach", "FETCH_HEAD")
    head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if head != s["commit"]:
        sys.exit(f"fetched {head}, expected {s['commit']}")
    # submodules come over https, so a private plugin's submodules must be public
    os.environ.pop("GIT_SSH_COMMAND", None)
    run("git", "-C", repo, "submodule", "update", "-q", "--init", "--recursive", "--depth", "1")

def main():
    args = sys.argv[1:]
    work, path, ssh_key = option(args, "--work"), option(args, "--file"), option(args, "--ssh-key")
    repo_url = option(args, "--repo-url")
    fetch_only, no_fetch = option(args, "--fetch-only", False), option(args, "--no-fetch", False)
    if not args or len(args) != (1 if fetch_only else 2) or (fetch_only and no_fetch) or ((fetch_only or no_fetch) and not work):
        sys.exit(__doc__)
    name = args[0]
    out = None if fetch_only else os.path.abspath(args[1])
    path = path or os.path.join(sources.SOURCES, f"{name}.json")
    if not os.path.isfile(path):
        sys.exit(f"no {path}")
    e = json.load(open(path, encoding="utf-8"))
    errors = sources.check(name, e)
    if errors:
        sys.exit("\n".join(errors))
    s = e["source"]
    work = os.path.abspath(work) if work else tempfile.mkdtemp(prefix=f"mtp-{name}-")
    os.makedirs(work, exist_ok=True)
    repo = os.path.join(work, "repo")
    if no_fetch:
        if not os.path.isdir(repo):
            sys.exit(f"--no-fetch: {repo} does not exist")
    else:
        repo_url = repo_url or s.get("repo")
        if not repo_url or not sources.REPO.match(repo_url):
            sys.exit("a private submission needs --repo-url https://github.com/<owner>/<repo> (from tools/seal.py open)")
        fetch(s, repo, work, ssh_key, repo_url)
    if fetch_only:
        print(f"fetched {s['commit']} into {repo}")
        return
    cfg, plat = s.get("configuration", "Release"), s.get("platform", "x64")
    target = os.path.join(repo, *s["build"].replace("\\", "/").split("/"))
    if target.lower().endswith((".vcxproj", ".sln")):
        if not os.path.isfile(target):
            sys.exit(f"source.build: {s['build']} is not in the repo")
        run(msbuild(), target, f"/p:Configuration={cfg}", f"/p:Platform={plat}", "/m", "/nologo", "/v:minimal")
    elif os.path.isfile(os.path.join(target, "CMakeLists.txt")):
        bdir = os.path.join(repo, "_build")
        run("cmake", "-S", target, "-B", bdir, "-A", plat)
        run("cmake", "--build", bdir, "--config", cfg, "--parallel")
    else:
        sys.exit(f"source.build: {s['build']} is neither a .vcxproj, a .sln nor a folder with CMakeLists.txt")

    if os.path.exists(out):
        remove(out)
    os.makedirs(out)
    built = []
    for f in e["files"]:
        src = os.path.join(repo, *f["from"].split("/"))
        if not os.path.isfile(src):
            sys.exit(f"{f['path']}: {f['from']} does not exist after the build")
        dst = os.path.join(out, "files", *f["path"].split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        data = open(dst, "rb").read()
        if f["path"].lower().endswith(".dll") and not is_x64_dll(dst):
            sys.exit(f"{f['path']}: not a 64-bit DLL")
        built.append({"path": f["path"], "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    if not any(b["path"].lower() == f"{name.lower()}.dll" for b in built):
        sys.exit(f"'files' must include {name}.dll")
    info = {"name": name, "version": e["version"], "commit": s["commit"], "files": built}
    json.dump(info, open(os.path.join(out, "build.json"), "w", encoding="utf-8"), indent=2)

    index = json.load(open(os.path.join(sources.ROOT, "index.json"), encoding="utf-8"))
    old = next((x for x in index.get("plugins", []) if x.get("name") == name), {})
    old_commit = (old.get("source") or {}).get("commit")
    if sources.is_private(e):
        review = f"Private source at {s['commit']}"
    elif old_commit:
        review = f"Changes since {old.get('version')}: {s['repo']}/compare/{old_commit}...{s['commit']}"
    else:
        review = f"First build from source: review the whole tree at {s['repo']}/tree/{s['commit']}"
    lines = [f"### {name} {e['version']}", "", review, "",
             "| File | Size | SHA-256 |", "| ---- | ---- | ------- |"]
    lines += [f"| {b['path']} | {b['size']} | `{b['sha256']}` |" for b in built]
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n\n")

if __name__ == "__main__":
    main()
