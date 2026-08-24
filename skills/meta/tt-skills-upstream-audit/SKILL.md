---
name: tt-skills-upstream-audit
description: Check whether the vendored skills in this repo have drifted from their recorded upstream sources, and propose re-vendors where the drift matters.
disable-model-invocation: true
metadata:
  tier: process
  upstream: []
---

# Upstream drift audit

This repo is an **aggregation**. Its skills are vendored copies of content that lives in four other
repositories and keeps moving. Without a deliberate check, the copies rot silently.

Run this periodically, or before relying on a skill for something important.

## Run it

```bash
python3 skills/meta/tt-skills-upstream-audit/scripts/check_drift.py
python3 skills/meta/tt-skills-upstream-audit/scripts/check_drift.py --json
python3 skills/meta/tt-skills-upstream-audit/scripts/check_drift.py --sources   # SOURCES.md table
```

Requires an authenticated `gh`. Two of the four upstreams are private, so the audit resolves them
only if **your own** credential can see them — a Tenstorrent employee gets a full report, anyone
else gets `unreachable` rows and an otherwise working audit.

That is deliberate. A scheduled workflow doing this in CI would need a credential with private-repo
read access stored as a secret in a **public** repo, on a timer, for a convenience feature. Running
locally under the caller's own access has no secret to store and no standing access, and the
boundary matches the person.

## What the statuses mean

| Status | Meaning |
|---|---|
| `ok` | No commits touched that upstream path since the recorded ref |
| `DRIFT` | The path moved; the report gives the file count, last author and date |
| `GONE` | The path has no commits upstream — moved, deleted, or recorded wrong. **A repo bug, fix it** |
| `UNRCH` | Not visible to your credential, or the API call failed |
| `BAD` | Malformed `metadata.upstream` entry |

`recorded` is the **snapshot SHA we vendored from**, which is a repo-level SHA and generally is not
the last commit touching that path. Drift is therefore a path-filtered comparison, not SHA equality
— comparing SHAs directly reports drift on every row forever and trains you to ignore it.

## The honest limit — read this before trusting a clean report

**Most skills here synthesise two to four upstreams rather than copying one.** For those, this tool
tells you *"upstream moved, here is the diff"*. It cannot tell you whether the synthesis is now
wrong.

So it is a **notification tool that hands you a reading list, not an auto-updater**. The subset that
is close to a straight lift — `llk-perf-audit-review`, `llk-race-audit-review` — is where it comes
closest to a real staleness check.

**A clean audit does not mean the skills are current.** It means nothing moved in the specific paths
we recorded. If a skill's domain changed somewhere we never recorded, this reports `ok`.

## Triage: which drift matters

Not all drift is worth acting on. Read the diff and sort:

- **Act now** — a new hazard class, a changed invariant, a reversed recommendation, a new
  false-positive guard. These change what a review should flag.
- **Act eventually** — an upstream restructure, new examples, expanded prose that does not change
  the rules.
- **Ignore, but re-pin** — typo fixes, formatting, link updates. Bump the recorded ref so the row
  goes quiet; leave the vendored text alone.

## Proposing a re-vendor

Report and propose. **Do not auto-apply.** For each drift worth acting on:

1. Read the actual upstream diff, not just the file count.
2. State what changed in terms of *review behaviour* — what would a reviewer now flag, or stop
   flagging?
3. Propose the edit to the vendored file, and the `metadata.upstream[].ref` bump alongside it.
4. Keep them in the same change. A ref bump without the content update is worse than no bump: it
   silences the signal while leaving the copy stale.

## Every re-vendor crosses the private/public boundary

**This is why the skill reports and proposes rather than auto-applying.**

Two upstreams are private and this repo is public, so a drift-driven update pulls fresh text across
that boundary while looking like routine maintenance.

The review is narrow — see `CLAUDE.md` for the settled scope. Architecture detail stays, including
Quasar. What comes out is internal-only pointers (Confluence page IDs and similar: dead links in a
public repo, not secrets), machine-specific paths, and personal identity mappings.

Apply it to the text you are proposing to bring across, not to the whole file — and if a call is
genuinely uncertain, that is a question for a person, not a judgement to make inside the proposal.
