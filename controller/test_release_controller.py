import hashlib
import hmac
import json
import time
import tempfile
from pathlib import Path
from release_controller import consume_nonce
import unittest
from unittest.mock import patch

from release_controller import canonical, evaluate, fetch_runs, read_founder_key

SHA = "a" * 40
SECRET = "x" * 48
NOW = 2000000000

def approval(**overrides):
    payload = {"repository": "Mahfuz24/ai-pos", "candidate_sha": SHA,
               "founder": "Mahfuz24", "decision": "approve-release",
               "issued_at": NOW - 30, "expires_at": NOW + 300, "nonce": "n" * 40}
    payload.update(overrides)
    sig = hmac.new(SECRET.encode(), canonical(payload), hashlib.sha256).hexdigest()
    return payload, sig

def runs(sha=SHA):
    return [{"name": n, "path": path, "repository": {"full_name": "Mahfuz24/ai-pos"},
             "head_sha": sha, "status": "completed", "conclusion": "success", "event": "push"}
            for n, path in (("AI-POS Stage C Verification", ".github/workflows/stage-c-verify.yml"),
                            ("AI-POS Foundation Smoke", ".github/workflows/foundation-smoke.yml"))]

class ControllerTests(unittest.TestCase):
    def test_public_api_does_not_send_authorization(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"workflow_runs":[]}'
        def fake_open(request, timeout):
            self.assertIsNone(request.get_header("Authorization"))
            self.assertEqual(timeout, 15)
            return Response()
        with patch("release_controller.urllib.request.urlopen", fake_open):
            self.assertEqual(fetch_runs(None, SHA), [])

    def test_local_key_read_and_reject_permissive_file(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            key = Path(folder) / "founder.key"
            key.write_text("a" * 64 + "\n")
            os.chmod(key, 0o600)
            self.assertEqual(read_founder_key(key), "a" * 64)
            os.chmod(key, 0o644)
            with self.assertRaises(ValueError):
                read_founder_key(key)

    def test_local_key_rejects_symlink(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            key = Path(folder) / "founder.key"
            key.write_text("a" * 64)
            os.chmod(key, 0o600)
            alias = Path(folder) / "alias.key"
            alias.symlink_to(key)
            with self.assertRaises(ValueError):
                read_founder_key(alias)

    def test_valid_signature_and_ci(self):
        p, s = approval()
        self.assertTrue(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_forged_signature(self):
        p, s = approval()
        p["decision"] = "approve-release-immediately"
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_wrong_key(self):
        p, s = approval()
        self.assertFalse(evaluate(p, s, "z"*48, runs(), NOW)[0])
    def test_expired(self):
        p, s = approval(expires_at=NOW-1)
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_stale_sha(self):
        p, s = approval()
        self.assertFalse(evaluate(p, s, SECRET, runs("b"*40), NOW)[0])
    def test_missing_ci(self):
        p, s = approval()
        self.assertFalse(evaluate(p, s, SECRET, runs()[:1], NOW)[0])
    def test_untrusted_founder(self):
        p, s = approval(founder="attacker")
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_invalid_repo(self):
        p, s = approval(repository="attacker/repo")
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_wrong_workflow_path(self):
        p, s = approval()
        rs = runs()
        rs[0]["path"] = ".github/workflows/attacker.yml"
        self.assertFalse(evaluate(p, s, SECRET, rs, NOW)[0])
    def test_wrong_workflow_repository(self):
        p, s = approval()
        rs = runs()
        rs[0]["repository"] = {"full_name": "attacker/repo"}
        self.assertFalse(evaluate(p, s, SECRET, rs, NOW)[0])
    def test_replay_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "redeemed.sqlite3")
            self.assertTrue(consume_nonce(db, "n" * 40, SHA))
            self.assertFalse(consume_nonce(db, "n" * 40, SHA))
    def test_missing_nonce(self):
        p, s = approval(nonce="")
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])
    def test_future_timestamp(self):
        p, s = approval(issued_at=NOW+10)
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])

if __name__ == "__main__":
    unittest.main()
