# Style rules worth flagging, and what not to flag

Assumes `tt-review-core`. The scope bound below is LLK-specific and narrower than `tt-review-core`'s general guards; apply both.

Lifted verbatim from the LLK team's review rubric (`tenstorrent/llk_code_gen`, `dashboard/pr_review/knowledge/review-rubric.md`).

## Style rules that ARE worth flagging (also in CLAUDE.md / references)

Kept self-contained here because the repo's own `tt_metal/tt-llk/.claude/` is **not**
guaranteed to be in the review's context — it's nested under `tt_metal/tt-llk/` and
tt-metal has no root `CLAUDE.md`, so don't assume the reviewer can see it.
- `const <type>` ordering — `const uint32_t x`, never `uint32_t const x`. Same
  for `volatile`/`constexpr` qualifiers on declarations.
- Doxygen on every LLK API (`@brief`/`@param`/`@tparam`/`@ref`/`@note`, with the
  init/execute/uninit `@note`). **No** `@pre`/`@post` and no bloat tags
  (`@details`/`@author`/`@date`/`@version`/`@todo`/`@remark`, or `@return` on
  void). AI-generated doxygen is acceptable as long as it follows the policy. The
  Compute API keeps its published prose+table format instead of `@param`.

## Out of scope — do NOT flag (false positives)

This list bounds *scope*, not *confidence* — it does not override the recall
mandate. It excludes the categories below; it does **not** license dropping an
uncertain-but-genuine LLK finding (surface those as suspicions instead).
- Pre-existing issues on lines the PR didn't touch.
- Generic C++ modernization churn (enum-class-everything, `std::` aliases,
  `reinterpret_cast`, includes, formatting) on code the PR didn't change, or
  anything a compiler / `clang-tidy` / pre-commit already reports. Flag the
  LLK-specific consequence (HW-dim literals, `if constexpr` code-size,
  register-field enums, unpack-to-dest semantics), not blanket style churn.
- Build/test signal — do not try to build or run tests.
- General "needs more tests"/"add docs" unless CLAUDE.md requires it.
- Intentional changes clearly part of the broader PR.
- Style rules silenced explicitly in code (e.g. lint-ignore).
</content>
