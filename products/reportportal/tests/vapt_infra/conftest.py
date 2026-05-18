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


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def vapt_infra_targets(vapt_base_url) -> list[str]:
    raw = os.environ.get("VAPT_INFRA_TARGETS", "").strip()
    if raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    m = re.match(r"https?://([^/:]+)", vapt_base_url)
    return [m.group(1) if m else "localhost"]


@pytest.fixture(scope="session")
def vapt_host(vapt_infra_targets) -> str:
    return vapt_infra_targets[0] if vapt_infra_targets else "localhost"


@pytest.fixture(scope="session")
def vapt_https_port(vapt_base_url) -> int | None:
    if vapt_base_url.startswith("https://"):
        m = re.match(r"https://[^/:]+:(\d+)", vapt_base_url)
        return int(m.group(1)) if m else 443
    return None


@pytest.fixture(scope="session")
def vapt_domain(vapt_host) -> str:
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", vapt_host) or vapt_host in ("localhost", "127.0.0.1", "::1"):
        return ""
    return vapt_host
