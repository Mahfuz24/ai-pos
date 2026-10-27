"""AI-POS Stage C validation: schema, references, transitions, approvals, evidence."""
import hashlib,json,re
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parent
REGISTRY=json.loads((ROOT/'registry.json').read_text())
TRANSITIONS={
'requirement':{'proposed':{'under_review','rejected','deferred'},'under_review':{'approved','rejected','deferred'},'approved':{'implemented','superseded','blocked'},'implemented':{'verified','blocked'},'verified':{'accepted','blocked'},'accepted':{'superseded'}},
'change':{'proposed':{'impact_review','rejected','deferred'},'impact_review':{'approved','rejected','deferred'},'approved':{'implementing'},'implementing':{'verifying','blocked'},'verifying':{'closed','implementing','blocked'}},
'approval':{'pending':{'approved','rejected'}},
'acceptance':{'not_run':{'pass','fail','blocked','not_applicable'},'fail':{'pass','blocked'},'blocked':{'pass','fail'},'pass':{'superseded'}},
'evidence':{'not_run':{'pass','fail','blocked'},'fail':{'pass','blocked'},'blocked':{'pass','fail'}},
}
REF_KEYS={'feature_id','module_id','requirement_id','request_id','fix_task_id','approval_ref','founder_approval_ref','requirement_ids','affected_requirement_ids','affected_module_ids','subject_ids','affected_ids','dependency_ids','dependencies','test_ids','evidence_ids','acceptance_ids','included_requirement_ids','completed_record_ids','unresolved_defect_ids','retest_evidence_ids'}
EXTERNAL_KEYS={'criterion_ids','evidence_ref','artifact_refs','artifact_hashes'}
def schema_check(kind,record):
    schema=json.loads((ROOT/'schemas'/f'{kind}.schema.json').read_text())
    return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(record)]
def transition_check(kind,old,new):
    return old==new or new in TRANSITIONS.get(kind,{}).get(old,set())
def reference_check(records):
    errors=[]; ids={}
    for kind,record in records:
        key=(record.get('project_id'),record.get('id'))
        if key in ids:errors.append(f'duplicate id: {key}')
        ids[key]=record
    for kind,record in records:
        for field,value in record.items():
            if field not in REF_KEYS or value is None:continue
            for ref in value if isinstance(value,list) else [value]:
                if isinstance(ref,str) and re.fullmatch(r'[A-Z]+-\d{3,}',ref) and (record.get('project_id'),ref) not in ids:
                    errors.append(f"{record.get('id')}.{field}: missing {ref}")
    # Project root is represented by its PRJ record.
    for kind,record in records:
        if kind!='project' and (record.get('project_id'),record.get('project_id')) not in ids:
            errors.append(f"{record.get('id')}: missing project root")
    return errors
def dependency_cycles(records):
    graph={r['id']:r.get('dependencies',[])+r.get('dependency_ids',[]) for _,r in records}
    visiting=set();visited=set();errors=[]
    def visit(node):
        if node in visiting:errors.append(f'cycle at {node}');return
        if node in visited:return
        visiting.add(node)
        for target in graph.get(node,[]):visit(target)
        visiting.remove(node);visited.add(node)
    for node in graph:visit(node)
    return errors
def approval_check(subject,approval):
    if not approval or approval.get('decision')!='approved' or approval.get('approver_role')!='founder':return False
    if approval.get('approved_subject_revision')!=subject.get('revision'):return False
    canonical=json.dumps(subject,sort_keys=True,separators=(',',':')).encode()
    return approval.get('approved_content_hash')==hashlib.sha256(canonical).hexdigest()
def evidence_check(acceptance,evidence,required_test_ids):
    if acceptance.get('status')!='pass':return False
    if not acceptance.get('candidate_sha') or not required_test_ids:return False
    found=set()
    for ev in evidence:
        if ev.get('id') not in acceptance.get('evidence_ids',[]):continue
        if ev.get('source_sha')!=acceptance['candidate_sha'] or ev.get('result')!='pass':continue
        if not ev.get('environment_id') or not ev.get('artifact_refs'):continue
        if ev.get('test_id'):found.add(ev['test_id'])
    return set(required_test_ids)<=found and not acceptance.get('unresolved_defect_ids')
def validate_records(records):
    errors=[]
    for kind,record in records:errors += [f"{record.get('id')} schema: {e}" for e in schema_check(kind,record)]
    return errors+reference_check(records)+dependency_cycles(records)
