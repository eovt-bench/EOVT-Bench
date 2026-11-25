from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'baselines'))
from eovt_baseline.metrics import generic_metrics,occlusion_metrics,identity_metrics
from shared_analysis import summarize_stt,summarize_or,summarize_ic,ic_event_metrics
