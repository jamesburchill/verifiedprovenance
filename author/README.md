# Human Authorship Provenance

This repo gives you a practical, low-friction workflow to prove *you* authored content over time — without blockchains on every keystroke and **without** any NFTs.

## What this does
- Captures an authorship trail using **Git signed commits** (GPG)
- Periodically anchors a **Merkle root** via **OpenTimestamps (OTS)** to get a durable Bitcoin-backed timestamp
- Emits a compact `provenance.json` you can ship alongside your article
- Provides a simple `verify_provenance.py` checker users or indexers can run

## Prereqs
- Git
- GPG (for commit signing)
- Python 3.9+
- OpenTimestamps client: `pip install opentimestamps-client`
- Optional: IPFS CLI if you want to pin proofs (`ipfs add -r proofs/`)

## Quick start
```bash
# 0) Clone this folder where you write
cd author

# 1) Init a local Git repo and set commit signing (one-time)
git init
gpg --full-generate-key    # if you do not have a GPG key
gpg --list-secret-keys --keyid-format=long
git config user.name "Your Name"
git config user.email "you@example.com"
git config commit.gpgsign true
git config user.signingkey <YOUR-GPG-KEYID>

# 2) Start writing
$EDITOR article.md

# Commit often (manual) or run autosave to commit every 60s
./autosave.sh

# 3) Periodically anchor last N commits with OpenTimestamps
make anchor

# 4) Generate provenance.json and sign it
make manifest
make sign

# 5) Verify locally
make verify
python3 scripts/verify_provenance.py --file article.md --manifest provenance.json --sig provenance.json.asc
```

## What to publish with your article
- `article.md` (or your rendered HTML/PDF)
- `provenance.json`
- `provenance.json.asc` (the GPG detached signature)
- Optionally, host `/proofs/merkle_root.bin.ots` somewhere and point to it in the manifest

## Add a badge (optional)
Embed this where you publish:
```html
<a href="/path/to/provenance.json" rel="author-provenance">Verified Human Authorship</a>
```

---

### Notes
- We **do not** store your draft text off-device. We only store hashes and OTS proof metadata.
- To disclose AI or pasted segments, populate `author.disclosures` in `provenance.json` before signing.
- If you prefer **did:key** or **did:web**, swap the `author.did` value accordingly later.
