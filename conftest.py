import logging
import os
import shutil
import warnings
from pathlib import Path

# urllib3 v2 + macOS LibreSSL mismatch — cosmetic warning, not a real issue
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except ImportError:
    pass

import yaml
import pytest
from pytest_html import extras as html_extras
from utils.logger import create_logger
from utils.ai_factory import create_ai_client
from utils.step import reset as _reset_steps, snapshot as _snapshot_steps
from api.rest_client import RestClient
from api.graphql_client import GraphQLClient

ROOT_DIR = Path(__file__).resolve().parent
_ARTIFACT_ROOT = ROOT_DIR / "reports" / "artifacts"

# Artifacts are attached to ReportPortal via Python's logging bridge when RP is active.
# When RP_API_KEY is not set the extra= attachment fields are silently ignored.
_rp_log = logging.getLogger(__name__)


def pytest_configure(config):
    rp_key = os.environ.get("RP_API_KEY", "")
    if rp_key:
        config._inicache["rp_api_key"] = rp_key


# ── Artifact helpers ─────────────────────────────────────────────────────────

def _artifact_dir(item) -> Path:
    safe = (
        item.nodeid
        .replace("/", "_")
        .replace("::", "__")
        .replace("[", "_")
        .replace("]", "")
    )
    d = _ARTIFACT_ROOT / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_page(item):
    """Return the active Playwright Page for this test, or None for non-browser tests."""
    for name in ("page", "logged_in_page"):
        pg = item.funcargs.get(name)
        if pg is not None and hasattr(pg, "screenshot"):
            return pg
    return None


# ── API request log reset (autouse — clears per-test so logs are test-scoped) ──

@pytest.fixture(scope="function", autouse=True)
def _api_log_reset(request):
    for name in request.fixturenames:
        try:
            val = request.getfixturevalue(name)
            if hasattr(val, "clear_log"):
                val.clear_log()
        except Exception:
            pass
    yield


@pytest.fixture(scope="function", autouse=True)
def _step_tracker():
    _reset_steps()
    yield


# ── Console log capture (autouse for web tests) ───────────────────────────────

@pytest.fixture(scope="function", autouse=True)
def console_log_capture(request):
    """
    Attach a console-message listener to the Playwright page when the test uses one.
    Yields the accumulated log lines so the failure hook can persist/attach them.
    Skipped for API/non-browser tests (avoids spinning up a browser unnecessarily).
    """
    browser_fixtures = {"page", "logged_in_page"}
    if not browser_fixtures.intersection(request.fixturenames):
        yield []
        return

    page = None
    for name in browser_fixtures:
        if name in request.fixturenames:
            try:
                pg = request.getfixturevalue(name)
                if hasattr(pg, "on"):
                    page = pg
                    break
            except Exception:
                pass

    if page is None:
        yield []
        return

    logs: list[str] = []
    page.on("console", lambda msg: logs.append(f"[{msg.type.upper()}] {msg.text}"))
    yield logs


# ── Failure artifact hook ─────────────────────────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # ── Step table (all UI call results — pass and fail) ─────────────────────
    if report.when == "call":
        steps = _snapshot_steps()
        if steps:
            rows = [
                '<table style="width:100%;border-collapse:collapse;font-size:13px">',
                '<tr style="background:#f5f5f5">',
                '<th style="text-align:left;padding:5px 8px;border-bottom:1px solid #ddd">#</th>',
                '<th style="text-align:left;padding:5px 8px;border-bottom:1px solid #ddd">Step</th>',
                '<th style="text-align:left;padding:5px 8px;border-bottom:1px solid #ddd">Status</th>',
                '</tr>',
            ]
            for i, (desc, passed) in enumerate(steps, 1):
                color = "#27ae60" if passed else "#e74c3c"
                label = "PASS" if passed else "FAIL"
                rows.append(
                    f'<tr>'
                    f'<td style="padding:4px 8px;border-bottom:1px solid #eee">{i}</td>'
                    f'<td style="padding:4px 8px;border-bottom:1px solid #eee">{desc}</td>'
                    f'<td style="padding:4px 8px;border-bottom:1px solid #eee;color:{color};font-weight:bold">{label}</td>'
                    f'</tr>'
                )
            rows.append('</table>')
            report.extras = getattr(report, "extras", [])
            report.extras.append(html_extras.html("".join(rows)))

    if report.when != "call" or not report.failed:
        return

    adir = _artifact_dir(item)

    # ── API artifact (non-browser tests) ─────────────────────────────────────
    api_client = next(
        (v for v in item.funcargs.values() if hasattr(v, "_request_log") and v._request_log),
        None,
    )
    if api_client is not None:
        lines = []
        for i, entry in enumerate(api_client._request_log, 1):
            lines.append(f"### Request {i}  [{entry['status']}  {entry['elapsed_ms']}ms]")
            lines.append(entry["curl"])
            lines.append("")
            lines.append(f"Response ({entry['status']}):")
            resp = entry["response"]
            lines.append(
                __import__("json").dumps(resp, indent=2) if isinstance(resp, (dict, list)) else str(resp)
            )
            lines.append("")
        log_text = "\n".join(lines)
        api_log_path = adir / "api_calls.log"
        try:
            api_log_path.write_text(log_text, encoding="utf-8")
        except Exception:
            pass
        try:
            _rp_log.error(
                "Failure — API request/response log",
                extra={"attachment": {
                    "name": "api_calls.log",
                    "data": log_text.encode(),
                    "mime": "text/plain",
                }},
            )
        except Exception:
            pass

    page = _safe_page(item)
    if page is None:
        return

    # 1. Full-page screenshot (pytest-playwright's --screenshot captures viewport only)
    fp_path = adir / "screenshot_full_page.png"
    try:
        page.screenshot(path=str(fp_path), full_page=True)
    except Exception:
        pass

    # 2. Console logs captured by the fixture above
    logs: list = item.funcargs.get("console_log_capture") or []
    log_path = adir / "console.log"
    if logs:
        try:
            log_path.write_text("\n".join(logs), encoding="utf-8")
        except Exception:
            pass

    # 3. Copy playwright trace if it was written to test-results/
    #    (--tracing=retain-on-failure writes trace.zip alongside video/screenshot)
    safe_name = item.nodeid.replace("/", "-").replace("::", "-").replace("[", "-").replace("]", "")
    trace_src = ROOT_DIR / "test-results" / safe_name / "trace.zip"
    if trace_src.exists():
        try:
            shutil.copy(trace_src, adir / "trace.zip")
        except Exception:
            pass

    # 4. Attach to ReportPortal via Python logging (no-op when RP is disabled)
    if fp_path.exists():
        try:
            _rp_log.error(
                "Failure — full-page screenshot",
                extra={"attachment": {
                    "name": fp_path.name,
                    "data": fp_path.read_bytes(),
                    "mime": "image/png",
                }},
            )
        except Exception:
            pass

    if logs:
        try:
            _rp_log.error(
                "Failure — browser console log",
                extra={"attachment": {
                    "name": "console.log",
                    "data": "\n".join(logs).encode(),
                    "mime": "text/plain",
                }},
            )
        except Exception:
            pass

    if trace_src.exists():
        try:
            _rp_log.error(
                "Failure — Playwright network/browser trace",
                extra={"attachment": {
                    "name": "trace.zip",
                    "data": (adir / "trace.zip").read_bytes(),
                    "mime": "application/zip",
                }},
            )
        except Exception:
            pass


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        help="Environment profile to use: qa, staging, prod",
    )
    parser.addoption(
        "--locale",
        action="store",
        default="en-US",
        help="Localization locale code",
    )
    parser.addoption(
        "--session-login",
        action="store_true",
        default=False,
        help="Reuse one authenticated browser session per worker (skips per-test login)",
    )


@pytest.fixture(scope="session")
def config(request):
    env = request.config.getoption("--env")
    config_file = ROOT_DIR / "config" / f"env_{env}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Environment config not found: {config_file}")
    return load_yaml(config_file)


@pytest.fixture(scope="session")
def locale(request):
    return request.config.getoption("--locale")


@pytest.fixture(scope="session")
def logger(config):
    return create_logger(config.get("logging", {}))


@pytest.fixture(scope="session")
def rest_client(config, logger):
    return RestClient(base_url=config["api"]["rest_base_url"], logger=logger)


@pytest.fixture(scope="session")
def graphql_client(config, logger):
    return GraphQLClient(endpoint=config["api"]["graphql_endpoint"], logger=logger)


@pytest.fixture(scope="function")
def browser_page(page, config, logger, locale, ai_client, ai_config):
    page.set_default_timeout(config.get("browser", {}).get("timeout", 10000))
    ai_self_healing = ai_config.get("self_healing", False)
    # Note: ai_client is passed to page objects, but for now, we can store it in a way
    # Since page is from playwright, we can't modify it directly, but page objects will get it
    yield page


@pytest.fixture(scope="session")
def ai_config(config):
    return config.get("sentinelflux", {}).get("ai", {})


@pytest.fixture(scope="session")
def ai_client(ai_config):
    client = create_ai_client(ai_config)
    from utils.ai_registry import set_ai_client
    set_ai_client(client)
    return client


@pytest.fixture(scope="function")
def locator_manager(locale):
    from utils.locator_manager import LocatorManager

    return LocatorManager(locale=locale)


