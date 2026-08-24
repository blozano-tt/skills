# ADR-0003 — Invariants are tests, not conventions

**Status:** accepted, 2026-08-24.

## Context

`mattpocock/skills` — the repo this one's structure is borrowed from — keeps four parallel indexes
in sync by hand: the top-level README, the bucket README, `plugin.json`'s `skills[]`, and `docs/`.
Its own `CLAUDE.md` concedes this is fragile. Nothing checks it.

We inherited the structure. We did not inherit the hand-syncing.

## Decision

Every invariant that can be checked is checked in `tests/test_skill_frontmatter.py`. The
non-obvious ones and what each is actually protecting:

| Invariant | Failure it prevents |
|---|---|
| Names globally unique | gh-aw resolves pins **by name, not path**, so two skills sharing a name make `owner/repo/name@sha` ambiguous |
| `metadata.upstream` shape | The drift audit *parses* this; a malformed entry silently drops an upstream from the audit |
| Referenced files exist | A router pointing at a missing file degrades silently — the agent just gets nothing |
| `SKILL.md` ≤130 lines, references <4500 bytes | gh-aw reviewers only read a skill file when inline guidance is insufficient; a monolith fights that budget |
| No posting from skills | Agents run read-only; the workflow posts via `safe-outputs` |
| Workflow pins resolve | gh-aw reports a failed skill install as a **non-fatal warning** — an unresolvable pin degrades a review into a generic one instead of failing the run |
| Review-path scripts stdlib-only | See [ADR-0002](0002-self-containment.md) |
| Duplicated references identical | See [ADR-0002](0002-self-containment.md) |
| Every vendored repo credited in README | Attribution is not decoration; a source added and never credited is the failure |

## Why these and not more

An invariant earns a test when violating it fails **silently**. Most of the list above shares that
property: a bad pin, a missing reference, a malformed upstream entry, an uncredited source — none
raises an error, all quietly degrade something. A rule whose violation is loud does not need a test.

## Evidence this was the right call

Three bugs during the initial build were caught by running the checks, not by reading the code:

- The drift script's `REPO_ROOT` was off by one level and reported **zero** upstreams — a silent
  pass that looked like success.
- Drift was computed by comparing repo-level SHAs rather than a path-filtered diff, which would have
  reported `DRIFT` on every row forever and trained everyone to ignore it.
- Eight upstream refs pointed at a non-default branch and resolved to nothing.

A fourth was caught by a test rather than by review: a `references/` pointer crossing a skill-folder
boundary, days after the rule forbidding it was written down.

## Note on this file's siblings

`CLAUDE.md` carries the rules and is capped at 90 lines, because it is loaded into context every
session in this repo. Justification lives here, where it is read once — when someone is about to
change a rule rather than follow one.
