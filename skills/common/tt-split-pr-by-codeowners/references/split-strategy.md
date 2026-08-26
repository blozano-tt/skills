# Choosing the split

## The objective, and why it is this one

Minimise the number of CODEOWNERS groups **each resulting PR** requires. Not diff size.

Size is a bad proxy for review cost. What makes a PR expensive is the number of independent
decisions a reviewer holds at once, which does not track line count: a 5,000-file mechanical rename
is one decision, while a 300-line diff that changes an API, adds a cache and fixes an unrelated bug
is three. Thresholding on lines flags the first and misses the second.

Reviewer-group count is better: computable, and each group is a human whose approval blocks the
merge. Reducing it cuts latency directly. It is still no guarantee of *coherence*, which is why the
rejection rules below exist.

## Clustering

1. Compute the owner set per file (`scripts/codeowners_map.py`). Files sharing an owner set are the
   natural grain — the script emits these clusters directly, largest first.
2. The largest cluster is usually PR 1.
3. Merge a small cluster into a larger one when it adds no *new* group — a file owned by
   `{A}` costs nothing in a PR that already requires `{A, B}`. Unowned files are free anywhere.
4. Every remaining cluster that would add a group to PR 1 is a candidate for its own PR.
5. Stop when the next split saves no group. Two PRs requiring the same two groups are strictly
   worse than one.

## Rules that override the objective

**A behaviour change and its test belong in the same slice.** Never separate them to shed a group.
Correctness is not reviewable in a PR whose evidence landed somewhere else.

**A split that separates a change from its reason is rejected**, even when it reduces group count.
This is the failure mode of optimising on ownership: file ownership cuts across concerns, so it is
possible to produce a PR that touches exactly one group and means nothing on its own. Each PR must
be reviewable as one idea, not merely mergeable.

**Every slice compiles and passes on its own.** Where a later slice consumes something an earlier
one renames, whatever keeps the old spelling working — alias, re-export, deprecation wrapper —
belongs in the *earlier* slice, and the dependency gets stated in both. Dependencies fix merge
order, so an unstated one is a broken build waiting for someone to merge out of sequence.

**Ask on a file that straddles two clusters.** One placed wrong pulls a whole extra group in.

## Wide mechanical refactors

The case that looks unsplittable: one mechanical change — rename a symbol, retype a shared
parameter — whose blast radius fans across thousands of call sites. No vertical slice of it lands
green, so the usual advice does not apply.

Sequence it as **expand / migrate / contract**:

1. **Expand.** Add the new form beside the old so nothing breaks. This is the only PR in the
   sequence containing a decision, and it is small — it gets real scrutiny instead of being buried
   in call-site noise.
2. **Migrate.** Move call sites over in batches, each blocked by the expand, each green because the
   old form still exists.
3. **Contract.** Delete the old form once no caller remains, blocked by every migrate batch.

Expand–contract never says how large a migrate batch should be. **CODEOWNERS groups answer that**:
batch by owner set, so each batch is reviewed by exactly the people who own that code and by nobody
else. That is the natural batch boundary, and it falls straight out of the clustering above.

If the API cannot be made backward compatible, say so — and price the alternative rather than
declaring it unsplittable. Making it *temporarily* backward compatible is itself a deliverable, and
it converts "cannot be split" into "can be split, at this cost", which is a decision for a human.

## When to recommend not splitting

A confident **do not split** is a first-class output, not a failure. Say it plainly when:

- the PR already requires one or two groups — there is nothing to win;
- the change is one decision spread across many files, and splitting would produce N PRs that must
  all land together: N review contexts, none independently correct;
- the split would need a shim whose cost exceeds the latency it saves;
- the repo does not enforce code-owner review at all (check both mechanisms — see
  `references/codeowners-semantics.md`).

Always state the price of the split you propose: N× CI, N× review latency, and a rebase chain to
maintain. If that exceeds the saving, recommend against your own proposal.
