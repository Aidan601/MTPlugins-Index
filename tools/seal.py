#!/usr/bin/env python3
"""Encryption for private submissions: a libsodium sealed box to the list's public key (tools/list_key.txt), so only the
list's builder and the maintainer can read a private repo's address and deploy key. Needs PyNaCl (pip install pynacl).
Usage: python tools/seal.py keygen <private key file>        (maintainer, once: prints the public key for tools/list_key.txt)
       python tools/seal.py open <private/<Name>.json> <private key file | env:VAR> <out folder>   (writes repo.txt and key)"""
import base64, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def nacl():
    try:
        from nacl.public import PrivateKey, PublicKey, SealedBox
        return PrivateKey, PublicKey, SealedBox
    except ImportError:
        sys.exit("needs PyNaCl: python -m pip install pynacl")

def seal(data):
    _, PublicKey, SealedBox = nacl()
    pub = open(os.path.join(HERE, "list_key.txt"), encoding="ascii").read().split()[0]
    return base64.b64encode(SealedBox(PublicKey(base64.b64decode(pub))).encrypt(data)).decode("ascii")

def unseal(blob, private_b64):
    PrivateKey, _, SealedBox = nacl()
    return SealedBox(PrivateKey(base64.b64decode(private_b64.strip()))).decrypt(base64.b64decode(blob))

def read_private(where):
    if where.startswith("env:"):
        v = os.environ.get(where[4:], "")
        if not v:
            sys.exit(f"{where[4:]} is empty")
        return v
    return open(where, encoding="ascii").read()

def open_entry(path, private_b64):
    """The sealed part of a private submission: {"repo": ..., "key": ...}."""
    e = json.load(open(path, encoding="utf-8"))
    return json.loads(unseal(e["source"]["sealed"], private_b64))

def main():
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "keygen":
        PrivateKey, _, _ = nacl()
        if os.path.exists(a[1]):
            sys.exit(f"{a[1]} already exists")
        k = PrivateKey.generate()
        os.makedirs(os.path.dirname(os.path.abspath(a[1])), exist_ok=True)
        fd = os.open(a[1], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, base64.b64encode(bytes(k)) + b"\n"); os.close(fd)
        print(base64.b64encode(bytes(k.public_key)).decode("ascii"))
    elif len(a) == 4 and a[0] == "open":
        info = open_entry(a[1], read_private(a[2]))
        os.makedirs(a[3], exist_ok=True)
        open(os.path.join(a[3], "repo.txt"), "w", encoding="ascii").write(info["repo"] + "\n")
        fd = os.open(os.path.join(a[3], "key"), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, info["key"].encode("ascii")); os.close(fd)
        print(f"opened {os.path.basename(a[1])}")
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
