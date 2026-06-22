"""Chính sách retry (SPEC 02 §3, 04 §4) — backoff luỹ thừa."""

from __future__ import annotations


def should_retry(retryable: bool, attempt: int, max_retries: int) -> bool:
    return retryable and attempt < max_retries


def backoff_seconds(attempt: int, base: int) -> int:
    return base * (2**attempt)
