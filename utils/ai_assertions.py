"""Assertion utilities for non-deterministic and AI-integrated test outputs.

Two modes:
  Hard assertions  — standalone functions; fail immediately on violation.
  Soft assertions  — SoftAssertions context manager; collects every failure
                     and raises one combined AssertionError at block exit.

Use soft assertions when validating multiple aspects of an AI response in a
single test — you get the full failure picture instead of stopping at the first.

Example (soft):
    with SoftAssertions() as soft:
        soft.assert_confidence_above(result["score"], AI_CONFIDENCE_THRESHOLD)
        soft.assert_category_in(result["label"], {"positive", "negative", "edge"})
        soft.assert_text_contains_any(result["summary"], ["error", "warning"])

Example (hard):
    assert_confidence_above(result["score"], AI_CONFIDENCE_THRESHOLD)
    assert_category_in(result["label"], {"positive", "negative"})
"""
from __future__ import annotations

import difflib
from typing import Any, Collection, Iterable

from utils.constants import (
    AI_CONFIDENCE_THRESHOLD,
    AI_RESPONSE_TIMEOUT_S,
    AI_TEXT_SIMILARITY_RATIO,
)


# ── hard assertions ───────────────────────────────────────────────────────────

def assert_confidence_above(
    score: float,
    min_score: float = AI_CONFIDENCE_THRESHOLD,
    label: str = "",
) -> None:
    """Fail if score < min_score. Both values should be in [0.0, 1.0]."""
    tag = f"[{label}] " if label else ""
    assert score >= min_score, (
        f"{tag}confidence {score:.3f} is below minimum {min_score:.3f}"
    )


def assert_confidence_below(
    score: float,
    max_score: float,
    label: str = "",
) -> None:
    """Fail if score > max_score — useful for uncertainty / low-confidence ceilings."""
    tag = f"[{label}] " if label else ""
    assert score <= max_score, (
        f"{tag}confidence {score:.3f} exceeds ceiling {max_score:.3f}"
    )


def assert_category_in(
    value: Any,
    valid: Collection[Any],
    label: str = "",
) -> None:
    """Fail if value is not a member of the valid set."""
    tag = f"[{label}] " if label else ""
    assert value in valid, (
        f"{tag}AI output {value!r} not in expected set {set(valid)!r}"
    )


def assert_text_contains_any(
    text: str,
    keywords: Iterable[str],
    *,
    case_sensitive: bool = False,
    label: str = "",
) -> None:
    """Fail if none of the keywords appear in text."""
    tag = f"[{label}] " if label else ""
    kws = list(keywords)
    haystack = text if case_sensitive else text.lower()
    needles = kws if case_sensitive else [k.lower() for k in kws]
    found = [k for k, n in zip(kws, needles) if n in haystack]
    assert found, (
        f"{tag}text contains none of {kws!r}.\n"
        f"  Text (first 200 chars): {text[:200]!r}"
    )


def assert_text_contains_all(
    text: str,
    keywords: Iterable[str],
    *,
    case_sensitive: bool = False,
    label: str = "",
) -> None:
    """Fail if any keyword is absent from text."""
    tag = f"[{label}] " if label else ""
    kws = list(keywords)
    haystack = text if case_sensitive else text.lower()
    needles = kws if case_sensitive else [k.lower() for k in kws]
    missing = [k for k, n in zip(kws, needles) if n not in haystack]
    assert not missing, (
        f"{tag}text missing required keywords {missing!r}.\n"
        f"  Text (first 200 chars): {text[:200]!r}"
    )


def assert_text_similarity(
    actual: str,
    expected: str,
    min_ratio: float = AI_TEXT_SIMILARITY_RATIO,
    label: str = "",
) -> None:
    """
    Fail if fuzzy similarity between actual and expected is below min_ratio.

    Uses difflib.SequenceMatcher (stdlib) — no extra dependencies.
    Suitable for comparing AI-generated text against a reference without
    requiring an exact match.
    """
    tag = f"[{label}] " if label else ""
    ratio = difflib.SequenceMatcher(None, actual.lower(), expected.lower()).ratio()
    assert ratio >= min_ratio, (
        f"{tag}text similarity {ratio:.1%} is below minimum {min_ratio:.0%}.\n"
        f"  Actual:   {actual[:150]!r}\n"
        f"  Expected: {expected[:150]!r}"
    )


def assert_response_within(
    elapsed_seconds: float,
    max_seconds: float = AI_RESPONSE_TIMEOUT_S,
    label: str = "",
) -> None:
    """Fail if an AI endpoint response time exceeds the latency budget."""
    tag = f"[{label}] " if label else ""
    assert elapsed_seconds <= max_seconds, (
        f"{tag}AI response took {elapsed_seconds:.2f}s, exceeded limit of {max_seconds:.2f}s"
    )


def assert_field_present(result: dict, *fields: str, label: str = "") -> None:
    """Fail if any expected field is absent from the AI result dict."""
    tag = f"[{label}] " if label else ""
    missing = [f for f in fields if f not in result]
    assert not missing, (
        f"{tag}AI response missing field(s) {missing!r}. Present: {list(result.keys())!r}"
    )


# ── soft assertion context manager ────────────────────────────────────────────

class SoftAssertions:
    """
    Collect failures across a block; raise one combined AssertionError at block exit.

    If a hard (non-assertion) exception is raised inside the block it propagates
    immediately — soft collection only applies to AssertionError failures.
    """

    def __init__(self) -> None:
        self._failures: list[str] = []

    def __enter__(self) -> "SoftAssertions":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            return False  # let hard exceptions propagate
        if self._failures:
            n = len(self._failures)
            detail = "\n".join(f"  {i + 1}. {msg}" for i, msg in enumerate(self._failures))
            raise AssertionError(f"{n} soft assertion(s) failed:\n{detail}")
        return False

    def _collect(self, fn, *args, **kwargs) -> None:
        try:
            fn(*args, **kwargs)
        except AssertionError as exc:
            self._failures.append(str(exc))

    @property
    def failure_count(self) -> int:
        return len(self._failures)

    @property
    def passed(self) -> bool:
        return not self._failures

    # ── mirrors of every hard assertion ──────────────────────────────────────

    def assert_confidence_above(
        self, score: float, min_score: float = AI_CONFIDENCE_THRESHOLD, label: str = ""
    ) -> None:
        self._collect(assert_confidence_above, score, min_score, label)

    def assert_confidence_below(
        self, score: float, max_score: float, label: str = ""
    ) -> None:
        self._collect(assert_confidence_below, score, max_score, label)

    def assert_category_in(
        self, value: Any, valid: Collection[Any], label: str = ""
    ) -> None:
        self._collect(assert_category_in, value, valid, label)

    def assert_text_contains_any(
        self,
        text: str,
        keywords: Iterable[str],
        *,
        case_sensitive: bool = False,
        label: str = "",
    ) -> None:
        self._collect(assert_text_contains_any, text, keywords,
                      case_sensitive=case_sensitive, label=label)

    def assert_text_contains_all(
        self,
        text: str,
        keywords: Iterable[str],
        *,
        case_sensitive: bool = False,
        label: str = "",
    ) -> None:
        self._collect(assert_text_contains_all, text, keywords,
                      case_sensitive=case_sensitive, label=label)

    def assert_text_similarity(
        self,
        actual: str,
        expected: str,
        min_ratio: float = AI_TEXT_SIMILARITY_RATIO,
        label: str = "",
    ) -> None:
        self._collect(assert_text_similarity, actual, expected, min_ratio, label)

    def assert_response_within(
        self, elapsed_seconds: float, max_seconds: float = AI_RESPONSE_TIMEOUT_S, label: str = ""
    ) -> None:
        self._collect(assert_response_within, elapsed_seconds, max_seconds, label)

    def assert_field_present(self, result: dict, *fields: str, label: str = "") -> None:
        self._collect(assert_field_present, result, *fields, label=label)
