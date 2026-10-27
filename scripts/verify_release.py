#!/usr/bin/env python3
"""Fail-closed advisory release gate for free/private GitHub repositories."""
import json
import os
import re
import sys
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
def fail(message):
    print("RELEASE BLOCKED: " + message, file=sys.stderr)
    sys.exit(1)

def main():
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    if repo != "Mahfuz24/ai-pos":
        fail("unexpected repository")
    if not SHA.fullmatch(sha):
        fail("missing exact 40-character commit SHA")
    if event not in {"push", "pull_request", "workflow_dispatch"}:
        fail("unsupported event")
    try:
        data = json.loads(Path("governance/release-approval.json").read_text())
    except (OSError, ValueError) as exc:
        fail("missing/invalid approval record: " + str(exc))
    if data.get("schema_version") != 1 or data.get("repository") != repo:
        fail("approval record contract mismatch")
    if data.get("target_branch") != "main":
        fail("unexpected target branch")
    if not data.get("release_authorized") is True:
        fail("release authorization not granted")
    if data.get("candidate_sha") != sha or data.get("approved_sha") != sha:
        fail("stale or mismatched exact SHA")
    if data.get("approved_by") != "Mahfuz24":
        fail("founder identity mismatch")
    if not data.get("approved_at") or data.get("approved_at") == "UNSET":
        fail("missing approval timestamp")
    # Critical: repository-controlled JSON is never proof of founder identity.
    # No trusted independent verification exists under this plan.
    fail("trusted GitHub approval attestation is not configured; JSON is untrusted")

if __name__ == "__main__":
    main()
