---
name: llk-api-contract-review
description: Reviews tt-llk changes against the LLK API and hardware-state contract — unpack-to-dest bit-width and Math-thread rules, TTI/TT_OP macro class, pool-type clear values, CFG read-after-write ordering, STALLWAIT necessity, missing asserts, WH/BH/QSR parity, metal-side propagation and breaking changes, and the maintainability patterns the team consistently flags. Use when reviewing changes under tt_metal/tt-llk.
metadata:
  tier: kernel
  upstream:
    - repo: tenstorrent/llk_code_gen
      ref: f45ebabd3c7e7feac7932dffbb5cdde1a1ed91da
      path: dashboard/pr_review/knowledge/review-rubric.md
---

# LLK API contract review

Assumes `tt-review-core`. This is how the team's senior LLK reviewers actually review: the recurring
things they flag on Tensix kernel changes, at the level of the **API and hardware-state contract**
rather than the instruction stream.

Do not restate the generic C++ advice a compiler, `clang-tidy` or pre-commit already gives. Flag the
LLK-specific version — the consequence on hardware, on another architecture, or on the layer above.

## Where this sits among the LLK skills

| Skill | Owns |
|---|---|
| `llk-race-audit-review` | Intra-kernel race hazard classes and stale config **across invocations** |
| `llk-perf-audit-review` | Wasted cycles, redundant traffic, cheaper equivalent sequences |
| **this skill** | The API/state contract, guards, architecture parity, metal propagation, cleanup |

Overlap is real and the boundary is by *verdict*, not by topic. A drain that is missing is a race
finding; a drain that is provably redundant is a perf finding; a drain whose **contract** is wrong —
an end-of-call clear where the next call is supposed to assume clean state — is this skill's.
Cross-link, never contradict.

## Reference map

Read the file for the class you are checking. Each is self-contained.

- **`references/correctness-and-hazards.md`** — what the codebase is, and the correctness and
  hardware-hazard classes: SFPLOADMACRO sequencing, reconfig escapes, DEST/SRCB reuse corruption,
  the two `unpack_to_dest` rules, the counter/state contract, CFG register read-after-write
  ordering, STALLWAIT necessity in both directions, pool-type clear values, integer and format edge
  cases, and `TTI_*` versus `TT_OP_*` macro class. **Read this one first** — everything in it is a
  silent-corruption or build-break class.
- **`references/asserts-parity-and-propagation.md`** — the guards the team wants
  (`LLK_ASSERT` / `static_assert`), WH/BH/QSR parity including Quasar's structural divergence and
  its test gate, the metal 4-layer stack an LLK change must propagate through, and the
  breaking-change gate.
- **`references/cleanup-patterns.md`** — the maintainability rubric: hardcoded tile and face
  literals, unused parameters and when `[[maybe_unused]]` is the right answer instead of deletion,
  `if` that should be `if constexpr` and why it costs TRISC instruction memory, magic numbers,
  address math, redundant programming, dead branches, commented-out code, naming, reuse. Plus PR
  scope.
- **`references/style-and-scope.md`** — the style rules that *are* worth flagging (qualifier
  ordering, the doxygen tag policy), and the LLK-specific **do-not-flag** list that bounds them.

## Two traps worth knowing before you start

**The repository's own documentation is stale on the state contract.** `common-errors.md` and
`porting-guide.md` under `tt_metal/tt-llk/.claude/` still frame it as "`_uninit_` must restore every
register `_init_` touched." The team's current direction is clean-state-on-entry. A reviewer that
grounds a finding in those files will confidently recommend the wrong fix — flag the state escape
and prefer a clean re-set on entry. `references/correctness-and-hazards.md` states the current rule.

**`tt_metal/tt-llk/.claude/` is not guaranteed to be in context.** It is nested, and tt-metal has no
root `CLAUDE.md`, so do not assume the reviewer can see it. The style rules that matter are restated
in `references/style-and-scope.md` for that reason.

## Scope

`tt-review-core`'s scope rules apply, and `references/style-and-scope.md` narrows them further for
LLK. The short form: review what this PR changed, read past the diff for context, and do not
relitigate untouched code.

Severity uses `tt-review-core`'s vocabulary. The rubric's own internal ordering —
correctness, hazard, parity, propagation, style, cleanup — is a useful way to rank findings within a
review, but it is not a second severity scale: map it onto `MUST-FIX` / `SHOULD-FIX` / `CONSIDER`
and report those.
