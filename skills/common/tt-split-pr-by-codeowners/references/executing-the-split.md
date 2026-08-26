# Executing an approved plan

**This skill does not do any of this.** It emits a plan and stops. Skills in this catalogue are
read-only: they can be pinned into a review workflow, and a workflow agent that moves branches
around or opens pull requests is a bug rather than a feature. What follows is for the person
carrying the plan out, recorded here because the mechanics are where people lose time.

## One branch per proposed PR, each based on the last

```bash
git fetch origin
git switch -c split/1-api origin/main
git diff origin/main...<work-branch> -- <paths assigned to PR 1> | git apply
git add -A && git commit -m "<what PR 1 does>"
git push -u origin split/1-api

git switch -c split/2-callsites split/1-api
git diff origin/main...<work-branch> -- <paths assigned to PR 2> | git apply
git add -A && git commit -m "<what PR 2 does>"
git push -u origin split/2-callsites
```

Open PR 1 against the default branch and PR 2 against `split/1-api`, both as drafts until the plan
has survived contact with a reviewer.

**Use three dots, not two.** `origin/main...<work-branch>` diffs from the merge base, so commits that
landed on the default branch after the work started stay out of the extracted patch. Two dots drags
them in, and the result is a PR containing other people's changes.

**Squash each slice into one commit** rather than cherry-picking the original ones. The original
history interleaves across the boundaries the plan just drew, so replaying it means untangling that
interleaving once per slice — the same work the plan already did, done again by hand and worse.

**Verify each branch builds before opening anything.** The plan asserts every slice stands alone;
that assertion is worth exactly as much as the check behind it. A slice missing a symbol its
sibling defines is the failure mode the whole exercise exists to avoid.

## Keeping the stack alive

Every time the default branch moves, rebase the stack from the bottom up and re-push in order. This
is the standing cost of a split and the reason the plan has to quantify it up front.

As each PR merges, the one above it needs its base moved to the default branch. Hosts usually do
this automatically when the base branch is deleted on merge — check that it happened rather than
assuming. Merging a PR whose base still points at an unmerged sibling lands the squash on that
sibling instead of where it was meant to go, and the result is awkward to unpick.

## Where you cannot push a branch

Some repositories only accept contributions from forks, and a pull request's base has to be a branch
on the receiving repository. There is nothing to stack onto, so the sequence above does not apply:
every PR opens against the default branch and the dependencies live in prose and merge order rather
than in the branch graph.

Establish which situation you are in before promising an order, because it changes what the plan can
deliver.

## Replacing the original pull request

If the split supersedes the original PR rather than sitting beside it, ask before force-pushing to
its branch. Someone may already be reading it, and rewriting those commits detaches every review
comment anchored to them.

## When the work is not yours

Splitting somebody else's pull request is bookkeeping performed on their work. Each resulting PR
should name them and link the PR it came from, in the description, without being asked.
