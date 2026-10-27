#!/usr/bin/env python3
"""External release eligibility checker; never merges or deploys."""
import argparse
import hashlib
import hmac
import json
import pathlib
import sqlite3
import stat
import uuid
import os
import re
import sys
import time
import urllib.request

REPO = "Mahfuz24/ai-pos"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {
    "AI-POS Stage C Verification": ".github/workflows/stage-c-verify.yml",
    "AI-POS Foundation Smoke": ".github/workflows/foundation-smoke.yml",
    "AI-POS Controller Unit Tests": ".github/workflows/controller-tests.yml",
}

def read_founder_key(path=None):
    """Read local-only secret; reject symlinks and permissive key files."""
    key_path = pathlib.Path(path) if path else pathlib.Path.home() / ".config/ai-pos-controller/founder.key"
    info = key_path.lstat()
    if not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o077):
        raise ValueError("Founder key must be a regular file inaccessible to group/others")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ValueError("Founder key must be owned by current user")
    secret = key_path.read_text(encoding="utf-8").strip()
    if len(secret) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}", secret):
        raise ValueError("Founder key format invalid")
    return secret

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

def verify_signature(payload, signature, secret):
    if not isinstance(secret, str) or len(secret) < 32 or not isinstance(signature, str):
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
    issued, expiry = payload.get("issued_at"), payload.get("expires_at")
    if not isinstance(issued, int) or not isinstance(expiry, int) or issued > now or expiry <= now or expiry - issued > 600:
        return False, "invalid or expired approval window"
    nonce = payload.get("nonce")
    if not isinstance(nonce, str) or len(nonce) < 32 or len(nonce) > 128:
        return False, "missing/invalid approval nonce"
    if not verify_signature(payload, signature, secret):
        return False, "invalid founder-controlled signature"
    for name, path in REQUIRED.items():
        if not any(r.get("name") == name and r.get("path") == path
                   and r.get("head_sha") == sha and r.get("status") == "completed"
                   and r.get("conclusion") == "success" and r.get("event") == "push"
                   and r.get("repository", {}).get("full_name") == REPO
                   for r in runs):
            return False, "missing exact-SHA CI with matching workflow path: " + name
    return True, "eligibility checks passed; no deployment performed"

def fetch_runs(token, sha):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "ai-pos-external-controller"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        "https://api.github.com/repos/" + REPO + "/actions/runs?head_sha=" + sha + "&per_page=100",
        headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response).get("workflow_runs", [])

def consume_nonce(db_path, nonce, sha):
    """Atomic one-time redemption; database must live outside repository."""
    if not db_path:
        raise ValueError("AI_POS_REPLAY_DB missing")
    path = pathlib.Path(db_path).expanduser().resolve()
    if not path.parent.is_dir():
        raise ValueError("replay database parent directory missing")
    with sqlite3.connect(str(path), timeout=10, isolation_level=None) as conn:
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS approvals (nonce TEXT PRIMARY KEY, sha TEXT NOT NULL)")
        try:
            conn.execute("INSERT INTO approvals(nonce,sha) VALUES (?,?)", (nonce, sha))
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            return False
        conn.execute("COMMIT")
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--approval", required=True)
    p.add_argument("--sha", required=True)
    args = p.parse_args()
    try:
        with open(args.approval, encoding="utf-8") as f:
            document = json.load(f)
        payload, signature = document["payload"], document["signature"]
        if payload.get("candidate_sha") != args.sha:
            raise ValueError("requested SHA mismatch")
        runs = fetch_runs(os.environ.get("GITHUB_TOKEN"), args.sha)
        allowed, reason = evaluate(payload, signature, read_founder_key(), runs, int(time.time()))
        if allowed and not consume_nonce(os.environ.get("AI_POS_REPLAY_DB"), payload["nonce"], args.sha):
            allowed, reason = False, "approval nonce already redeemed"
    except (OSError, ValueError, KeyError, TypeError) as exc:
        allowed, reason = False, str(exc)
    print(("ELIGIBLE: " if allowed else "BLOCKED: ") + reason)
    return 0 if allowed else 1

if __name__ == "__main__":
    sys.exit(main())
