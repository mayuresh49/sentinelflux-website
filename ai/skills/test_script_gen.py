"""Generate runnable pytest scripts from test case documentation."""

import re
from pathlib import Path

from ai.clients.base_client import AIClient
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader
from ai.prompts.prompt_templates import TEST_SCRIPT_GEN_PROMPT

_CONVENTIONS: dict[str, str] = {
    "api": """\
Imports:
    import pytest
    import requests  # only for unauthenticated raw calls
    from utils.assertions import assert_status_code

Marker: @pytest.mark.api

FIXTURE RULES — read before choosing a fixture:
  {product}_client           — use for all AUTHENTICATED product API calls (e.g. orangehrm_client, rb_api_client)
                               calls: resp = {product}_client.get("/resource")  resp = {product}_client.post("/resource", json={{}})
  {product}_api_base_url     — use for UNAUTHENTICATED raw calls (testing 401/403 enforcement)
                               calls: requests.get(f"{{product_api_base_url}}/resource")
  {product}_credentials      — use when credentials are required as test INPUT (e.g. testing login endpoint directly)
                               value: {{"username": ..., "password": ...}} — loaded from config, never hardcoded
  rest_client / graphql_client — ONLY for framework-level non-product tests (e.g. Restful Booker generic REST)

NEVER write an authenticate() helper with hardcoded strings. NEVER pass literal username/password strings.

GraphQL fixture — graphql_client:
    response = graphql_client.execute(query_name="countries_list", variables={"filter": {"code": {"eq": "AU"}}})

Assertions:
    assert_status_code(response, 200)
    body = response.json()
    assert "bookingid" in body
    assert body["booking"]["firstname"] == "John"

Example — authenticated product call:
    @pytest.mark.api
    def test_OH_API_001_list_users_returns_200(orangehrm_client):
        resp = orangehrm_client.get("/admin/users")
        assert_status_code(resp, 200)
        assert isinstance(resp.json().get("data"), list)

Example — unauthenticated enforcement:
    @pytest.mark.api
    def test_OH_API_003_list_users_without_auth_returns_401(orangehrm_api_base_url):
        resp = requests.get(f"{orangehrm_api_base_url}/admin/users")
        assert resp.status_code == 401

Example — credentials as test input:
    @pytest.mark.api
    def test_OH_API_029_valid_login_returns_200(orangehrm_api_base_url, orangehrm_credentials):
        resp = requests.post(f"{orangehrm_api_base_url}/auth/login",
                             json={{"username": orangehrm_credentials["username"],
                                    "password": orangehrm_credentials["password"]}})
        assert resp.status_code in (200, 302)
""",

    "web": """\
Imports:
    import pytest
    from pages.web.<page_module> import <PageClass>
    from pages.web.login_page import LoginPage

Marker: @pytest.mark.web

Fixtures (all from conftest — never hardcode URLs or credentials):
    page                     — Playwright Page, injected by pytest-playwright
    {product}_base_url       — web base URL from config/env_{env}.yaml, e.g. orangehrm_base_url, rb_web_base
    {product}_credentials    — {"username": ..., "password": ...} from config, e.g. orangehrm_credentials, rb_web_credentials
    session_authed_page      — optional shared authenticated page (session-scoped)
    logged_in_page           — defined locally in each test file (see pattern below)

Step tracking (automatic — do NOT import or call step() manually):
    Page object action methods are decorated with @step_method("description").
    Every call to a page object method is automatically recorded as a step.
    Steps appear in the HTML report and ReportPortal without any extra code in tests.

IMPORTANT — constructor signatures:
    All page objects require base_url as the second argument: PageClass(page, base_url)
    Never instantiate a page object without passing base_url from the fixture.

Pattern:
    @pytest.fixture(scope="function")
    def logged_in_page(page, session_authed_page, {product}_base_url, {product}_credentials):
        if session_authed_page is not None:
            return session_authed_page
        lp = LoginPage(page, {product}_base_url)
        lp.navigate_to_login()
        lp.login({product}_credentials["username"], {product}_credentials["password"])
        assert lp.is_on_dashboard()
        return page

    @pytest.mark.web
    def test_something(logged_in_page, {product}_base_url):
        po = SomePage(logged_in_page, {product}_base_url)
        po.navigate_to_list()        # recorded as step automatically
        po.search_by_name("Alice")   # recorded as step automatically
        assert po.get_record_count_text() != ""

Example test function (OrangeHRM):
    @pytest.fixture(scope="function")
    def logged_in_page(page, session_authed_page, orangehrm_base_url, orangehrm_credentials):
        if session_authed_page is not None:
            return session_authed_page
        lp = LoginPage(page, orangehrm_base_url)
        lp.navigate_to_login()
        lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
        assert lp.is_on_dashboard()
        return page

    @pytest.mark.web
    def test_user_list_loads_on_navigation(logged_in_page, orangehrm_base_url):
        admin = AdminUsersPage(logged_in_page, orangehrm_base_url)
        admin.navigate_to_list()
        assert admin.is_on_list_page()
""",

    "mobile": """\
Imports:
    import pytest
    from pages.mobile.<screen_module> import <ScreenClass>

Marker: @pytest.mark.mobile

Fixture: appium_driver (injected by conftest)

CRITICAL — Mobile POM constructors signature: __init__(self, driver, platform="android")
  - NEVER pass base_url or any URL to a mobile POM constructor.
  - NEVER add {product}_base_url as a fixture parameter in mobile tests.
  - Mobile navigation is driven by the Appium driver, not URLs.

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

IMPORTANT — never hardcode URLs or credentials. Use fixtures:
    {product}_api_base_url  — API base URL from config, e.g. orangehrm_api_base_url, rb_api_base
    {product}_base_url      — web base URL from config, e.g. orangehrm_base_url, rb_web_base
    {product}_credentials   — {"username": ..., "password": ...} from config

--- API security patterns ---
Fixtures: {product}_api_client (authenticated), {product}_api_base_url for raw unauthenticated requests

    # Auth bypass — use fixture, not a hardcoded constant
    def test_unauthenticated_request_returns_401({product}_api_base_url):
        resp = requests.get(f"{{product}_api_base_url}/resource")
        assert resp.status_code == 401

    # SQL injection
    resp = {product}_api_client.get("/resource", params={"q": "' OR '1'='1"})
    assert resp.status_code != 500
    assert "sql" not in resp.text.lower()

    # IDOR
    def test_idor_rejected({product}_api_base_url):
        resp = requests.get(f"{{product}_api_base_url}/resource/OTHER_ID")
        assert resp.status_code in (401, 403)

    # Response content-type
    resp = {product}_api_client.get("/resource")
    assert "application/json" in resp.headers.get("Content-Type", "")

    # Security headers
    assert resp.headers.get("X-Content-Type-Options", "").lower() == "nosniff"

Example API test (OrangeHRM):
    @pytest.mark.api
    @pytest.mark.security
    def test_OH_SEC_001_unauthenticated_request_returns_401(orangehrm_api_base_url):
        resp = requests.get(f"{orangehrm_api_base_url}/admin/users")
        assert resp.status_code == 401

--- Web security patterns (Playwright) ---
Fixtures: page (pytest-playwright), {product}_base_url, {product}_credentials

    # XSS non-execution
    def test_xss_does_not_execute(page):
        dialog_fired = []
        page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
        page.locator("input[name='field']").fill("<script>window.__xss=true</script>")
        assert not dialog_fired
        assert not page.evaluate("() => window.__xss === true")

    # Redirect to login when unauthenticated — use fixture, not hardcoded URL
    def test_protected_url_redirects_to_login(page, {product}_base_url):
        page.goto(f"{{product}_base_url}/protected-url", wait_until="networkidle")
        assert "/login" in page.url

    # HttpOnly cookie check
    cookies = page.context.cookies()
    for c in [c for c in cookies if "session" in c["name"].lower()]:
        assert c.get("httpOnly"), f"Cookie {c['name']} missing HttpOnly"

Example web test (OrangeHRM):
    @pytest.mark.web
    @pytest.mark.security
    def test_OH_SEC_008_xss_in_username_does_not_execute(page, orangehrm_base_url):
        dialog_fired = []
        page.on("dialog", lambda d: (dialog_fired.append(d.message), d.dismiss()))
        lp = LoginPage(page, orangehrm_base_url)
        lp.navigate_to_login()
        lp.login("<script>window.__xss=true</script>", "pass")
        assert not dialog_fired
        assert not page.evaluate("() => window.__xss === true")

    @pytest.mark.web
    @pytest.mark.security
    def test_OH_SEC_009_dashboard_without_auth_redirects(page, orangehrm_base_url):
        page.goto(f"{orangehrm_base_url}/web/index.php/dashboard/index", wait_until="networkidle")
        assert "/auth/login" in page.url
""",

    "a11y": """\
Imports:
    import pytest
    from pages.web.<page_module> import <PageClass>
    from pages.web.login_page import LoginPage

Markers: @pytest.mark.web  @pytest.mark.a11y  (both always present)

Fixtures (never hardcode URLs or credentials):
    page                  — Playwright Page, injected by pytest-playwright
    {product}_base_url    — web base URL from config, e.g. orangehrm_base_url, rb_web_base
    {product}_credentials — {"username": ..., "password": ...} from config

IMPORTANT — page objects require base_url: LoginPage(page, {product}_base_url)

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

Example test (OrangeHRM):
    @pytest.mark.web
    @pytest.mark.a11y
    def test_OH_A11Y_001_login_inputs_have_labels(page, orangehrm_base_url):
        LoginPage(page, orangehrm_base_url).navigate_to_login()
        for field in ("Username", "Password"):
            assert page.get_by_placeholder(field).count() >= 1
""",
}


def _build_api_constraints(kb_loader: KnowledgeBaseLoader, feature_name: str) -> str:
    """Build an endpoint allowlist + response code constraints for API script gen.
    Prevents the LLM from asserting undocumented paths or status codes.
    """
    try:
        specs = kb_loader.load_api_specs()
        endpoints = specs.get("rest_api", {}).get("endpoints", [])
        base_url = specs.get("rest_api", {}).get("base_url", "")
        if not endpoints:
            return ""
        if feature_name:
            fn_lower = feature_name.lower().replace("_", " ")
            fn_prefix = feature_name.lower().split("_")[0]
            relevant = [
                e for e in endpoints
                if fn_lower in e.get("name", "").lower().replace("_", " ")
                or fn_prefix in e.get("path", "").lower()
                or any(feature_name.lower() in a.lower() for a in e.get("feature_aliases", []))
            ] or endpoints  # fallback to all if no feature match
        else:
            relevant = endpoints

        lines = [
            "--- API CONSTRAINTS (authoritative — do not deviate) ---",
            f"Base URL: use the {{product}}_api_base_url fixture (do NOT hardcode '{base_url}')",
            "Allowed endpoints and permitted response codes:",
        ]
        for e in relevant:
            lines.append(f"  {e['method']} {e['path']}")
            codes = e.get("response_codes")
            if codes:
                lines.append(f"    permitted status codes: {codes}")
        return "\n".join(lines)
    except Exception:
        return ""


def _discover_page_objects(output_base: Path | None, domain: str) -> str:
    """
    Scan the product's pages directory and return a catalog of importable page classes.
    Provides the LLM with exact import paths so it cannot hallucinate class names.
    """
    from utils.paths import ROOT

    page_domain = "web" if domain in ("web", "a11y", "security") else domain
    if page_domain not in ("web", "mobile"):
        return ""

    search_dirs = []
    if output_base:
        search_dirs.append(output_base / "pages" / page_domain)
    search_dirs.append(ROOT / "pages" / page_domain)

    entries: list[str] = []
    for base in search_dirs:
        if not base.exists():
            continue
        for py_file in sorted(base.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            # Derive importable module path relative to ROOT
            try:
                rel = py_file.with_suffix("").relative_to(ROOT)
                module_path = ".".join(rel.parts)
            except ValueError:
                continue
            classes = re.findall(r"^class (\w+)", py_file.read_text(encoding="utf-8"), re.MULTILINE)
            for cls in classes:
                entries.append(f"  from {module_path} import {cls}")

    if not entries:
        return ""
    return (
        "Available page object imports — use ONLY these exact names, do NOT invent others:\n"
        + "\n".join(entries)
    )


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
        categories_instruction: str = "",
        output_base: Path | None = None,
        exploration_context: str = "",
    ) -> str:
        """Generate a runnable pytest file from a test case markdown document."""
        _fallback = "web" if domain == "a11y" else "api"
        conventions = _CONVENTIONS.get(domain, _CONVENTIONS[_fallback])
        tc_prefix_hint = (
            f" If no ID is present and tc_prefix='{tc_prefix}', infer IDs from order in document."
            if tc_prefix else ""
        )
        page_catalog = _discover_page_objects(output_base, domain)
        formatted_exploration = f"\n--- LIVE APPLICATION EXPLORATION CONTEXT ---\n{exploration_context}\n" if exploration_context else ""
        raw_constraints = _build_api_constraints(self.kb_loader, feature_name) if domain == "api" and self.kb_loader else ""
        formatted_constraints = f"\n{raw_constraints}\n" if raw_constraints else ""
        prompt = TEST_SCRIPT_GEN_PROMPT.format(
            domain=domain,
            feature_name=feature_name,
            test_case_doc=test_case_doc,
            conventions=conventions,
            tc_prefix_hint=tc_prefix_hint,
            test_type_instruction=test_type_instruction,
            categories_instruction=categories_instruction,
            page_catalog=page_catalog,
            exploration_context=formatted_exploration,
            api_constraints=formatted_constraints,
        )
        code = self.ai_client.generate(prompt, max_tokens=5000, temperature=0.1).strip()
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
