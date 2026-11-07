"""Evidence classification.

These are evidence classes, NOT probabilities of engineering success.
A study without a PMID/DOI reference is ignored: every finding must be traceable.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

EvidenceLevel = Literal["strong", "moderate", "limited"]
LEVELS: tuple[EvidenceLevel, ...] = ("strong", "moderate", "limited")


@dataclass(frozen=True)
class Study:
    reference: str  # PMID or DOI
    experimental: bool  # True = functionally/experimentally characterised, False = computational


def classify_evidence(studies: Iterable[Study]) -> EvidenceLevel:
    """Classify a body of studies.

    - strong:   at least 2 distinct references, at least one experimental
    - moderate: 1 experimental reference, or 2+ computational references
    - limited:  anything else (including no traceable references)
    """
    by_ref: dict[str, bool] = {}
    for study in studies:
        ref = (study.reference or "").strip()
        if not ref:
            continue
        by_ref[ref] = by_ref.get(ref, False) or study.experimental

    total = len(by_ref)
    experimental = sum(by_ref.values())

    if total >= 2 and experimental >= 1:
        return "strong"
    if experimental >= 1 or total >= 2:
        return "moderate"
    return "limited"
