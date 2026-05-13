"""Polling utility for async/deferred state verification in tests."""

import time


def wait_for(condition_fn, timeout: int, interval: int = 2, description: str = "condition") -> bool:
    """Poll condition_fn every interval seconds until it returns True or timeout expires.

    Raises TimeoutError with a clear message if the condition is never met.
    Use for scheduler-based steps: background jobs, approval workflows, email delivery, etc.

    Example:
        wait_for(
            lambda: client.get_status(job_id) == "completed",
            timeout=REPORT_GEN_TIMEOUT,
            description="report job status = completed",
        )
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition_fn():
            return True
        time.sleep(interval)
    raise TimeoutError(
        f"wait_for timed out after {timeout}s waiting for: {description}"
    )
