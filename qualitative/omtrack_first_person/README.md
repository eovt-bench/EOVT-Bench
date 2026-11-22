# OmTrackVLA qualitative videos

Twelve fresh, selected closed-loop rollouts: two successes and two failures for each of STT, OR and IC.
Raw robot jaw RGB, one initial frame and one frame after each evaluation step; presentation at 10 fps.
These are illustrative cases, not an unbiased performance sample. Full result JSONs and step trajectories accompany each video.

STT labels follow the original success field. OR labels use the existing facing-loss/recovery evaluator;
they do not claim independent geometric visibility or a new stable-K-step criterion.
IC labels describe the original-target proximity ratio (OTPR), a Euclidean-distance behavioral proxy.
Each IC case has a newly rerun successful, collision-free Same control and a valid Similar trial.
OTPR > 0.5 is retention and < 0.5 is switching; ties and invalid trials are excluded.

| Case | Scene | Outcome | Steps | Evidence |
| --- | --- | --- | ---: | --- |
| [STT_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/STT_success_01.mp4) | industrial | success | 101 | SR=1, TR=1.000 |
| [STT_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/STT_success_02.mp4) | road | success | 100 | SR=1, TR=1.000 |
| [STT_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/STT_failure_01.mp4) | road | failure | 103 | SR=0, TR=0.718 |
| [STT_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/STT_failure_02.mp4) | indoor | failure | 102 | SR=0, TR=0.843 |
| [OR_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/OR_success_01.mp4) | indoor | success | 100 | RSR=1, loss=40, recovery=45 |
| [OR_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/OR_success_02.mp4) | road | success | 108 | RSR=1, loss=22, recovery=31 |
| [OR_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/OR_failure_01.mp4) | indoor | failure | 89 | RSR=0, loss=51, recovery=None |
| [OR_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/OR_failure_02.mp4) | road | failure | 95 | RSR=0, loss=77, recovery=None |
| [IC_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/IC_success_01.mp4) | industrial | success | 145 | OTPR=0.837, Same success=1 |
| [IC_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/IC_success_02.mp4) | road | success | 123 | OTPR=0.783, Same success=1 |
| [IC_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/IC_failure_01.mp4) | indoor | failure | 106 | OTPR=0.114, Same success=1 |
| [IC_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/IC_failure_02.mp4) | road | failure | 74 | OTPR=0.078, Same success=1 |

See the Chinese README and per-case JSONs for exact episode IDs, conditions and interpretation.
Local reruns use Habitat-Sim 0.3.1 on WSL2; they are not claimed to reproduce the old server frame-for-frame.
No scene/humanoid meshes or pretrained weights are bundled. Original resource terms still apply.

Download the complete [video and evidence archive](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.1.0-videos.20261121/eovt-omtrack-first-person-cases-20261121.zip) from the public [qualitative release](https://github.com/eovt-bench/EOVT-Bench/releases/tag/v0.1.0-videos.20261121).

Archive SHA-256: `ad73975a27164769aa6dd68b1c6e0d765265c448653d63e63081206dac4ccb54`.
