# Getting the inputs right

Three ways to compute a confidently wrong answer before any ownership logic runs.

## The base branch is not `main`

GitHub resolves ownership, branch protection and rulesets against the PR's **base** branch. A PR may
target a release or feature branch — a real example, tt-metal#54493, targets `sadesoye/H3_attention`.
Every downstream step keys off it.

```bash
BASE=$(gh pr view <n> --repo <o>/<r> --json baseRefName --jq .baseRefName)
```

## CODEOWNERS lives in one of three places, on that branch

GitHub takes the **first found** of `.github/CODEOWNERS`, `CODEOWNERS`, `docs/CODEOWNERS`. Reading
your working tree's copy is wrong whenever the base is not your checkout, and picking the wrong
location silently maps against rules that are not in force.

```bash
for p in .github/CODEOWNERS CODEOWNERS docs/CODEOWNERS; do
  gh api "repos/<o>/<r>/contents/$p?ref=$BASE" --jq '.content' 2>/dev/null \
    | base64 -d > CODEOWNERS.base && [ -s CODEOWNERS.base ] && echo "using $p" && break
done
```

If the PR edits CODEOWNERS itself, the base copy still governs it.

## The file list truncates at 100, silently

`gh pr view --json files` builds a `files(first: 100)` query and does not paginate. Verified: a
174-file PR returns exactly 100 rows, with no error and no indication anything is missing. Large PRs
are this skill's entire target, so the failure lands precisely where it does most damage — every
owner count downstream is quietly short.

```bash
gh api --paginate "repos/<o>/<r>/pulls/<n>/files?per_page=100" --jq '.[].filename'
```

Pass `--expect-files "$(gh pr view <n> --repo <o>/<r> --json changedFiles --jq .changedFiles)"` so
the matcher aborts on a short list rather than under-counting. The REST endpoint itself stops at
3000 files; past that, say so in the output rather than pretending to a full picture.

## Cross-check against reviewRequests — but do not call it validation

```bash
gh pr view <n> --repo <o>/<r> --json reviewRequests \
  --jq '[.reviewRequests[].name // .reviewRequests[].login] | sort'
```

A smell test, and **proof of nothing in either direction**:

- The API returns a bare team name or user login; the matcher emits `@org/team`, `@user` or an
  email address. Normalise both sides or every row looks like a mismatch.
- **Extra computed** names are usually benign — GitHub never asks the PR author to review, skips
  owners without write access, and drops anyone who already approved. Parser over-matching looks
  identical from here.
- **Extra requested** names do not prove a missed rule: a human can request any reviewer by hand,
  code owner or not.

Account for each difference individually. If one is unexplained, report the parse as **unverified**
and name what is unaccounted for. Never infer correctness from which set is larger.

## Confirm code-owner review is enforced at all

Worth doing once per base branch, and the obvious check gives the wrong answer. Classic branch
protection and rulesets are separate mechanisms; a repo may use either or both.

```bash
gh api "repos/<o>/<r>/branches/$BASE/protection" \
  --jq '.required_pull_request_reviews.require_code_owner_reviews'
gh api "repos/<o>/<r>/rules/branches/$BASE" \
  --jq '[.[] | select(.type=="pull_request") | .parameters.require_code_owner_review]'
```

On tt-metal's `main` the first returns `false` and the second returns `[false, true]` — two
overlapping rulesets, which GitHub composes by taking the **most restrictive**. Code-owner review is
required. Reading only the first says the opposite, and would make this skill look pointless on the
repo it matters most for.
