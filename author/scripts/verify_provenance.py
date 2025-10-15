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
    ap = argparse.ArgumentParser(description="Verify human authorship provenance (MVP)")
    ap.add_argument("--file", required=True, help="Path to the content file (e.g., article.md)")
    ap.add_argument("--manifest", default="provenance.json", help="Path to provenance.json")
    ap.add_argument("--sig", default=None, help="Optional GPG detached signature file (provenance.json.asc)")
    args = ap.parse_args()

    # 1) manifest present
    if not os.path.exists(args.manifest):
        print("FAIL: provenance.json not found")
        sys.exit(2)

    man = json.load(open(args.manifest,"r",encoding="utf-8"))

    # 2) content hash matches
    if not os.path.exists(args.file):
        print(f"FAIL: file not found: {args.file}")
        sys.exit(2)
    file_hash = sha256(args.file)
    if file_hash != man.get("content",{}).get("sha256",""):
        print("FAIL: file hash does not match manifest content.sha256")
        sys.exit(2)
    print("OK: content hash matches")

    # 3) repo head matches timeline.repo_commit_head (if in a repo)
    try:
        head = git("rev-parse","HEAD")
        if head != man.get("timeline",{}).get("repo_commit_head",""):
            print("WARN: git HEAD does not match manifest timeline.repo_commit_head (did you copy files?)")
        else:
            print("OK: git HEAD matches manifest")
    except Exception:
        print("INFO: not a git repo or git not available; skipping HEAD check")

    # 4) OTS proof present
    anchors = man.get("timeline",{}).get("anchors",[])
    if anchors:
        proof_uri = anchors[0].get("proof_uri","")
        if proof_uri and os.path.exists(proof_uri):
            print(f"OK: OTS proof present at {proof_uri} (run `ots verify {proof_uri.replace('.ots','')}` locally)")
        else:
            print("WARN: OTS proof not found locally")
    else:
        print("WARN: No anchors listed in manifest")

    # 5) Optional GPG signature verification
    if args.sig and os.path.exists(args.sig):
        try:
            subprocess.check_call(["gpg","--verify",args.sig,args.manifest])
            print("OK: provenance.json GPG signature valid")
        except subprocess.CalledProcessError:
            print("FAIL: provenance.json GPG signature invalid")
            sys.exit(2)

    print("DONE: basic checks complete")

if __name__ == "__main__":
    main()
