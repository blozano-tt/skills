# ADR-0002 — Self-containment, and why duplication beats sharing

**Status:** accepted, 2026-08-24.

## Context

gh-aw installs a pinned skill by copying **one skill folder**. Nothing outside that folder comes
along. This is the constraint the whole repo is shaped around, and it is precisely why
`tenstorrent/tt-buddy` — structurally a fine skills repo — cannot be pinned by a gh-aw workflow:

- its skills reach into a sibling `knowledge/` tree and a `~/.tt-buddy/notes/` repo;
- it is a Claude Code plugin whose manifest declares MCP servers and whose hooks inject content at
  session start;
- its review skill calls `AskUserQuestion`, which is fatal in a non-interactive workflow;
- several skills assume real silicon and profiling tooling.

None of that survives being copied into a CI runner.

## Decision

A skill on the review path must not require an MCP server, hooks, a sibling directory, a cross-skill
invocation, an interactive prompt, hardware, non-stdlib Python, a symlink, or **any tooling the CI
runner does not already provide**.

The test is availability in the runner, not whether something counts as "external". `gh` passes it:
every GitHub Actions runner ships it preinstalled and authenticated via `GITHUB_TOKEN`, so a skill
that shells out to `gh` survives being copied into a runner exactly as a stdlib Python script does.
The consumer must allow it in `tools.bash` — a smaller ask than the ones above, and one that fails
loudly at compile time rather than silently at review time.

Two consequences that are easy to get wrong:

**A `references/` path may only point inside its own skill folder.** A pointer at a sibling skill's
reference file resolves to nothing when that skill is pinned alone — and it fails *silently*, which
is the worst kind. Where two skills genuinely need the same reference, **duplicate the file** and
register the path in `DUPLICATED` in the test suite, which asserts the copies stay identical.

Duplication is the price of self-containment. Drift is its risk, so drift is enforced rather than
trusted. `references/special-values.md` is the first case: both `tt-precision-review` and
`llk-perf-audit-review` need the NaN/Inf tables, and neither can borrow the other's copy.

**Symlinks are out.** They break on Windows checkouts and in some archive extractions. `AGENTS.md`
was briefly a symlink to `CLAUDE.md`; it is now a real file with a test asserting the two match.

## The exemption

`meta/` is exempt. `tt-skills-upstream-audit` needs `pyyaml` — a pip install, which no runner
guarantees — and it is maintenance tooling for this catalogue rather than a review skill, so it is
never pinned by a review workflow. `test_review_path_scripts_are_stdlib_only` encodes the exemption
rather than leaving it to memory.

`meta/` is that bucket and no other: tooling that maintains the skills themselves. Needing `gh` is
not a reason to land there — `tt-split-pr-by-codeowners` was briefly filed under `meta/` on exactly
that misreading and belongs in `common/`, which is where the buckets-track-teams rule puts it.

## What is *not* a dependency

Cross-skill mentions in prose — "assumes `tt-review-core`", "see `tt-perf-claim-review`" — are a
documented composition expectation, satisfied by pinning both. They are not imports, and a skill
pinned alone still works; it just restates less.

## How this was found

Not by review. Wiring `references/special-values.md` into a second skill tripped
`test_referenced_files_exist`, because the pointer crossed a folder boundary. The constraint was
already written down and still got violated within hours — which is the argument for the test.
