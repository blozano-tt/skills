---
"tt-review-skills": minor
---

Add `llk-api-contract-review` to the `llk` bucket, and complete `llk-perf-audit-review` with the
check catalogue it was shipped without.

`llk-api-contract-review` carries the LLK team's review rubric: the API and hardware-state contract
(the two `unpack_to_dest` rules, `TTI_*` versus `TT_OP_*` macro class, pool-type clear values, CFG
read-after-write ordering, STALLWAIT necessity in both directions), the guards the team wants,
WH/BH/QSR parity, the metal 4-layer propagation path and its breaking-change gate, and the
maintainability patterns reviewers flag most. None of it was covered: a coverage check across
`skills/` returned zero hits for `unpack_to_dest`, `TT_OP_`, `UNPACR_NOP`, `FACE_R_DIM`,
`STALLWAIT`, `llk_api`, `if constexpr` and doxygen. **Its upstream is private and unlicensed and
its disclosure gate is open — see ADR-0004; this skill is separable from the rest of the change.**

`llk-perf-audit-review` gains the four upstream references that were left behind when it was
vendored: the six-step method, catalogues A–F, and the disassembly and perf-counter validation
workflow. It previously carried the judgement framework — provenance lens, equivalence gate,
false-positive guards, verdicts — with nothing to apply it to. Two of the lifted checks are absent
from the LLK team's own current corpus: dead-initialized vector locals (`sfpi-gcc` does not
dead-store-eliminate them) and the `TT_`→`TTI_` upgrade when every operand is compile-time.

Also gates `PERF-WIN` on evidence the skill can actually obtain: the verdict is defined as "provably
removes instructions", the proof is an assembly diff, and a CI reviewer has no compiler — so
`SUGGESTION` is now stated as the ceiling absent disassembly.
