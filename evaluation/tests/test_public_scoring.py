import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared_analysis import ic_event_metrics
class PublicScoringTests(unittest.TestCase):
 def test_same_control_and_similar_switch(self):
  ts=[{'condition':'same','success':1,'collision':0}]+[{'condition':'similar','success':1,'collision':0,'target_dominance_rate':x} for x in [0.2,0.8,0.5]]
  r=ic_event_metrics([{'data':{'identity_trial_results':ts}}])
  self.assertEqual(r['rfr_pct'],0);self.assertEqual(r['dsr_pct'],50);self.assertEqual(r['uncertain_trials'],1)
  ts[0]['success']=0;r=ic_event_metrics([{'data':{'identity_trial_results':ts}}])
  self.assertEqual(r['rfr_pct'],100);self.assertIsNone(r['dsr_pct'])
 def test_collision_is_excluded(self):
  ts=[{'condition':'same','success':1,'collision':1}]+[{'condition':'similar','success':1,'collision':0,'target_dominance_rate':0.2} for _ in range(3)]
  r=ic_event_metrics([{'data':{'identity_trial_results':ts}}])
  self.assertEqual(r['same_collision_excluded'],1);self.assertIsNone(r['rfr_pct']);self.assertIsNone(r['dsr_pct'])

 def test_events_are_balanced_instead_of_pooling_trials(self):
  control={'condition':'same','success':1,'collision':0}
  def trial(value):
   return {'condition':'similar','success':1,'collision':0,'target_dominance_rate':value}
  a={'data':{'identity_trial_results':[control,trial(0.2),trial(0.5),trial(0.5)]}}
  b={'data':{'identity_trial_results':[control,trial(0.8),trial(0.8),trial(0.8)]}}
  result=ic_event_metrics([a,b])
  self.assertEqual(result['dsr_pct'],50)
  self.assertEqual(result['trial_dsr_pct'],25)
