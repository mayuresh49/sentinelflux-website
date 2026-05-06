import functools
import logging
from contextlib import contextmanager

_log = logging.getLogger("sentinelflux.steps")
_steps: list[tuple[str, bool]] = []


def reset():
    _steps.clear()


def snapshot() -> list[tuple[str, bool]]:
    return list(_steps)


@contextmanager
def step(description: str):
    _log.info(f"→ {description}")
    try:
        yield
        _steps.append((description, True))
    except Exception as exc:
        _steps.append((description, False))
        _log.error(f"✗ {description}: {exc}")
        raise


def step_method(description: str):
    """Decorator for page object methods — records the call as a named step."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with step(description):
                return fn(*args, **kwargs)
        return wrapper
    return decorator
