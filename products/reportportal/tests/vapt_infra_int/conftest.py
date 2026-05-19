"""VAPT infrastructure (internal/grey-box) fixture set — authenticated SSH scan.
VAPT_INFRA_TARGETS   env var (comma-separated) overrides the host list.
VAPT_SSH_USER        SSH username.
VAPT_SSH_AUTH_METHOD key_path | key_paste | password  (default: key_path)
VAPT_SSH_KEY_PATH    path to private key on server (key_path mode)
VAPT_SSH_KEY_CONTENT PEM key content (key_paste mode)
VAPT_SSH_PASSWORD    password (password mode)
"""
import os
import re
import tempfile
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


def _creds_present() -> bool:
    user = os.environ.get("VAPT_SSH_USER", "").strip()
    if not user:
        return False
    method = os.environ.get("VAPT_SSH_AUTH_METHOD", "key_path")
    if method == "key_path":
        return bool(os.environ.get("VAPT_SSH_KEY_PATH", "").strip())
    if method == "key_paste":
        return bool(os.environ.get("VAPT_SSH_KEY_CONTENT", "").strip())
    if method == "password":
        return bool(os.environ.get("VAPT_SSH_PASSWORD", "").strip())
    return False


def pytest_runtest_setup(item):
    """Fast-skip all SSH tests when credentials are not configured."""
    if "ssh_client" in item.fixturenames and not _creds_present():
        pytest.skip(
            "SSH credentials not configured — set SSH Username and credentials "
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
    """Session-scoped SSH factory — yields callable: ssh_client(host) -> paramiko.SSHClient.

    Supports three auth methods via VAPT_SSH_AUTH_METHOD:
      key_path  — VAPT_SSH_KEY_PATH points to private key on server (default)
      key_paste — VAPT_SSH_KEY_CONTENT holds PEM key text; written to a temp file
      password  — VAPT_SSH_PASSWORD
    """
    if not _creds_present():
        pytest.skip(
            "SSH credentials not configured — set SSH Username and credentials "
            "in the engagement scope to enable grey-box internal infrastructure checks"
        )

    try:
        import paramiko
    except ImportError:
        pytest.skip("paramiko not installed — run: pip install paramiko>=3.0")

    ssh_user = os.environ.get("VAPT_SSH_USER", "").strip()
    auth_method = os.environ.get("VAPT_SSH_AUTH_METHOD", "key_path")

    if auth_method == "key_path":
        ssh_key = os.environ.get("VAPT_SSH_KEY_PATH", "").strip()
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
            if auth_method == "password":
                client.connect(
                    hostname=host,
                    username=ssh_user,
                    password=os.environ.get("VAPT_SSH_PASSWORD", ""),
                    timeout=15,
                    look_for_keys=False,
                    allow_agent=False,
                )
            elif auth_method == "key_paste":
                key_content = os.environ.get("VAPT_SSH_KEY_CONTENT", "")
                fd, tmp_path = tempfile.mkstemp(suffix=".pem")
                try:
                    os.write(fd, key_content.encode())
                    os.close(fd)
                    os.chmod(tmp_path, 0o600)
                    client.connect(
                        hostname=host,
                        username=ssh_user,
                        key_filename=tmp_path,
                        timeout=15,
                        look_for_keys=False,
                        allow_agent=False,
                    )
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            else:  # key_path
                client.connect(
                    hostname=host,
                    username=ssh_user,
                    key_filename=os.environ.get("VAPT_SSH_KEY_PATH", ""),
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
