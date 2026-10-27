# Stage D — Live Enforcement Activation Checklist

Status: BLOCKED until independently verified on GitHub.

## Stage C baseline
The offline Stage C candidate contains 67 source/fixture/test files and locally passed 98 pytest cases. This is **not** evidence of a GitHub CI run.

## Activation gates (all required)
- [ ] Import all Stage C source files under stage-c/; exclude caches and generated files.
- [ ] Confirm source inventory and SHA-256 of imported package.
- [ ] Run `stage-c-verify.yml` on the exact branch HEAD.
- [ ] Verify test count, test failures and workflow run URL from GitHub.
- [ ] Add branch protection or repository ruleset with required CI status check.
- [ ] Restrict merge permissions and disallow bypass where supported.
- [ ] Bind founder approval to a trusted GitHub identity and an exact commit/revision.
- [ ] Verify evidence provenance from trusted CI, not a self-declared YAML field.
- [ ] Run tampered approval, stale SHA, revoked approval and missing evidence negative cases.
- [ ] Run Stage E six-batch dry run; only then request Stage F freeze.

## Important
GitHub workflow definitions in a feature branch are not equivalent to an enforced ruleset. Never mark Stage D PASS without a live workflow and branch protection verification.
No project has been selected and no deployment is authorized.
