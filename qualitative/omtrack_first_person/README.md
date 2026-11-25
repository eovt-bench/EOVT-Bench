# Current OmTrackVLA first-person cases

Current OR/IC evaluation: `eovt-or-ic-v0.2`. Twelve selected demonstrations, two successes and two failures per task.
STT was captured again with true timestamps; OR uses the completed raw collection and IC retains its November 25 recordings.
OR cases are Road/Indoor only with sustained complete disappearance. All task videos and Same controls use actual simulation timing at 1x.
The four main IC cases have four different Same controls. The archive includes four full IC events (1 Same + 3 Similar each) and all sixteen IC recordings.
These are selected examples, not population estimates. Failure is not automatically an identity switch. OTPR is not a decision input.

| Case | Scene | Decision evidence |
| --- | --- | --- |
| [STT_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/STT_success_01.mp4) | industrial | SR=1.0, TR=1.000 |
| [STT_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/STT_success_02.mp4) | road | SR=1.0, TR=1.000 |
| [STT_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/STT_failure_01.mp4) | road | SR=0.0, TR=0.718 |
| [STT_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/STT_failure_02.mp4) | indoor | SR=0.0, TR=0.843 |
| [OR_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/OR_success_01.mp4) | indoor | recovered; RSR=1.0 |
| [OR_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/OR_success_02.mp4) | road | recovered; RSR=1.0 |
| [OR_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/OR_failure_01.mp4) | road | visible_but_not_recovered; RSR=0.0 |
| [OR_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/OR_failure_02.mp4) | indoor | visible_but_not_recovered; RSR=0.0 |
| [IC_success_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/IC_success_01.mp4) | industrial | T_FULL |
| [IC_success_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/IC_success_02.mp4) | industrial | T_FULL |
| [IC_failure_01](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/IC_failure_01.mp4) | indoor | F_DISTRACTOR_POSE |
| [IC_failure_02](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/IC_failure_02.mp4) | road | F_DISTRACTOR_POSE |

[Download all videos and evidence](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.3-videos.20261125/eovt-omtrack-realtime-cases-20261125.zip)

Archive SHA-256: `3be87b4fc029a5f8fed8d6a1e9065668ba0b14d5d2dab682a5c71c350d9f56b6`.

Earlier video Releases are superseded by this selection and timing update.
No model weights or internal model implementation are distributed.
