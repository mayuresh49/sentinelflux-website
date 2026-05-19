"""VAPT infrastructure (internal/grey-box) fixture set — authenticated SSH scan.
VAPT_INFRA_TARGETS env var (comma-separated) overrides the host list when set by the scan runner.
VAPT_SSH_USER / VAPT_SSH_KEY_PATH enable authenticated checks — set via the engagement scope.
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


def pytest_runtest_setup(item):
    """Fast-skip all SSH tests when credentials are not configured — avoids entering the fixture."""
    if "ssh_client" in item.fixturenames:
        if not os.environ.get("VAPT_SSH_USER", "").strip() or \
           not os.environ.get("VAPT_SSH_KEY_PATH", "").strip():
            pytest.skip(
                "SSH credentials not configured — set ssh_username and ssh_key_path "
                "in the engagement scope to enable grey-box internal infrastructure checks"
            )


def pytest_generate_tests(metafunc):
    if "vapt_host" in metafunc.fixturenames:
        metafunc.parametrize("vapt_host", _resolve_targets())


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def ssh_client():
    """Session-scoped SSH connection factory.
    Yields a callable: ssh_client(host) -> paramiko.SSHClient.
    Skips all SSH tests when VAPT_SSH_USER / VAPT_SSH_KEY_PATH are absent or paramiko is missing.
    Each unique host gets one connection, cached for the session lifetime.
    """
    ssh_user = os.environ.get("VAPT_SSH_USER", "").strip()
    ssh_key = os.environ.get("VAPT_SSH_KEY_PATH", "").strip()

    if not ssh_user or not ssh_key:
        pytest.skip(
            "SSH credentials not configured — set ssh_username and ssh_key_path "
            "in the engagement scope to enable grey-box internal infrastructure checks"
        )

    try:
        import paramiko
    except ImportError:
        pytest.skip("paramiko not installed — run: pip install paramiko>=3.0")

    if not Path(ssh_key).exists():
        pytest.skip(f"SSH private key not found on server: {ssh_key}")

    _clients: dict = {}

    def _connect(host: str):
        if host in _clients:
            return _clients[host]
        client = paramiko.SSHClient()
        # AutoAddPolicy is acceptable here — VAPT targets are known, controlled hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=host,
                username=ssh_user,
                key_filename=ssh_key,
                timeout=15,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException as e:
            pytest.skip(f"SSH authentication failed for {ssh_user}@{host}: {e}")
        except Exception as e:
            pytest.skip(f"SSH connection failed to {host}: {e}")
        _clients[host] = client
        return client

    yield _connect

    for c in _clients.values():
        try:
            c.close()
        except Exception:
            pass
