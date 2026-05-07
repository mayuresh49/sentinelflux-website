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
    """Decorator for page object methods — records as a named step and routes through try_resilient.

    On playwright.sync_api.TimeoutError: escalates Tier-2 (Browser-Use/Ollama) then Tier-3 (Skyvern).
    Falls back to direct call when self has no try_resilient (non-BasePage usage).
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            page_obj = args[0] if args else None
            with step(description):
                if page_obj is not None and hasattr(page_obj, "try_resilient"):
                    return page_obj.try_resilient(description, fn, *args, **kwargs)
                return fn(*args, **kwargs)
        return wrapper
    return decorator
