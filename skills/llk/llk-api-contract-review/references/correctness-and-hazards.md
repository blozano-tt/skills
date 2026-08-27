# LLK correctness and hardware hazards

Assumes `tt-review-core`. The highest-value section of this skill: each item below is a silent-corruption or build-break class, not a style preference.

Lifted verbatim from the LLK team's review rubric (`tenstorrent/llk_code_gen`, `dashboard/pr_review/knowledge/review-rubric.md`).

## What the codebase is

Header-only library for Tensix kernels across three archs: **Wormhole B0 (WH)**,
**Blackhole (BH)**, **Quasar (QSR)**. Tensix = 5 RISC-V cores (B, T0/unpack,
T1/math, T2/pack, NC) + 3-way threaded coprocessor. The init/execute/uninit
contract across T0/T1/T2 is an imperative the caller must satisfy — not a
guarantee. TRISC instruction memory is small, so code size matters.

## Correctness & HW hazards (look hard for these)

- **SFPLOADMACRO hazards** — macro-load sequencing on the vector unit can race
  with dependent ops. `recip.h`-style sequences are historically fragile; verify
  the hazard guide (`docs/sfploadmacro_hazard_guide.md`) and that a "fix" doesn't
  silently regress per-tile cycles.
- **Reconfig escapes** — HW state (formats, DEST modes) leaking between kernel
  reconfigurations. A change that reconfigures unpack/pack/DEST must restore or
  fully re-set state; tests can pass while leaking onto the *next* test.
- **DEST / SRCB reuse corruption** — e.g. `UnpackToDestFp32` leaking via
  `DEST_TO_SRCB` reuse corrupted `binary_dest_reuse` ELWMUL on BH
  (nondeterministic, watcher-masked). Scrutinise DEST-reuse / fp32-dest paths.
- **`unpack_to_dest` skips Math** — when unpacking straight to DEST, the Math
  thread should do nothing functional and the dvalid/client setup must reflect
  only UNPACK + PACK clients (no FPU client). Flag leftover Math programming, an
  `unpack_dest_dvalid`/`setup_dvalid` block, or an FPU client left in for the
  unpack-to-dest path — it does nothing or corrupts.
- **`unpack_to_dest` format/DEST bit-width must match** — the direct-to-DEST path
  is only valid when the format bit-width matches DEST mode: non-32-bit +
  `dest_acc=No` (16b→16b), or 32-bit + `dest_acc=Yes` (32b→32b). A mismatch
  silently produces **all-zeros** in DEST and must instead take the FPU/datacopy
  path. Flag an `unpack_to_dest=true` path that doesn't gate on this bit-width
  match.
- **Counter / state contract** — every LLK API should *start* from a clean
  counter state, not clear it at the end. Flag an end-of-call counter clear; the
  next call is supposed to assume clean state (that's the shared API contract).
  Note: the repo's own `common-errors.md` / `porting-guide.md` still frame this as
  "`_uninit_` must restore every register `_init_` touched" — the team's current
  direction is clean-state-on-entry (see `learnings.md`, the move away from
  `unset`/`revert`/`uninit`-flag APIs), so don't push a *missing `_uninit_`
  restore* as the fix; flag the state escape and prefer a clean re-set on entry.
- **CFG register read-after-write ordering** — reading a config register that may
  have in-flight tensix/MMIO writes needs ordering: drain prior writes, read into
  a temp, place NOPs/sync correctly (reads usually belong *before* the NOPs).
  Racing a CFG read against its write is a silent-wrong-value hazard.
- **STALLWAIT necessity** — question both directions: a STALLWAIT added "to be
  safe" may just burn cycles (some registers aren't latched while the engine
  runs / shadow registers handle it), and a removed one may open a real race.
- **Pool-type clear value** — `UNPACR_NOP` / SrcB clear must use `-inf` for
  `PoolType::MAX` but `0`/plain clear for `SUM`/`AVG`. A single clear path for all
  pool types is a correctness bug.
- **Integer/format edge cases** — signed Int8, fp32→uint16, MOVD2B overlays,
  `transpose_dest_32b` bit handling. Off-by-one-bit and clamp bugs hide here.
- **`TTI_*` vs `TT_OP_*` macro type** — `TTI_*` executes immediately (inline
  asm); `TT_OP_*` returns a constexpr encoding for `ckernel_template` /
  `load_replay_buf`. A `TTI_*` macro handed to a `ckernel_template` constructor
  (or vice-versa) is a bug — it fails to build (`impossible constraint in 'asm'`)
  or programs the wrong thing. Relatedly, flag a boolean expression passed where a
  HW constant is required (e.g. `pool_type == PoolType::MAX` instead of
  `p_unpacr_nop::CLR_SRC_NEGINF`).
