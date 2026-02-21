# Conformance Test Vectors (Draft v1.1)

This directory contains deterministic vectors for:
- canonical JSON serialization
- artifact URL canonicalization
- event hash computation (`event_hash` excluded from hash input)

Run vectors with:

```bash
python3 scripts/vp_verify.py run-vectors
```

The command exits non-zero when any expected output diverges.
