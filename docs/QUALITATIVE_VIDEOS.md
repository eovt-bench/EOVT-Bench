# OmTrackVLA: current task videos and evaluation evidence

Twelve selected robot-first-person demonstrations: STT, OR and IC each have
two successes and two failures. These are illustrations, not a balanced
performance estimate. OmTrackVLA weights and internal implementation are not
included. No video is an Oracle PID substitute or an offline motion replay.

STT retains its unchanged original success definition and reuses the actual
November 21 camera captures. OR comes from the complete November 24/25 raw
closed-loop collection and is rescored with synchronized instance masks,
complete target projections and real timestamps. IC was newly run on
November 25: two full events, each with one Same and three distinct Similar
trials, with actual timestamps and camera frames recorded together.

The 12 main videos are indexed in case_index.json/csv and index.html.
OR videos were encoded from original captured JPEG frames. IC/STT videos
were encoded directly from camera RGB. Display fps is for viewing; consult
the OR/IC simulation timestamps for elapsed-time evaluation. STT retains its
legacy per-step recording without claiming recovered simulation timestamps.

OR labels follow eovt-or-visibility-v0.2: actual loss, >=0.2 s of a usable
observation opportunity, then >=0.4 s of stable following within the declared
50-step window. No-loss/censored cases are not selected as failures.

IC labels follow eovt-ic-behavior-v0.2: qualify Same geometrically, compare
complete post-activation trajectories and body headings, then use direct
pose support where needed. OTPR is audit-only. Failure does not necessarily
mean an identity switch. The same geometric field is distinct from original
evaluator success. The rule was checked against 20 frozen development pairs;
that is a code regression check, not independent human validation.

Each selected IC video links to a full ic_events/event_XX/ic_event.json,
including its own Same and all three Similar trials. The Same reference
videos and all eight IC recordings are retained in those event directories.
Recompute an event with:

    python evaluation/score_or_ic.py ic ic_event.json --output scored.json

For OR use `python evaluation/score_or_ic.py or frames.jsonl --output scored.json`.
Instance masks and full projections
are bundled as NPZ arrays to verify the numerical pixel evidence.

See protocol/PROTOCOL.md and the four v0.2 configuration files.
The package excludes model source, weights, scenes, and humanoid meshes.

[Current archive](https://github.com/eovt-bench/EOVT-Bench/releases/download/v0.2.2-videos.20261125/eovt-omtrack-current-cases-20261125.zip)
