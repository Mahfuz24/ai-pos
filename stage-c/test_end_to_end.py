"""Offline synthetic end-to-end integration: never a real founder/CI attestation."""
import copy, hashlib, json
from pathlib import Path
from hardening import digest, signed, validate_bundle, transition_verified
from release_gate import evaluate_release

ROOT=Path(__file__).resolve().parent
FOUNDER={'founder-demo': b'F'*32, 'ci-demo': b'C'*32}
SHA='a'*40

def fixture(kind):
    return json.loads((ROOT/'fixtures'/'valid'/f'{kind}.json').read_text())

def attest(kind, issuer, payload):
    return {'kind':kind,'issuer':issuer,'payload':payload,'signature':signed({'kind':kind,'issuer':issuer,'payload':payload},FOUNDER[issuer])}

def scenario():
    p=fixture('project')
    f=fixture('feature'); f['id']='FEAT-001'; f['status']='accepted'
    r=fixture('requirement'); r.update(status='verified',feature_id=f['id'])
    t=fixture('test'); t.update(status='ready',requirement_ids=[r['id']],criterion_ids=['AC-001'])
    ev=fixture('evidence'); ev.update(status='pass',result='pass',source_sha=SHA,test_id=t['id'],environment_id='offline-demo')
    artifact=b'PASS: synthetic test executed locally'
    ev['artifact_hashes']={'test-log':hashlib.sha256(artifact).hexdigest()}
    ev['artifact_refs']=['test-log']
    a=fixture('acceptance'); a.update(status='pass',candidate_sha=SHA,criterion_ids=['AC-001'],evidence_ids=[ev['id']])
    rel=fixture('release'); rel.update(status='ready',candidate_sha=SHA,included_requirement_ids=[r['id']],acceptance_ids=[a['id']],founder_approval_ref='APR-001')
    approval=fixture('approval'); approval.update(status='approved',decision='approved',request_id=rel['id'],approved_subject_revision=rel['revision'],approved_content_hash=digest(rel))
    ev_payload={'evidence_id':ev['id'],'project_id':ev['project_id'],'test_id':t['id'],'source_sha':SHA,'environment_id':ev['environment_id'],'result':'pass','artifact_hashes':ev['artifact_hashes']}
    approval_payload={'approval_id':approval['id'],'project_id':approval['project_id'],'request_id':rel['id'],'revision':rel['revision'],'content_hash':digest(rel),'decision':'approved'}
    records=[('project',p),('feature',f),('requirement',r),('test',t),('evidence',ev),('acceptance',a),('release',rel),('approval',approval)]
    atts={ev['id']:attest('ci_test_evidence','ci-demo',ev_payload),approval['id']:attest('founder_approval','founder-demo',approval_payload)}
    return rel,records,atts,{ev['id']:{'test-log':artifact}}

def test_positive_offline_end_to_end():
    release,records,atts,artifacts=scenario()
    assert validate_bundle(records)==[]
    assert evaluate_release(release,records,atts,FOUNDER,artifacts)==('PASS',[])

def test_missing_artifact_fails_closed():
    rel,recs,atts,arts=scenario(); arts['EVD-001']={}
    assert evaluate_release(rel,recs,atts,FOUNDER,arts)[0]=='BLOCKED'

def test_forged_ci_fails_closed():
    rel,recs,atts,arts=scenario(); atts['EVD-001']['signature']='0'*64
    assert evaluate_release(rel,recs,atts,FOUNDER,arts)[0]=='BLOCKED'

def test_wrong_candidate_sha_fails_closed():
    rel,recs,atts,arts=scenario(); rel['candidate_sha']='b'*40
    assert evaluate_release(rel,recs,atts,FOUNDER,arts)[0]=='BLOCKED'

def test_revoked_release_fails_closed():
    rel,recs,atts,arts=scenario()
    rev=attest('approval_revocation','founder-demo',{'approval_id':'APR-001','reason':'withdrawn'})
    assert evaluate_release(rel,recs,atts,FOUNDER,arts,[rev])[0]=='BLOCKED'

def test_cross_project_reference_fails_closed():
    rel,recs,atts,arts=scenario(); recs[3][1]['project_id']='PRJ-002'
    assert evaluate_release(rel,recs,atts,FOUNDER,arts)[0]=='BLOCKED'

def test_approval_transition_requires_authority():
    assert not transition_verified('requirement','under_review','approved')
    assert transition_verified('requirement','under_review','approved',approval_valid=True)
