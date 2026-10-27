# AI-POS Stage C — Project-agnostic Validation Package

This is a **prototype implementation**, not a complete production governance enforcement system. No project was selected and no GitHub repository was modified.

## Contents
- 18 record-specific JSON Schemas, one common metadata schema
- 18 valid and 18 invalid fixture files
- `validator.py`: structural, cross-reference, duplicate-ID, dependency-cycle, status-transition, founder-approval content-hash, and source-matched evidence coverage checks
- `test_validator.py`: automated tests

## Run
```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## Important limitations / work remaining
- Schemas are minimal **structural contracts**. They do not yet enforce all conditional state-specific requirements, domain enums, nullability rules, or full acceptance criteria.
- Example fixtures are individually schema-valid, not necessarily a cross-referenced complete project dataset.
- Founder approval checks verify the *consistency* of a supplied record and digest; they do **not authenticate** who issued it. A trusted approval source or signature is required.
- Evidence checks validate a supplied candidate SHA and test coverage; they do **not prove** the artifact was executed or prevent forged evidence. Trusted CI provenance, hashes and artifact retrieval are required.
- Record owner access controls, PR permissions, protected merges, release gates, secrets scanning, and complete lifecycle enforcement are not implemented.
- Dependency cycle checks cover explicit `dependencies` and `dependency_ids` only.
- An implementation-specific `test_id` is supported in evidence checking but is not yet required by the evidence JSON Schema.
- Schema/validator consistency, canonical status enums, and comprehensive negative integration fixtures require a further hardening pass before Stage C can be accepted as complete.

## Hardening checkpoint (not production certification)

Run: `python -m pytest -q test_validator.py test_hardening.py`

The original Stage C prototype is preserved separately at `/mnt/data/AI-POS-Stage-C-Prototype.zip`.

### What is verified
- All 18 record-specific JSON Schema definitions parse, with typed ID prefix and status enums.
- Valid/invalid fixtures for each record type.
- Reference typing, project isolation, duplicate IDs, and dependency cycles.
- Transition checks, including explicit approval requirement for promotion to approved.
- HMAC attestation checking with a trusted configured issuer, subject revision/content hash binding, tampering/revocation rejection.
- CI-style evidence attestation binding to source SHA, environment, test ID and actual artifact byte hashes; acceptance coverage checks.

### Explicit limitations / blockers
- HMAC is a demonstration trust mechanism, NOT Founder identity authentication. Real identity must be established by an external authenticated approval provider, with its verification and key management outside the repository.
- Test signing keys in test_hardening.py are intentionally public dummy fixtures and MUST NEVER be treated as trusted deployment keys.
- No external CI issuer is connected; CI provenance is simulated with locally generated test attestations. Real CI workload identity, immutable run URL, branch protection and artifact retention are not configured.
- Per-record schemas are improved but not fully normalized into a shared schema reference graph; some conditional requirements remain outside schema and require policy validation.
- State transitions are available for all 18 types, but some are provisional generalized transitions; production approval and migration rules need additional review.
- validate_bundle checks references and cycles, but does not independently verify authorization of all historical edits or integrate all attestation checks into a single release gate.
- No live project, repository, authenticated founder approval service, or release candidate exists. End-to-end tests are offline synthetic fixtures only.

Status: HARDENING PARTIAL; STAGE C FINAL ACCEPTANCE BLOCKED until above integration and trust gates are addressed.

## Next engineering checkpoint: offline release gate

- `release_gate.py` adds fail-closed release evaluation, requirement-to-acceptance linking, criterion coverage, source-matched evidence checks, and externally signed release approval checking.
- Approval revocation records are checked; untrusted revocation conflicts also block rather than granting permission.
- `test_release_gate.py` includes negative cases for missing approvals, tampering, revocation, invalid source SHA, and blockers.
- Run `python -m pytest -q` for the entire suite.

**Security limitations:** local HMAC attestations authenticate possession of a configured symmetric key, not the real Founder or CI service. No trusted identity provider, CI workload identity, repository protections, or real deployment gate is configured. Revocation history requires an external immutable log; local records can be removed by an adversary. The offline gate must NOT be used to authorize real deployment. No positive end-to-end release certification with a real identity/CI source has been completed. Stage C remains PARTIAL/BLOCKED.

## Latest offline engineering checkpoint
See `STAGE-C-ACCEPTANCE.md`. The synthetic positive end-to-end release and negative integration cases are in `test_end_to_end.py`. `evidence.schema.json` was reconciled with the validator. `python -m pytest -q`: **98 passed**. This does **not** certify real Founder identity or CI provenance.
