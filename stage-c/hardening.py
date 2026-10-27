"""Offline validation of canonical records and externally issued signed attestations.
HMAC verifies a configured trusted issuer, NOT the human identity of the Founder.
"""
import hashlib,hmac,json,re
from collections import defaultdict
from pathlib import Path
from validator import ROOT,REGISTRY,schema_check
ROOT=Path(__file__).resolve().parent
STATUS=json.loads((ROOT/'schemas/status-policy.json').read_text())
PREFIX={v['prefix']:k for k,v in REGISTRY.items()}
REF_TYPES={'feature_id':'feature','module_id':'module','requirement_id':'requirement','request_id':None,'fix_task_id':'task','approval_ref':'approval','founder_approval_ref':'approval','requirement_ids':'requirement','affected_requirement_ids':'requirement','affected_module_ids':'module','test_ids':'test','evidence_ids':'evidence','acceptance_ids':'acceptance','included_requirement_ids':'requirement','retest_evidence_ids':'evidence','unresolved_defect_ids':'defect','dependency_ids':'task','subject_ids':None,'affected_ids':None,'completed_record_ids':None,'dependencies':None}
STATES={
'requirement':{'proposed':['under_review','deferred','rejected'],'under_review':['approved','deferred','rejected'],'approved':['implemented','blocked','superseded'],'implemented':['verified','blocked'],'verified':['accepted','blocked'],'accepted':['superseded']},
'change':{'proposed':['impact_review','rejected','deferred'],'impact_review':['approved','rejected','deferred'],'approved':['implementing'],'implementing':['verifying','blocked'],'verifying':['closed','implementing','blocked']},
'approval':{'pending':['approved','rejected'],'approved':['revoked']},
'acceptance':{'not_run':['pass','fail','blocked','not_applicable'],'fail':['pass','blocked'],'blocked':['pass','fail'],'pass':['superseded']},
'evidence':{'not_run':['pass','fail','blocked'],'fail':['pass','blocked'],'blocked':['pass','fail']}}
for k,values in STATUS.items():
 if k not in STATES:
  STATES[k]={a:[b for b in values if b!=a and (b in {'blocked','rejected','superseded','archived','deprecated'} or values.index(b)==values.index(a)+1)] for a in values}

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def signed(payload,key):return hmac.new(key,canonical(payload),hashlib.sha256).hexdigest()
def verify_attestation(attestation, trusted_keys, expected_kind, expected_payload):
 if not isinstance(attestation,dict):return False
 if attestation.get('kind')!=expected_kind or attestation.get('payload')!=expected_payload:return False
 issuer=attestation.get('issuer'); key=trusted_keys.get(issuer)
 if not isinstance(key,bytes) or len(key)<32:return False
 sig=attestation.get('signature','')
 return isinstance(sig,str) and hmac.compare_digest(sig,signed({'kind':expected_kind,'issuer':issuer,'payload':expected_payload},key))
def approval_verified(subject,approval,attestation,trusted_keys):
 if approval.get('decision')!='approved' or approval.get('approver_role')!='founder':return False
 if approval.get('request_id')!=subject.get('id') or approval.get('project_id')!=subject.get('project_id'):return False
 if approval.get('approved_subject_revision')!=subject.get('revision') or approval.get('approved_content_hash')!=digest(subject):return False
 return verify_attestation(attestation,trusted_keys,'founder_approval',{'approval_id':approval['id'],'project_id':approval['project_id'],'request_id':subject['id'],'revision':subject['revision'],'content_hash':digest(subject),'decision':'approved'})
def evidence_verified(evidence,attestation,trusted_keys,artifact_bytes):
 if evidence.get('result')!='pass' or not re.fullmatch('[a-f0-9]{40}',str(evidence.get('source_sha',''))):return False
 if not evidence.get('environment_id') or not evidence.get('test_id'):return False
 hashes=evidence.get('artifact_hashes',{})
 if not isinstance(hashes,dict) or not hashes:return False
 if set(hashes)!=set(artifact_bytes):return False
 if any(hashlib.sha256(v).hexdigest()!=hashes[k] for k,v in artifact_bytes.items()):return False
 return verify_attestation(attestation,trusted_keys,'ci_test_evidence',{'evidence_id':evidence['id'],'project_id':evidence['project_id'],'test_id':evidence['test_id'],'source_sha':evidence['source_sha'],'environment_id':evidence['environment_id'],'result':'pass','artifact_hashes':hashes})
def transition_verified(kind,old,new,approval_valid=False):
 if kind not in STATES or old not in STATES[kind] or new not in STATUS[kind]:return False
 if old==new:return True
 if new not in STATES[kind][old]:return False
 if kind in ('requirement','change') and new=='approved' and not approval_valid:return False
 if kind=='approval' and new=='approved' and not approval_valid:return False
 return True

def validate_bundle(records):
 errors=[];index={};graph=defaultdict(list)
 for kind,r in records:
  rid=r.get('id'); pid=r.get('project_id')
  if kind not in REGISTRY:errors.append(f'unknown kind {kind}');continue
  errors.extend(f'{rid}: schema {msg}' for msg in schema_check(kind,r))
  key=(pid,rid)
  if key in index:errors.append(f'duplicate {key}')
  index[key]=kind
 for kind,r in records:
  pid=r.get('project_id');rid=r.get('id')
  if kind!='project' and (pid,pid) not in index:errors.append(f'{rid}: missing project root {pid}')
  for field,expected in REF_TYPES.items():
   if field not in r or r[field] is None:continue
   values=r[field] if isinstance(r[field],list) else [r[field]]
   for target in values:
    if not isinstance(target,str) or not re.fullmatch('[A-Z]+-[0-9]{3,}',target):errors.append(f'{rid}.{field}: malformed reference');continue
    actual=index.get((pid,target))
    if actual is None:errors.append(f'{rid}.{field}: missing {target}')
    elif expected and actual!=expected:errors.append(f'{rid}.{field}: expected {expected}, got {actual}')
    if field in ('dependency_ids','dependencies'):graph[(pid,rid)].append((pid,target))
 visiting=set();visited=set()
 def visit(node):
  if node in visiting:errors.append(f'dependency cycle {node}');return
  if node in visited:return
  visiting.add(node)
  for nxt in graph[node]:visit(nxt)
  visiting.remove(node);visited.add(node)
 for node in list(graph):visit(node)
 return errors

def acceptance_verified(acc,tests,evidence,attestations,trusted_keys,artifacts):
 if acc.get('status')!='pass' or acc.get('unresolved_defect_ids'):return False
 required=set(tests)
 if not required or not re.fullmatch('[a-f0-9]{40}',str(acc.get('candidate_sha',''))):return False
 covered=set()
 for ev in evidence:
  if ev.get('id') not in acc.get('evidence_ids',[]):continue
  if ev.get('source_sha')!=acc['candidate_sha']:continue
  if evidence_verified(ev,attestations.get(ev['id']),trusted_keys,artifacts.get(ev['id'],{})):covered.add(ev['test_id'])
 return required<=covered
