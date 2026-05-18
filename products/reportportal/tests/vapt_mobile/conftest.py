"""VAPT mobile security fixture set — auto-detected from products/<product>/config/env_*.yaml.
VAPT_MOBILE_APP_PATH env var (set by the scan runner) points to the APK/IPA for static analysis.
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
def vapt_api_token() -> str:
    return _find(_load_config(), "api_token", "token", "api_key", "auth_token")


@pytest.fixture(scope="session")
def vapt_host(vapt_base_url) -> str:
    m = re.match(r"https?://([^/:]+)", vapt_base_url)
    return m.group(1) if m else "localhost"


@pytest.fixture(scope="session")
def vapt_https_port(vapt_base_url) -> "int | None":
    if vapt_base_url.startswith("https://"):
        m = re.match(r"https://[^/:]+:(\d+)", vapt_base_url)
        return int(m.group(1)) if m else 443
    return None


@pytest.fixture(scope="session")
def vapt_mobile_app_path() -> "Path | None":
    """Path to the APK/IPA for static analysis; None if not provided.
    Tests that require the app binary should call pytest.skip() when this is None.
    """
    raw = os.environ.get("VAPT_MOBILE_APP_PATH", "").strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


@pytest.fixture(scope="session")
def vapt_apk_zip(vapt_mobile_app_path) -> "zipfile.ZipFile | None":
    """Open APK as a ZipFile for pure-Python inspection. Skipped if no path."""
    import zipfile
    if vapt_mobile_app_path is None:
        return None
    if not str(vapt_mobile_app_path).endswith(".apk"):
        return None
    try:
        return zipfile.ZipFile(str(vapt_mobile_app_path), "r")
    except Exception:
        return None
