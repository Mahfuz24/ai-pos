import copy
from hardening import signed, digest
from release_gate import approval_active, evaluate_release

KEY = {'founder-issuer': b'F'*32}

def attest(kind, payload):
    return {'kind':kind,'issuer':'founder-issuer','payload':payload,'signature':signed({'kind':kind,'issuer':'founder-issuer','payload':payload},KEY['founder-issuer'])}

def subject_and_approval():
    subject={'id':'CR-001','project_id':'PRJ-001','revision':1,'title':'Approve change'}
    approval={'id':'APR-001','project_id':'PRJ-001','request_id':'CR-001','decision':'approved','approver_role':'founder','approved_subject_revision':1,'approved_content_hash':digest(subject)}
    payload={'approval_id':'APR-001','project_id':'PRJ-001','request_id':'CR-001','revision':1,'content_hash':digest(subject),'decision':'approved'}
    return subject,approval,attest('founder_approval',payload)

def test_valid_local_attestation():
    s,a,t=subject_and_approval()
    assert approval_active(s,a,t,KEY)

def test_revocation_blocks():
    s,a,t=subject_and_approval()
    rev=attest('approval_revocation',{'approval_id':'APR-001','reason':'withdrawn'})
    assert not approval_active(s,a,t,KEY,[rev])

def test_untrusted_revocation_conflict_fails_closed():
    s,a,t=subject_and_approval()
    assert not approval_active(s,a,t,KEY,[{'kind':'approval_revocation','payload':{'approval_id':'APR-001'}}])

def test_tampered_approval_blocks():
    s,a,t=subject_and_approval()
    a['approved_subject_revision']=2
    assert not approval_active(s,a,t,KEY)

def test_unknown_issuer_blocks():
    s,a,t=subject_and_approval()
    assert not approval_active(s,a,t,{})

def test_release_missing_records_fails_closed():
    release={'id':'REL-001','project_id':'PRJ-001','status':'ready','candidate_sha':'a'*40,'included_requirement_ids':['REQ-001'],'acceptance_ids':['ACC-001'],'unresolved_blockers':[],'founder_approval_ref':'APR-001'}
    status,reasons=evaluate_release(release,[],{},KEY,{})
    assert status=='BLOCKED' and len(reasons)>=3

def test_release_blockers_fail_closed():
    release={'id':'REL-001','project_id':'PRJ-001','status':'ready','candidate_sha':'a'*40,'included_requirement_ids':[],'acceptance_ids':[],'unresolved_blockers':['SEC-001']}
    status,reasons=evaluate_release(release,[],{},KEY,{})
    assert status=='BLOCKED' and 'unresolved release blockers' in reasons

def test_release_invalid_sha_fails_closed():
    release={'id':'REL-001','project_id':'PRJ-001','status':'ready','candidate_sha':'invalid','included_requirement_ids':[],'acceptance_ids':[],'unresolved_blockers':[]}
    assert evaluate_release(release,[],{},KEY,{})[0]=='BLOCKED'
