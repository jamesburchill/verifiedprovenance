#!/usr/bin/env python3
import argparse, subprocess, os, time, json, pathlib, hashlib, datetime

PROOFDIR = "proofs"
STATE = f"{PROOFDIR}/state.json"
COMMITS_TXT = f"{PROOFDIR}/commits.txt"
ROOT_HEX = f"{PROOFDIR}/merkle_root.hex"
ROOT_BIN = f"{PROOFDIR}/merkle_root.bin"
OTS = "ots"

ANCHOR_MINUTES = 10      # minimum minutes between anchors
ANCHOR_COMMITS = 20      # or if >= this many commits since last anchor

def git(*args):
    return subprocess.check_output(["git", *args]).decode().strip()

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def maybe_load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE,"r"))
        except Exception:
            return {}
    return {}

def save_state(st):
    pathlib.Path(PROOFDIR).mkdir(parents=True, exist_ok=True)
    json.dump(st, open(STATE,"w"), indent=2)

def get_recent_commits(n=ANCHOR_COMMITS):
    # Return up to n most recent commit hashes (newest first)
    try:
        out = git("rev-list", f"--max-count={n}", "HEAD")
        return [c for c in out.splitlines() if c]
    except Exception:
        return []

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1<<16)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def anchor(force=False):
    state = maybe_load_state()
    last_ts = state.get("last_anchor_time", 0)
    last_head = state.get("last_anchor_head", "")
    try:
        head = git("rev-parse","HEAD")
    except Exception:
        return False, "Not a git repo"

    # thresholds
    too_soon = (time.time() - last_ts) < (ANCHOR_MINUTES*60)
    commits_since = 0
    if last_head:
        try:
            rng = git("rev-list", f"{last_head}..HEAD", "--count")
            commits_since = int(rng)
        except Exception:
            commits_since = ANCHOR_COMMITS  # force on error

    if not force and too_soon and commits_since < ANCHOR_COMMITS:
        return False, f"Skip anchor: {commits_since} commits since last, {int((time.time()-last_ts)/60)} minutes elapsed"

    # Build batch list
    commits = get_recent_commits(ANCHOR_COMMITS)
    pathlib.Path(PROOFDIR).mkdir(exist_ok=True, parents=True)
    with open(COMMITS_TXT,"w") as f:
        for c in commits:
            f.write(c+"\n")

    # Simple merkle root approximation: hash of list file (MVP)
    # For a real merkle tree, replace with pairwise hashing. This keeps MVP simple.
    roothex = subprocess.check_output(["sha256sum", COMMITS_TXT]).decode().split()[0]
    open(ROOT_HEX,"w").write(roothex)
    subprocess.check_call(["xxd","-r","-p",ROOT_HEX,ROOT_BIN])

    # ots stamp
    subprocess.check_call([OTS,"stamp",ROOT_BIN])
    # try upgrade; failure is fine
    try:
        subprocess.check_call([OTS,"upgrade",ROOT_BIN])
    except subprocess.CalledProcessError:
        pass

    state.update({
        "last_anchor_time": time.time(),
        "last_anchor_head": head,
        "last_merkle_root_hex": roothex,
        "last_commits_file": COMMITS_TXT,
        "last_root_bin": ROOT_BIN,
        "last_root_hex": ROOT_HEX,
        "updated_at": now_iso()
    })
    save_state(state)
    print(f">> Anchored OTS for HEAD {head[:8]} root {roothex[:12]}...")
    return True, "Anchored"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="force an anchor now")
    args = ap.parse_args()
    ok, msg = anchor(force=args.force)
    if not ok:
        print(msg)
