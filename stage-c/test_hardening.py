import copy,hashlib,json
from pathlib import Path
import pytest
from hardening import *
KEY=b'controlled-test-issuer-key-32-bytes-minimum!'
KEYS={'test-trusted-issuer':KEY}
def att(kind,payload):
 a={'kind':kind,'issuer':'test-trusted-issuer','payload':payload}
 a['signature']=signed(a,KEY);return a
def test_all_schema_definitions():
 import jsonschema
 for kind in REGISTRY:jsonschema.Draft202012Validator.check_schema(json.loads((ROOT/'schemas'/f'{kind}.schema.json').read_text()))
@pytest.mark.parametrize('kind',list(REGISTRY))
def test_valid_and_invalid_fixtures(kind):
 valid=json.loads((ROOT/'fixtures/valid'/f'{kind}.json').read_text());invalid=json.loads((ROOT/'fixtures/invalid'/f'{kind}.json').read_text())
 assert not schema_check(kind,valid),(kind,schema_check(kind,valid))
 assert schema_check(kind,invalid),kind
@pytest.mark.parametrize('kind',list(REGISTRY))
def test_status_enum_rejects_unrecognized(kind):
 r=json.loads((ROOT/'fixtures/valid'/f'{kind}.json').read_text());r['status']='totally_fabricated';assert schema_check(kind,r)
def test_approval_attestation_tampering_and_revocation():
 subject={'id':'CR-001','project_id':'PRJ-001','revision':3,'title':'test'}
 approval={'id':'APR-001','project_id':'PRJ-001','request_id':'CR-001','decision':'approved','approver_role':'founder','approved_subject_revision':3,'approved_content_hash':digest(subject)}
 payload={'approval_id':'APR-001','project_id':'PRJ-001','request_id':'CR-001','revision':3,'content_hash':digest(subject),'decision':'approved'}
 proof=att('founder_approval',payload)
 assert approval_verified(subject,approval,proof,KEYS)
 assert not approval_verified({**subject,'title':'changed'},approval,proof,KEYS)
 assert not approval_verified(subject,{**approval,'decision':'revoked'},proof,KEYS)
 assert not approval_verified(subject,approval,{**proof,'signature':'0'*64},KEYS)
 assert not approval_verified(subject,approval,proof,{})
 assert not approval_verified(subject,{**approval,'request_id':'CR-002'},proof,KEYS)
def test_evidence_attestation_integrity():
 blob=b'PASS test output';hashes={'run.log':hashlib.sha256(blob).hexdigest()}
 ev={'id':'EVD-001','project_id':'PRJ-001','test_id':'TEST-001','source_sha':'a'*40,'environment_id':'ci-1','result':'pass','artifact_hashes':hashes}
 payload={'evidence_id':'EVD-001','project_id':'PRJ-001','test_id':'TEST-001','source_sha':'a'*40,'environment_id':'ci-1','result':'pass','artifact_hashes':hashes}
 proof=att('ci_test_evidence',payload)
 assert evidence_verified(ev,proof,KEYS,{'run.log':blob})
 assert not evidence_verified(ev,proof,KEYS,{'run.log':b'FAIL'})
 assert not evidence_verified({**ev,'source_sha':'b'*40},proof,KEYS,{'run.log':blob})
 assert not evidence_verified(ev,None,KEYS,{'run.log':blob})
 acc={'status':'pass','candidate_sha':'a'*40,'evidence_ids':['EVD-001'],'unresolved_defect_ids':[]}
 assert acceptance_verified(acc,['TEST-001'],[ev],{'EVD-001':proof},KEYS,{'EVD-001':{'run.log':blob}})
 assert not acceptance_verified(acc,['TEST-001','TEST-002'],[ev],{'EVD-001':proof},KEYS,{'EVD-001':{'run.log':blob}})
 assert not acceptance_verified({**acc,'unresolved_defect_ids':['BUG-001']},['TEST-001'],[ev],{'EVD-001':proof},KEYS,{'EVD-001':{'run.log':blob}})
def test_transitions():
 assert transition_verified('requirement','proposed','under_review')
 assert not transition_verified('requirement','under_review','approved')
 assert transition_verified('requirement','under_review','approved',True)
 assert not transition_verified('requirement','proposed','accepted',True)
 assert not transition_verified('test','draft','pass')
def test_reference_types_project_isolation_cycles():
 p1=json.loads((ROOT/'fixtures/valid/project.json').read_text());p2={**p1,'id':'PRJ-002','project_id':'PRJ-002'}
 r=json.loads((ROOT/'fixtures/valid/requirement.json').read_text());r['feature_id']='FEAT-001'
 f=json.loads((ROOT/'fixtures/valid/feature.json').read_text());f['project_id']='PRJ-002'
 assert any('missing FEAT-001' in x for x in validate_bundle([('project',p1),('project',p2),('requirement',r),('feature',f)]))
 f2={**f,'project_id':'PRJ-001'}
 assert not validate_bundle([('project',p1),('requirement',r),('feature',f2)])
 assert any('duplicate' in x for x in validate_bundle([('project',p1),('project',p1)]))
 t1={'id':'TASK-001','project_id':'PRJ-001','dependency_ids':['TASK-002']};t2={'id':'TASK-002','project_id':'PRJ-001','dependency_ids':['TASK-001']}
 assert any('cycle' in x for x in validate_bundle([('project',p1),('task',t1),('task',t2)]))
