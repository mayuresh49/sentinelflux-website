"""Standard VAPT infrastructure port exposure tests."""
import socket
import pytest

_SENSITIVE_PORTS = [
    (21, "FTP"), (23, "Telnet"), (25, "SMTP"),
    (111, "RPC"), (512, "rexec"), (513, "rlogin"), (514, "rsh"),
    (1433, "MSSQL"), (1521, "Oracle DB"),
    (3306, "MySQL"), (5432, "PostgreSQL"),
    (6379, "Redis"), (11211, "Memcached"),
    (27017, "MongoDB"), (9200, "Elasticsearch"), (9300, "Elasticsearch cluster"),
    (5601, "Kibana"), (2375, "Docker daemon (unencrypted)"),
    (2379, "etcd"), (2380, "etcd peer"),
    (8500, "Consul"), (8161, "ActiveMQ console"),
    (4848, "GlassFish admin"), (9090, "Prometheus"),
]


@pytest.mark.security
def test_INFRA_sensitive_service_ports_not_exposed(vapt_host):
    """Sensitive service ports must not be reachable from the test network — indicates firewall gaps."""
    exposed = []
    for port, name in _SENSITIVE_PORTS:
        try:
            with socket.create_connection((vapt_host, port), timeout=2):
                exposed.append(f"{port}/{name}")
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass
    if exposed:
        pytest.fail(
            f"Service ports reachable from test network — firewall gap confirmed: {exposed}. "
            "These must only be accessible from trusted internal networks."
        )


@pytest.mark.security
def test_INFRA_ssh_port_not_on_default(vapt_host):
    """SSH on default port 22 increases automated attack surface — consider moving to a non-standard port."""
    try:
        with socket.create_connection((vapt_host, 22), timeout=2) as sock:
            banner = sock.recv(256).decode(errors="replace")
            if "SSH" in banner.upper():
                pytest.fail(
                    f"SSH running on default port 22 at {vapt_host}. "
                    "Move SSH to a non-standard port to reduce automated brute-force surface."
                )
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass


@pytest.mark.security
def test_INFRA_no_telnet_service(vapt_host):
    """Telnet (port 23) must not be running — transmits credentials in cleartext."""
    try:
        with socket.create_connection((vapt_host, 23), timeout=2):
            pytest.fail(f"Telnet service detected on {vapt_host}:23 — replace with SSH immediately")
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass


@pytest.mark.security
def test_INFRA_no_ftp_service(vapt_host):
    """FTP (port 21) must not be running — transmits credentials in cleartext; use SFTP instead."""
    try:
        with socket.create_connection((vapt_host, 21), timeout=2) as sock:
            banner = sock.recv(256).decode(errors="replace")
            if "FTP" in banner.upper() or "220" in banner:
                pytest.fail(
                    f"FTP service detected on {vapt_host}:21 — replace with SFTP (SSH port 22) "
                    "or FTPS; FTP transmits credentials in cleartext"
                )
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass
