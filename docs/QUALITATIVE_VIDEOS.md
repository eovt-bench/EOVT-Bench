# Qualitative videos

See the [12-case index](../qualitative/omtrack_first_person/README.md) and [Chinese interpretation guide](QUALITATIVE_VIDEOS.zh-CN.md).

All videos use OmTrackVLA only as the demonstration model; OmTrackVLA weights
and internal implementation are not released. Two successful and two failed
examples are selected per task. The binary video/evidence package is a
separate release asset; it is not embedded in Git history.

The existing OR/IC case labels retain their recorded legacy evaluator version.
They are qualitative demonstrations and are not silently recomputed under
`eovt-or-ic-initial-v0.1`. New OR/IC evidence should be scored with the
versioned modules documented in [`evaluation/PROTOCOL.md`](../evaluation/PROTOCOL.md).
