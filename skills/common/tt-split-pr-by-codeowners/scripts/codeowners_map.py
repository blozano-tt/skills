#!/usr/bin/env python3
"""Map changed files to the CODEOWNERS groups that must approve them.

    git diff --name-only origin/main... | codeowners_map.py --codeowners .github/CODEOWNERS
    codeowners_map.py --files-from changed.txt --json

Reads newline-separated repository-relative paths on stdin (or `--files-from`)
and reports, per file, the owner set GitHub would require -- then clusters the
files by that owner set, which is the unit a split proposal is built from.

Why a parser rather than asking the model to read CODEOWNERS: tt-metal's file
is ~573 active rules, and the two semantics that matter are both easy to get
wrong by eye and invisible when wrong.

  1. LAST match wins. Not the first, and never the union. A file matched by
     six rules is owned by the sixth alone. Unioning inflates the group count
     and produces "splits" that reduce nothing.
  2. A rule with a pattern and NO owners resets ownership to nobody. tt-metal
     uses this deliberately (`.github/deprecations.json`).

Pattern syntax is the gitignore subset GitHub documents for CODEOWNERS:

  * `*` matches within one path segment; `**` crosses segments.
  * A pattern containing no `/` (trailing slash aside) matches at any depth:
    `docs/` matches `a/b/docs/x`. Any other pattern is anchored at the root.
  * A trailing `/` marks a directory and matches everything beneath it.
  * A pattern whose final segment ends in a `*` wildcard does NOT recurse:
    `/*` is root-level entries only, per GitHub's documented example. A final
    segment with no wildcard may name a directory, so it does recurse.

CODEOWNERS has no negation, so there is no `!` handling to get wrong.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict

OWNER = re.compile(r"^(?:@[\w.-]+(?:/[\w.-]+)?|[^@\s]+@[^@\s]+\.[^@\s]+)$")


def _translate(glob: str) -> str:
    """Translate one CODEOWNERS glob body into a regex body."""
    out: list[str] = []
    i, n = 0, len(glob)
    while i < n:
        char = glob[i]
        if char == "*":
            j = i
            while j < n and glob[j] == "*":
                j += 1
            if j - i >= 2:  # ** -- crosses segments
                if j < n and glob[j] == "/":
                    out.append("(?:.*/)?")
                    i = j + 1
                    continue
                out.append(".*")
            else:
                out.append("[^/]*")
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
    # A trailing slash does not make a pattern anchored; an interior one does.
    anchored = pattern.startswith("/") or "/" in pattern.rstrip("/")
    prefix = "" if anchored else "(?:.*/)?"
    body = _translate(core)
    if directory_only:
        suffix = "/.*"
    elif core.split("/")[-1].endswith("*"):
        suffix = ""  # `/*` and `docs/*` stop at that level
    else:
        suffix = "(?:/.*)?"  # the final segment may name a directory
    return re.compile(f"^{prefix}{body}{suffix}$")


def parse(text: str) -> list[tuple[str, re.Pattern[str], tuple[str, ...]]]:
    """Parse CODEOWNERS into (pattern, regex, owners) in file order."""
    rules = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern, *rest = line.split()
        owners = tuple(token for token in rest if OWNER.match(token))
        if len(owners) != len(rest):
            print(
                f"warning: ignoring unparseable owner token(s) in {raw.strip()!r}",
                file=sys.stderr,
            )
        rules.append((pattern, compile_pattern(pattern), owners))
    return rules


def owners_for(path: str, rules) -> tuple[str, tuple[str, ...]]:
    """Return the (pattern, owners) of the LAST rule matching path."""
    match: tuple[str, tuple[str, ...]] = ("", ())
    for pattern, regex, owners in rules:
        if regex.match(path):
            match = (pattern, owners)
    return match


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codeowners", default=".github/CODEOWNERS")
    ap.add_argument("--files-from", help="file of paths; default is stdin")
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
        paths = [line.strip() for line in source if line.strip()]
    if not paths:
        print("error: no paths given", file=sys.stderr)
        return 2

    per_file = {path: owners_for(path, rules) for path in paths}
    clusters: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for path, (_pattern, owners) in per_file.items():
        clusters[owners].append(path)
    every_group = sorted({owner for _p, owners in per_file.values() for owner in owners})

    if args.json:
        json.dump(
            {
                "rules": len(rules),
                "files": len(paths),
                "distinct_groups": len(every_group),
                "groups": every_group,
                "per_file": {
                    path: {"matched_pattern": pattern, "owners": list(owners)}
                    for path, (pattern, owners) in sorted(per_file.items())
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

    print(f"{len(paths)} files, {len(every_group)} distinct owner groups\n")
    for owners, files in sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        label = " ".join(owners) if owners else "(unowned)"
        print(f"{len(files):>4}  {label}")
        for path in sorted(files)[:8]:
            print(f"        {path}")
        if len(files) > 8:
            print(f"        ... and {len(files) - 8} more")
        print()
    print("Required approvals across the whole PR:")
    for owner in every_group:
        print(f"  {owner}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
