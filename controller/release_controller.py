#!/usr/bin/env python3
"""External, operator-controlled release decision. No deployment is performed."""
import argparse
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.request

REPO = "Mahfuz24/ai-pos"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {"AI-POS Stage C Verification", "AI-POS Foundation Smoke"}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

def verify_signature(payload, signature, secret):
    if not secret or len(secret) < 32:
        return False
    expected = hmac.new(secret.encode(), canonical(payload), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

def evaluate(payload, signature, secret, runs, now):
    if not isinstance(payload, dict) or payload.get("repository") != REPO:
        return False, "repository mismatch"
    sha = payload.get("candidate_sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        return False, "invalid SHA"
    if payload.get("founder") != "Mahfuz24" or payload.get("decision") != "approve-release":
        return False, "founder/decision mismatch"
    if payload.get("expires_at", 0) <= now or payload.get("issued_at", now + 1) > now:
        return False, "expired/future approval"
    if not verify_signature(payload, signature, secret):
        return False, "invalid founder-controlled signature"
    for name in REQUIRED:
        if not any(r.get("name") == name and r.get("head_sha") == sha
                   and r.get("status") == "completed" and r.get("conclusion") == "success"
                   and r.get("event") in ("push", "pull_request")
                   for r in runs):
            return False, "missing exact-SHA successful CI: " + name
    return True, "release eligible; no deployment performed"

def fetch_runs(token, sha):
    if not token:
        raise ValueError("GITHUB_TOKEN missing")
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/actions/runs?head_sha=" + sha + "&per_page=100",
        headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                 "User-Agent": "ai-pos-external-controller"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response).get("workflow_runs", [])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--approval", required=True, help="Founder-signed JSON stored OUTSIDE repository")
    p.add_argument("--sha", required=True, help="Exact release candidate SHA")
    args = p.parse_args()
    import time
    try:
        document = json.load(open(args.approval, encoding="utf-8"))
        payload, signature = document["payload"], document["signature"]
        if payload.get("candidate_sha") != args.sha:
            raise ValueError("requested SHA mismatch")
        # Fetch directly from GitHub rather than accepting repository-supplied CI claims.
        runs = fetch_runs(os.environ.get("GITHUB_TOKEN"), args.sha)
        allowed, reason = evaluate(payload, signature, os.environ.get("AI_POS_FOUNDER_KEY"), runs, int(time.time()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        allowed, reason = False, str(exc)
    print(("ELIGIBLE: " if allowed else "BLOCKED: ") + reason)
    return 0 if allowed else 1

if __name__ == "__main__":
    sys.exit(main())
