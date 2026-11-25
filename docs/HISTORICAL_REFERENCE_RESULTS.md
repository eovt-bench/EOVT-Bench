# Historical baseline reference results

These tables are archived numerical references, not current OR/IC scores.
No per-episode baseline results are distributed.


These are historical aggregate values from completed baseline runs, evaluated
with `eovt-evaluator-20261121`. Brackets give 95% layout-cluster bootstrap intervals
(2,000 repetitions). Rates are percentages; MRS is in steps. The current video
update does not rerun these baselines or change their measured values.
Per-episode baseline result JSONs, result-file inventories and result archives
are not distributed in Git or Releases.

## STT

| Method | Episodes/events | SR | TR | CR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 1800 | 49.28 [46.50, 52.06] | 69.31 [66.88, 71.60] | 0.00 [0.00, 0.00] |
| Oracle PID | 1800 | 42.28 [38.94, 45.39] | 65.74 [63.02, 68.30] | 0.00 [0.00, 0.00] |

## OR — historical protocol

| Method | Episodes/events | RSR | VOR | CRR | MRS |
| --- | --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 31.43 [27.82, 35.33] | 72.54 [69.23, 75.94] | 43.33 [38.53, 48.28] | 4.50 [3.29, 5.89] |
| Oracle PID | 630 | 11.43 [8.62, 14.24] | 72.54 [69.69, 75.46] | 15.75 [11.85, 19.75] | 11.29 [9.66, 12.94] |

## IC — historical protocol

| Method | Valid Same | DSR eligible events | RFR | DSR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 174 | 72.22 [68.97, 75.39] | 72.80 [65.15, 80.61] |
| Oracle PID | 629 | 130 | 79.17 [75.97, 82.38] | 61.79 [51.99, 71.78] |

**Version and interpretation.** The tables above preserve the previously
reported aggregate reference values and are labeled with their original
evaluator version. They are not silently recomputed under the new OR/IC
protocol. New runs must record the evaluator and protocol version alongside
their results. The protocol is diagnostic: it describes capability failure
modes and is not intended to establish a universal ranking of models.
