# Event selection metadata

The fixed reference event index uses 0.25 m path sampling, a 2.0 m observer
lag, and 9 visibility rays with at least 5 blocked. Selection requires a clear
pre-occlusion path length greater than 2.5 m and an occlusion length of at
least 0.5 m, with no additional post-reappearance requirement.

These are reference geometry conditions, not runtime loss or reacquisition
observations. Current runtime evaluation follows
[`evaluation/PROTOCOL.md`](../../evaluation/PROTOCOL.md) and the v0.2
settings under `configs/evaluation/`. Reference lengths and selection criteria
remain fixed in each event's metadata; descriptive protocol updates do not
regenerate the index or alter geometry.
