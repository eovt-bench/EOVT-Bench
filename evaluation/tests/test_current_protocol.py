"""Regression checks for real timestamps, Same screening and full-path IC."""
import copy
import math
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ic_current import SpatialWorker, qualify_same, score_event, score_similar_trial
from or_current import score_event as score_or
from shared_analysis import ic_event_metrics


def trial(candidate=False):
    rows=[]
    for i in range(60):
        x=i*0.03
        row=dict(step=i,simulation_time_s=i*0.05,robot_position=[x,0.,0.],
                 original_position=[x+1.5,0.,0.],robot_heading_rad=0.)
        if candidate and i>=10:
            row.update(candidate_active=True,distractor_position=[x,0.,2.])
        rows.append(row)
    return dict(status="Normal",finish=True,success=1,collision=0,records=rows)


class CurrentTests(unittest.TestCase):
    def test_same_missing_success_is_not_silently_defaulted(self):
        t=trial()
        del t["success"]
        q=qualify_same(t)
        self.assertTrue(q["same_success_geometry"])
        self.assertIsNone(q["original_same_success"])

    def test_bad_same_final_distance_excludes_similar(self):
        t=trial()
        for row in t["records"]:
            row["original_position"][0]+=2
        result=score_event(dict(same=t,similar=[dict(trial(True),candidate_id=str(i)) for i in range(3)]))
        self.assertFalse(result["same_success"])
        self.assertEqual(result["similar_count"],0)

    def test_actual_timestamps_required(self):
        t=trial()
        del t["records"][1]["simulation_time_s"]
        with self.assertRaises(ValueError):
            qualify_same(t)

    def test_recorded_same_collision_has_consistent_failure_diagnostics(self):
        t = trial()
        t["collision"] = 1
        qualification = qualify_same(t)
        self.assertFalse(qualification["same_success_geometry"])
        self.assertEqual(qualification["same_geometry_label"], "失败")
        self.assertIn("no_recorded_collision", qualification["failed_checks"])
        self.assertIn("碰撞", qualification["reason"])

    def test_positive_does_not_depend_on_otpr(self):
        a,b=trial(),trial(True)
        b["target_dominance"]=0.
        scored=score_similar_trial(a,b)
        self.assertEqual(scored["behavior_label"],"follow_original_target")
        self.assertFalse(scored["otpr_used_for_decision"])

    def test_lost_remains_failure_without_claiming_switch(self):
        a,b=trial(),trial(True)
        b["status"]="Lost"
        scored=score_similar_trial(a,b)
        self.assertEqual(scored["failure_reason"],"F_LOST")
        self.assertFalse(scored["clear_distractor_behavior"])

    def test_weighted_dtw_full_endpoints(self):
        w=SpatialWorker()
        a=np.array([[0.,0.],[1.,0.],[2.,0.]])
        same=w.compare(a,a)
        self.assertEqual(same["dtw_rms"],0.)
        longer=w.compare(a,np.array([[0.,0.],[1.,0.],[2.,0.],[5.,0.]]))
        self.assertEqual(longer["path"][-1],[2,3])
        self.assertEqual(longer["frechet"],3.)

    def test_or_elapsed_time_and_no_loss(self):
        rows=[]
        for i in range(50):
            visible=not 5<=i<10
            rows.append(dict(step=i,simulation_time_s=i*0.05,target_pixels=6000 if visible else 0,
                image_height=384,image_width=384,target_distance_m=1.5,
                target_visibility_ratio=1. if visible else 0.,collision=False,
                env_episode_over=i==49))
        scored=score_or(rows)
        self.assertTrue(scored["recovered"])
        self.assertGreaterEqual(scored["recovery_after_opportunity_s"],0.4)
        for r in rows:
            r["target_pixels"]=6000
            r["target_visibility_ratio"]=1.
        result=score_or(rows)
        self.assertEqual(result["status"],"no_runtime_loss")
        self.assertIsNone(result["rsr"])

    def test_or_projection_is_required_not_fabricated(self):
        with self.assertRaises(ValueError):
            score_or([dict(step=0,simulation_time_s=0.,target_pixels=5000,
                image_height=384,image_width=384,target_distance_m=1.5)])

    def test_or_administrative_stop_is_not_a_failure(self):
        rows=[dict(step=i,simulation_time_s=i*0.05,target_pixels=6000 if i<5 else 0,
                   image_height=384,image_width=384,target_distance_m=1.5,
                   target_visibility_ratio=1. if i<5 else 0.,collision=False)
              for i in range(12)]
        rows[-1]["termination_reason"]="administrative_stop"
        scored=score_or(rows)
        self.assertTrue(scored["actual_loss"])
        self.assertTrue(scored["censored"])
        self.assertIsNone(scored["rsr"])

    def test_current_aggregation_never_falls_back_to_otpr(self):
        data=dict(identity_evaluator_version="eovt-ic-behavior-v0.2",same_success=True,
                  similar_results=[dict(behavior_label=label) for label in
                                   ("follow_original_target","follow_original_target","failure")])
        result=ic_event_metrics([dict(data=data)])
        self.assertAlmostEqual(result["effective_follow_ratio_pct"],200/3)
        self.assertIsNone(result["dsr_pct"])
        with self.assertRaises(ValueError):
            ic_event_metrics([dict(data=data),dict(data={})])


if __name__=="__main__":
    unittest.main()
