"""
Domain-specific registries for artifacts, prompts, failure hints, markers, and fixtures.

How to add a new domain (e.g. "graphql", "grpc", "desktop"):
  1. Add an entry to each dict below.
  2. Add a prompt template to ai/prompts/prompt_templates.py if generation is needed.
  3. No changes to BaseAgent or any existing agent class.

How to add a new DIMENSION (e.g. "browser", "auth_type"):
  - Pass it in AgentContext.extra at call time: ctx.extend(browser="firefox")
  - Retrieve inside any agent: self.ctx.get("browser", "chromium")
  - If the dimension changes registry behavior, add a new dict here and
    look it up via ctx.get() in the relevant agent method.
"""

# Artifact file names relative to reports/artifacts/<safe_test_nodeid>/
# Used by ResultAnalyzerAgent to read failure context per domain.
ARTIFACT_PATHS: dict[str, list[str]] = {
    "api":      ["api_calls.log"],
    "web":      ["screenshot_full_page.png", "console.log", "trace.zip"],
    "mobile":   ["screenshot.png", "logcat.txt"],
    "security": ["api_calls.log"],
    "graphql":  ["api_calls.log"],
    "a11y":     ["screenshot_full_page.png", "console.log"],
}

# Prompt template keys → maps to constant names in ai/prompts/prompt_templates.py.
# All script-generation domains use TEST_SCRIPT_GEN_PROMPT (domain-specific conventions
# are injected at call time via the 'conventions' argument).
PROMPT_KEYS: dict[str, str] = {
    "api":      "API_TEST_GENERATION_PROMPT",
    "web":      "TEST_SCRIPT_GEN_PROMPT",
    "mobile":   "TEST_SCRIPT_GEN_PROMPT",
    "security": "TEST_SCRIPT_GEN_PROMPT",
    "graphql":  "API_TEST_GENERATION_PROMPT",
    "a11y":     "TEST_SCRIPT_GEN_PROMPT",
}

# Failure analysis guidance injected into ResultAnalyzerAgent prompts per domain
FAILURE_HINTS: dict[str, str] = {
    "api": (
        "Focus on HTTP status codes, response schemas, auth errors, and timeout patterns "
        "in the API call log. Distinguish 5xx (infra) from 4xx (assertion) errors."
    ),
    "web": (
        "Focus on selector timeouts (locator failures), screenshot evidence of UI state, "
        "browser console errors, and network trace anomalies. "
        "Distinguish flaky animations/timing issues from genuine assertion failures."
    ),
    "mobile": (
        "Focus on element not found errors, Appium session drops, device-specific issues "
        "in logcat, and screen state from the screenshot."
    ),
    "security": (
        "Focus on unexpected 2xx responses where a 4xx was expected, missing auth headers, "
        "and injection payload reflections in response bodies."
    ),
    "graphql": (
        "Focus on GraphQL errors array in the response, auth failures (401/403), "
        "and schema violations in the API call log."
    ),
    "a11y": (
        "Focus on accessibility violations: missing labels, broken keyboard navigation, "
        "missing alt text, and ARIA role mismatches visible in the console log."
    ),
}

# pytest marker name used on generated test scripts per domain
DOMAIN_MARKERS: dict[str, str] = {
    "api":      "api",
    "web":      "web",
    "mobile":   "mobile",
    "security": "security",
    "graphql":  "api",
    "a11y":     "a11y",
}

# Default fixture names injected into generated test scripts per domain
DOMAIN_FIXTURES: dict[str, list[str]] = {
    "api":      ["rest_client"],
    "web":      ["page"],
    "mobile":   ["mobile_driver"],
    "security": ["rest_client"],
    "graphql":  ["graphql_client"],
    "a11y":     ["page"],
}

# Classification labels used by ResultAnalyzerAgent
FAILURE_CLASSIFICATIONS: list[str] = [
    "assertion",  # wrong expected value / product bug
    "infra",      # server down, network timeout, 5xx
    "flaky",      # intermittent, no clear cause
    "env",        # config, credentials, environment mismatch
    "locator",    # UI element not found (web/mobile only)
]
