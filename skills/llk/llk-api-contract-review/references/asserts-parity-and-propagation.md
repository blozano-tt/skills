# Guards, architecture parity, and metal propagation

Assumes `tt-review-core`. Missing guards, one-architecture changes that should be three, and LLK changes that do not reach the layers consuming them.

Lifted verbatim from the LLK team's review rubric (`tenstorrent/llk_code_gen`, `dashboard/pr_review/knowledge/review-rubric.md`).

## Asserts & safety guards

The team actively wants unsupported combinations and HW assumptions guarded —
not silently miscompiled. Flag a missing guard, and prefer suggesting one:
- `LLK_ASSERT(...)` for runtime preconditions (e.g. "this path only valid for
  ELWADD/SUB/MUL", "thread 1 is the one accessing L1").
- `static_assert(...)` for compile-time invariants on template params (e.g.
  `row_num_datums < TILE_C_DIM`), instead of commenting code out.
- When a guard is a temporary workaround, it should carry a note + a linked
  issue ("temporary until #NNNN is investigated"), never a bare `TODO`.
- A raw int/enum value handed to a register field that only accepts a few modes
  should be validated (static_assert / template specialization) — otherwise an
  invalid value compiles happily.

## Arch parity

- A change to one arch usually needs the matching change in the others. WH/BH use
  letter-based filenames (`llk_unpack_A.h`); QSR uses semantic names
  (`llk_unpack_unary_operand.h`). Flag a one-arch change that *looks* like it
  should be three ("same comment applies to the WH/BH copy too").
- **Quasar diverges structurally** — QSR has unpack0/1/2 + pack0/1 (different
  engine counts) and newer/stricter naming conventions. A WH/BH idiom may be
  outright wrong on QSR.
- **Quasar is gated on testing** — QSR files must not be modified until proper
  regressions exist for them. Flag QSR changes that ride along without test
  coverage.

## Metal integration & breaking changes

LLK is consumed through a 4-layer stack. If the PR changes an LLK function
signature, adds an op, or changes unpack/pack behaviour, the matching layers must
change too — flag missing propagation:
1. CKernels LLK API — `tt_metal/hw/ckernels/{arch}/metal/llk_api/` (almost always)
2. Compute API — `tt_metal/hw/inc/api/compute/` (if the public interface changes)
3. TTNN bypass includes — some TTNN ops include LLK headers directly
See `tt_metal/tt-llk/.claude/references/metal-integration.md` for the full list.

- **Breaking changes are a hard gate.** A changed signature, **changed parameter
  order**, changed default-param contract, or a changed golden/PCC threshold
  breaks tt-metal. The metal counterpart must be prepared and tested *before*
  this merges (per the breaking-changes guide in `CONTRIBUTING.md`), and the PR
  labelled accordingly. Flag the breaking change and the missing metal-side plan.
- **Regression gating** — changes to strides, tile/face dims, or perf-sensitive
  paths need tt-metal op sweeps and/or perf-regression runs. Ask for them.
