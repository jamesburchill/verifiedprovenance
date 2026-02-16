# Verified Provenance Discovery and Evidence Specification v1.1 (Draft)

## 1. Purpose
This specification defines deterministic discovery and durable provenance evidence for long-term authenticity verification.

v1.1 extends v1 discovery with a mandatory append-only event model.

## 2. TIME Doctrine Requirements
Conformant systems MUST provide:
- Immutable event history (append-only, no destructive mutation)
- First-class temporal anchoring
- Rich contextual metadata for future interpretation
- Retrievable, decision-supportive meaning

Mutable materialized state is allowed. Immutable events are mandatory.

## 3. Design Principles
- Deterministic lookup for domain policy and artifact evidence
- Vendor-neutral verification with replayable history
- Supersession over deletion
- Cryptographic tamper evidence
- Backward-compatible discovery with forward-evolving schema

## 4. Discovery Endpoints
### 4.1 Domain-level control document
- `GET https://<domain>/.well-known/provenance`
- MUST be served over HTTPS.
- MUST return JSON with `Content-Type: application/json`.

### 4.2 Legacy artifact manifest endpoint (compatibility)
- `GET <artifact-canonical-url>.provenance.json`
- This endpoint MAY be retained as a convenience projection.
- This endpoint MUST NOT be treated as authoritative history.

### 4.3 Evidence endpoints (authoritative)
- `GET https://<domain>/.well-known/provenance/events?artifact_url=<url-encoded-canonical-artifact-url>`
- `GET https://<domain>/.well-known/provenance/events/<event_id>`
- `GET https://<domain>/.well-known/provenance/chain/<artifact_id>`
- `GET https://<domain>/.well-known/provenance/proof/<event_id>`

## 5. Domain-level JSON (minimum fields)
```json
{
  "spec_version": "1.1",
  "domain": "acme.example",
  "issued_at": "2026-02-12T00:00:00Z",
  "keys": [
    {
      "id": "did:web:acme.example#provenance-key-1",
      "type": "ed25519",
      "public_key": "BASE58_OR_JWK"
    }
  ],
  "artifact_discovery": {
    "method": "suffix",
    "suffix": ".provenance.json",
    "html_link_rel": "provenance"
  },
  "evidence_api": {
    "events_by_artifact": "https://acme.example/.well-known/provenance/events?artifact_url={artifact_url}",
    "event_by_id": "https://acme.example/.well-known/provenance/events/{event_id}",
    "chain_by_artifact": "https://acme.example/.well-known/provenance/chain/{artifact_id}",
    "proof_by_event": "https://acme.example/.well-known/provenance/proof/{event_id}"
  },
  "policy": {
    "signature_required": true,
    "timestamp_required": true,
    "transparency_anchoring_required": true,
    "deletion_allowed": false
  }
}
```

## 6. Event Model (Authoritative)
Each event is immutable and append-only.

### 6.1 Required Event Fields
```json
{
  "spec_version": "1.1",
  "event_id": "evt_01J9...",
  "artifact_id": "art_9b57...",
  "artifact_url": "https://acme.example/news/q4-update/",
  "event_type": "ATTESTATION_ISSUED",
  "recorded_at": "2026-02-12T00:00:05Z",
  "effective_at": "2026-02-12T00:00:00Z",
  "issuer": {
    "did": "did:web:acme.example",
    "key_id": "did:web:acme.example#provenance-key-1"
  },
  "canonicalization": {
    "method": "http-representation-v1",
    "method_version": "1.0"
  },
  "artifact": {
    "content_sha256": "hex-encoded-sha256",
    "content_type": "text/html",
    "byte_length": 48219,
    "encoding": "utf-8"
  },
  "context": {
    "source_platform": "wordpress",
    "source_record_id": "42",
    "retrieval_method": "https_get",
    "policy_version": "2026-02-01"
  },
  "supersedes_event_id": null,
  "reason_code": null,
  "prev_event_hash": "hex-encoded-hash-or-null",
  "event_hash": "hex-encoded-hash",
  "signature": {
    "format": "dsse",
    "alg": "Ed25519",
    "value": "BASE64_SIGNATURE"
  },
  "timestamp": {
    "type": "rfc3161",
    "value": "BASE64_TSR"
  },
  "transparency": {
    "log_id": "rekor-public",
    "entry_id": "1234567890",
    "inclusion_proof": "BASE64_OR_OBJECT",
    "root_hash": "hex-encoded-root"
  }
}
```

### 6.2 Allowed Event Types
- `ARTIFACT_OBSERVED`
- `ATTESTATION_ISSUED`
- `ATTESTATION_SUPERSEDED`
- `KEY_ROTATED`
- `KEY_REVOKED`
- `POLICY_CHANGED`
- `ARTIFACT_RETRACTED`

### 6.3 Event Rules
- Events MUST be append-only.
- Events MUST NOT be deleted or overwritten.
- Every non-genesis event for an artifact MUST include `prev_event_hash`.
- `event_hash` MUST be computed over a canonical serialized event payload excluding `event_hash` itself.
- `ATTESTATION_ISSUED` and `ATTESTATION_SUPERSEDED` MUST include non-empty `signature`, `timestamp`, and `transparency` fields.
- Supersession MUST use `supersedes_event_id`; prior events remain retrievable.

## 7. Validation Rules
A verifier MUST:
1. Resolve domain policy from `/.well-known/provenance`.
2. Retrieve full artifact chain from authoritative evidence endpoint.
3. Verify hash-chain continuity from genesis to latest relevant event.
4. Verify each event signature against key material valid at `effective_at`.
5. Verify timestamp token and transparency inclusion proof.
6. Apply supersession semantics to compute state at evaluation time.
7. Return verdict with evidence references, not only a boolean.

Normative verification procedure details are defined in:
- `docs/spec/verification-profile-v1.1.md`

## 8. Retrieval Semantics
### 8.1 Events by artifact
- Ordered by `recorded_at` ascending.
- Response MUST include pagination cursor and total count.

### 8.2 Chain by artifact
- MUST return canonical ordered chain, latest event pointer, and integrity status.

### 8.3 Proof by event
- MUST include signature, timestamp material, log inclusion proof, and current consistency proof metadata.

## 9. Audit Defensibility Requirements
Systems claiming conformance MUST support deterministic replay:
- "state as of time T" reconstruction
- key validity and revocation evaluation as of time T
- full event and proof retrieval for independent auditors

## 10. Storage Requirements
Implementation storage MUST provide:
- Append-only write model for events
- WORM or immutability controls for persisted event objects
- Periodic checkpointing of Merkle roots to an external transparency mechanism

## 11. Error Semantics
- Missing domain control document means provenance undeclared.
- Missing evidence endpoints means non-conformant to v1.1.
- Broken event hash chain means invalid provenance.
- Missing required proof material means unverifiable event.

## 12. Migration from v1.0
### 12.1 Compatibility posture
- v1.0 discovery endpoints MAY remain unchanged.
- Existing `.provenance.json` manifests MAY continue as convenience outputs.

### 12.2 Required migration steps
1. Introduce immutable event storage and event IDs.
2. Start emitting signed, timestamped `ATTESTATION_ISSUED` events.
3. Backfill prior manifests into synthetic genesis events where source data allows.
4. Publish evidence API URLs in domain control document.
5. Mark legacy manifest endpoint as `projection_only: true` in domain policy.

### 12.3 Legacy manifest mapping
A legacy manifest maps to one `ATTESTATION_ISSUED` event:
- `artifact_url` -> `artifact_url`
- `content_sha256` -> `artifact.content_sha256`
- `issued_at` -> `effective_at`
- `source.*` -> `context.*`
- `signature.*` -> `signature.*` (must be non-empty in conformant production)

## 13. Versioning
- Discovery paths remain stable; schema version is in-document (`spec_version`).
- Clients SHOULD ignore unknown fields.
- Clients MUST reject required-field omissions for declared spec version.
