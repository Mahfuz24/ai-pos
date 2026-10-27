import hashlib
import hmac
import json
import time
import unittest

from release_controller import canonical, evaluate

SHA = "a" * 40
SECRET = "x" * 48
NOW = 2000000000

def approval(**overrides):
    payload = {"repository": "Mahfuz24/ai-pos", "candidate_sha": SHA,
               "founder": "Mahfuz24", "decision": "approve-release",
               "issued_at": NOW - 30, "expires_at": NOW + 300}
    payload.update(overrides)
    sig = hmac.new(SECRET.encode(), canonical(payload), hashlib.sha256).hexdigest()
    return payload, sig

def runs(sha=SHA):
    return [{"name": n, "head_sha": sha, "status": "completed",
             "conclusion": "success", "event": "push"}
            for n in ("AI-POS Stage C Verification", "AI-POS Foundation Smoke")]

class ControllerTests(unittest.TestCase):
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
    def test_future_timestamp(self):
        p, s = approval(issued_at=NOW+10)
        self.assertFalse(evaluate(p, s, SECRET, runs(), NOW)[0])

if __name__ == "__main__":
    unittest.main()
