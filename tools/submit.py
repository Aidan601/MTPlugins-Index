#!/usr/bin/env python3
"""Write your plugin's submission from your plugin's git repo; then open a pull request with that one file.
Public repo: sources/<Name>.json. Private repo (--private): private/<Name>.json with a read-only deploy key made for the
list, added to your repo (by the GitHub CLI when you have it) and sealed so only the list can read it and your repo's address.
For a new version run it again: it keeps everything and asks for the new version and what changed.
Usage: python tools/submit.py <your plugin repo folder> [--private] [--new-key] [--test-build]"""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources

def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

def ask(question, default=""):
    a = input(f"{question}" + (f" [{default}]" if default else "") + ": ").strip()
    return a or default

def github_url(remote):
    m = re.match(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", remote or "")
    return f"https://github.com/{m.group(1)}/{m.group(2)}" if m else None

def guess_build(repo):
    top = sorted(os.listdir(repo))
    for ext in (".sln", ".vcxproj"):
        hits = [f for f in top if f.lower().endswith(ext)]
        if len(hits) == 1:
            return hits[0]
    return "." if "CMakeLists.txt" in top else ""

def guess_output(repo, name):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            if f.lower() == f"{name.lower()}.dll" and "release" in root.lower():
                return os.path.relpath(os.path.join(root, f), repo).replace(os.sep, "/")
    return f"x64/Release/{name}.dll"

def deploy_key(url):
    """A new read-only deploy key on the author's repo, returned sealed together with the repo's address."""
    import seal
    tmp = tempfile.mkdtemp(prefix="mtp-key-")
    try:
        key = os.path.join(tmp, "key")
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "MTPlugins plugin list", "-f", key], check=True)
        slug = url[len("https://github.com/"):]
        added = shutil.which("gh") and subprocess.run(["gh", "repo", "deploy-key", "add", key + ".pub", "--repo", slug,
                                                       "--title", "MTPlugins plugin list"]).returncode == 0
        if added:
            print(f"added a read-only deploy key 'MTPlugins plugin list' to {slug}")
        else:
            print(f"\nAdd this key to {url}: Settings > Deploy keys > Add deploy key, title 'MTPlugins plugin list',")
            print("'Allow write access' unticked. It can only read this repo, and you can delete it at any time.\n")
            print(open(key + ".pub", encoding="ascii").read())
            input("Press Enter once it is added: ")
        return seal.seal(json.dumps({"repo": url, "key": open(key, encoding="ascii").read()}).encode("utf-8"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    args = sys.argv[1:]
    private, new_key, test = "--private" in args, "--new-key" in args, "--test-build" in args
    args = [a for a in args if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    repo = os.path.abspath(args[0])
    url = github_url(git(repo, "remote", "get-url", "origin"))
    if not url:
        sys.exit(f"{repo}: no GitHub 'origin' remote")
    commit = git(repo, "rev-parse", "HEAD")
    if git(repo, "status", "--porcelain"):
        sys.exit("commit your changes first: the list builds a commit, not your working folder")
    if not git(repo, "branch", "-r", "--contains", "HEAD"):
        sys.exit(f"push {commit[:12]} to GitHub first")

    name = ask("Plugin name (the DLL's name, letters, digits, _ or -)", url.rsplit("/", 1)[1])
    if not sources.NAME.match(name):
        sys.exit("bad name")
    existing = {"sources": os.path.join(sources.SOURCES, f"{name}.json"), "private": os.path.join(sources.PRIVATE, f"{name}.json")}
    old_kind = next((k for k, p in existing.items() if os.path.isfile(p)), None)
    private = private or old_kind == "private"
    path = existing["private" if private else "sources"]
    if old_kind and old_kind != ("private" if private else "sources"):
        sys.exit(f"{name} is already submitted as {old_kind}/{name}.json")

    if old_kind:
        e = json.load(open(path, encoding="utf-8"))
        print(f"{name} {e['version']} is submitted at {e['source']['commit'][:12]}; now {commit[:12]}")
        if e["source"]["commit"] == commit:
            sys.exit("that commit is already submitted: push the new version first")
        while True:
            v = ask("New version", "")
            if re.match(r"^[0-9]+(\.[0-9]+){0,3}$", v) and sources.version_key(v) > sources.version_key(e["version"]):
                break
            print(f"numbers and dots, higher than {e['version']}")
        e["version"], e["changes"] = v, ask("What changed (one line)", "")[:200]
        e["source"]["commit"] = commit
    else:
        e = {"name": name,
             "displayName": ask("Display name", name),
             "author": ask("Author", url.split("/")[3]),
             "version": ask("Version", "1.0"),
             "description": ask("Description (one or two sentences)"),
             "changes": ask("What is new (one line)", "Initial release.")[:200],
             "apps": [a.strip() for a in ask("Editors it runs in: radiant, ape, launcher", "radiant").split(",") if a.strip()],
             "apiVersion": int(ask("apiVersion (MODTOOLS_PLUGIN_API_VERSION)", "1")),
             "source": {"commit": commit, "build": ask("What to build: .sln, .vcxproj or CMake folder", guess_build(repo))},
             "files": [{"path": f"{name}.dll", "from": ask(f"Where is {name}.dll after a Release x64 build", guess_output(repo, name))}]}
        if not private:
            e["source"] = {"repo": url, **e["source"]}
            e["url"] = url
        for f in [x.strip() for x in ask(f"Other files to ship (repo paths, comma separated)", f"{name}.ini" if os.path.isfile(os.path.join(repo, f"{name}.ini")) else "").split(",") if x.strip()]:
            item = {"path": os.path.basename(f), "from": f}
            if f.lower().endswith(".ini"):
                item["config"] = True
            e["files"].append(item)
    if private and (new_key or "sealed" not in e["source"]):
        e["source"]["sealed"] = deploy_key(url)

    import check_index
    errors = sources.check(name, e)
    check_index.check_fields(e, f"{name}", errors)
    if errors:
        sys.exit("\n".join(errors))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(e, indent=2, ensure_ascii=False) + "\n")
    rel = os.path.relpath(path, sources.ROOT).replace(os.sep, "/")
    print(f"\nwrote {rel}")

    if test:
        out = tempfile.mkdtemp(prefix="mtp-test-")
        cmd = [sys.executable, os.path.join(sources.ROOT, "tools", "build_source.py"), name, out, "--file", path, "--repo-url", url]
        print("test build (your own git login fetches the commit)")
        if subprocess.run(cmd).returncode != 0:
            sys.exit("the test build failed: fix it before you open the pull request")

    print(f"""
Next: commit {rel} on a branch of your fork of the plugin list and open a pull request, for example
  git checkout -b {name}-{e['version']}
  git add {rel}
  git commit -m "{name} {e['version']}"
  git push -u origin {name}-{e['version']}
  gh pr create --fill
Once it is merged the list builds and publishes it, nothing else to do.""")

if __name__ == "__main__":
    main()
