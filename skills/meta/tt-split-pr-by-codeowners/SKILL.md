---
name: tt-split-pr-by-codeowners
description: Decide whether a wide-ranging pull request should be broken up so each piece needs fewer CODEOWNERS approvals, and propose how. Use for 'too many reviewers on this', 'can this be broken up', 'why does this need six approvals'.
disable-model-invocation: true
metadata:
  tier: process
  upstream: []
---

# Split a PR by CODEOWNERS approvals

Given a pull request, work out who has to approve it and propose a split where each piece needs
fewer of them. User-invoked, and in `meta/` because it needs an authenticated `gh`: per
[ADR-0002](../../../.agents/adr/0002-self-containment.md) a skill on the review path may not depend
on external tooling, so this one is never pinned by a review workflow.

**It plans. It does not execute.** It emits a proposal and stops — no branches, no pushes, nothing
written to GitHub. `references/executing-the-split.md` records the recipe for whoever carries it out.

## Why approvals and not diff size

A large diff is not automatically a hard review. What costs a reviewer is the number of independent
decisions held at once, which does not track line count — a 5,000-file mechanical rename is one
decision. Thresholding on size flags exactly the PRs that do not need splitting.

Blocking approvals are computable, and each one is a person who must act before the PR can land.
On tt-metal this is not theoretical: `.github/CODEOWNERS` is ~573 active rules across ~160 owners.

**Count approvals, not owners.** Owners on a single CODEOWNERS rule are *alternatives* — GitHub
requires "an approval from any of the owners", not all of them. A PR matching 36 owners can be
unblocked by 7 approvals, and splitting on the larger number proposes work that buys nothing.
`scripts/codeowners_map.py` reports both, and takes the branch's own `required_approving_review_count`
as a floor: coverage is not the only gate.

## Constraints

Lead with these when asked a split-planning question; they decide most cases before any analysis.

- Every slice must **stand on its own twice over**: green when merged alone, and coherent as a
  single idea to whoever reads it. A lower approval count never buys an incoherent PR.
- **A behaviour change ships with its test.** Never separate them to shed a reviewer.
- When a later slice consumes something an earlier one renames, whatever keeps the old spelling
  working belongs in the **earlier** slice, and the dependency is stated in both.
- **Recommending no split is a valid, expected outcome.** Say it plainly when the PR is one decision,
  or when its owner sets overlap enough that a couple of approvals already cover everything.
- **Price every proposal**: N× CI, N× review latency, a rebase chain. Recommend against your own
  split when the cost exceeds the saving.
- Splitting is cheapest before the code is written. On an open PR the work already exists, so the
  bar for proposing one is higher than it would be at planning time.

## Workflow

### 1. Gather, keyed off the base branch

```bash
gh pr view <n> --repo <owner>/<repo> --json baseRefName,changedFiles,title,author,reviewRequests
```

**Everything downstream keys off `baseRefName`** — ownership, protection and merge base all resolve
against the PR's base, which is often not `main`.

### 2. Fetch inputs without truncating them

`gh pr view --json files` silently caps at 100 files, and this skill's whole target is PRs larger
than that. Paginate, and fetch CODEOWNERS from the base branch by GitHub's location precedence.
`references/fetching-pr-data.md` has the commands and the two other ways to get this wrong.

### 3. Resolve ownership

```bash
<paginated file list> | python3 scripts/codeowners_map.py \
  --codeowners CODEOWNERS.base --expect-files <n> --required-approvals <count> --json
```

Do not read CODEOWNERS by eye. Last-match-wins, owner alternatives and empty-owner resets are all
silent when got wrong — see `references/codeowners-semantics.md`.

### 4. Sanity-check, do not "validate"

Compare against `reviewRequests` as a smell test only; it proves nothing in either direction.
Account for every difference or call the parse unverified.

### 5. Propose, then stop

Cluster by owner set, merge clusters that add no new approver, and stop once the next split saves
nothing. Wide mechanical refactors take the expand / migrate / contract sequence, with migrate
batches cut along owner-set boundaries. Strategy and the rules that override the objective are in
`references/split-strategy.md`. Output the proposal and hand it over; create nothing.

## Output

```
## Current

<n> files on base <branch>. <m> owners matched, but <a> approvals would unblock it: <who>.
<If the branch floor binds: "the branch requires <k> regardless, so the real number is <k>.">
Cross-checked against reviewRequests: <agrees | differs, because ...>

## Proposed

### PR 1 — <what it does, as one idea>
Approvals: <who>       (was <a>, now 1)
Files:     <paths, or a pattern plus a count>
Depends on: —

### PR 2 — <...>
Depends on: PR 1 — <the symbol or shim that creates the dependency>

## Cost

<N>x CI, <N> review cycles, a <N>-deep rebase chain.

## Recommendation

<Split, or do not split, and why — in one sentence.>
```

## When this does not apply

Say so and stop: a couple of approvals already cover every file; the change is one decision spread
wide, so splitting yields N PRs that must all land together; the base branch does not enforce
code-owner review; or no split reduces the approval count, because ownership does not align with a
seam here.
