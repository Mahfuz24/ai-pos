#!/usr/bin/env python3
"""Founder-only local signer. Never run in GitHub Actions or send the key to AI."""
import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path
from release_controller import read_founder_key

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        parser.error("SHA must be a full 40-character lowercase Git commit")
    destination = Path(args.output).expanduser()
    if destination.exists():
        parser.error("output already exists; will not overwrite approval")
    secret = read_founder_key()
    now = int(time.time())
    payload = {
        "repository": "Mahfuz24/ai-pos",
        "candidate_sha": args.sha,
        "founder": "Mahfuz24",
        "decision": "approve-release",
        "issued_at": now,
        "expires_at": now + 600,
        "nonce": secrets.token_hex(32),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest()
    data = json.dumps({"payload": payload, "signature": signature}, indent=2) + "\n"
    fd = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(data)
    print("Signed approval written to", destination)
    print("Expires in 10 minutes. This is an approval document, NOT a deployment.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
