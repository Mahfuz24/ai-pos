#!/usr/bin/env python3
"""Offline verification of local Founder key and signature; no approval or deployment."""
import hashlib
import hmac
import json
import os
import stat
from pathlib import Path

def main():
    path = Path.home() / ".config/ai-pos-controller/founder.key"
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode) or (mode & 0o077):
        raise SystemExit("BLOCKED: founder.key must be a regular file with no group/other permissions")
    secret = path.read_text(encoding="utf-8").strip()
    if len(secret) != 64:
        raise SystemExit("BLOCKED: expected 64-character random hex secret")
    try:
        bytes.fromhex(secret)
    except ValueError:
        raise SystemExit("BLOCKED: key must be hexadecimal")
    from release_controller import canonical, verify_signature
    payload = {"check": "offline-local-signature-only", "nonce": os.urandom(32).hex()}
    sig = hmac.new(secret.encode(), canonical(payload), hashlib.sha256).hexdigest()
    if not verify_signature(payload, sig, secret):
        raise SystemExit("BLOCKED: local signature verification failed")
    if verify_signature({**payload, "check": "tampered"}, sig, secret):
        raise SystemExit("BLOCKED: signature tampering was accepted")
    print("PASS: key permissions, key format, signing and tamper rejection")
    print("No approval generated. No release authorized. No deployment performed.")

if __name__ == "__main__":
    main()
