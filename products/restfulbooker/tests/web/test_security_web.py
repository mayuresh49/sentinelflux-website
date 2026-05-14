import pytest
from pages.web.home_page import HomePage
from pages.web.admin_page import AdminPage

_XSS = "<script>window.__xss_fired=true</script>"


@pytest.mark.web
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_006_xss_in_contact_form_does_not_execute(page, rb_web_base):
    dialog_fired = []
    page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))

    home = HomePage(page, rb_web_base)
    home.navigate()

    # Fill contact form with XSS payload
    contact_name = page.locator("#name")
    if contact_name.count() > 0:
        contact_name.fill(_XSS)

    contact_email = page.locator("#email")
    if contact_email.count() > 0:
        contact_email.fill("xss@example.com")

    contact_msg = page.locator("#message, textarea[name='message']")
    if contact_msg.count() > 0:
        contact_msg.fill(_XSS)

    assert not dialog_fired, f"XSS dialog triggered: {dialog_fired}"
    xss_executed = page.evaluate("() => window.__xss_fired === true")
    assert not xss_executed, "XSS payload executed on page"


@pytest.mark.web
@pytest.mark.security
@pytest.mark.sanity
def test_RB_SEC_007_admin_panel_requires_login(page, rb_web_base):
    page.goto(f"{rb_web_base}/admin", wait_until="networkidle")
    # Admin page exposes a login form with #username / #password before granting access
    login_form = page.locator("#username, #password, input[name='username']")
    assert login_form.count() > 0, \
        "Admin panel accessible without credentials — no login form found"


@pytest.mark.web
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_008_xss_in_booking_firstname_does_not_execute(page, rb_web_base):
    dialog_fired = []
    page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))

    home = HomePage(page, rb_web_base)
    home.navigate()

    # Open booking form if available
    book_btn = page.locator("button:has-text('Book'), a:has-text('Book')").first
    if book_btn.count() > 0:
        book_btn.click()
        page.wait_for_timeout(500)

    firstname = page.locator("input[name='firstname'], #firstname").first
    if firstname.count() > 0:
        firstname.fill(_XSS)

    assert not dialog_fired, f"XSS dialog triggered: {dialog_fired}"
    xss_executed = page.evaluate("() => window.__xss_fired === true")
    assert not xss_executed, "XSS payload executed in booking form"


@pytest.mark.web
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_009_home_page_does_not_expose_server_version(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    # Server header leakage check via Playwright response interception
    server_headers = []

    def capture(response):
        srv = response.headers.get("server", "")
        if srv:
            server_headers.append(srv)

    page.on("response", capture)
    page.reload(wait_until="networkidle")

    for srv in server_headers:
        assert not any(v in srv.lower() for v in ("apache/", "nginx/", "iis/")), \
            f"Server version exposed in response header: {srv}"
