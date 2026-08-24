# `ttnn`

TTNN op authoring: code that *implements* TTNN ops.

| Skill | Description |
|---|---|
| [`ttnn-op-kernel-review`](ttnn-op-kernel-review/SKILL.md) | Structural correctness review for TTNN op kernels — init and data-format reconfig, TRISC synchronization, the tile_regs protocol, circular-buffer ownership and UB, work distribution, semaphores, control-flow CB balance, and in-place misuse. Use when reviewing changes to reader/compute/writer kernels, program factories, or program descriptors under ttnn/ or tt_metal/. |

See the [top-level Reference](../../README.md#reference) for the full catalogue.
