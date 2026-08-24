# ADR-0001 — Scope of the vendoring review

**Status:** accepted, 2026-08-24. Supersedes an earlier, broader policy applied on the same day.

## Context

Two of the four upstreams — `tt-buddy` and `tt_ops_code_gen` — are private. This repo is public.
Vendoring their content was approved, which makes the question not *whether* to copy but *what to
remove on the way across*.

## The first policy, and why it was wrong

The initial policy stripped **Quasar hardware architecture** while keeping Quasar software rules and
APIs, and rewrote rules that carried a hardware justification to keep the imperative and drop the
*because*. Under it:

- The `Accumulate` reduce constraint kept its rule and lost its reason.
- The `race-audit-all` architecture note was not vendored.
- Both LLK skills **abstained on Quasar** — a Quasar-targeted change got no verdict.

Measurement during the build undermined the premise. The codename appears roughly **1,400 times in
public tt-metal**; the Quasar API surface is public (`temp_quasar_api.hpp`, `quasar_nanobind.cpp`,
`qa_hal.hpp`); and the `race-audit-all` architecture note itself is on public `main`.

So the policy was withholding, from an aggregator that points at tt-metal, material already
published *in* tt-metal — at the cost of real review coverage, and protecting nothing. Vague
architectural description in a `SKILL.md` is not a reverse-engineering vector.

## Decision

Architecture detail stays, including Quasar. What comes out is narrower:

1. **Internal-only pointers** — Confluence page IDs and similar. Not on sensitivity grounds: they
   are *dead links* in a public repo. Anyone able to resolve one has better access already; anyone
   else hits a wall. Replace with a description of what the source establishes.
2. **Machine-specific and personal content** — laptop paths, identity mappings, harness-specific
   instructions that do not generalise.
3. **Anything a disclosure owner asks to be stripped.** That is their call. Not an agent's, and not
   a maintainer's acting alone.

## Consequences

- The abstentions were removed; the LLK skills cover all three architectures with divergences named.
- The `race-audit-all` architecture note was vendored, recovering a genuine false-negative guard:
  the recall tool pre-clears some Quasar writes out of its findings while the underlying tracking
  has exceptions, so a seam must be discharged against the actual consumer, not the tool's silence.
- The reduce constraint regained its justification.
- **A keyword denylist is a regression guard, not detection.** With ~1,400 legitimate public hits,
  grep-based screening is almost pure noise. Judgement is semantic and belongs to a person.
- **This applies to every re-vendor.** A drift-driven update pulls fresh text across the same
  boundary while looking like routine maintenance, which is why `tt-skills-upstream-audit` reports
  and proposes but never auto-applies.

## Note

The audit that produced the first policy was not wasted. Its durable output was the part that was
never about Quasar: the machine-path and identity scrub, the provenance and attribution
requirement, and the re-vendor checkpoint. Those survive unchanged.
