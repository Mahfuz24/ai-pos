"""Offline fail-closed release evaluation; never authenticates real people by itself."""
from hardening import approval_verified, acceptance_verified, validate_bundle, verify_attestation, digest


def approval_active(subject, approval, attestation, trusted_keys, revocations=()):
    """Revocation entries must themselves be trusted signed attestations."""
    if not approval_verified(subject, approval, attestation, trusted_keys):
        return False
    for item in revocations:
        payload = item.get('payload', {}) if isinstance(item, dict) else {}
        if payload.get('approval_id') != approval['id']:
            continue
        if verify_attestation(item, trusted_keys, 'approval_revocation', payload):
            return False
        # Unverifiable revocation information is a security conflict, not permission to proceed.
        return False
    return True


def evaluate_release(release, records, attestations, trusted_keys, artifacts, revocations=()):
    """Return (PASS/BLOCKED, reasons); local attestation keys are not real identity proof."""
    reasons = []
    index = {(r.get('project_id'), r.get('id')): (kind, r) for kind, r in records}
    pid = release.get('project_id')
    sha = release.get('candidate_sha')
    if release.get('status') not in ('ready', 'approved'):
        reasons.append('release is not ready/approved')
    if not isinstance(sha, str) or len(sha) != 40 or any(c not in '0123456789abcdef' for c in sha):
        reasons.append('invalid candidate SHA')
    if release.get('unresolved_blockers'):
        reasons.append('unresolved release blockers')
    if not release.get('included_requirement_ids'):
        reasons.append('no included requirements')
    if not release.get('acceptance_ids'):
        reasons.append('no acceptance records')
    reasons += validate_bundle(records)
    for reqid in release.get('included_requirement_ids', []):
        matches = [r for kind, r in records if kind == 'acceptance' and r.get('project_id') == pid and r.get('requirement_id') == reqid and r.get('id') in release.get('acceptance_ids', [])]
        if not matches:
            reasons.append(f'{reqid}: missing linked acceptance')
            continue
        if not any(_acceptance_ok(a, sha, records, attestations, trusted_keys, artifacts) for a in matches):
            reasons.append(f'{reqid}: no independently evidenced PASS')
    for aid in release.get('acceptance_ids', []):
        entry = index.get((pid, aid))
        if not entry or entry[0] != 'acceptance' or entry[1].get('requirement_id') not in release.get('included_requirement_ids', []):
            reasons.append(f'{aid}: acceptance not linked to included requirement')
    approval_id = release.get('founder_approval_ref')
    entry = index.get((pid, approval_id))
    if not entry or entry[0] != 'approval':
        reasons.append('missing release approval record')
    elif not approval_active(release, entry[1], attestations.get(approval_id), trusted_keys, revocations):
        reasons.append('release approval untrusted, stale, or revoked')
    return ('PASS' if not reasons else 'BLOCKED', reasons)


def _acceptance_ok(acc, sha, records, attestations, trusted_keys, artifacts):
    if acc.get('candidate_sha') != sha:
        return False
    pid = acc.get('project_id')
    reqid = acc.get('requirement_id')
    reqs = [r for k, r in records if k == 'requirement' and r.get('id') == reqid and r.get('project_id') == pid]
    if len(reqs) != 1 or reqs[0].get('status') not in ('verified', 'accepted'):
        return False
    criterion_ids = set(acc.get('criterion_ids', []))
    defined = {c.get('criterion_id') for c in reqs[0].get('acceptance_criteria', [])}
    if not defined or criterion_ids != defined:
        return False
    tests = [r for k, r in records if k == 'test' and r.get('project_id') == pid and r.get('status') == 'ready' and r.get('id') in {ev.get('test_id') for k2, ev in records if k2 == 'evidence' and ev.get('id') in acc.get('evidence_ids', [])}]
    covered_criteria = set()
    for t in tests:
        covered_criteria.update(t.get('criterion_ids', []))
    if not criterion_ids <= covered_criteria:
        return False
    evs = [r for k, r in records if k == 'evidence' and r.get('project_id') == pid]
    return acceptance_verified(acc, [t['id'] for t in tests], evs, attestations, trusted_keys, artifacts)
