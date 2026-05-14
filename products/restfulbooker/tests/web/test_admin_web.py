import pytest
from pages.web.admin_page import AdminPage


@pytest.mark.web
@pytest.mark.sanity
def test_RB_WEB_006_admin_login_valid(page, rb_web_base, rb_web_credentials):
    admin = AdminPage(page, rb_web_base)
    admin.login(rb_web_credentials["username"], rb_web_credentials["password"])
    assert admin.is_admin_panel_visible()


@pytest.mark.web
@pytest.mark.regression
def test_RB_WEB_007_admin_login_invalid(page, rb_web_base):
    admin = AdminPage(page, rb_web_base)
    admin.login("wronguser", "wrongpassword")
    assert page.locator(".alert-danger, .alert, [class*='error']").count() > 0 or \
           not admin.is_admin_panel_visible()


@pytest.mark.web
@pytest.mark.regression
def test_RB_WEB_008_admin_panel_shows_rooms_menu(page, rb_web_base, rb_web_credentials):
    admin = AdminPage(page, rb_web_base)
    admin.login(rb_web_credentials["username"], rb_web_credentials["password"])
    assert page.get_by_role("link", name="Rooms").is_visible()


@pytest.mark.web
@pytest.mark.regression
def test_RB_WEB_009_admin_logout(page, rb_web_base, rb_web_credentials):
    admin = AdminPage(page, rb_web_base)
    admin.login(rb_web_credentials["username"], rb_web_credentials["password"])
    admin.logout()
    assert page.url.endswith("#/") or "admin" not in page.url or \
           page.locator("#username").is_visible()
