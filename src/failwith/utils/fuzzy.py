"""
Fuzzy matching utilities using only stdlib (difflib).
"""

from __future__ import annotations

import difflib
from typing import List, Optional, Sequence


def closest_match(target: str, candidates: Sequence[str], cutoff: float = 0.6) -> Optional[str]:
    """
    Find the closest match to `target` in `candidates`.

    Returns None if no match is above the cutoff threshold.
    """
    matches = difflib.get_close_matches(target, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def closest_matches(
    target: str, candidates: Sequence[str], n: int = 5, cutoff: float = 0.4
) -> List[str]:
    """Find up to `n` close matches, sorted by similarity."""
    return difflib.get_close_matches(target, candidates, n=n, cutoff=cutoff)


def edit_distance(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein edit distance between two strings.
    """
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]
