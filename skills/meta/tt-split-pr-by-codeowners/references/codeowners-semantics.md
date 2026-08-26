# How ownership actually resolves

Three rules decide every answer this skill gives. All are easy to get wrong by eye, and a wrong
answer looks exactly like a right one.

**Last match wins.** Not the first, and never the union across rules. tt-metal's file opens with
`/* @tenstorrent/metalium-developers-infra` and narrows over ~573 further rules. A file matched by
six rules is owned by the sixth *alone*.

**Owners on one rule are alternatives.** GitHub: *"an approval from any of the owners is sufficient
to meet this requirement."* A rule's owner list is a set of substitutes, so the approvals a PR needs
is a **cover** over its rules, not the size of the union — files owned by `{A,B}` and `{A,C}` are
unblocked by A alone. Counting the union overstates the cost, sometimes badly: a real 174-file
tt-metal PR requests 36 reviewers and is unblocked by 7 approvals. Splitting on 36 buys nothing.

**A rule with no owners resets ownership to nobody.** Used deliberately to carve an exception out of
a broader rule — tt-metal does this for `.github/deprecations.json`. Unowned files are free: they go
in any slice without adding an approver.

## Pattern syntax

The gitignore subset GitHub documents. There is **no negation** — `!` is unsupported.

| Pattern | Matches | Does not match |
|---|---|---|
| `/*` | `README.md` | `ttnn/core/x.cpp` — root level only |
| `docs/` | `a/b/docs/x.md` — no interior `/`, so any depth | — |
| `/docs/` | `docs/deep/x.md` | `a/docs/x.md` — anchored |
| `docs/*` | `docs/x.md` | `docs/deep/x.md` — a wildcard tail does not recurse |
| `docs/*.md` | `docs/x.md` | `docs/x.md/child` — likewise |
| `apps/**/test` | `apps/test`, `apps/x/y/test` | — `**/` matches zero directories too |
| `foo**bar` | `fooZbar` | `foo/z/bar` — `**` is recursive only as a whole segment |

`*` stays inside one segment. A trailing `/` marks a directory and does not count as "contains a
slash" for anchoring.

**A line with a malformed owner token is skipped entirely.** Dropping the bad token and keeping the
rule would turn it into an ownership reset, silently erasing a valid earlier rule — a failure that
reads as "these files are unowned" rather than as an error.

## Do not parse it by hand

`scripts/codeowners_map.py` implements all of the above in stdlib Python. A model reasoning over 573
rules will be right most of the time, and the times it is wrong are silent.

```bash
gh api --paginate "repos/<o>/<r>/pulls/<n>/files?per_page=100" --jq '.[].filename' \
  | python3 scripts/codeowners_map.py --codeowners CODEOWNERS.base --expect-files <changedFiles> --json
```

It reports `requested_reviewers` (who GitHub will ask) and `minimum_approvals` (who actually has to
act). Optimise the second. The cover is a greedy approximation to a minimum hitting set, so treat it
as an upper bound on the true minimum.

Getting `CODEOWNERS.base` and the file list right is its own problem — see
`references/fetching-pr-data.md`.
