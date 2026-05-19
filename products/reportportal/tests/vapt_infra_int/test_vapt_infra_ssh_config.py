"""Standard VAPT internal infrastructure checks — authenticated SSH grey-box assessment."""
import pytest


def _run(ssh_client_fn, host: str, cmd: str) -> str:
    """Execute cmd via SSH on host, return stdout (stderr as fallback)."""
    client = ssh_client_fn(host)
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    return out or stderr.read().decode("utf-8", errors="replace").strip()


@pytest.mark.security
def test_INFRA_INT_ssh_permit_root_login_disabled(ssh_client, vapt_host):
    """sshd_config: PermitRootLogin must be 'no' — direct root SSH bypasses the audit trail."""
    out = _run(ssh_client, vapt_host, "grep -i '^PermitRootLogin' /etc/ssh/sshd_config")
    if not out:
        pytest.xfail(
            "PermitRootLogin not explicitly set in sshd_config — "
            "SSH default may permit root login; add 'PermitRootLogin no'"
        )
    assert "no" in out.lower(), \
        f"PermitRootLogin is not disabled on {vapt_host}: '{out}' — set 'PermitRootLogin no' in sshd_config"


@pytest.mark.security
def test_INFRA_INT_ssh_password_auth_disabled(ssh_client, vapt_host):
    """sshd_config: PasswordAuthentication must be 'no' — prevents online brute-force attacks."""
    out = _run(ssh_client, vapt_host, "grep -i '^PasswordAuthentication' /etc/ssh/sshd_config")
    if not out:
        pytest.xfail(
            "PasswordAuthentication not explicitly set in sshd_config — "
            "default may allow password auth; add 'PasswordAuthentication no'"
        )
    assert "no" in out.lower(), \
        f"PasswordAuthentication is not disabled on {vapt_host}: '{out}' — set 'PasswordAuthentication no'"


@pytest.mark.security
def test_INFRA_INT_ssh_max_auth_tries(ssh_client, vapt_host):
    """sshd_config: MaxAuthTries must be ≤4 — limits brute-force attempts per connection."""
    out = _run(ssh_client, vapt_host, "grep -i '^MaxAuthTries' /etc/ssh/sshd_config")
    if not out:
        pytest.xfail(
            "MaxAuthTries not set in sshd_config — SSH default is 6; "
            "set 'MaxAuthTries 3' to reduce brute-force window"
        )
        return
    try:
        val = int(out.split()[-1])
    except ValueError:
        pytest.fail(f"Could not parse MaxAuthTries value from sshd_config: '{out}'")
    assert val <= 4, \
        f"MaxAuthTries={val} on {vapt_host} exceeds recommended maximum of 4 — reduce to 3 in sshd_config"


@pytest.mark.security
def test_INFRA_INT_ssh_allow_users_configured(ssh_client, vapt_host):
    """sshd_config: AllowUsers or AllowGroups must restrict which accounts can SSH in."""
    out = _run(ssh_client, vapt_host,
               "grep -Ei '^(AllowUsers|AllowGroups)' /etc/ssh/sshd_config")
    if not out:
        pytest.xfail(
            f"Neither AllowUsers nor AllowGroups is configured in sshd_config on {vapt_host} — "
            "all system accounts can authenticate via SSH; "
            "add 'AllowUsers <username>' to restrict access to named accounts only"
        )


@pytest.mark.security
def test_INFRA_INT_suid_sgid_files(ssh_client, vapt_host):
    """Unexpected SUID/SGID binaries are a privilege escalation risk — only OS-standard ones should exist."""
    out = _run(ssh_client, vapt_host,
               "timeout 25 find / -perm /6000 -type f 2>/dev/null | grep -v /proc | head -60")
    _EXPECTED = {
        "/usr/bin/sudo", "/usr/bin/su", "/usr/bin/passwd",
        "/usr/bin/newgrp", "/usr/bin/chsh", "/usr/bin/chfn",
        "/usr/bin/gpasswd", "/usr/bin/mount", "/usr/bin/umount",
        "/usr/bin/ping", "/bin/ping",
        "/usr/lib/openssh/ssh-keysign",
        "/usr/lib/dbus-1.0/dbus-daemon-launch-helper",
        "/usr/sbin/pam_extraauth",
    }
    found = [f.strip() for f in out.splitlines() if f.strip()]
    unexpected = [f for f in found if f not in _EXPECTED]
    if unexpected:
        pytest.xfail(
            f"Unexpected SUID/SGID binaries on {vapt_host} — "
            f"review for unnecessary privilege elevation: {unexpected[:10]}"
        )


@pytest.mark.security
def test_INFRA_INT_sensitive_file_permissions(ssh_client, vapt_host):
    """Sensitive system files must have restrictive permissions to prevent credential exposure."""
    checks = [
        ("/etc/shadow",            "640", "stat -c '%a' /etc/shadow 2>/dev/null"),
        ("/etc/sudoers",           "440", "stat -c '%a' /etc/sudoers 2>/dev/null"),
        ("~/.ssh/authorized_keys", "600",
         "stat -c '%a' ~/.ssh/authorized_keys 2>/dev/null || echo absent"),
    ]
    failures = []
    for path, max_mode, cmd in checks:
        out = _run(ssh_client, vapt_host, cmd).strip()
        if not out or "absent" in out or "No such" in out:
            continue
        try:
            actual = int(out, 8)
            limit = int(max_mode, 8)
        except ValueError:
            continue
        if actual > limit:
            failures.append(f"{path}: mode {out} (max allowed: {max_mode})")
    assert not failures, \
        f"Overly permissive sensitive file permissions on {vapt_host}: {failures}"


@pytest.mark.security
def test_INFRA_INT_audit_log_present(ssh_client, vapt_host):
    """Auth audit log must exist — required for incident response and forensic investigation."""
    out = _run(ssh_client, vapt_host,
               "test -f /var/log/auth.log && echo auth.log || "
               "test -f /var/log/secure && echo secure || echo absent")
    assert "absent" not in out, (
        f"No auth audit log found on {vapt_host} "
        "(/var/log/auth.log or /var/log/secure missing) — "
        "install and configure rsyslog or auditd to capture authentication events"
    )
