---
"tt-review-skills": patch
---

Fix `--exclude` silently ignoring a bare login in `tt-split-pr-by-codeowners`. `key()` lowercases a
token only when it starts with `@`, so `halghTT` never matched the `@halghTT` CODEOWNERS spells: the
excluded party stayed in the cover while `excluded_from_cover` still listed them, which reads as
applied. Callers hold the bare form — `gh pr view --json author` yields `halghTT` — so the flag
missed exactly where it was needed, reporting a minimum approval count that cannot occur. `--exclude`
now normalises like `--approved` already did, leaving email principals untouched. Regression tests
added in `tests/test_codeowners_map.py`.
