#!/usr/bin/env python3
import argparse, json, subprocess, hashlib, os, sys

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1<<16)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def git(*args):
    return subprocess.check_output(["git", *args]).decode().strip()

def main():
    ap = argparse.ArgumentParser(description="Verify human authorship provenance (Automated MVP)")
    ap.add_argument("--file", required=True, help="Path to the content file")
    ap.add_argument("--manifest", default="provenance.json", help="Path to provenance.json")
    ap.add_argument("--sig", default=None, help="Optional GPG detached signature file")
    args = ap.parse_args()

    if not os.path.exists(args.manifest):
        print("FAIL: provenance.json not found"); sys.exit(2)
    man = json.load(open(args.manifest,"r",encoding="utf-8"))

    if not os.path.exists(args.file):
        print(f"FAIL: file not found: {args.file}"); sys.exit(2)
    if sha256(args.file) != man.get("content",{}).get("sha256",""):
        print("FAIL: file hash does not match manifest"); sys.exit(2)
    print("OK: content hash matches")

    try:
        head = git("rev-parse","HEAD")
        if head == man.get("timeline",{}).get("repo_commit_head",""):
            print("OK: git HEAD matches manifest")
        else:
            print("WARN: git HEAD differs from manifest")
    except Exception:
        print("INFO: not a git repo or git not available")

    anchors = man.get("timeline",{}).get("anchors",[])
    if anchors:
        proof_uri = anchors[0].get("proof_uri","")
        if proof_uri and os.path.exists(proof_uri):
            print(f"OK: OTS proof present at {proof_uri}")
        else:
            print("WARN: OTS proof not found locally")
    else:
        print("WARN: No anchors listed in manifest")

    if args.sig and os.path.exists(args.sig):
        try:
            subprocess.check_call(["gpg","--verify",args.sig,args.manifest])
            print("OK: provenance.json GPG signature valid")
        except subprocess.CalledProcessError:
            print("FAIL: provenance.json GPG signature invalid"); sys.exit(2)

    print("DONE")
if __name__ == "__main__":
    main()
