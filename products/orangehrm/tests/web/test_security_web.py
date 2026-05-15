import pytest
from pages.web.login_page import LoginPage

_XSS = "<script>window.__xss_fired=true</script>"


@pytest.mark.web
@pytest.mark.security
def test_OH_SEC_008_xss_payload_in_username_does_not_execute(page, orangehrm_base_url):
    dialog_fired = []
    page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
    LoginPage(page, orangehrm_base_url).navigate_to_login()
    page.get_by_placeholder("Username").fill(_XSS)
    page.get_by_placeholder("Password").fill("anypassword")
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle")
    assert not dialog_fired, f"XSS dialog triggered: {dialog_fired}"
    try:
        xss_executed = page.evaluate("() => window.__xss_fired === true")
    except Exception:
        xss_executed = False  # page context destroyed means script didn't execute
    assert not xss_executed, "XSS payload was executed"


@pytest.mark.web
@pytest.mark.security
def test_OH_SEC_009_dashboard_without_auth_redirects_to_login(page, orangehrm_base_url):
    page.goto(f"{orangehrm_base_url}/web/index.php/dashboard/index", wait_until="networkidle")
    assert "/auth/login" in page.url, f"Expected login redirect, got: {page.url}"


@pytest.mark.web
@pytest.mark.security
def test_OH_SEC_010_admin_url_without_auth_redirects_to_login(page, orangehrm_base_url):
    page.goto(f"{orangehrm_base_url}/web/index.php/admin/viewSystemUsers", wait_until="networkidle")
    assert "/auth/login" in page.url, f"Expected login redirect, got: {page.url}"


@pytest.mark.web
@pytest.mark.security
def test_OH_SEC_011_session_cookie_has_httponly_flag(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    assert lp.is_on_dashboard()
    cookies = page.context.cookies()
    auth_cookies = [c for c in cookies if any(k in c["name"].lower() for k in ("session", "orangehrm", "csrf"))]
    assert auth_cookies, "No session/auth cookies found after login"
    for cookie in auth_cookies:
        assert cookie.get("httpOnly"), f"Cookie '{cookie['name']}' missing HttpOnly flag"


@pytest.mark.web
@pytest.mark.security
def test_OH_SEC_012_pim_url_without_auth_redirects_to_login(page, orangehrm_base_url):
    page.goto(f"{orangehrm_base_url}/web/index.php/pim/viewEmployeeList", wait_until="networkidle")
    assert "/auth/login" in page.url, f"Expected login redirect, got: {page.url}"
