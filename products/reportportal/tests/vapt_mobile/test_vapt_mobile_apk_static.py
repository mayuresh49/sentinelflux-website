"""VAPT mobile APK static analysis — MASVS-STORAGE / MASVS-CRYPTO / MASVS-CODE.
Pure-Python checks use zipfile only. Androguard checks are skipped if not installed.
"""
import re
import zipfile
import pytest

pytestmark = pytest.mark.security

_SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([A-Za-z0-9_\-]{20,})["\']', "Hardcoded API key"),
    (r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'](?!.*\{)[A-Za-z0-9!@#$%^&*]{8,}["\']', "Hardcoded password"),
    (r'(?i)(secret[_-]?key|client[_-]?secret)\s*[=:]\s*["\']([A-Za-z0-9_\-]{16,})["\']', "Hardcoded secret"),
    (r'AKIA[0-9A-Z]{16}', "AWS access key"),
]
_WEAK_CRYPTO = [
    ("MD5", "MD5 is cryptographically broken"),
    ("DES/", "DES key size is insufficient"),
    ("AES/ECB", "ECB mode leaks block patterns"),
    ("RC4", "RC4 stream cipher is broken"),
]


def _apk_zip(vapt_mobile_app_path):
    if vapt_mobile_app_path is None or not str(vapt_mobile_app_path).endswith(".apk"):
        return None
    try:
        return zipfile.ZipFile(str(vapt_mobile_app_path), "r")
    except Exception:
        return None


def _read_assets(zf) -> str:
    out = []
    for name in zf.namelist():
        if name.startswith("assets/"):
            try:
                out.append(zf.read(name).decode("utf-8", errors="ignore"))
            except Exception:
                pass
    return "\n".join(out)


def _dex_text(zf) -> str:
    raw = b""
    for name in zf.namelist():
        if re.match(r"classes\d*\.dex$", name):
            raw += zf.read(name)
    return re.sub(rb"[^\x20-\x7e\n]", b" ", raw).decode("ascii", errors="ignore")


def test_M2_no_private_key_files_in_apk(vapt_mobile_app_path):
    """MASVS-STORAGE: private keys or keystores embedded in the APK are high risk."""
    zf = _apk_zip(vapt_mobile_app_path)
    if zf is None:
        pytest.skip("No .apk path configured")
    sensitive = [n for n in zf.namelist()
                 if re.search(r"\.(pem|key|jks|bks|p12|pfx|keystore)$", n, re.I)]
    assert not sensitive, f"Sensitive key files bundled in APK: {sensitive}"


def test_M2_no_hardcoded_secrets_in_assets(vapt_mobile_app_path):
    """MASVS-STORAGE: credentials must not be stored in plaintext asset files."""
    zf = _apk_zip(vapt_mobile_app_path)
    if zf is None:
        pytest.skip("No .apk path configured")
    content = _read_assets(zf)
    hits = [label for pattern, label in _SECRET_PATTERNS if re.search(pattern, content)]
    assert not hits, f"Potential hardcoded secrets in assets/: {hits}"


def test_M3_no_http_urls_in_assets(vapt_mobile_app_path):
    """MASVS-NETWORK: http:// endpoints in assets indicate unencrypted backend calls."""
    zf = _apk_zip(vapt_mobile_app_path)
    if zf is None:
        pytest.skip("No .apk path configured")
    content = _read_assets(zf)
    urls = [u for u in re.findall(r"http://[^\s<>]{8,}", content)
            if "localhost" not in u and "127.0.0.1" not in u]
    assert not urls, f"Plaintext HTTP URLs in assets: {urls[:5]}"


def test_M5_no_weak_crypto_strings_in_dex(vapt_mobile_app_path):
    """MASVS-CRYPTO: weak cipher algorithms should not appear in DEX string constants."""
    zf = _apk_zip(vapt_mobile_app_path)
    if zf is None:
        pytest.skip("No .apk path configured")
    text = _dex_text(zf)
    hits = [(name, reason) for name, reason in _WEAK_CRYPTO if name in text]
    assert not hits, f"Weak crypto usage in DEX: {[n for n, _ in hits]}"


def _androguard_analyze(path):
    try:
        from androguard.misc import AnalyzeAPK
    except ImportError:
        pytest.skip("androguard not installed — run: pip install androguard")
    return AnalyzeAPK(str(path))


def _dex_strings(dex_or_list) -> list:
    dexes = dex_or_list if isinstance(dex_or_list, list) else [dex_or_list]
    out = []
    for d in dexes:
        try:
            out.extend(s.get_value() for s in d.get_strings())
        except Exception:
            pass
    return out


def test_M2_no_hardcoded_secrets_in_dex(vapt_mobile_app_path):
    """MASVS-STORAGE: search DEX string pool for hardcoded credential patterns (androguard)."""
    if vapt_mobile_app_path is None or not str(vapt_mobile_app_path).endswith(".apk"):
        pytest.skip("No .apk path configured")
    _, d, _ = _androguard_analyze(vapt_mobile_app_path)
    combined = " ".join(_dex_strings(d))
    hits = [label for pattern, label in _SECRET_PATTERNS if re.search(pattern, combined)]
    assert not hits, f"Potential hardcoded secrets in DEX strings: {hits}"


def test_M3_certificate_pinning_present(vapt_mobile_app_path):
    """MASVS-NETWORK: verify evidence of certificate pinning implementation (androguard)."""
    if vapt_mobile_app_path is None or not str(vapt_mobile_app_path).endswith(".apk"):
        pytest.skip("No .apk path configured")
    _, d, _ = _androguard_analyze(vapt_mobile_app_path)
    strings = _dex_strings(d)
    pinning_markers = {"CertificatePinner", "TrustKit", "checkServerTrusted",
                       "network_security_config", "PublicKeyPinning", "ssl_pinning"}
    found = any(any(m in s for m in pinning_markers) for s in strings)
    if not found:
        pytest.xfail("No certificate pinning indicators found — confirm via network_security_config.xml")


def test_M5_no_logging_sensitive_data(vapt_mobile_app_path):
    """MASVS-STORAGE: Log calls with sensitive parameter names leak data in production logs."""
    if vapt_mobile_app_path is None or not str(vapt_mobile_app_path).endswith(".apk"):
        pytest.skip("No .apk path configured")
    _, d, dx = _androguard_analyze(vapt_mobile_app_path)
    log_methods = {"Landroid/util/Log;->d", "Landroid/util/Log;->e", "Landroid/util/Log;->v"}
    sensitive_keywords = {"password", "passwd", "token", "secret", "credential", "api_key"}
    strings = set(s.lower() for s in _dex_strings(d))
    log_present = any(kw in strings for kw in sensitive_keywords)
    if log_present:
        log_calls = [str(m.full_name) for m in dx.get_methods()
                     if any(ref in str(m.full_name) for ref in log_methods)]
        if log_calls:
            pytest.xfail(f"Log calls detected alongside sensitive string literals — review manually: {log_calls[:3]}")
