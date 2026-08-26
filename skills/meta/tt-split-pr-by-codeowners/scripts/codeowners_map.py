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


def minimum_cover(owner_sets: list[tuple[str, ...]]) -> list[str]:
    """Greedily pick approvers covering every owned rule.

    Each set is a group of alternatives, so one member unblocks it. Choosing the
    fewest approvers is a minimum hitting set -- NP-hard, so this is the standard
    greedy approximation and may occasionally pick one more than strictly needed.
    Treat it as an upper bound on the true minimum, and the union as the number
    of review requests GitHub will actually send.
    """
    remaining = {frozenset(s) for s in owner_sets if s}
    chosen: list[str] = []
    while remaining:
        counts: dict[str, int] = defaultdict(int)
        for group in remaining:
            for owner in group:
                counts[owner] += 1
        # Sort by name after count so the result is deterministic.
        best = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        chosen.append(best)
        remaining = {g for g in remaining if best not in g}
    return sorted(chosen)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codeowners", default="CODEOWNERS",
                    help="CODEOWNERS file from the PR's BASE branch")
    ap.add_argument("--files-from", help="file of paths; default is stdin")
    ap.add_argument("--expect-files", type=int,
                    help="changed_files from the API; errors if the input is short")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.codeowners, encoding="utf-8") as handle:
            rules = parse(handle.read())
    except OSError as exc:
        print(f"error: cannot read {args.codeowners}: {exc}", file=sys.stderr)
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
    requested = sorted({o for _p, owners in per_file.values() for o in owners})
    cover = minimum_cover(list(clusters))

    if args.json:
        json.dump(
            {
                "rules": len(rules),
                "files": len(paths),
                "requested_reviewers": requested,
                "requested_count": len(requested),
                "minimum_approvals": cover,
                "minimum_approval_count": len(cover),
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
    print(f"Review requests GitHub will send ({len(requested)}):")
    for owner in requested:
        print(f"  {owner}")
    print(f"\nApprovals that would actually unblock it ({len(cover)}, greedy upper bound):")
    for owner in cover:
        print(f"  {owner}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
