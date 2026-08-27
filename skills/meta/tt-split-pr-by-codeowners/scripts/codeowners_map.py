#!/usr/bin/env python3
"""Map changed files to the CODEOWNERS owners that can approve them.

    gh api --paginate repos/<o>/<r>/pulls/<n>/files --jq '.[].filename' \
      | codeowners_map.py --codeowners CODEOWNERS.base --json

Reads newline-separated repository-relative paths on stdin (or `--files-from`),
reports the owner set GitHub would apply to each, clusters files by that set,
and computes how few approvals could actually unblock the whole list.

Three semantics decide every answer here. All are easy to get wrong by eye, and
a wrong answer looks exactly like a right one.

  1. LAST match wins -- not the first, and never the union across rules. A file
     matched by six rules is owned by the sixth alone.
  2. Owners on ONE rule are ALTERNATIVES. GitHub: "an approval from any of the
     owners is sufficient to meet this requirement." So a rule's owner list is
     a set of substitutes, not a list of required approvers, and the number of
     approvals a PR needs is a set-cover over rules -- not the size of the
     union. Files owned by {A,B} and {A,C} are unblocked by A alone.
  3. A rule with a pattern and NO owners resets ownership to nobody. Used
     deliberately in the wild to carve exceptions out of a broader rule.

Pattern syntax is the gitignore subset GitHub documents for CODEOWNERS. There
is no negation, so there is no `!` handling to get wrong.

  * `*` matches within one path segment.
  * `**` is recursive only as a COMPLETE segment -- `**/`, `/**`, `/**/`. In any
    other position (`foo**bar`) consecutive stars collapse to a single `*`.
  * A pattern with no `/` (trailing slash aside) matches at any depth; any other
    pattern is anchored at the root.
  * A trailing `/` marks a directory and matches everything beneath it.
  * A final segment containing a wildcard does NOT match descendants: `/*` is
    root-level entries only, and `docs/*.md` does not match `docs/x.md/y`. A
    final segment with no wildcard may name a directory, so it does recurse.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

OWNER = re.compile(r"^(?:@[\w.-]+(?:/[\w.-]+)?|[^@\s]+@[^@\s]+\.[^@\s]+)$")


def _translate(glob: str) -> str:
    """Translate a CODEOWNERS glob body into a regex body."""
    out: list[str] = []
    i, n = 0, len(glob)
    while i < n:
        char = glob[i]
        if char == "*":
            j = i
            while j < n and glob[j] == "*":
                j += 1
            whole_segment = (i == 0 or glob[i - 1] == "/") and (j == n or glob[j] == "/")
            if j - i >= 2 and whole_segment:
                if j < n:  # '**/' -- zero or more directories
                    out.append("(?:.*/)?")
                    i = j + 1
                    continue
                out.append(".*")  # trailing '**'
            else:
                out.append("[^/]*")  # ordinary wildcard, incl. 'foo**bar'
            i = j
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    return "".join(out)


def compile_pattern(pattern: str) -> re.Pattern[str]:
    directory_only = pattern.endswith("/")
    core = pattern.strip("/")
    # A trailing slash does not anchor a pattern; an interior one does.
    anchored = pattern.startswith("/") or "/" in pattern.rstrip("/")
    prefix = "" if anchored else "(?:.*/)?"
    last = core.split("/")[-1]
    if directory_only:
        suffix = "/.*"
    elif "*" in last or "?" in last:
        suffix = ""  # a wildcard tail stops at that level
    else:
        suffix = "(?:/.*)?"  # the final segment may name a directory
    return re.compile(f"^{prefix}{_translate(core)}{suffix}$")


def parse(text: str) -> list[tuple[str, re.Pattern[str], tuple[str, ...]]]:
    """Parse CODEOWNERS into (pattern, regex, owners) in file order."""
    rules = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern, *rest = line.split()
        owners = tuple(token for token in rest if OWNER.match(token))
        if len(owners) != len(rest):
            # GitHub skips a syntactically invalid line entirely. Keeping the
            # rule with its bad tokens dropped would turn it into an
            # empty-owner reset and silently erase a valid earlier rule.
            bad = [t for t in rest if not OWNER.match(t)]
            print(f"warning: line {lineno}: skipping rule, bad owner(s) {bad}", file=sys.stderr)
            continue
        rules.append((pattern, compile_pattern(pattern), tuple(sorted(set(owners)))))
    return rules


def owners_for(path: str, rules) -> tuple[str, tuple[str, ...]]:
    """Return the (pattern, owners) of the LAST rule matching path."""
    match: tuple[str, tuple[str, ...]] = ("", ())
    for pattern, regex, owners in rules:
        if regex.match(path):
            match = (pattern, owners)
    return match


def _greedy(groups: set[frozenset[str]]) -> list[str]:
    remaining, chosen = set(groups), []
    while remaining:
        counts: dict[str, int] = defaultdict(int)
        for group in remaining:
            for owner in group:
                counts[owner] += 1
        # Break count ties by name so the result is deterministic.
        best = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        chosen.append(best)
        remaining = {g for g in remaining if best not in g}
    return chosen


def minimum_cover(
    owner_sets: list[tuple[str, ...]], node_budget: int = 200_000
) -> tuple[list[str], bool]:
    """Smallest set of approvers hitting every owned rule, and whether it is exact.

    Each rule's owners are alternatives, so one member unblocks that rule and the
    fewest approvals is a minimum hitting set. That is NP-hard in general, but
    branching on the *smallest* uncovered rule and pruning against the best
    answer so far settles real inputs immediately -- a 174-file tt-metal PR with
    12 distinct owner sets proves optimality in 14 nodes. Greedy seeds the bound.

    Returns (cover, exact). `exact` is False only if the node budget ran out, in
    which case the cover is a valid upper bound rather than a proven minimum.
    """
    groups = {frozenset(s) for s in owner_sets if s}
    if not groups:
        return [], True
    best = sorted(_greedy(groups))
    state = {"nodes": 0, "exact": True}

    def search(remaining: set[frozenset[str]], chosen: list[str]) -> None:
        nonlocal best
        if not remaining:
            if len(chosen) < len(best):
                best = sorted(chosen)
            return
        if len(chosen) + 1 >= len(best):
            return  # cannot beat the incumbent
        state["nodes"] += 1
        if state["nodes"] > node_budget:
            state["exact"] = False
            return
        target = min(remaining, key=lambda g: (len(g), sorted(g)))
        for owner in sorted(target):
            search({g for g in remaining if owner not in g}, chosen + [owner])

    search(groups, [])
    return best, state["exact"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codeowners", default="CODEOWNERS",
                    help="CODEOWNERS file from the PR's BASE branch")
    ap.add_argument("--files-from", help="file of paths; default is stdin")
    ap.add_argument("--expect-files", type=int,
                    help="changed_files from the API; errors if the input is short")
    ap.add_argument("--required-approvals", type=int, default=0,
                    help="required_approving_review_count on the base branch; the "
                         "cover cannot go below this floor")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.codeowners, encoding="utf-8") as handle:
            rules = parse(handle.read())
    except OSError as exc:
        print(f"error: cannot read {args.codeowners}: {exc}", file=sys.stderr)
        return 2
    if not rules:
        # An empty file is what a swallowed fetch failure looks like. Left
        # unchecked it reports every path as unowned -- "no approvals needed" --
        # which is the confidently wrong answer this tool exists to prevent.
        print(
            f"error: {args.codeowners} yielded no usable rules. Refusing, because "
            "an empty CODEOWNERS makes every file look unowned.",
            file=sys.stderr,
        )
        return 2

    source = open(args.files_from, encoding="utf-8") if args.files_from else sys.stdin
    with source:
        paths = sorted({line.strip() for line in source if line.strip()})
    if not paths:
        print("error: no paths given", file=sys.stderr)
        return 2
    if args.expect_files is not None and len(paths) != args.expect_files:
        print(
            f"error: got {len(paths)} paths but the PR changed {args.expect_files} files. "
            "A truncated file list undercounts owners; paginate the fetch.",
            file=sys.stderr,
        )
        return 2

    per_file = {path: owners_for(path, rules) for path in paths}
    clusters: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for path, (_pattern, owners) in per_file.items():
        clusters[owners].append(path)
    matched = sorted({o for _p, owners in per_file.values() for o in owners})
    cover, exact = minimum_cover(list(clusters))
    # Code-owner coverage is not the only gate: the branch may also demand a
    # fixed number of approvals, and a one-owner cover cannot satisfy a floor
    # of two. The real cost is whichever binds harder.
    approvals = max(len(cover), args.required_approvals)

    if args.json:
        json.dump(
            {
                "rules": len(rules),
                "files": len(paths),
                "matched_owners": matched,
                "matched_owner_count": len(matched),
                "approval_cover": cover,
                "cover_is_exact": exact,
                "required_approvals_floor": args.required_approvals,
                "approvals_needed": approvals,
                "per_file": {
                    p: {"matched_pattern": pat, "owners": list(o)}
                    for p, (pat, o) in sorted(per_file.items())
                },
                "clusters": [
                    {"owners": list(owners), "files": sorted(files)}
                    for owners, files in sorted(
                        clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])
                    )
                ],
            },
            sys.stdout,
            indent=2,
        )
        print()
        return 0

    print(f"{len(paths)} files, {len(clusters)} distinct owner sets\n")
    for owners, files in sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        label = " or ".join(owners) if owners else "(unowned -- free to place anywhere)"
        print(f"{len(files):>4}  {label}")
        for path in sorted(files)[:8]:
            print(f"        {path}")
        if len(files) > 8:
            print(f"        ... and {len(files) - 8} more")
        print()
    print(f"Owners matched across the diff ({len(matched)}) -- GitHub will request a")
    print("subset of these, dropping the author and anyone without write access:")
    for owner in matched:
        print(f"  {owner}")
    qualifier = "proven minimum" if exact else "upper bound, search truncated"
    print(f"\nApprovals that would unblock it ({len(cover)}, {qualifier}):")
    for owner in cover:
        print(f"  {owner}")
    if args.required_approvals > len(cover):
        print(f"\nBase branch requires {args.required_approvals} approvals regardless,")
        print(f"so the real floor is {approvals}, not {len(cover)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
