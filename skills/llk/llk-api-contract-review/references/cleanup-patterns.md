# Maintainability patterns the team consistently flags

Assumes `tt-review-core`. These are `cleanup` severity — maintainability, not behaviour. Flag only on lines the PR touches.

Lifted verbatim from the LLK team's review rubric (`tenstorrent/llk_code_gen`, `dashboard/pr_review/knowledge/review-rubric.md`).

## Code-quality patterns the team consistently flags (severity: `cleanup`)

These are maintainability, not behaviour — use `cleanup` (or `nit:` for the
smallest preferences). Flag only on lines the PR touches.
- **Hardcoded tile/face/dim literals** — `16`/`32`/`64`/`256`/`512` used as a
  dimension must be derived from the named HW constants (`FACE_R_DIM`,
  `TILE_C_DIM`, `TILE_R_DIM`, `NUM_FACES`, …): e.g. `num_rows = num_faces *
  FACE_R_DIM`, not `32`. This is the single most common reviewer comment.
- **Unused params / variables / flags** — a template or function param not used
  in the body (e.g. `narrow_tile`, `num_faces`, `tile_size`) should be removed
  (the llk_api wrapper often makes it unnecessary), not silently carried. **But**
  if the signature must stay to match the test harness (`tests/sources/*`) or the
  API contract, mark it `[[maybe_unused]]` instead of removing it — don't tell the
  author to delete a param a caller/harness depends on.
- **Missing `const` / `constexpr`** — compile-time-known values should be
  `constexpr`; non-mutating methods should be `const`. Very high frequency.
- **`if` that should be `if constexpr`** — a non-`constexpr` `if` on a template
  param duplicates code in TRISC instruction memory and bloats code size; use
  `if constexpr` / combine duplicated branches.
- **Magic numbers / masks** — name them (anonymous-namespace `constexpr`) and add
  a comment for HW magic (bit masks, register values, `0x2`-style constants).
- **Address math via division** — L1/address math should use named shift
  constants (`addr >> L1_ADDR_SHIFT_AMT`), not `/16`; prefer shifts/masks over
  `*`, `/`, `%` in hot loops.
- **Redundant / duplicate programming** — an `ADDR_MOD`/config write identical to
  one already done earlier in the function; remove it.
- **No-op / dead branches** — an `else`/branch/function that programs nothing
  (a `dbg_halt_pack()` that does nothing, an empty config path); remove it or
  implement it — leaving it "only confuses people".
- **Commented-out code & bare TODOs** — per `CLAUDE.md` §Dead Code, any
  commented-out call/instruction (lines like `// TTI_*`, `// llk_*`, `// _llk_*`,
  `// MATH(`, `// UNPACK(`, `// PACK(`, `// sfpi::`) must carry an inline or
  adjacent comment explaining *why* it's disabled — acceptable reasons are a known
  HW-bug workaround, arch-specific divergence (WH vs BH), or pending re-evaluation.
  The explanation is what matters, not the mere presence; scan every such line and
  flag the unexplained ones. A `TODO` must link an issue number, never bare.
- **Raw int/string for HW modes** — pass an `enum class` and cast with
  `std::underlying_type_t<>` when writing register fields, instead of bare ints
  or string compares; it documents intent and rejects invalid values.
- **Naming** — names must describe behaviour and follow existing conventions; in
  Quasar don't reuse legacy names like `is_fp32_dest_acc_en` (check
  `llk_math_common.h` for current naming). Don't name a variable after the
  `#define` it reads.
- **Reuse over duplication** — call an existing helper/kernel (`_calculate_sqrt_`)
  and include its header rather than copy-pasting the body.

## PR hygiene

- **Scope** — a PR should be single-purpose. Flag orthogonal bugfixes, debug
  utilities, or unrelated refactors that belong in a separate PR (scope creep).
