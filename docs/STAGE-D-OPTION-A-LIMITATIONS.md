# Stage D — Option A: private and free

Founder decision: keep the repository private and free. Do not enable public visibility or purchase a plan.

## Implemented
- Existing Stage C verification and foundation smoke workflows remain active.
- A separate release-gate workflow runs on pull requests, branch pushes and manual dispatch.
- Its verifier fails closed on missing/mismatched approval, SHA, identity, and most importantly on untrusted self-asserted JSON approvals.
- The approval record defaults to release_authorized=false.

## Non-negotiable limitations
GitHub returned HTTP 403: "Upgrade to GitHub Pro or make this repository public to enable this feature." Branch protection/rulesets cannot be enforced in the present private/free configuration. Consequently an administrator or actor with sufficient write privileges can bypass workflow checks, push to main, modify the workflow, or merge without a passing gate. A GitHub Actions failure is a signal, **not a preventive control**.

The checked-in approval JSON cannot authenticate the Founder. Even if it says approved_by=Mahfuz24, this is attacker-editable repository content. Until an independent trusted GitHub identity attestation is implemented and validated, the release gate intentionally fails even with release_authorized=true.

## Operational release policy
No merges to main, protected changes, or production deployments are authorized by this implementation. Human review and explicit Founder decision are required. Never represent a failed release gate as a passing acceptance gate or claim branch protection is enabled.

## Exit criteria
1. Trusted, tamper-resistant approval evidence bound to exact candidate SHA and GitHub identity.
2. Negative tests: fabricated approval, stale SHA, missing approval, tampered workflow, and bypass attempts.
3. Enforceable protection via supported GitHub plan or equivalent external trusted gate.
4. Exact-SHA CI evidence and independent acceptance.
