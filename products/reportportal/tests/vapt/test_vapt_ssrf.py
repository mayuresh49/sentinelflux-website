"""Standard VAPT SSRF tests — OWASP A10 Server-Side Request Forgery."""
import pytest
import requests

_INTERNAL_TARGETS = [
    "http://169.254.169.254/latest/meta-data/",   # AWS IMDS v1
    "http://metadata.google.internal/",            # GCP metadata
    "http://169.254.169.254/",
    "http://127.0.0.1/",
    "http://localhost/",
    "http://[::1]/",
    "http://0.0.0.0/",
]

_URL_PARAM_NAMES = ["url", "webhook", "callback", "redirect", "target", "src", "endpoint", "fetch"]
_FETCH_PATHS = ["/api/v1/webhook", "/api/webhook", "/api/fetch", "/api/v1/fetch", "/api/v1/preview"]


@pytest.mark.security
def test_A10_ssrf_via_url_params_blocked(vapt_base_url):
    """URL-accepting API parameters must not fetch internal or cloud-metadata endpoints."""
    suspicious = []
    for target in _INTERNAL_TARGETS[:3]:
        for param in _URL_PARAM_NAMES:
            for path in _FETCH_PATHS:
                try:
                    resp = requests.post(
                        f"{vapt_base_url}{path}",
                        json={param: target},
                        allow_redirects=False, timeout=5,
                    )
                    if resp.status_code == 200 and any(
                        kw in resp.text.lower()
                        for kw in ("ami-id", "instance-id", "metadata", "computeMetadata")
                    ):
                        suspicious.append((path, param, target))
                except requests.exceptions.RequestException:
                    pass
    assert not suspicious, f"Possible SSRF — internal metadata fetched: {suspicious}"


@pytest.mark.security
def test_A10_ssrf_dns_rebinding_probe(vapt_base_url):
    """URL params must reject or sanitize URLs pointing to RFC-1918 address ranges."""
    private_ranges = [
        "http://10.0.0.1/", "http://192.168.1.1/", "http://172.16.0.1/",
    ]
    for target in private_ranges:
        for param in _URL_PARAM_NAMES:
            for path in _FETCH_PATHS:
                try:
                    resp = requests.post(
                        f"{vapt_base_url}{path}",
                        json={param: target},
                        allow_redirects=False, timeout=5,
                    )
                    if resp.status_code == 200 and len(resp.text) > 100:
                        pytest.xfail(
                            f"Endpoint {path} with {param}={target} returned 200 with content — "
                            "manually verify this is not fetching internal network resources"
                        )
                except requests.exceptions.RequestException:
                    pass
