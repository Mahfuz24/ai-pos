# External Release Controller — prototype

This is a **separate operator-run decision engine**, not a GitHub-enforced merge gate or production deployer.

The operator must store `AI_POS_FOUNDER_KEY` (minimum 32 characters) **outside GitHub, the repository, and all AI chats**. A founder-approved payload must be signed using HMAC-SHA256 over canonical JSON, and the signed document must also remain outside the repository. The key is a local shared-secret credential, **not cryptographic proof of a GitHub account identity**. Protect it as a release credential.

Run only in a trusted operator environment with a read-only GitHub token in `GITHUB_TOKEN`:
`python3 controller/release_controller.py --approval /private/path/approval.json --sha <40-character-sha>`

The controller fetches successful workflow runs from GitHub for the exact SHA and checks Stage C Verification and Foundation Smoke. It never deploys or merges. This is an initial proof of concept; no real founder key, external host, approval, or deployment credential has been provisioned.

**Security limitations:** HMAC key theft or local compromise allows forgery. CI workflows can be changed by a repository writer; check-name-only matching does not establish trusted workflow provenance. Private/free GitHub permits direct push/merge bypass. No deployment credential isolation has been verified. Accordingly do not use this prototype to authorize real production releases. The repository release gate remains fail-closed.

Next engineering: pin workflow identity/path and source, verify workflow provenance from GitHub API, implement nonce/replay prevention and key rotation, isolate execution credentials, and run independent adversarial tests before any release.
