# How ownership actually resolves

Two rules decide every answer this skill gives. Both are easy to get wrong by eye, and a wrong
answer looks exactly like a right one.

**Last match wins.** Not the first, and never the union. tt-metal's file opens with `/*
@tenstorrent/metalium-developers-infra` and then narrows over ~573 further rules. A file matched by
six rules is owned by the sixth *alone*. Unioning the matches inflates the group count and produces
proposals that split a PR without reducing anything.

**A rule with no owners resets ownership to nobody.** tt-metal uses this deliberately —
`.github/deprecations.json` appears with an empty owner list, which un-owns it after `.github/`
claimed it. Unowned files are free: they can go in any PR without adding a reviewer group.

## Pattern syntax

The gitignore subset GitHub documents for CODEOWNERS. There is **no negation** — `!` is not
supported, so there is nothing there to get wrong.

| Pattern | Matches | Does not match |
|---|---|---|
| `/*` | `README.md` | `ttnn/core/x.cpp` — root level only |
| `*` | anything, any depth | — |
| `docs/` | `a/b/docs/x.md` — no interior `/`, so any depth | — |
| `/docs/` | `docs/deep/x.md` | `a/docs/x.md` — anchored |
| `docs/*` | `docs/x.md` | `docs/deep/x.md` — a `*` tail does not recurse |
| `models/tt_dit/` | everything beneath it | — |
| `apps/**/test` | `apps/test`, `apps/x/y/test` | — `**/` matches zero directories too |

`*` stays inside one path segment; `**` crosses segments. A trailing `/` marks a directory and does
not count as "contains a slash" for anchoring.

## Do not parse this by hand

`scripts/codeowners_map.py` implements the above in stdlib Python. Use it. A model reading 573 rules
and reasoning about which one wins will be right most of the time, and the times it is wrong are
silent.

```bash
gh pr view <n> --repo <owner>/<repo> --json files --jq '.files[].path' \
  | python3 scripts/codeowners_map.py --codeowners .github/CODEOWNERS --json
```

## Validate before proposing anything

Compare the computed group set for **all** changed files against what GitHub actually requested:

```bash
gh pr view <n> --repo <owner>/<repo> --json reviewRequests \
  --jq '[.reviewRequests[].name // .reviewRequests[].login] | sort'
```

They should agree. Where they differ, the difference is almost always GitHub filtering *after*
CODEOWNERS resolves, always in the direction of requesting **fewer** reviewers than the file
designates:

- **The PR author is never asked to review their own PR.** An author who is a code owner of the
  paths they touched drops out of the requested list but is still in the file.
- **A code owner without write access is skipped silently.**
- **An approval already given** removes that reviewer from the pending request list.

So computed ⊇ requested is expected and fine. **Computed ⊂ requested is a bug** — the parse missed a
rule, and any split built on it is worthless. Stop and say so rather than proposing one.

## The trap when checking whether any of this is enforced

Confirming that code-owner approval is actually required is worth doing once per repo, and the
obvious check gives the wrong answer. Classic branch protection and rulesets are separate
mechanisms, and a repo can use either or both:

```bash
gh api repos/<owner>/<repo>/branches/main/protection \
  --jq '.required_pull_request_reviews.require_code_owner_reviews'
gh api repos/<owner>/<repo>/rules/branches/main \
  --jq '[.[] | select(.type=="pull_request") | .parameters.require_code_owner_review]'
```

On tt-metal the first returns `false` and the second returns `[false, true]` — two overlapping
rulesets, which GitHub composes by taking the **most restrictive**. Code-owner review is required.
Reading only the first check would say the opposite, and would make this whole skill look pointless
on a repo where it matters most.
