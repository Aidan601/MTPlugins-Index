#!/usr/bin/env python3
"""Maintainer: review the submissions of one pull request. Fetches each pinned commit (a private one with its sealed
deploy key) into ~/.mtplugins-review/<Name>/ and lists the files changed since the listed version, the build files among
them and every line with a risky call. --build also builds it here (Windows). Merging the pull request publishes it.
Usage: python tools/review.py <pull request number> [--build] [--key <list key file>]
       python tools/review.py --file <sources or private json> [--build] [--key <list key file>]"""
import json, os, re, shutil, subprocess, sys, tempfile, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources

LIST = "Aidan601/MTPlugins-Index"
INDEX = f"https://raw.githubusercontent.com/{LIST}/main/index.json"
BASE = os.path.join(os.path.expanduser("~"), ".mtplugins-review")
# the Windows profile's copy is found from WSL too
KEY = os.environ.get("MTPLUGINS_LIST_KEY") or next((p for p in [os.path.join(os.path.expanduser("~"), ".mtplugins-keys", "list.key")]
      + sorted(__import__("glob").glob("/mnt/c/Users/*/.mtplugins-keys/list.key")) if os.path.isfile(p)), "~/.mtplugins-keys/list.key")
HOST_KEY = "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
BUILD_FILES = re.compile(r"(\.(vcxproj|props|targets|sln|cmake|bat|cmd|ps1|py|sh)|CMakeLists\.txt)$", re.I)
RISKY = re.compile(r"URLDownload|WinHttp|InternetOpen|HttpOpen|WSAStartup|\bsocket\s*\(|\bconnect\s*\(|CreateProcess|ShellExecute|WinExec|"
                   r"\bsystem\s*\(|_popen|LoadLibrary|GetProcAddress|VirtualAlloc|VirtualProtect|WriteProcessMemory|CreateRemoteThread|"
                   r"RegSetValue|RegCreateKey|CryptUnprotect|RadiantAddress|ApeAddress|Detour|__readgsqword|"
                   r"PreBuildEvent|PostBuildEvent|PreLinkEvent|<Exec\b|execute_process|add_custom_command|file\s*\(\s*DOWNLOAD", re.I)
SOURCE_EXT = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".inl", ".vcxproj", ".props", ".targets", ".cmake", ".txt", ".bat", ".cmd", ".ps1", ".py")
BINARY_EXT = (".dll", ".exe", ".lib", ".obj", ".bin", ".pyd")

def git(repo, *args, capture=False):
    r = subprocess.run(["git", "-C", repo, *args], check=True, text=True, capture_output=capture)
    return r.stdout if capture else None

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MTPlugins-Index-review"}), timeout=60).read()

def pr_submissions(number):
    files = json.loads(subprocess.run(["gh", "api", "--paginate", f"repos/{LIST}/pulls/{number}/files"],
                                      capture_output=True, text=True, check=True).stdout)
    subs, others = [], []
    for f in files:
        fn = f["filename"]
        if re.match(r"^(sources|private)/[A-Za-z0-9_-]+\.json$", fn) and f["status"] != "removed":
            subs.append((fn, json.loads(get(f["raw_url"]))))
        else:
            others.append(f"{f['status']} {fn}")
    return subs, others

def review(fn, e, listed, build, key_file):
    import check_index
    name = os.path.splitext(os.path.basename(fn))[0]
    errors = sources.check(name, e)
    check_index.check_fields(e, fn, errors)
    old = listed.get(name)
    if old and sources.version_key(e.get("version", "0")) <= sources.version_key(old.get("version", "0")):
        errors.append(f"{fn}: version {e.get('version')} is not higher than the listed {old.get('version')}")
    print(f"\n==== {name} {e.get('version')} by {e.get('author')} ({'private' if sources.is_private(e) else 'public'} source)")
    print(f"     {e.get('description')}\n     changes: {e.get('changes', '')}\n     runs in: {', '.join(e.get('apps', []))}")
    if errors:
        print("PROBLEMS (ask the author for a fixed pull request):\n  " + "\n  ".join(errors))
        return False
    s = e["source"]
    work = os.path.join(BASE, name)
    repo = os.path.join(work, "repo")
    os.makedirs(repo, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="mtp-review-")
    try:
        if sources.is_private(e):
            import seal
            if not os.path.isfile(key_file):
                sys.exit(f"no list key at {key_file} (--key or MTPLUGINS_LIST_KEY)")
            info = json.loads(seal.unseal(s["sealed"], open(key_file, encoding="ascii").read()))
            url = info["repo"]
            key = os.path.join(tmp, "key")
            fd = os.open(key, os.O_WRONLY | os.O_CREAT, 0o600); os.write(fd, info["key"].encode("ascii")); os.close(fd)
            known = os.path.join(tmp, "known_hosts")
            open(known, "w").write(HOST_KEY + "\n")
            os.environ["GIT_SSH_COMMAND"] = f'ssh -i "{key}" -o IdentitiesOnly=yes -o UserKnownHostsFile="{known}" -o StrictHostKeyChecking=yes'
            fetch_url = "git@github.com:" + url[len("https://github.com/"):] + ".git"
            print(f"     repo: {url} (private)")
        else:
            url = fetch_url = s["repo"] + ".git"
        if not os.path.isdir(os.path.join(repo, ".git")):
            git(repo, "init", "-q")
        git(repo, "config", "core.autocrlf", "false")
        old_commit = (old or {}).get("source", {}).get("commit")
        try:
            git(repo, "fetch", "-q", "--depth", "1", fetch_url, *([s["commit"], old_commit] if old_commit and old_commit != s["commit"] else [s["commit"]]))
            git(repo, "checkout", "-q", "--force", "--detach", s["commit"])
            git(repo, "submodule", "update", "-q", "--init", "--recursive", "--depth", "1")
        except subprocess.CalledProcessError:
            print("PROBLEM: could not fetch that commit (not pushed, or the deploy key was removed from the repo)")
            return False
    finally:
        os.environ.pop("GIT_SSH_COMMAND", None)
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"     code: {repo}")
    if old_commit and old_commit != s["commit"]:
        changed = git(repo, "diff", "--name-only", old_commit, s["commit"], capture=True).split()
        print(f"\nChanged since the listed {old['version']}: {len(changed)} file(s). Full diff: git -C \"{repo}\" diff {old_commit} {s['commit']}")
    else:
        changed = git(repo, "ls-files", capture=True).split()
        print(f"\nNew to the list built from source: read the whole tree ({len(changed)} files).")
    for f in changed:
        print(("  BUILD " if BUILD_FILES.search(f) else "        ") + f)
    print("\nLines with risky calls (read each one):")
    hits = 0
    for f in changed:
        p = os.path.join(repo, *f.split("/"))
        # the SDK header names every host function, its lines are no finding
        if not os.path.isfile(p) or not f.lower().endswith(SOURCE_EXT) or os.path.basename(f).lower().startswith("modtools_plugin."):
            continue
        for n, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            if RISKY.search(line):
                hits += 1
                print(f"  {f}:{n}: {line.strip()[:160]}")
    if not hits:
        print("  none")
    binaries = [f for f in changed if f.lower().endswith(BINARY_EXT)]
    if binaries:
        print("\nPrebuilt binaries (the build can link or copy them, find out what they are):\n  " + "\n  ".join(binaries))

    if build:
        sub = os.path.join(work, "submission.json")
        json.dump(e, open(sub, "w", encoding="utf-8"), indent=2)
        out = os.path.join(work, "out")
        r = subprocess.run([sys.executable, os.path.join(sources.ROOT, "tools", "build_source.py"), name, out, "--no-fetch", "--work", work, "--file", sub])
        print("\nTest build: " + ("OK, files in " + os.path.join(out, "files") if r.returncode == 0 else "FAILED (ask the author for a fix)"))
        return r.returncode == 0
    return True

def main():
    sys.stdout.reconfigure(line_buffering=True)
    args = sys.argv[1:]
    build = "--build" in args
    args = [a for a in args if a != "--build"]
    key_file = KEY
    if "--key" in args:
        i = args.index("--key"); key_file = args[i + 1]; del args[i:i + 2]
    listed = {e.get("name"): e for e in json.loads(get(INDEX)).get("plugins", [])}
    if len(args) == 2 and args[0] == "--file":
        subs, others, number = [(args[1], json.load(open(args[1], encoding="utf-8")))], [], None
    elif len(args) == 1 and args[0].isdigit():
        number = args[0]
        subs, others = pr_submissions(number)
    else:
        sys.exit(__doc__)
    if others:
        print("This pull request also changes (a submission changes only its own json, read these closely):\n  " + "\n  ".join(others))
    if not subs:
        sys.exit("no sources/ or private/ submission in it")
    ok = all([review(fn, e, listed, build, key_file) for fn, e in subs])
    if number:
        print(f"\n{'Looks complete' if ok and not others else 'Not ready'}. After reading the code, merge to publish: gh pr merge {number} --repo {LIST} --squash")

if __name__ == "__main__":
    main()
