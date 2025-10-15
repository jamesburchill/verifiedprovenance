#!/usr/bin/env python3
import json, subprocess, hashlib, os, sys, pathlib, datetime

ARTICLE = os.environ.get("ARTICLE", "article.md")
PROOFDIR = "proofs"
ROOTHEX_PATH = f"{PROOFDIR}/merkle_root.hex"

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

if not os.path.exists(ARTICLE):
    print(f"Error: {ARTICLE} not found", file=sys.stderr)
    sys.exit(1)

content_hash = sha256(ARTICLE)
head = git("rev-parse", "HEAD")

roothex = ""
if os.path.exists(ROOTHEX_PATH):
    roothex = pathlib.Path(ROOTHEX_PATH).read_text().strip()
else:
    print("Warning: no proofs/merkle_root.hex yet. Run `make anchor` for a timestamp.", file=sys.stderr)

manifest = {
  "spec":"human-authorship-provenance/0.1",
  "content":{"sha256":content_hash},
  "author":{
    "did":"did:key:REPLACE_ME",
    "keys":[{"kid":"gpg-main","alg":"pgp","pub":"REPLACE_WITH_GPG_FPR_OR_PUB"}],
    "disclosures":{"ai_used": False, "segments":[]}
  },
  "timeline":{
    "repo_commit_head": head,
    "anchors":[
      {
        "type":"opentimestamps",
        "from_commit":"",          # optional in MVP
        "to_commit": head,
        "merkle_root": roothex,
        "proof_uri": "proofs/merkle_root.bin.ots",
        "bitcoin_txid": ""
      }
    ] if roothex else []
  },
  "signatures":[],
  "publisher":{"domain":"","at":datetime.datetime.utcnow().isoformat()+"Z","commitment":f"sha256:{content_hash}"}
}

with open("provenance.json","w",encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
