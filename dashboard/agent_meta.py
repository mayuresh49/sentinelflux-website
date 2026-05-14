"""Static agent metadata: responsibilities, I/O, and configurable parameters."""

AGENT_META: dict = {
    "doc_gen": {
        "responsibility": "Reads the Knowledge Base (product YAML files + any increments) and generates a structured Markdown test case document covering all testable scenarios for a given feature and domain.",
        "inputs": ["KB YAML files", "Feature name", "Domain"],
        "outputs": ["products/<product>/docs/test_cases/<domain>/<feature>.md"],
        "config_params": [],
    },
    "script_gen": {
        "responsibility": "Takes a test case Markdown document and generates a fully working pytest script with correct fixtures, markers, imports, and domain-specific patterns (rest_client for API, page for web, etc.).",
        "inputs": ["Test case Markdown document", "Domain"],
        "outputs": ["products/<product>/tests/<domain>/test_<feature>.py"],
        "config_params": [],
    },
    "result_analyzer": {
        "responsibility": "Reads a pytest JSON report and classifies each failure using AI into one of five buckets: assertion (product bug), infra (server/network issue), flaky (intermittent), env (config/credentials mismatch), or locator (UI element not found). Reads domain-specific artifacts (logs, screenshots) for context.",
        "inputs": ["pytest-json-report JSON", "Failure artifacts (api_calls.log, console.log, screenshot)"],
        "outputs": ["Classified failures with confidence score and one-line fix suggestion per test"],
        "config_params": [],
    },
    "flaky_detector": {
        "responsibility": "Reads run_history.yaml and identifies tests with high failure rates (quarantine candidates) or long consecutive pass streaks (unquarantine candidates). Pure rule-based — no AI or network required.",
        "inputs": ["data/run_history.yaml"],
        "outputs": ["quarantine_candidates list", "unquarantine_candidates list"],
        "config_params": [
            {"name": "window", "type": "int", "default": 10, "description": "Number of recent runs to analyse"},
            {"name": "fail_threshold", "type": "float", "default": 0.3, "description": "Fail rate ≥ threshold → quarantine candidate"},
            {"name": "pass_streak", "type": "int", "default": 5, "description": "Consecutive passes ≥ streak → unquarantine candidate"},
        ],
    },
    "regression_guard": {
        "responsibility": "Compares the current pytest JSON report against a saved baseline report. Buckets changes into regressions (passed→failing), new_failures (not in baseline), fixed (failed→passing), and new_tests. No AI required.",
        "inputs": ["Current pytest-json-report JSON", "data/baseline_report.json"],
        "outputs": ["regressions list", "fixed list", "new_failures list", "new_tests list"],
        "config_params": [
            {"name": "save_as_baseline", "type": "bool", "default": False, "description": "Overwrite baseline with current run after comparison"},
        ],
    },
    "coverage_gap": {
        "responsibility": "Diffs KB test scenarios against existing test function names. For each scenario in the KB that has no matching test function, it suggests a snake_case test name and assigns a priority (high/medium/low).",
        "inputs": ["Knowledge Base YAML files", "Existing test .py files"],
        "outputs": ["Gap list with scenario description, suggested test name, and priority"],
        "config_params": [],
    },
    "locator_healer": {
        "responsibility": "When a UI selector fails to find an element, takes the element name, the failed selector, and a page HTML/accessibility snapshot, then uses AI to propose a stable replacement selector and up to 3 fallback alternatives. Prefers data-testid, aria-label, role over positional selectors.",
        "inputs": ["Element name", "Failed CSS/XPath selector", "Page HTML or accessibility snapshot"],
        "outputs": ["Updated locator entry: { primary, alternatives }"],
        "config_params": [],
    },
    "quarantine_manager": {
        "responsibility": "Manages the quarantine lifecycle via quarantine.yaml. Proposals from FlakyDetector are staged via propose() and require apply_pending() to activate. Active quarantined tests are marked xfail at pytest collection time. Separately records all run outcomes to run_history.yaml.",
        "inputs": ["Quarantine/unquarantine candidates", "Per-test run results"],
        "outputs": ["quarantine.yaml (active + pending)", "run_history.yaml"],
        "config_params": [
            {"name": "auto_apply", "type": "bool", "default": False, "description": "Skip human gate — immediately promote proposals to active quarantine"},
        ],
    },
    "sentinel_orchestrator": {
        "responsibility": "Post-suite coordinator. After a test run it sequences: ResultAnalyzer → FlakyDetector → RegressionGuard → CoverageGap → LocatorHealer. Each step is fault-tolerant. Writes ActivityLog entries per agent and routes human-gated actions to ApprovalManager. Returns a structured blockers list for the dashboard.",
        "inputs": ["pytest-json-report JSON", "Domain", "Product", "Optional: locator failures, baseline report"],
        "outputs": ["ActivityLog entries", "ApprovalManager requests", "Structured summary with blockers count"],
        "config_params": [
            {"name": "run_result_analyzer", "type": "bool", "default": True, "description": "Enable AI failure classification step"},
            {"name": "run_flaky_detector", "type": "bool", "default": True, "description": "Enable flaky detection + quarantine proposals"},
            {"name": "run_regression_guard", "type": "bool", "default": True, "description": "Enable regression comparison vs baseline"},
            {"name": "run_coverage_gap", "type": "bool", "default": True, "description": "Enable KB coverage gap analysis"},
            {"name": "run_locator_healer", "type": "bool", "default": True, "description": "Enable locator healing (web/mobile domains only)"},
        ],
    },
}
