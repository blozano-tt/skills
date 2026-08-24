# `models`

Model bringup and optimization: code that *calls* TTNN.

| Skill | Description |
|---|---|
| [`tt-model-bringup-review`](tt-model-bringup-review/SKILL.md) | Reviews TTNN model code — layout and memory-config defaults, the decode residual contract, composite-op preference, program-config pitfalls, hidden host fallbacks, and logical batch versus tile padding. Use when reviewing model bringup or optimization changes under models/ or ttnn/ Python. |
| [`tt-multichip-ccl-review`](tt-multichip-ccl-review/SKILL.md) | Reviews multi-chip and collective-communication code — num_links against device topology, bias-before-all-reduce numerics, distributed RMSNorm correctness, gather and reduce axes, fabric initialisation order, and CCL tuning claims. Use when reviewing changes touching CCL ops, mesh devices, fabric, or any all_gather / reduce_scatter / all_reduce path. |
| [`tt-precision-review`](tt-precision-review/SKILL.md) | Reviews dtype and math-fidelity policy — per-tensor-group precision, the prefill versus decode KV-cache dtype asymmetry, reduced-cache candidates, and PCC-collapse triage. Use when reviewing changes to dtypes, math fidelity, compute kernel configs, or cache precision. |
| [`tt-trace-review`](tt-trace-review/SKILL.md) | Reviews trace capture and replay safety — nothing host-side inside capture, program-cache warmup with exact signatures including scalar argument values, no allocation after capture, and device-owned autoregressive state. Use when reviewing changes touching begin_trace_capture, execute_trace, generator decode paths, or program-cache warmup. |

See the [top-level Reference](../../README.md#reference) for the full catalogue.
