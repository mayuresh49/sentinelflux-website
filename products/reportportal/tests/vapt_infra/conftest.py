"""VAPT infrastructure fixture set — auto-detected from products/<product>/config/env_*.yaml.
VAPT_INFRA_TARGETS env var (comma-separated) overrides the host list when set by the scan runner.
"""
import os
import re
from pathlib import Path
import pytest
import yaml

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    cfg_dir = _PRODUCT_ROOT / "config"
    for f in sorted(cfg_dir.glob("env_*.yaml")):
        try:
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    return {}


def _find(cfg: dict, *keys: str) -> str:
    for section in cfg.values():
        if isinstance(section, dict):
            for k in keys:
                if k in section and section[k]:
                    return str(section[k])
    return ""


def _resolve_targets() -> list[str]:
    raw = os.environ.get("VAPT_INFRA_TARGETS", "").strip()
    if raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    url = _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"
    m = re.match(r"https?://([^/:]+)", url)
    return [m.group(1) if m else "localhost"]


def pytest_generate_tests(metafunc):
    if "vapt_host" in metafunc.fixturenames:
        metafunc.parametrize("vapt_host", _resolve_targets())


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def vapt_https_port(vapt_base_url) -> int | None:
    if vapt_base_url.startswith("https://"):
        m = re.match(r"https://[^/:]+:(\d+)", vapt_base_url)
        return int(m.group(1)) if m else 443
    return None


@pytest.fixture
def vapt_domain(vapt_host) -> str:
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", vapt_host) or vapt_host in ("localhost", "127.0.0.1", "::1"):
        return ""
    return vapt_host
