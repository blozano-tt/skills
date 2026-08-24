# `llk`

Low-level kernels (tt-llk).

| Skill | Description |
|---|---|
| [`llk-perf-audit-review`](llk-perf-audit-review/SKILL.md) | Static performance review of Tensix compute kernels — wasted cycles, redundant register and memory traffic, loop-invariant work, and cheaper numerically-equivalent instruction sequences. Gated by a provenance lens (sfpi-compiled versus hand-written) and a semantic-equivalence test. Use when reviewing SFPU or Tensix kernel changes under tt_metal/tt-llk. |
| [`llk-race-audit-review`](llk-race-audit-review/SKILL.md) | Reviews tt-llk kernel changes for the nine race hazard classes — cfg-word overlap, dataflow CB sync, instruction latency, mailbox sync, MMIO ordering, NoC sync, reconfig stalls, semaphore handshakes, and srcreg bank sync — plus the cross-class seams between them. Use when reviewing changes under tt_metal/tt-llk. |

See the [top-level Reference](../../README.md#reference) for the full catalogue.
