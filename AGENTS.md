# Maintaining this repo

Rules for the skill catalogue. Reasoning lives in `.agents/adr/` — read the relevant ADR before
*changing* a rule, not before following one. This repo is an **aggregation**: vendored copies from
five repositories, three private. Copies rot, and provenance is load-bearing.

## Vendoring

Three upstreams are private; this repo is public. When bringing text across, strip:

1. **Internal-only pointers** — Confluence page IDs, ticket links, intranet URLs. Dead links here,
   not secrets. Replace with a description of what the source establishes.
2. **Machine-specific and personal content** — absolute paths, identity mappings, harness-specific
   instructions.
3. **Anything a disclosure owner asks you to strip.** Their call, not yours.

**Architecture detail stays, including Quasar** — do not re-expand by instinct. [ADR-0001](.agents/adr/0001-vendoring-scope.md) records an abstention tried and reversed.
**An unlicensed source needs approval, not a strip list** — [ADR-0004](.agents/adr/0004-llk-code-gen-vendoring.md).

**Vendoring is not endorsement.** No source wins a technical disagreement by provenance, however
well-evidenced; check a rule against the code it describes first. Four defects entered behind a
precedence rule that said otherwise — see `SOURCES.md`.

All of this applies to **every re-vendor**, which is why `tt-skills-upstream-audit` proposes but
never auto-applies.

## Self-containment

gh-aw copies **one skill folder**. A skill on the review path must not require: an MCP server,
hooks, a sibling dir, a cross-skill invocation, an interactive prompt, hardware, non-stdlib Python,
a symlink, or **tooling the runner lacks**. `gh` is allowed; list it in the consumer's `tools.bash`.

- A `references/` path may only point **inside its own skill folder**. Where two skills need the
  same reference, duplicate it and add the path to `DUPLICATED` in the test suite, which asserts the
  copies stay identical.
- Cross-skill mentions are prose, not imports. A skill pinned alone still works.
- **`meta/` is the single exemption** — tooling that maintains the skills. Needing `gh` is not.

See [ADR-0002](.agents/adr/0002-self-containment.md).

## Skill invariants

Enforced by `tests/test_skill_frontmatter.py`. Run it before pushing.

- `name` equals the directory name, and is **globally unique across buckets** — gh-aw resolves pins
  by name, not path. The corollary: skills move between buckets freely.
- `metadata.tier` ∈ `model | op | kernel | process`.
- `metadata.upstream` is a list of `{repo, ref, path}`, optionally `branch`; `ref` is a 40-character
  lowercase SHA; `[]` for original work. **The drift audit parses this** — a malformed entry
  silently drops that upstream from the audit.
- `SKILL.md` is a **router**, ≤130 lines; depth goes in `references/*.md`, each <4500 bytes.
- Every `references/…` path named in a `SKILL.md` exists.
- **Skills never post.** No `gh api -X POST`, no `gh pr review`.
- Promoted skills appear in `README.md` and `.claude-plugin/plugin.json`.
- Every vendored repo is credited in the README with a linked GitHub handle.

See [ADR-0003](.agents/adr/0003-enforced-invariants.md) for why these are tests rather than
convention.

## Buckets

`common`, `models`, `ttnn`, `metal`, `llk`, `inference`, `meta`. They track **teams**: the
`models`/`ttnn` line is consumer versus author — `models` reviews code that *calls* TTNN, `ttnn`
reviews code that *implements* TTNN ops.

`in-progress/` holds drafts, excluded from the README and plugin manifest. A retired skill is deleted
and its changeset names the replacement.

## Adding a skill

1. Write it as a router plus references; record every source in `metadata.upstream`.
2. Apply the vendoring rules above if any source is private.
3. Add it to `README.md` (reference table **and** credit section) and regenerate
   `.claude-plugin/plugin.json`.
4. Regenerate `SOURCES.md`:
   `python3 skills/meta/tt-skills-upstream-audit/scripts/check_drift.py --sources`
5. `pytest tests/`.

## Pins

Every external pin is a 40-character lowercase SHA. **gh-aw reports a failed skill install as a
non-fatal warning**, so an unresolvable pin silently degrades a review into a generic one rather than
failing the run. Tests guard the reference workflow; nothing can guard consumers'.

## Style, and this file

Match the vendored prose — **em-dashes stay**; rewriting vendored text to satisfy a style rule
introduces transcription errors for no gain. This file is capped at 90 lines by
`test_claude_md_stays_a_rulebook`: it is loaded every session, so it carries rules and justification
goes to `.agents/adr/`.
