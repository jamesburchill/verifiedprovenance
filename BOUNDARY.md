# Verified Provenance Trust Boundary

This repository is the public, protocol-side surface for Verified Provenance.

## Public Repo Scope
- Open protocol specs (`vp-spec`) and normative behavior.
- JSON schemas and conformance vectors.
- Open verifier logic (`vp-verify` library/CLI) and tests.
- Open integrations such as WordPress plugin source and docs.
- Demo/fictitious examples and public educational docs.

## Out of Scope
- Accounts, billing, analytics, queueing, moderation, or support tools.
- Deployment internals (IaC, CI/CD internals, environment configs).
- Internal ops docs (runbooks, incidents, SLO dashboards).
- Non-public domains, private fixtures, or internal business assets.
- Private keys, secrets, API credentials, or signing-custody integration details.

## Hard Rule
Public artifacts must be sufficient for independent verification without
`verifiedprovenance.com`, and no protocol behavior required for trust may exist
only in private systems.
