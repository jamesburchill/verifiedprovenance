# Verified Provenance

Prove what is real in a synthetic world.

This public repository is the open-facing home for:
- specifications
- public examples
- docs and educational material
- public widgets and integration references

## Scope
- This repo is public-facing only.
- Core/private implementation code is maintained separately.
- Trust boundary policy: `BOUNDARY.md`

## Repository Structure
```text
verifiedprovenance/
├─ docs/
│  └─ spec/                  # Discovery spec draft and example payloads
├─ examples/                 # Public examples and samples
└─ README.md
```

## Specifications
- Discovery spec draft: `docs/spec/verified-provenance-discovery-spec-v1.md`
- Discovery + evidence spec draft (TIME-aligned): `docs/spec/verified-provenance-discovery-spec-v1.1.md`
- Verification profile (v1.1): `docs/spec/verification-profile-v1.1.md`
- Domain document example: `docs/spec/examples/well-known-provenance.example.json`
- Domain document example (v1.1): `docs/spec/examples/well-known-provenance-v1.1.example.json`
- Artifact manifest example: `docs/spec/examples/artifact-provenance.example.json`
- Event example (v1.1): `docs/spec/examples/provenance-event.example.json`
- Chain example (v1.1): `docs/spec/examples/provenance-chain.example.json`
- Conformance vectors (v1.1 draft): `docs/spec/test-vectors/canonicalization-v1.1.json`

## Reference Verifier CLI (Draft)
Run conformance vectors:

```bash
python3 scripts/vp_verify.py run-vectors
```

Verify a local v1.1 chain against a domain policy document:

```bash
python3 scripts/vp_verify.py verify-chain \
  --domain-doc docs/spec/examples/well-known-provenance-v1.1.example.json \
  --chain-doc docs/spec/examples/provenance-chain.example.json \
  --evaluated-at 2026-02-15T00:00:00Z
```

Verify a live URL (discovery + evidence endpoints):

```bash
python3 scripts/vp_verify.py verify-url https://acmewidgets.com/news/new-widget-launch/
```

## Principles
- Open standards
- Portable proofs
- Independent verification
- Privacy-preserving defaults

## Status
This project is under active development and specifications are currently draft (`v1` and `v1.1`).

## License
MIT. See `LICENSE`.

## Links
- Website: [verifiedprovenance.com](https://verifiedprovenance.com)
