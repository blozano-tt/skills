# Maintaining this repo

Invariants for whoever works on the skill catalogue. Read before adding or changing a skill.

## What this repo is

An **aggregation** of Tenstorrent code-review knowledge that lives in four other repositories, in
incompatible formats, two of them private. The skills are vendored copies, adapted for gh-aw.

That shapes everything below: the copies rot, the provenance is load-bearing, and two of the
upstreams sit on the other side of a disclosure boundary.

## Vendoring from private upstreams — read this first

**Two upstreams are private. This repo is public.** Content crossing that boundary gets a look
before it lands. The scope of that look was deliberately settled, so do not re-expand it by
instinct:

**Architecture detail is in scope for the catalogue, including Quasar.** Ordering semantics,
per-architecture divergence, and tool caveats are exactly what makes these skills better than a
generic reviewer. Most of this material is already public in tt-metal — `race-audit-all` and the
Quasar API surface both live on `main` — so withholding it from an aggregator that points at
tt-metal costs real review coverage and protects nothing. An earlier draft of this repo had the LLK
skills abstain on Quasar; that was reversed for this reason.

What actually gets stripped when vendoring:

1. **Internal-only pointers.** Confluence page IDs, internal ticket links, intranet URLs. Not
   because they are sensitive — because they are *dead* in a public repo. Anyone who can resolve
   one already has better access; anyone who cannot just hits a wall. Replace with a description of
   what the source establishes.
2. **Machine-specific and personal content.** Absolute paths from a contributor's laptop, identity
   mappings, harness-specific instructions that do not generalise.
3. **Anything a disclosure owner tells you to strip.** That call is theirs, not an agent's, and not
   a maintainer's acting alone.

**This applies to every re-vendor, not just the initial import.** A drift-driven update pulls fresh
text across the same boundary while looking like routine maintenance, which is why
`tt-skills-upstream-audit` reports and proposes but never auto-applies.

A keyword denylist is a *regression guard*, not detection: the Quasar codename appears legitimately
around 1400 times in public tt-metal, so grep-based screening produces almost pure noise. Judgement
is semantic and belongs to a person.

## Skill invariants

Enforced by `tests/test_skill_frontmatter.py`; run it before pushing.

- `name` equals the directory name.
- **Names are globally unique across buckets.** gh-aw resolves pins by name, not path — the bucket
  is invisible to the resolver, so two skills sharing a name make a pin ambiguous. The corollary:
  skills can move between buckets freely without breaking pins.
- `metadata.tier` is one of `model`, `op`, `kernel`, `process`.
- `metadata.upstream` is a list of `{repo, ref, path}`, optionally `branch`. `ref` is a 40-character
  lowercase SHA. Use `[]` for original work. **This is not documentation** — the drift audit parses
  it, so a malformed entry silently drops that upstream from the audit.
- `SKILL.md` is a **router**, capped at 130 lines. Depth goes in `references/*.md`, each under 4500
  bytes. This is not style: gh-aw reviewers only read a skill file when inline guidance is
  insufficient, and a monolith fights that budget.
- Every `references/…` path named in a `SKILL.md` exists.
- **Skills never post.** No `gh api -X POST`, no `gh pr review`. Agents run read-only; the workflow
  posts through `safe-outputs`.
- Promoted skills appear in `README.md` and `.claude-plugin/plugin.json`.

## Buckets track teams

`common`, `models`, `ttnn`, `metal`, `llk`, `inference`, `meta`. The `models` / `ttnn` line is
**consumer versus author**: `models` reviews code that *calls* TTNN, `ttnn` reviews code that
*implements* TTNN ops.

`in-progress/` holds drafts, excluded from the README and the plugin manifest. A retired skill is
deleted and its changeset names the replacement.

## Adding a skill

1. Write it as a router plus references. Ground every rule in an upstream and record it in
   `metadata.upstream`.
2. Run the disclosure gate if any source is private.
3. Add it to `README.md` and regenerate `.claude-plugin/plugin.json`.
4. Regenerate `SOURCES.md`:
   `python3 skills/meta/tt-skills-upstream-audit/scripts/check_drift.py --sources`
5. `pytest tests/`.

## Pin hygiene

Every external pin is a 40-character lowercase SHA. **gh-aw reports a failed skill install as a
non-fatal warning**, so a pin that does not resolve silently degrades a review into a generic one
rather than failing the run. `test_workflow_pins_only_real_skills` guards the reference workflow;
nothing can guard consumers' workflows, so get it right here.

## Style

Match the vendored prose. In particular, **em-dashes stay** — every Tenstorrent source uses them
heavily, and rewriting vendored text to satisfy a style rule introduces transcription errors for no
gain.

## Self-containment

The reason `tt-buddy` cannot be pinned by gh-aw, and the constraint this repo exists to satisfy.
gh-aw copies **one skill folder** — anything outside it does not come along.

So a skill on the review path must not require:

- **an MCP server** — no `deepwiki`, no device MCP, no plugin-declared servers
- **hooks** — no `SessionStart` injection, nothing that assumes a Claude Code session
- **sibling directories** — no reaching into a `knowledge/` tree next to `skills/`
- **cross-skill command invocations** — no calling another skill to fetch context mid-review
- **interactive prompts** — `AskUserQuestion` is fatal in a non-interactive workflow
- **hardware or external tooling** — no device, no profiler, no repo checkout beyond the PR
- **non-stdlib Python** — a review-path script may not need a pip install
- **symlinks** — they break on Windows checkouts and in some archive extractions

Enforced by `test_review_path_scripts_are_stdlib_only` and `test_agents_md_matches_claude_md`.
`AGENTS.md` is therefore a real file kept identical to this one, not a symlink.

**The meta bucket is the single exemption.** `tt-skills-upstream-audit` needs `gh` and `pyyaml`; it
is user-invoked maintenance tooling, never pinned by a review workflow, and it degrades to a warning
rather than a crash when either is missing.

**Cross-skill references are prose, not imports.** Skills say "assumes `tt-review-core`" and point
at each other by name. That is a documented composition expectation the workflow satisfies by
pinning both — not a load-bearing link. A skill pinned alone still works; it just restates less.
