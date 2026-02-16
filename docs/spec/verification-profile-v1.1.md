# Verified Provenance Verification Profile v1.1 (Draft)

## 1. Scope
This profile defines deterministic verification behavior for v1.1 provenance evidence.

Goal: independent verifiers processing the same inputs produce the same verdict.

## 2. Inputs
Verifier input MUST include:
- Artifact target (canonical URL or artifact identifier)
- Evaluation time `T_eval` (RFC 3339 UTC)
- Domain control document from `/.well-known/provenance`
- Authoritative event chain and proof material from evidence endpoints

## 3. Canonicalization Requirements
### 3.1 Artifact URL canonicalization
Implementations MUST normalize artifact URLs before lookup:
- Lowercase scheme and host
- Remove default ports (`:80` for HTTP, `:443` for HTTPS)
- Resolve dot segments
- Normalize percent-encoding to uppercase hex
- Preserve trailing slash semantics
- Strip URL fragment

If canonicalization fails, verifier MUST return `INVALID_INPUT`.

### 3.2 Event canonicalization for hashing/signing
For `event_hash` and signature verification, event payload MUST be canonicalized as follows:
1. Remove the top-level `event_hash` field.
2. Serialize JSON using a deterministic canonical JSON form:
- UTF-8 encoding
- Lexicographic object key order
- No insignificant whitespace
- Arrays preserve input order
3. Hash bytes with SHA-256.

`event_hash` MUST equal hex(lowercase) SHA-256 digest of canonical bytes.

## 4. Hash-Chain Verification
For each artifact chain ordered by `recorded_at` ascending:
1. First event MAY have `prev_event_hash = null`.
2. Every subsequent event MUST set `prev_event_hash` equal to previous event `event_hash`.
3. Recompute each event hash and compare with declared value.

Any mismatch MUST produce verdict `INVALID_CHAIN`.

## 5. Key and Signature Verification
### 5.1 Key material
Verifier MUST resolve key material from domain policy and key lifecycle events (`KEY_ROTATED`, `KEY_REVOKED`).

### 5.2 Temporal key validity
A signature is valid only if the signing key is valid at event `effective_at`.

### 5.3 Signature envelope
For `ATTESTATION_ISSUED` and `ATTESTATION_SUPERSEDED`:
- `signature.format` MUST be recognized (recommended: `dsse`)
- `signature.alg` MUST be recognized and permitted by policy
- Signature MUST validate over canonical event bytes

Failure MUST produce `INVALID_SIGNATURE`.

## 6. Timestamp and Transparency Verification
### 6.1 Timestamp
Verifier MUST validate timestamp token cryptographically (for example RFC 3161 profile):
- token integrity
- token signer trust chain
- message imprint binds to canonical event digest
- token time <= `T_eval`

Failure MUST produce `INVALID_TIMESTAMP`.

### 6.2 Transparency inclusion
Verifier MUST validate inclusion proof for event commitment in declared transparency log:
- log identifier recognized
- inclusion proof verifies against published root
- root consistency check passes for log state used in verification

Failure MUST produce `INVALID_TRANSPARENCY_PROOF`.

## 7. Supersession and State-at-Time
### 7.1 Supersession semantics
- Supersession is modeled only by new events.
- `ATTESTATION_SUPERSEDED` MUST reference `supersedes_event_id`.
- Referenced event MUST exist in same artifact chain.

### 7.2 State reconstruction at `T_eval`
Verifier MUST:
1. Filter events where `effective_at <= T_eval` and `recorded_at <= T_eval`.
2. Validate chain/proofs for all considered events.
3. Apply supersession graph to derive active attestation set.
4. Return active verdict and full evidence references.

## 8. Verdict Model
Verifier output MUST include a machine code and evidence pointers.

### 8.1 Required verdict codes
- `VERIFIED`
- `UNDECLARED`
- `UNVERIFIABLE`
- `INVALID_INPUT`
- `INVALID_CHAIN`
- `INVALID_SIGNATURE`
- `INVALID_TIMESTAMP`
- `INVALID_TRANSPARENCY_PROOF`
- `POLICY_VIOLATION`

### 8.2 Output shape (minimum)
```json
{
  "spec_version": "1.1",
  "verdict": "VERIFIED",
  "evaluated_at": "2026-02-15T00:00:00Z",
  "artifact_url": "https://acme.example/news/q4-update/",
  "active_event_id": "evt_...",
  "checked_events": 12,
  "evidence": {
    "chain_url": "https://acme.example/.well-known/provenance/chain/art_...",
    "proof_urls": [
      "https://acme.example/.well-known/provenance/proof/evt_..."
    ]
  },
  "errors": []
}
```

## 9. Policy Gating
If domain policy declares any required control and it is absent, verifier MUST return `POLICY_VIOLATION`.

Typical required controls:
- signature required
- timestamp required
- transparency anchoring required
- deletion disallowed

## 10. Failure Handling
- A verifier MUST fail closed for malformed critical fields.
- Unknown optional fields MUST be ignored.
- Unknown critical algorithm identifiers MUST return `UNVERIFIABLE`.

## 11. Interop Test Vectors
Implementers SHOULD publish test vectors for:
- canonicalization edge cases
- valid hash chain
- broken chain
- revoked key at verification time
- supersession replay at multiple `T_eval` timestamps

## 12. Conformance Statement
An implementation may claim "Verification Profile v1.1 conformant" only if it:
- implements sections 2 through 10 without weakening MUST requirements
- exposes deterministic verdict output including evidence pointers
