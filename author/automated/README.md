# Human Authorship Provenance — Automated OTS Stamping

This variant wires **OpenTimestamps** into your writing flow so anchors happen with **no extra steps**.
It uses a Git **post-commit** hook that stamps a Merkle root periodically.

## What it automates
- On every commit, a hook checks if enough time or commits have elapsed since the last anchor.
- If yes, it computes a Merkle root over the recent commit IDs, runs `ots stamp`, and stores the proof in `proofs/`.
- `make manifest` produces `provenance.json` pointing to the latest proof.
- Optional GitHub Actions workflow validates the manifest and uploads it as a build artifact.

## Policy defaults
- Anchor at most every **10 minutes** OR after **20 commits**, whichever comes first.
- You can change these in `scripts/anchor_ots.py` (`ANCHOR_MINUTES`, `ANCHOR_COMMITS`).

## Install
```bash
git init
# Configure signed commits one-time
gpg --full-generate-key   # if needed
gpg --list-secret-keys --keyid-format=long
git config user.name "Your Name"
git config user.email "you@example.com"
git config commit.gpgsign true
git config user.signingkey <YOUR-GPG-KEYID>

# Install hooks
make install-hooks

# Start writing and committing normally
$EDITOR article.md
git add article.md && git commit -m "start"
# Hooks will handle OTS anchoring as you work
```

## Commands
```bash
make anchor        # manual anchor now
make manifest      # regenerate provenance.json from latest proof + HEAD
make sign          # sign provenance.json with GPG
make verify        # check OTS proof exists and is verifiable
```

## CI (optional)
A GitHub Actions workflow is included at `.github/workflows/provenance.yml`. It:
- checks out the repo
- verifies the OTS proof if present
- uploads `provenance.json` and `provenance.json.asc` as artifacts

> Note: OTS verification may fail on a fresh anchor that has not been upgraded yet. That is normal. The workflow will warn but continue.

## Privacy
- Only hashes and proofs are stored. Your draft text never leaves your device.
- `provenance.json` contains content hash and proof pointers only.
