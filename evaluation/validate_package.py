#!/usr/bin/env python3
from pathlib import Path
import gzip,json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def validate():
 errors=[];counts={};layouts=set();actors={'male_4','female_2'}
 def ref(value):
  if not (ROOT/value).is_file():errors.append('missing episode asset: '+value)
 for task,total in [('STT',1800),('OR',630),('IC',630)]:
  f=ROOT/'episodes'/task/'val/val.json.gz'
  eps=json.load(gzip.open(f,'rt'))['episodes'];counts[task]=len(eps)
  if len(eps)!=total:errors.append('wrong count for '+task)
  ids=set()
  for ep in eps:
   if ep['episode_id'] in ids:errors.append('duplicate episode id '+ep['episode_id'])
   ids.add(ep['episode_id']);ref(ep['scene_id']);ref(ep['scene_dataset_config'])
   layouts.add(Path(ep['scene_id']).parent.name)
   info=ep['info'];actors.add(info['main_humanoid_name']);actors.update(info.get('extra_humanoid_names',[]))
   if task in ('OR','IC'):
    event=info['eovt_task']
    expected_name={'OR':'Post-Occlusion Target Reacquisition','IC':'Post-Occlusion Identity Consistency'}[task]
    if event.get('task_name')!=expected_name or event.get('task_version')!='eovt-or-ic-v0.2':errors.append('stale task description version '+ep['episode_id'])
   gen=info.get('eovt_generation',{})
   for k in ['human_navmesh','dog_navmesh']:
    if gen.get(k):ref(gen[k])
   if task=='IC':
    event=info['eovt_task'];trials=event.get('identity_trials',[])
    if ep.get('eovt_event')!=event:errors.append('conflicting IC aliases '+ep['episode_id'])
    if event.get('action_mode')!='closed_loop_model_actions_executed':errors.append('wrong effective IC action mode '+ep['episode_id'])
    same=[t for t in trials if t['condition']=='same'];similar=[t for t in trials if t['condition'] in ('similar','similar_swap')]
    cand=[t['actor_name_after_occlusion'] for t in similar];actors.update(cand)
    if len(same)!=1 or len(similar)!=3 or len(set(cand))!=3 or info['main_humanoid_name'] in cand:errors.append('invalid IC '+ep['episode_id'])
 for actor in sorted(actors):
  for name in [actor+'.urdf',actor+'_motion_data_smplx.pkl']:
   ref(str(Path('assets/humanoids/humanoid_data')/actor/name))
 index=json.load(gzip.open(ROOT/'episodes/index/all_episodes.json.gz','rt'))['episodes']
 if len(index)!=1800:errors.append('wrong published index count')
 for ep in index:ref(ep['scene_id']);ref(ep['scene_dataset_config'])
 urdfs=list((ROOT/'assets').rglob('*.urdf'))
 for f in urdfs:
  for node in ET.parse(f).iter('mesh'):
   value=node.get('filename')
   if value and not (f.parent/value).is_file():errors.append('missing URDF mesh '+str(f.relative_to(ROOT))+': '+value)
 for f in (ROOT/'scenes').rglob('*.json'):
  if not any(f.name.endswith(x) for x in ['stage_config.json','semantic_config.json','scene_dataset_config.json']):continue
  d=json.loads(f.read_text())
  def walk(x,key=''):
   if isinstance(x,dict):
    for k,v in x.items():walk(v,k)
   elif isinstance(x,list):
    for v in x:walk(v,key)
   elif isinstance(x,str) and (key in ['render_asset','collision_asset','semantic_asset','semantic_descriptor_filename','.json'] or x.endswith('.navmesh')):
    if not (f.parent/x).is_file():errors.append('missing scene dependency '+str(f.relative_to(ROOT))+': '+x)
  walk(d)
 return {'status':'PASS' if not errors else 'FAIL','task_counts':counts,'layout_count':len(layouts),'referenced_actor_count':len(actors),'urdf_count':len(urdfs),'errors':errors}
if __name__=='__main__':
 report=validate();print(json.dumps(report,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
