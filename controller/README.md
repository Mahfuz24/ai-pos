# External Release Controller — fail-closed prototype

The Fedora controller is a **local eligibility checker only**, not a production deployment pipeline.

Founder key: `~/.config/ai-pos-controller/founder.key`, owned by the operator and mode `0600`. The signer and checker both read this file locally. **Never paste the key into ChatGPT, export it as an environment variable, commit it, or upload it to CI.** It is a shared-secret credential, not proof of GitHub account identity.

The public GitHub Actions API needs no token. An optional read-only `GITHUB_TOKEN` may improve API rate limits.

After selecting a real release candidate and independently reviewing it, the Founder can issue a short-lived local approval:

```bash
python3 controller/sign_founder_approval.py --sha FULL_40_CHARACTER_SHA --output "$HOME/.local/state/ai-pos-controller/approval.json"
AI_POS_REPLAY_DB="$HOME/.local/state/ai-pos-controller/redeemed.sqlite3" python3 controller/release_controller.py --approval "$HOME/.local/state/ai-pos-controller/approval.json" --sha FULL_40_CHARACTER_SHA
```

**Do not run the approval commands for a hypothetical candidate or as a routine test.** The signer issues an actual ten-minute approval document. The controller checks its HMAC, repository, SHA, time window, nonce, and three exact-SHA successful push workflow runs (Stage C, Foundation, Controller Tests), then atomically redeems the nonce. It prints only `ELIGIBLE` or `BLOCKED`; it does not merge or deploy. If the replay database is missing or unavailable, it blocks.

Security limits: the local key can be stolen on a compromised workstation; GitHub workflow names and paths do not alone prove trusted source provenance; workflow definitions and repository permissions need separate protection. The replay database needs durable backup and anti-rollback safeguards. Deployment credentials, a real product target, six-role end-to-end acceptance, and independent production authorization are **not implemented**. The repository Release Gate remains intentionally fail-closed.
