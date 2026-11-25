# Current OmTrackVLA first-person cases

Current OR/IC evaluation: `eovt-or-ic-v0.2`. Twelve selected demonstrations, two successes and two failures per task.
STT captures retain their unchanged original scoring; OR uses the latest complete raw collection and IC was newly recorded on November 25.
The archive includes synchronized evidence, two full IC events (1 Same + 3 Similar each) and all eight IC recordings.
These are selected examples, not population estimates. Failure is not automatically an identity switch. OTPR is not a decision input.

| Case | Scene | Decision evidence |
| --- | --- | --- |
| [STT_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/STT_success_01.mp4) | industrial | SR=1.0, TR=1.000 |
| [STT_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/STT_success_02.mp4) | road | SR=1.0, TR=1.000 |
| [STT_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/STT_failure_01.mp4) | road | SR=0.0, TR=0.718 |
| [STT_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/STT_failure_02.mp4) | indoor | SR=0.0, TR=0.843 |
| [OR_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/OR_success_01.mp4) | industrial | recovered; RSR=1.0 |
| [OR_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/OR_success_02.mp4) | road | recovered; RSR=1.0 |
| [OR_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/OR_failure_01.mp4) | industrial | visible_but_not_recovered; RSR=0.0 |
| [OR_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/OR_failure_02.mp4) | road | no_observation_opportunity; RSR=0.0 |
| [IC_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/IC_failure_01.mp4) | indoor | F_DISTRACTOR_POSE |
| [IC_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/IC_failure_02.mp4) | indoor | F_DISTRACTOR_POSE |
| [IC_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/IC_success_01.mp4) | industrial | T_FULL |
| [IC_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/IC_success_02.mp4) | industrial | T_FULL |

[Download all videos and evidence](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/eovt-omtrack-current-cases-20261125.zip)

Archive SHA-256: `2b2fa8bee2154021744592ec42ba885ad429d13dc7874508df1996c83c0ff890`.

The November 21 video Release is superseded. Its labels remain historical and are not used by this current index.
No model weights or internal model implementation are distributed.
