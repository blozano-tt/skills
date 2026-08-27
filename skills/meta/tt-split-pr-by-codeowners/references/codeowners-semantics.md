# How ownership actually resolves

Three rules decide every answer this skill gives. All are easy to get wrong by eye, and a wrong
answer looks exactly like a right one.

**Last match wins.** Not the first, and never the union across rules. tt-metal's file opens with
`/* @tenstorrent/metalium-developers-infra` and narrows over ~573 further rules. A file matched by
six rules is owned by the sixth *alone*.

**Owners on one rule are alternatives.** GitHub: *"an approval from any of the owners is sufficient
to meet this requirement."* A rule's owners are substitutes, so the approvals a PR needs is a
**cover** over its rules, not the size of the union — `{A,B}` and `{A,C}` are unblocked by A alone.
The union overstates cost, sometimes badly: a real 174-file tt-metal PR matches 36 owners and is
unblocked by 7 approvals. Splitting on 36 buys nothing.

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
rules is right most of the time, and the times it is wrong are silent.

It reports `matched_owners` (everyone the rules name, before GitHub filters out the author and
anyone without write access) and `approval_cover` (who must actually act). Optimise the second. The
cover is an exact minimum hitting set proved by branch and bound; `cover_is_exact` goes `false` only
if the search budget runs out, leaving an upper bound. `approvals_needed` is
`max(cover, --required-approvals)`, since the branch's required-approval count is a floor.

Feeding it the right inputs is its own problem — see `references/fetching-pr-data.md`.

## Confirm code-owner review is enforced at all

Worth doing once per base branch, and the obvious check answers wrongly: classic branch protection
and rulesets are separate mechanisms, and a repo may use either or both.

```bash
gh api "repos/<o>/<r>/branches/$BASE/protection" \
  --jq '{owner: .required_pull_request_reviews.require_code_owner_reviews,
         count: .required_pull_request_reviews.required_approving_review_count}'
gh api "repos/<o>/<r>/rules/branches/$BASE" \
  --jq '[.[] | select(.type=="pull_request") | .parameters]
        | {owner: map(.require_code_owner_review) | any,
           count: map(.required_approving_review_count) | max}'
```

On tt-metal's `main` the first says `false` for code-owner review and the second says
`[false, true]` — two overlapping rulesets, which GitHub composes **most restrictive**. It is
required. Reading only the first says the opposite, and would make this skill look pointless on the
repo it matters most for.

**Take `required_approving_review_count` too and pass it as `--required-approvals`.** Coverage is
not the only gate: if the branch demands two approvals, a slice with a one-owner cover still needs
two, so the honest number is `max(cover, required_count)` — and N slices multiply that floor N
times. Ignoring it understates the current cost and the proposal's.
