---
name: tt-split-pr-by-codeowners
description: Decide whether a wide-ranging pull request should be broken up so each piece needs fewer CODEOWNERS approvals, and propose how. Use for 'too many reviewers on this', 'can this be broken up', 'why does this need six approvals'.
disable-model-invocation: true
metadata:
  tier: process
  upstream: []
---

# Split a PR by CODEOWNERS groups

Given a pull request, work out which CODEOWNERS groups its files pull in, and propose a split where
each resulting PR needs as few of those groups as possible. User-invoked: a human asks for this
about a specific PR.

**This skill plans. It does not execute.** It emits a proposal and stops — no branches, no pushes,
nothing written to GitHub. `references/executing-the-split.md` records the recipe for whoever
carries it out.

## Why reviewer groups and not diff size

A large diff is not automatically a hard review. What costs a reviewer is the number of independent
decisions held at once, and that does not track line count — a 5,000-file mechanical rename is one
decision. Thresholding on size flags exactly the PRs that do not need splitting.

Reviewer-group count is computable, and every group is a person whose approval blocks the merge.
Reducing it cuts merge latency directly. On tt-metal this is not theoretical: `.github/CODEOWNERS`
is ~573 active rules across ~160 distinct owners, and a diff that wanders across buckets collects
approvers fast.

## Constraints

Lead with these when asked a split-planning question; they decide most cases before any analysis.

- Every slice must **stand on its own twice over**: green when merged alone, and coherent as a
  single idea to whoever reads it. A lower group count never buys an incoherent PR.
- **A behaviour change ships with its test.** Never separate them to shed a reviewer group.
- When a later slice consumes something an earlier one renames, whatever keeps the old spelling
  working belongs in the **earlier** slice, and the dependency is stated in both.
- **Recommending no split is a valid, expected outcome.** Say it plainly when the PR is one decision
  or already needs one or two groups.
- **Price every proposal**: N× CI, N× review latency, a rebase chain. Recommend against your own
  split when the cost exceeds the saving.
- Splitting is cheapest before the code is written. On an open PR the work already exists, so the
  bar for proposing a split is higher than it would be at planning time.

## Workflow

### 1. Gather

```bash
gh pr view <n> --repo <owner>/<repo> --json title,body,author,headRefName,files,reviewRequests
```

Confirm code-owner review is actually enforced — it is checked in two separate places and the
obvious one gives the wrong answer on tt-metal. See `references/codeowners-semantics.md`.

### 2. Compute ownership

Do not read CODEOWNERS by eye. Last-match-wins and empty-owner resets are both silent when got
wrong, and this file is hundreds of rules long.

```bash
gh pr view <n> --repo <owner>/<repo> --json files --jq '.files[].path' \
  | python3 scripts/codeowners_map.py --codeowners .github/CODEOWNERS --json
```

### 3. Validate the parse

Compare the computed group set against `reviewRequests` from step 1. Computed ⊇ requested is
expected — GitHub drops the PR author and any owner lacking write access. **Computed ⊂ requested
means the parse is wrong**: stop, report it, propose nothing.

### 4. Propose

Cluster by owner set, merge clusters that add no new group, and stop splitting once the next split
saves nothing. Wide mechanical refactors take the expand / migrate / contract sequence instead, with
migrate batches cut along owner-set boundaries. Full strategy, and the rules that override the
objective, in `references/split-strategy.md`.

### 5. Stop

Output the proposal and hand it over. Do not create anything.

## Output

```
## Current

<n> files, <k> reviewer groups: <group>, <group>, ...
Parse validated against reviewRequests: <agrees | differs, because ...>

## Proposed

### PR 1 — <what it does, as one idea>
Groups: <group>            (was <k>, now 1)
Files:  <paths, or a pattern plus a count>
Depends on: —

### PR 2 — <...>
Groups: <group>
Files:  <...>
Depends on: PR 1 — <the symbol or shim that creates the dependency>

## Cost

<N>x CI, <N> review cycles, a <N>-deep rebase chain.

## Recommendation

<Split, or do not split, and why — in one sentence.>
```

## When this does not apply

Say so and stop:

- the PR needs one or two groups already;
- the change is one decision spread wide, and splitting yields N PRs that must all land together;
- the repo does not enforce code-owner review;
- no split reduces any group count — file ownership does not always align with a seam.
