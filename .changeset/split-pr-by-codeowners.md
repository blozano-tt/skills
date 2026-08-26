---
"tt-review-skills": minor
---

Add `tt-split-pr-by-codeowners` to the `common` bucket: a user-invoked skill that maps a PR's
changed files to the CODEOWNERS groups required to approve them and proposes a split minimising
groups per PR, rather than diff size. Plans and emits only — the execution recipe is documented for
a human to run. Ships a stdlib CODEOWNERS matcher implementing last-match-wins and empty-owner
resets, validated against tt-metal's ~573-rule file.
