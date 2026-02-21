#!/usr/bin/env python3
"""Reference verifier CLI for Verified Provenance draft specs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import posixpath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


VERDICT_VERIFIED = "VERIFIED"
VERDICT_UNDECLARED = "UNDECLARED"
VERDICT_UNVERIFIABLE = "UNVERIFIABLE"
VERDICT_INVALID_INPUT = "INVALID_INPUT"
VERDICT_INVALID_CHAIN = "INVALID_CHAIN"
VERDICT_POLICY_VIOLATION = "POLICY_VIOLATION"

ATTESTATION_EVENTS = {"ATTESTATION_ISSUED", "ATTESTATION_SUPERSEDED"}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_percent_hex(path: str) -> str:
    return re.sub(r"%[0-9a-fA-F]{2}", lambda m: m.group(0).upper(), path)


def canonicalize_artifact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL must include scheme and host")

    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL host is missing")

    userinfo = ""
    if parsed.username is not None:
        userinfo = parsed.username
        if parsed.password is not None:
            userinfo += ":" + parsed.password
        userinfo += "@"

    port = parsed.port
    include_port = port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    )
    netloc = f"{userinfo}{host}"
    if include_port:
        netloc += f":{port}"

    original_path = parsed.path or "/"
    trailing_slash = original_path.endswith("/")
    norm_path = posixpath.normpath(original_path)
    if not norm_path.startswith("/"):
        norm_path = "/" + norm_path
    if trailing_slash and not norm_path.endswith("/"):
        norm_path += "/"
    path = normalize_percent_hex(norm_path)
    query = normalize_percent_hex(parsed.query)

    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def parse_utc_or_die(text: str) -> datetime:
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid RFC3339 timestamp: {text}") from exc
    if dt.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


def json_load_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fetch_json(url: str, timeout: int) -> Any:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "vp-verify/0.1"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))


@dataclass
class VerificationResult:
    verdict: str
    errors: list[str]
    checked_events: int = 0
    active_event_id: str | None = None

    def to_json(self, artifact_url: str | None, evaluated_at: datetime) -> dict[str, Any]:
        return {
            "spec_version": "1.1",
            "verdict": self.verdict,
            "evaluated_at": evaluated_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "artifact_url": artifact_url,
            "active_event_id": self.active_event_id,
            "checked_events": self.checked_events,
            "errors": self.errors,
        }


def compute_event_hash(event: dict[str, Any]) -> str:
    evt = copy.deepcopy(event)
    evt.pop("event_hash", None)
    return sha256_hex(canonical_json_bytes(evt))


def verify_chain(
    domain_doc: dict[str, Any],
    chain_doc: dict[str, Any],
    evaluated_at: datetime,
) -> VerificationResult:
    errors: list[str] = []
    events = chain_doc.get("events")
    if not isinstance(events, list) or not events:
        return VerificationResult(VERDICT_INVALID_CHAIN, ["events array missing or empty"])

    # Deterministic ordering by recorded_at then event_id.
    def event_key(evt: dict[str, Any]) -> tuple[str, str]:
        return (str(evt.get("recorded_at", "")), str(evt.get("event_id", "")))

    ordered = sorted(events, key=event_key)
    prev_hash = None
    active_event_id = None

    policy = domain_doc.get("policy", {}) if isinstance(domain_doc.get("policy"), dict) else {}
    signature_required = bool(policy.get("signature_required"))
    timestamp_required = bool(policy.get("timestamp_required"))
    transparency_required = bool(policy.get("transparency_anchoring_required"))

    for index, evt in enumerate(ordered):
        if not isinstance(evt, dict):
            return VerificationResult(VERDICT_INVALID_CHAIN, ["event is not an object"], index)
        event_id = str(evt.get("event_id", "")).strip()
        event_hash = str(evt.get("event_hash", "")).strip()
        prev_event_hash = evt.get("prev_event_hash")

        if not event_id or not event_hash:
            return VerificationResult(VERDICT_INVALID_CHAIN, ["event_id or event_hash missing"], index)

        if index == 0:
            if prev_event_hash not in (None, "", "null"):
                return VerificationResult(
                    VERDICT_INVALID_CHAIN,
                    [f"genesis event {event_id} has non-null prev_event_hash"],
                    index + 1,
                )
        else:
            if prev_event_hash != prev_hash:
                return VerificationResult(
                    VERDICT_INVALID_CHAIN,
                    [f"prev_event_hash mismatch at {event_id}"],
                    index + 1,
                )

        if "issuer" in evt and "canonicalization" in evt and "artifact" in evt:
            recomputed = compute_event_hash(evt)
            if recomputed != event_hash:
                return VerificationResult(
                    VERDICT_INVALID_CHAIN,
                    [f"event_hash mismatch at {event_id}"],
                    index + 1,
                )

            event_type = str(evt.get("event_type", ""))
            if event_type in ATTESTATION_EVENTS:
                signature = evt.get("signature") if isinstance(evt.get("signature"), dict) else {}
                timestamp = evt.get("timestamp") if isinstance(evt.get("timestamp"), dict) else {}
                transparency = evt.get("transparency") if isinstance(evt.get("transparency"), dict) else {}

                if signature_required and not signature.get("value"):
                    return VerificationResult(
                        VERDICT_POLICY_VIOLATION,
                        [f"signature missing for required event {event_id}"],
                        index + 1,
                    )
                if timestamp_required and not timestamp.get("value"):
                    return VerificationResult(
                        VERDICT_POLICY_VIOLATION,
                        [f"timestamp missing for required event {event_id}"],
                        index + 1,
                    )
                if transparency_required and not transparency.get("entry_id"):
                    return VerificationResult(
                        VERDICT_POLICY_VIOLATION,
                        [f"transparency proof missing for required event {event_id}"],
                        index + 1,
                    )
                # Cryptographic signature/timestamp/transparency proof verification is not
                # implemented in this minimal reference CLI yet.
                if signature_required and signature.get("value"):
                    errors.append(f"cryptographic signature verification not implemented for {event_id}")

        if evt.get("effective_at") and evt.get("recorded_at"):
            try:
                if parse_utc_or_die(str(evt["effective_at"])) <= evaluated_at and parse_utc_or_die(
                    str(evt["recorded_at"])
                ) <= evaluated_at:
                    active_event_id = event_id
            except ValueError as exc:
                return VerificationResult(VERDICT_INVALID_INPUT, [str(exc)], index + 1)

        prev_hash = event_hash

    if errors:
        return VerificationResult(VERDICT_UNVERIFIABLE, errors, len(ordered), active_event_id)
    return VerificationResult(VERDICT_VERIFIED, [], len(ordered), active_event_id)


def verify_remote_artifact(url: str, timeout: int, evaluated_at: datetime) -> VerificationResult:
    canonical_url = canonicalize_artifact_url(url)
    domain = urllib.parse.urlsplit(canonical_url).netloc
    well_known_url = f"https://{domain}/.well-known/provenance"

    try:
        domain_doc = fetch_json(well_known_url, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return VerificationResult(VERDICT_UNDECLARED, [f"missing {well_known_url}"])
        return VerificationResult(VERDICT_UNVERIFIABLE, [f"domain policy fetch failed: HTTP {exc.code}"])
    except Exception as exc:  # noqa: BLE001
        return VerificationResult(VERDICT_UNVERIFIABLE, [f"domain policy fetch failed: {exc}"])

    spec_version = str(domain_doc.get("spec_version", "1.0"))
    if spec_version.startswith("1.1") and isinstance(domain_doc.get("evidence_api"), dict):
        template = domain_doc["evidence_api"].get("events_by_artifact")
        if not isinstance(template, str) or "{artifact_url}" not in template:
            return VerificationResult(VERDICT_UNVERIFIABLE, ["events_by_artifact URL template missing"])
        events_url = template.replace("{artifact_url}", urllib.parse.quote(canonical_url, safe=""))
        try:
            chain_doc = fetch_json(events_url, timeout)
        except Exception as exc:  # noqa: BLE001
            return VerificationResult(VERDICT_UNVERIFIABLE, [f"events fetch failed: {exc}"])

        if isinstance(chain_doc, list):
            chain_doc = {"events": chain_doc}
        return verify_chain(domain_doc, chain_doc, evaluated_at)

    # v1.0 artifact projection check
    suffix = ".provenance.json"
    artifact_discovery = domain_doc.get("artifact_discovery")
    if isinstance(artifact_discovery, dict) and isinstance(artifact_discovery.get("suffix"), str):
        suffix = artifact_discovery["suffix"]
    manifest_url = canonical_url + suffix
    try:
        manifest = fetch_json(manifest_url, timeout)
    except Exception as exc:  # noqa: BLE001
        return VerificationResult(VERDICT_UNVERIFIABLE, [f"manifest fetch failed: {exc}"])

    if canonicalize_artifact_url(str(manifest.get("artifact_url", ""))) != canonical_url:
        return VerificationResult(VERDICT_INVALID_INPUT, ["manifest artifact_url mismatch"])

    content_hash = str(manifest.get("content_sha256", "")).strip()
    if not re.fullmatch(r"[0-9a-f]{64}", content_hash):
        return VerificationResult(VERDICT_INVALID_INPUT, ["manifest content_sha256 is not valid hex sha256"])

    policy = domain_doc.get("policy", {}) if isinstance(domain_doc.get("policy"), dict) else {}
    signature_required = bool(policy.get("signature_required"))
    signature = manifest.get("signature") if isinstance(manifest.get("signature"), dict) else {}
    if signature_required and not signature.get("value"):
        return VerificationResult(VERDICT_POLICY_VIOLATION, ["signature required but missing"])
    if signature_required:
        return VerificationResult(
            VERDICT_UNVERIFIABLE,
            ["cryptographic signature verification is not implemented for v1.0 projection manifests"],
        )
    return VerificationResult(VERDICT_VERIFIED, [])


def run_vectors(path: str) -> int:
    vectors = json_load_file(path)
    failures: list[str] = []

    for case in vectors.get("json_canonicalization", []):
        case_id = case["id"]
        expected = case["expected_canonical_json"]
        actual = canonical_json_bytes(case["input"]).decode("utf-8")
        if actual != expected:
            failures.append(f"{case_id}: canonical JSON mismatch")
            continue
        digest = sha256_hex(actual.encode("utf-8"))
        if digest != case["expected_sha256"]:
            failures.append(f"{case_id}: sha256 mismatch")

    for case in vectors.get("url_canonicalization", []):
        case_id = case["id"]
        try:
            actual = canonicalize_artifact_url(case["input"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{case_id}: canonicalization raised {exc}")
            continue
        if actual != case["expected"]:
            failures.append(f"{case_id}: URL canonicalization mismatch")

    for case in vectors.get("event_hash", []):
        case_id = case["id"]
        actual = compute_event_hash(case["input"])
        if actual != case["expected_event_hash"]:
            failures.append(f"{case_id}: event hash mismatch")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("All conformance vectors passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verified Provenance reference verifier CLI (draft).")
    sub = parser.add_subparsers(dest="command", required=True)

    cmd_verify = sub.add_parser("verify-url", help="Verify an artifact URL using live discovery/evidence endpoints.")
    cmd_verify.add_argument("artifact_url")
    cmd_verify.add_argument("--timeout", type=int, default=10)
    cmd_verify.add_argument(
        "--evaluated-at",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    cmd_chain = sub.add_parser("verify-chain", help="Verify a local v1.1 chain file against a domain policy document.")
    cmd_chain.add_argument("--domain-doc", required=True)
    cmd_chain.add_argument("--chain-doc", required=True)
    cmd_chain.add_argument(
        "--evaluated-at",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    cmd_vectors = sub.add_parser("run-vectors", help="Run canonicalization and event-hash conformance vectors.")
    cmd_vectors.add_argument(
        "--vectors",
        default="docs/spec/test-vectors/canonicalization-v1.1.json",
    )

    args = parser.parse_args()

    if args.command == "run-vectors":
        return run_vectors(args.vectors)

    evaluated_at = parse_utc_or_die(args.evaluated_at)
    artifact_url = None
    if args.command == "verify-url":
        artifact_url = canonicalize_artifact_url(args.artifact_url)
        result = verify_remote_artifact(args.artifact_url, timeout=args.timeout, evaluated_at=evaluated_at)
    else:
        domain_doc = json_load_file(args.domain_doc)
        chain_doc = json_load_file(args.chain_doc)
        artifact_url = chain_doc.get("artifact_url")
        result = verify_chain(domain_doc, chain_doc, evaluated_at)

    print(json.dumps(result.to_json(artifact_url, evaluated_at), indent=2))
    return 0 if result.verdict == VERDICT_VERIFIED else 2


if __name__ == "__main__":
    sys.exit(main())
