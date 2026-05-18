"""VAPT mobile APK manifest security checks — MASVS-CODE / MASVS-NETWORK / MASVS-PLATFORM.
Requires androguard: pip install androguard
"""
import pytest

pytestmark = pytest.mark.security

_ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

try:
    from androguard.core.apk import APK as _APK_CLS
except ImportError:
    try:
        from androguard.core.bytecodes.apk import APK as _APK_CLS
    except ImportError:
        _APK_CLS = None


def _load_apk(path):
    if _APK_CLS is None:
        pytest.skip("androguard not installed — run: pip install androguard")
    return _APK_CLS(str(path))


def _manifest_xml(apk):
    try:
        return apk.get_android_manifest_xml()
    except AttributeError:
        return apk.get_android_manifest_axml().get_xml_obj()


@pytest.fixture(scope="module")
def android_apk(vapt_mobile_app_path):
    if vapt_mobile_app_path is None:
        pytest.skip("No mobile app file path configured in scope")
    if not str(vapt_mobile_app_path).endswith(".apk"):
        pytest.skip("Manifest analysis requires an .apk file")
    return _load_apk(vapt_mobile_app_path)


@pytest.fixture(scope="module")
def manifest(android_apk):
    return _manifest_xml(android_apk)


def test_M8_app_not_debuggable(manifest):
    """MASVS-CODE: android:debuggable must be absent or false in production builds."""
    app = manifest.find("application")
    assert app is not None, "No <application> element in manifest"
    val = app.get(f"{_ANDROID_NS}debuggable", "false").lower()
    assert val != "true", "android:debuggable=true — production build allows debugger attachment"


def test_M2_backup_not_allowed(manifest):
    """MASVS-STORAGE: android:allowBackup=true exposes app data via adb backup."""
    app = manifest.find("application")
    val = (app.get(f"{_ANDROID_NS}allowBackup", "true") if app is not None else "true").lower()
    assert val != "true", "android:allowBackup=true — app data extractable without root via adb backup"


def test_M3_cleartext_traffic_disabled(manifest):
    """MASVS-NETWORK: android:usesCleartextTraffic=true permits unencrypted HTTP."""
    app = manifest.find("application")
    val = (app.get(f"{_ANDROID_NS}usesCleartextTraffic", "false") if app is not None else "false").lower()
    assert val != "true", "android:usesCleartextTraffic=true — app permits plaintext HTTP traffic"


def test_M1_exported_components_require_permissions(manifest):
    """MASVS-PLATFORM: exported components without permission restrictions are reachable by any app."""
    vulnerable = []
    for tag in ("activity", "service", "receiver"):
        for elem in manifest.findall(f".//{tag}"):
            exported = elem.get(f"{_ANDROID_NS}exported", "").lower()
            if exported == "true":
                perm = elem.get(f"{_ANDROID_NS}permission", "")
                name = elem.get(f"{_ANDROID_NS}name", tag)
                if not perm:
                    vulnerable.append(f"{tag}: {name}")
    assert not vulnerable, f"Exported components without permission: {vulnerable}"


def test_M8_task_affinity_not_hijackable(manifest):
    """MASVS-PLATFORM: activities with empty taskAffinity can be task-hijacked."""
    hijackable = []
    for elem in manifest.findall(".//activity"):
        if elem.get(f"{_ANDROID_NS}taskAffinity", None) == "":
            name = elem.get(f"{_ANDROID_NS}name", "unknown")
            hijackable.append(name)
    assert not hijackable, f"Activities with empty taskAffinity (task hijacking risk): {hijackable}"
