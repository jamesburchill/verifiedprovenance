# Verified Provenance Discovery Specification v1 (Draft)

## 1. Purpose
This specification defines a deterministic way for clients to discover domain-level provenance policy and artifact-level provenance manifests without prior coordination.

## 2. Design Principles
- Deterministic lookup: clients should always know where to check first.
- Machine-first: discovery must work without human instructions.
- Domain-authoritative: domains declare their own provenance policy.
- Vendor-neutral verification: manifests must be independently verifiable.
- Extensible schema: fields may evolve without changing the discovery path.

## 3. Discovery Endpoints
### 3.1 Domain-level control document
- `GET https://<domain>/.well-known/provenance`
- MUST be served over HTTPS.
- MUST return JSON with `Content-Type: application/json`.

### 3.2 Artifact-level manifest
- Artifact manifest URL is `<artifact-canonical-url>.provenance.json`.
- Example:
  - Artifact: `https://acme.example/news/q4-update/`
  - Manifest: `https://acme.example/news/q4-update.provenance.json`

### 3.3 HTML discovery signal
Publishers SHOULD include:
```html
<link rel="provenance" href="https://acme.example/news/q4-update.provenance.json">
```

### 3.4 HTTP discovery signal
Publishers SHOULD include:
```http
Link: <https://acme.example/news/q4-update.provenance.json>; rel="provenance"
```

## 4. Domain-level JSON (minimum fields)
```json
{
  "spec_version": "1.0",
  "domain": "acme.example",
  "issued_at": "2026-02-12T00:00:00Z",
  "keys": [
    {
      "id": "did:web:acme.example#provenance-key-1",
      "type": "ed25519"
    }
  ],
  "artifact_discovery": {
    "method": "suffix",
    "suffix": ".provenance.json",
    "html_link_rel": "provenance"
  },
  "verification": {
    "public_verifier": "https://verifiedprovenance.com/verify"
  }
}
```

## 5. Artifact-level JSON (minimum fields)
```json
{
  "spec_version": "1.0",
  "domain": "acme.example",
  "artifact_url": "https://acme.example/news/q4-update/",
  "content_sha256": "hex-encoded-sha256",
  "issued_at": "2026-02-12T00:00:00Z",
  "signature": {
    "type": "none",
    "value": ""
  },
  "timestamp": {
    "type": "none",
    "value": ""
  }
}
```

## 6. Error Semantics
- If `/.well-known/provenance` is missing, clients MUST treat provenance as undeclared (not invalid).
- If artifact manifest is missing, clients MUST treat that artifact as unsigned/undeclared.

## 7. Caching Guidance
- Publishers SHOULD set cache headers on `/.well-known/provenance` (e.g., `max-age=86400`).
- Artifact manifests MAY use shorter cache TTLs.

## 8. Versioning
- Path versioning MUST NOT be used for discovery endpoints.
- Schema versioning MUST use the in-document `spec_version` field.
- Clients SHOULD ignore unknown fields.

