# Publication scope

The public source snapshot uses project attribution. It does not publish
personal email addresses, private workstation paths or server credentials.
Upstream copyright and license notices are retained.
The owner authorized MIT for benchmark-owned code and CC BY 4.0 for
benchmark-owned scenes, task data and documentation on 2026-11-25.
[Licensing](LICENSING.md) defines the component split and attribution;
third-party resources retain their original terms.

The repository is intended for public access. The published package contains
the benchmark interface, diagnostic baselines, versioned evaluator,
configuration, metadata and selected qualitative demonstrations.

Historical baseline aggregate values are archived separately from current
evaluation instructions in `docs/HISTORICAL_REFERENCE_RESULTS.md`.
No raw baseline result JSONs, result-file manifest, or baseline result archive
is distributed. Input episode JSONs and user-facing output schema documentation
remain part of the benchmark interface.

Selected OmTrackVLA cases remain separate from baseline results. They are
demonstrations of task behavior, not a release of OmTrackVLA weights or
internal implementation. Their metric caveats and evidence are described in
the qualitative case index.

OR and IC threshold settings are published as an initial versioned protocol.
Historical aggregate tables keep their original evaluator label; new runs
must report the protocol version used for scoring.

Rewriting repository history cannot revoke copies already downloaded by
others or independently clear hosting-provider caches.
