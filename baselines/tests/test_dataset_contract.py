import gzip,json,unittest
from occbench_baseline.paths import OCCBENCH_ROOT
class DatasetContractTests(unittest.TestCase):
 def test_counts_paths_and_new_ic(self):
  for name,count in [('STT',1800),('OR',630),('IC',630)]:
   data=json.load(gzip.open(OCCBENCH_ROOT/'episodes'/name/'val/val.json.gz','rt'))
   self.assertEqual(len(data['episodes']),count)
   for ep in data['episodes']:
    self.assertTrue((OCCBENCH_ROOT/ep['scene_id']).is_file())
    self.assertTrue((OCCBENCH_ROOT/ep['scene_dataset_config']).is_file())
    if name=='IC':
     event=ep['info']['eovt_task'];trials=event['identity_trials']
     self.assertEqual(ep['eovt_event'],event)
     self.assertEqual(event['action_mode'],'closed_loop_model_actions_executed')
     self.assertEqual(event['identity_protocol_version'],'appearance_top3_1same_3similar_v1')
     self.assertEqual(len(trials),4)
     self.assertEqual(sum(t['condition']=='same' for t in trials),1)
     similar=[t['actor_name_after_occlusion'] for t in trials if t['condition']=='similar_swap']
     self.assertEqual(len(set(similar)),3)
     self.assertNotIn(ep['info']['main_humanoid_name'],similar)
