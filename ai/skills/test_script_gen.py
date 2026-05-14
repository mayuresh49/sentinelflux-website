"""Generate runnable pytest scripts from test case documentation."""

from pathlib import Path
from ai.clients.base_client import AIClient
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
from ai.prompts.prompt_templates import TEST_SCRIPT_GEN_PROMPT

_CONVENTIONS: dict[str, str] = {
    "api": """\
Imports:
    import pytest
    from utils.assertions import assert_status_code

Marker: @pytest.mark.api

REST fixture — rest_client:
    response = rest_client.post(endpoint_name="create_booking", payload_name="create_booking", schema_name="booking_schema")
    response = rest_client.get(endpoint_name="get_booking", path_params={"booking_id": booking_id})
    response = rest_client.put(endpoint_name="update_booking", payload_name="update_booking", path_params={"booking_id": booking_id})
    response = rest_client.delete(endpoint_name="delete_booking", path_params={"booking_id": booking_id})

GraphQL fixture — graphql_client:
    response = graphql_client.execute(query_name="countries_list", variables={"filter": {"code": {"eq": "AU"}}})

Assertions:
    assert_status_code(response, 200)
    body = response.json()
    assert "bookingid" in body
    assert body["booking"]["firstname"] == "John"

Example test function:
    @pytest.mark.api
    def test_create_booking_returns_booking_id(rest_client):
        response = rest_client.post("create_booking", payload_name="create_booking", schema_name="booking_schema")
        assert_status_code(response, 200)
        body = response.json()
        assert "bookingid" in body
""",

    "web": """\
Imports:
    import pytest
    from pages.web.<page_module> import <PageClass>

Marker: @pytest.mark.web

Fixtures:
    page          — Playwright Page, injected by pytest-playwright
    logged_in_page — authenticated page (defined locally in each test file, falls back to session_authed_page)

Step tracking (automatic — do NOT import or call step() manually):
    Page object action methods are decorated with @step_method("description").
    Every call to a page object method is automatically recorded as a step.
    Steps appear in the HTML report and ReportPortal without any extra code in tests.

Pattern:
    @pytest.fixture(scope="function")
    def logged_in_page(page, session_authed_page):
        if session_authed_page is not None:
            return session_authed_page
        lp = LoginPage(page)
        lp.navigate_to_login()
        lp.login("Admin", "admin123")
        assert lp.is_on_dashboard()
        return page

    @pytest.mark.web
    def test_something(logged_in_page):
        po = SomePage(logged_in_page)
        po.navigate_to_list()        # recorded as step automatically
        po.search_by_name("Alice")   # recorded as step automatically
        assert po.get_record_count_text() != ""

Example test function:
    @pytest.mark.web
    def test_user_list_loads_on_navigation(logged_in_page):
        admin = AdminUsersPage(logged_in_page)
        admin.navigate_to_list()
        assert admin.is_on_list_page()
""",

    "mobile": """\
Imports:
    import pytest
    from pages.mobile.<screen_module> import <ScreenClass>

Marker: @pytest.mark.mobile

Fixture: appium_driver (injected by conftest)

Pattern:
    screen = BookingScreen(appium_driver)
    screen.fill_firstname("John")
    screen.tap_submit()
    assert screen.get_confirmation_text() == "Booking confirmed"

Example test function:
    @pytest.mark.mobile
    def test_booking_screen_submits_successfully(appium_driver):
        screen = BookingScreen(appium_driver)
        screen.fill_firstname("John")
        screen.tap_submit()
        assert "confirmed" in screen.get_confirmation_text().lower()
""",

    "security": """\
Imports:
    import pytest
    import requests
    from pages.web.login_page import LoginPage  # only for web security tests

Markers: @pytest.mark.security  PLUS  @pytest.mark.api (API layer) or @pytest.mark.web (browser layer)

--- API security patterns ---
Fixtures: product_api_client (authenticated), raw requests for unauthenticated calls

    # Auth bypass
    resp = requests.get(f"{_API_BASE}/resource")
    assert resp.status_code == 401

    # SQL injection
    resp = product_api_client.get("/resource", params={"q": "' OR '1'='1"})
    assert resp.status_code != 500
    assert "sql" not in resp.text.lower()

    # IDOR
    resp = requests.get(f"{_API_BASE}/resource/OTHER_ID")
    assert resp.status_code in (401, 403)

    # Response content-type
    resp = product_api_client.get("/resource")
    assert "application/json" in resp.headers.get("Content-Type", "")

    # Security headers
    assert resp.headers.get("X-Content-Type-Options", "").lower() == "nosniff"

Example API test:
    @pytest.mark.api
    @pytest.mark.security
    def test_OH_SEC_001_unauthenticated_request_returns_401():
        resp = requests.get(f"{_API_BASE}/admin/users")
        assert resp.status_code == 401

--- Web security patterns (Playwright) ---
Fixtures: page (pytest-playwright)

    # XSS non-execution
    dialog_fired = []
    page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
    page.locator("input[name='field']").fill("<script>window.__xss=true</script>")
    assert not dialog_fired
    assert not page.evaluate("() => window.__xss === true")

    # Redirect to login when unauthenticated
    page.goto(f"{_BASE}/protected-url", wait_until="networkidle")
    assert "/login" in page.url

    # HttpOnly cookie check
    cookies = page.context.cookies()
    for c in [c for c in cookies if "session" in c["name"].lower()]:
        assert c.get("httpOnly"), f"Cookie {c['name']} missing HttpOnly"

Example web test:
    @pytest.mark.web
    @pytest.mark.security
    def test_OH_SEC_008_xss_in_username_does_not_execute(page):
        dialog_fired = []
        page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
        lp = LoginPage(page)
        lp.navigate_to_login()
        lp.login("<script>window.__xss=true</script>", "pass")
        assert not dialog_fired
        assert not page.evaluate("() => window.__xss === true")
""",

    "a11y": """\
Imports:
    import pytest
    from pages.web.<page_module> import <PageClass>

Markers: @pytest.mark.web  @pytest.mark.a11y  (both always present)

Fixtures: page (pytest-playwright)

Patterns:
    # Labelled inputs
    inp = page.get_by_label("field name", exact=False)
    assert inp.count() >= 1

    # Heading present
    assert page.get_by_role("heading").count() >= 1

    # Keyboard navigation
    page.keyboard.press("Tab")
    tag = page.evaluate("document.activeElement.tagName")
    assert tag in ("INPUT", "BUTTON", "A", "SELECT", "TEXTAREA")

    # Image alt text
    images = page.locator("img")
    for i in range(images.count()):
        assert images.nth(i).get_attribute("alt") is not None

    # Visible error messages
    error = page.locator(".error, [class*='alert']").first
    assert error.is_visible()

    # Link/button text
    for i in range(page.locator("button").count()):
        btn = page.locator("button").nth(i)
        text = (btn.inner_text() or "").strip()
        aria = btn.get_attribute("aria-label") or ""
        assert text or aria

Example test:
    @pytest.mark.web
    @pytest.mark.a11y
    def test_OH_A11Y_001_login_inputs_have_labels(page):
        LoginPage(page).navigate_to_login()
        for field in ("username", "password"):
            assert page.get_by_label(field, exact=False).count() >= 1
""",
}


class TestScriptGenSkill:
    def __init__(self, ai_client: AIClient, kb_loader: KnowledgeBaseLoader = None):
        self.ai_client = ai_client
        self.kb_loader = kb_loader or KnowledgeBaseLoader()

    def generate_script(
        self,
        test_case_doc: str,
        domain: str,
        feature_name: str,
        tc_prefix: str = "",
        test_type_instruction: str = "",
    ) -> str:
        """Generate a runnable pytest file from a test case markdown document."""
        _fallback = "web" if domain == "a11y" else "api"
        conventions = _CONVENTIONS.get(domain, _CONVENTIONS[_fallback])
        tc_prefix_hint = (
            f" If no ID is present and tc_prefix='{tc_prefix}', infer IDs from order in document."
            if tc_prefix else ""
        )
        prompt = TEST_SCRIPT_GEN_PROMPT.format(
            domain=domain,
            feature_name=feature_name,
            test_case_doc=test_case_doc,
            conventions=conventions,
            tc_prefix_hint=tc_prefix_hint,
            test_type_instruction=test_type_instruction,
        )
        code = self.ai_client.generate(prompt, max_tokens=3000, temperature=0.1).strip()
        return _clean_code_output(code)

    def generate_script_from_file(
        self,
        doc_path: Path,
        domain: str,
        feature_name: str,
        tc_prefix: str = "",
    ) -> str:
        """Convenience: read doc from file then generate script."""
        test_case_doc = doc_path.read_text(encoding="utf-8")
        return self.generate_script(test_case_doc, domain, feature_name, tc_prefix=tc_prefix)


def _clean_code_output(text: str) -> str:
    """Strip markdown fences if the model wrapped the output anyway."""
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line
        lines = lines[1:]
        # drop closing fence if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
