"""VAPT fixture set — auto-detected from products/<product>/config/env_*.yaml."""
from pathlib import Path
import pytest
import yaml

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent  # products/<product>/


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
