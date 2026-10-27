import copy,hashlib,json
from pathlib import Path
import pytest
from validator import ROOT,REGISTRY,schema_check,transition_check,reference_check,dependency_cycles,approval_check,evidence_check
@pytest.mark.parametrize('kind',REGISTRY)
def test_valid_fixture(kind):
    record=json.loads((ROOT/'fixtures'/'valid'/f'{kind}.json').read_text())
    assert not schema_check(kind,record)
@pytest.mark.parametrize('kind',REGISTRY)
def test_invalid_fixture(kind):
    record=json.loads((ROOT/'fixtures'/'invalid'/f'{kind}.json').read_text())
    assert schema_check(kind,record)
def test_missing_reference():
    project={'id':'PRJ-001','project_id':'PRJ-001'}
    req={'id':'REQ-001','project_id':'PRJ-001','feature_id':'FEAT-999'}
    assert any('FEAT-999' in e for e in reference_check([('project',project),('requirement',req)]))
def test_duplicate_id():
    r={'id':'REQ-001','project_id':'PRJ-001'}
    assert reference_check([('requirement',r),('requirement',r)])
def test_dependency_cycle():
    records=[('task',{'id':'TASK-001','dependency_ids':['TASK-002']}),('task',{'id':'TASK-002','dependency_ids':['TASK-001']})]
    assert dependency_cycles(records)
def test_state_machine():
    assert transition_check('requirement','approved','implemented')
    assert not transition_check('requirement','proposed','accepted')
    assert not transition_check('change','proposed','implementing')
def test_approval_revision_and_hash():
    subject={'id':'CR-001','revision':2,'title':'new scope'}
    digest=hashlib.sha256(json.dumps(subject,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    approval={'decision':'approved','approver_role':'founder','approved_subject_revision':2,'approved_content_hash':digest}
    assert approval_check(subject,approval)
    assert not approval_check({**subject,'revision':3},approval)
    assert not approval_check(subject,{**approval,'approved_content_hash':'bad'})
def test_evidence_source_and_coverage():
    acc={'status':'pass','candidate_sha':'a'*40,'evidence_ids':['EVD-001'],'unresolved_defect_ids':[]}
    ev={'id':'EVD-001','test_id':'TEST-001','source_sha':'a'*40,'result':'pass','environment_id':'ci','artifact_refs':['test.log']}
    assert evidence_check(acc,[ev],['TEST-001'])
    assert not evidence_check(acc,[{**ev,'source_sha':'b'*40}],['TEST-001'])
    assert not evidence_check(acc,[ev],['TEST-001','TEST-002'])
    assert not evidence_check({**acc,'unresolved_defect_ids':['BUG-001']},[ev],['TEST-001'])
