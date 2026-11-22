# Frozen evaluation protocol

Evaluator: `eovt-evaluator-20261121`. This scorer reproduces current local
result-analysis definitions without reinterpreting logs as new experiments.

## STT

SR/TR/CR are means of numeric final `success`, `following_rate`, `collision`
over valid episode results, multiplied by 100. TR averages episode rates;
it does not pool all time steps.
Baseline runtime TR uses executed `human_following` flags. At early termination
success requires final success and following flags; at the 300-step limit
the existing runtime uses the final following flag.

## OR

Frozen reference selection: pre-clear path **>2.5 m**, occlusion **>=0.5 m**,
with no additional post-event reappearance requirement.
The policy runs from the source episode start; reference events need not be
identical to policy-specific runtime visibility.

The existing baseline finds the first visible-to-invisible transition in its
`facing` trace. A later observation step establishes opportunity; a later
return of the signal establishes recovery (`K=1`).

| Metric | Computation |
| --- | --- |
| RSR | Mean numeric `rsr` over valid event results |
| VOR | Mean numeric `vor` over valid event results |
| CRR | Mean recovery success conditional on numeric `vor >=0.5` |
| MRS | Mean finite, non-null `recovery_steps` |

RSR/VOR/CRR are percentages; MRS is in environment steps. MRS is the recorded
loss-to-first-return interval. VOR is the implementation's post-loss
window/opportunity condition. Neither is automatically a separately ray-tested
geometric visibility rate or a latency from reappearance to K stable steps.
Failed events have no recovery latency; report MRS together with RSR.

## IC

Each event has one Same and three distinct Similar trials. The original actor
remains and the robot continues applying actions.

1. Require a four-trial structure. Exclude Same collision >0 and missing numeric success.
2. Same success is `success >=0.5`; otherwise it is a Same failure.
3. RFR = Same failures / valid collision-free Same controls.
4. Only Same-success events enter interference analysis.
5. Exclude Similar collisions and missing/non-finite dominance.
6. Read `target_dominance`, falling back to `target_dominance_rate`.
7. `<0.5` is switch, `>0.5` is retain, `==0.5` is uncertain.
8. Compute switches / decisive trials within each event. DSR is the mean over
   events with at least one decisive trial.

RFR/DSR are percentages with different denominators. They cannot be added.
DSR is not a pooled trial rate or an error rate over all 630 events.
Effective controls, eligible events, Similar collisions, uncertain and decisive
trials are reported.
The two baselines' OTPR uses Euclidean distances and is a behavioral proxy,
not an explicit identity-classification prediction. Legacy BIA does not replace
missing trial dominance.

## Missing values and validation

Final JSONs are units; `*_info.json` and status files are not.
Numeric metrics exclude booleans, non-finite/missing values.
Completed failures, including valid Lost/finish=false records, remain outcomes.
Malformed data and incomplete structures are reported separately.
Zero denominators produce null. Aggregation preserves the existing scorer's
metric-specific eligibility rules rather than imposing a new complete-case
filter to match a preferred result.

## Uncertainty

Layout-cluster bootstrap uses replacement, 2,000 repetitions by default,
seed 20261121 and 95% empirical percentile intervals. Layout-internal records
stay together; IC aggregates Similar outcomes within each event first.
Ordinary aggregation uses layouts present in its input.
Event-filter analysis reuses paired draws of the original 60-layout frame,
including zero-selected layouts. Subset differences change event composition
and conditional denominators and are descriptive, not causal effects.
