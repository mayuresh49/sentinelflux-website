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
    from utils.assertions import assert_status_code

Marker: @pytest.mark.security

Fixtures: rest_client (for API-layer security tests)

Patterns:
    # Auth bypass
    response = requests.get(url, headers={})  # no token
    assert_status_code(response, 401)

    # SQL injection
    response = rest_client.post("create_booking", payload_name="sql_injection_payload")
    assert response.status_code in (400, 422)

    # IDOR
    response = rest_client.get("get_booking", path_params={"booking_id": other_user_booking_id})
    assert_status_code(response, 403)

Example test function:
    @pytest.mark.security
    def test_get_booking_without_auth_returns_401(rest_client):
        response = requests.get(f"{rest_client.base_url}/booking/1")
        assert_status_code(response, 401)
""",
}


class TestScriptGenSkill:
    def __init__(self, ai_client: AIClient, kb_loader: KnowledgeBaseLoader = None):
        self.ai_client = ai_client
        self.kb_loader = kb_loader or KnowledgeBaseLoader()

    def generate_script(self, test_case_doc: str, domain: str, feature_name: str) -> str:
        """Generate a runnable pytest file from a test case markdown document."""
        conventions = _CONVENTIONS.get(domain, _CONVENTIONS["api"])
        prompt = TEST_SCRIPT_GEN_PROMPT.format(
            domain=domain,
            feature_name=feature_name,
            test_case_doc=test_case_doc,
            conventions=conventions,
        )
        code = self.ai_client.generate(prompt, max_tokens=3000, temperature=0.1).strip()
        return _clean_code_output(code)

    def generate_script_from_file(self, doc_path: Path, domain: str, feature_name: str) -> str:
        """Convenience: read doc from file then generate script."""
        test_case_doc = doc_path.read_text(encoding="utf-8")
        return self.generate_script(test_case_doc, domain, feature_name)


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
