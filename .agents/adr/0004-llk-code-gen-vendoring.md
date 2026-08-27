# ADR-0004 — Vendoring from `llk_code_gen`, an unlicensed private repo

**Status:** proposed, 2026-08-27. **Blocks merge of `llk-api-contract-review`.**

## Context

`tenstorrent/llk_code_gen` holds the knowledge corpus the LLK team's own PR-review workflow
(`.github/workflows/llk-pr-review.yaml` in tt-metal) fetches at runtime. Six files under
`dashboard/pr_review/knowledge`. One of them, `review-rubric.md`, is the best single description of
how the team's senior LLK reviewers actually review, and nothing equivalent exists in this
catalogue: a coverage check across `skills/` returned zero hits for `unpack_to_dest`, `TT_OP_`,
`UNPACR_NOP`, `FACE_R_DIM`, `STALLWAIT`, `llk_api`, `if constexpr` and doxygen.

That is the case for vendoring it. Two things make it different from the four upstreams
[ADR-0001](0001-vendoring-scope.md) covers.

## What is different

**1. It is not one of the approved upstreams.** ADR-0001 records that vendoring `tt-buddy` and
`tt_ops_code_gen` "was approved", and frames the remaining question as *what to strip on the way
across*. `llk_code_gen` has no such approval. ADR-0001's third strip rule is explicit that a
disclosure call belongs to the disclosure owner — "not an agent's, and not a maintainer's acting
alone." The owning team here is the LLK team; the corpus's primary human author is
[@nstamatovicTT](https://github.com/nstamatovicTT).

**2. It carries no licence file.** The other four upstreams are Apache-2.0, which is what the
README's licence section asserted. `llk_code_gen` is an internal repository with no `LICENSE`, so
vendoring from it does not rest on an open licence — it rests on a disclosure decision, and the
README now says so.

There is a third, procedural point. This repo is public, so **the content becomes public when the
pull request opens, not when it merges.** A later decision to strip does not unpublish it; the
branch and its diff remain reachable. That makes the gate a pre-merge formality only in appearance.

## Decision

Vendoring is **proposed, not accepted**. `llk-api-contract-review` ships in the same PR as the
public-sourced perf catalogue so the content can be read and judged concretely, but the two are
separable and the API-contract skill should not merge until:

1. the LLK team, as disclosure owner, signs off on the specific text — the four files under
   `skills/llk/llk-api-contract-review/references/`; and
2. someone confirms an unlicensed internal source may be redistributed under this repo's Apache-2.0.

If either answer is no, delete `skills/llk/llk-api-contract-review/` and its index entries. Nothing
else in the PR depends on it.

## What was already stripped

ADR-0001's rules were applied on the way across. One hit: a rule attributing a review preference to
a named individual, rewritten to name the role instead. No internal pointers, ticket links,
Confluence IDs, absolute paths or credentials were present in the vendored sections.

Everything else is verbatim, which is the point — see the note in
[ADR-0001](0001-vendoring-scope.md) that rewriting vendored text introduces transcription errors for
no gain, and `CLAUDE.md`'s style rule to the same effect.

## Consequences

- The README's licence section now distinguishes the four Apache-2.0 upstreams from this one.
- `SOURCES.md` records it as `private`, `unlicensed`.
- The pinned `ref` is a commit on the default branch, so `tt-skills-upstream-audit` will report
  drift on it like any other upstream — and per ADR-0001 a drift-driven re-vendor "pulls fresh text
  across the same boundary while looking like routine maintenance." For this upstream that boundary
  is a disclosure gate, not a style gate. The audit proposes; it must not auto-apply here.
- The drift audit needs read access to a private repo. For a maintainer without it, `check_drift.py`
  reports the upstream as unreachable rather than failing — a silent gap in coverage for exactly the
  source that most needs watching.
