"""ScriptReviewAgent — post-generation quality gate for pytest scripts.

Runs two passes on every test function:

Static pass (AST + regex, no LLM — flags but never auto-fixes):
  - Hardcoded URL or credential strings
  - time.sleep() usage (use wait utilities instead)
  - POM instantiated without base_url on web/mobile domains
  - Duplicate test function names
  - Syntax errors in the generated file

LLM-rewrite pass (targeted per-function prompt):
  - Bare assertions: assert True, assert x is not None, assert bare_name
  - Missing assertions (test function has no assert at all)
  - API test makes an HTTP call but no status-code assertion
  - Missing @pytest.mark.<domain> decorator
  - Exact equality on AI-output fields (confidence, category, prediction, etc.)
    — should use threshold (>= 0.7) or membership (in (...)) checks

Best-effort: never raises; failures are logged and skipped.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from ai.agents.base_agent import BaseAgent

# ── regex patterns ─────────────────────────────────────────────────────────────
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_CRED_ASSIGN_RE = re.compile(
    r'(password|passwd|token|secret|api_key|auth_key|access_key)\s*=\s*["\']',
    re.IGNORECASE,
)
_SLEEP_RE = re.compile(r"\btime\.sleep\s*\(")
_STATUS_CODE_RE = re.compile(r"status_code|assert_status_code", re.IGNORECASE)
_AI_FIELD_RE = re.compile(
    r"^(confidence|score|prediction|ai_result|classification|category|suggestion|analysis|label|intent)$",
    re.IGNORECASE,
)

# ── issue types that the LLM can fix ──────────────────────────────────────────
_LLM_FIXABLE: frozenset[str] = frozenset({
    "missing_assertion",
    "weak_assertion",
    "missing_status_assert",
    "missing_marker",
    "ai_exact_match",
})

# ── human-readable issue descriptions (for LLM prompt context) ───────────────
_ISSUE_LABELS: dict[str, str] = {
    "missing_assertion": "test function has no assert statements",
    "weak_assertion": "assertion too weak (assert True / assert x is not None / bare assert name)",
    "missing_status_assert": "API/security test makes HTTP call but has no status-code assertion",
    "missing_marker": "missing @pytest.mark.<domain> decorator",
    "ai_exact_match": "exact string equality on AI-generated output field (non-deterministic)",
    "hardcoded_url": "hardcoded URL string — use config fixture instead",
    "hardcoded_credential": "hardcoded credential literal — use credentials fixture",
    "time_sleep": "time.sleep() usage — use wait_for() from utils.wait or page.wait_for_timeout()",
    "pom_missing_base_url": "page object instantiated without base_url argument",
    "duplicate_test_name": "duplicate test function name in same file",
    "syntax_error": "syntax error in generated script",
}

_REWRITE_PROMPT = """\
A pytest test function has quality issues that need fixing.
Rewrite it to meet world-class test automation standards.

Domain: {domain}
Issues to fix: {issues_summary}

Knowledge Base context (use for domain-specific field names and expected values):
{kb_context}

Original function:
{fn_source}

Rewrite rules — apply ALL that are relevant:

ASSERTIONS:
- Never use `assert True` or `assert False` — replace with a meaningful condition.
- Never use `assert x is not None` alone — assert a type, field value, or count instead.
- Never use bare `assert variable` — add a comparison or method call.
- API tests: always assert BOTH status code AND at least one body field.
  Prefer: `assert_status_code(response, 200)` + `assert "field" in body`.
- Web tests: call POM getter methods for assertions; do not call page.locator() in the test body.

AI-BASED SYSTEM OUTPUTS (non-deterministic):
- For fields like confidence_score, prediction, category, label, intent, analysis:
  * Prefer utils.ai_assertions helpers over raw comparisons:
      from utils.ai_assertions import assert_confidence_above, assert_category_in, SoftAssertions
      from utils.constants import AI_CONFIDENCE_THRESHOLD
      assert_confidence_above(result["confidence_score"], AI_CONFIDENCE_THRESHOLD)
      assert_category_in(result["category"], {"positive", "negative", "edge"})
  * When checking multiple AI fields in one test, use SoftAssertions to collect all failures:
      with SoftAssertions() as soft:
          soft.assert_confidence_above(result["score"], AI_CONFIDENCE_THRESHOLD)
          soft.assert_category_in(result["label"], {"positive", "negative"})
  * Never use exact string equality: `assert result["category"] == "positive"` is wrong.

MARKERS:
- Add `@pytest.mark.{domain}` if it is missing. Import pytest at top of file if not present.

WAIT STRATEGIES:
- Replace `time.sleep(N)` with `page.wait_for_timeout(N * 1000)` for web, or
  `wait_for(lambda: condition, timeout=30)` from `utils.wait` for API/background waits.

TEST DATA:
- NEVER hardcode URLs or credentials — use fixtures (e.g. orangehrm_base_url, rb_api_base,
  orangehrm_credentials). If the hardcoded value is inside the function, replace it with
  the appropriate fixture parameter.

Return ONLY the rewritten Python function(s) with their decorators.
Output must start with `@` (decorator) or `def`.
No markdown fences. No explanation. No preamble.
"""


class ScriptReviewAgent(BaseAgent):
    """
    Validates a generated pytest script and rewrites functions with quality issues.

    run() accepts:
      script_path: Path  — the .py file to review and optionally fix
      fix: bool          — if True, rewrite failing functions in-place (default True)
      kb_context: str    — pre-built KB context string for rewrite prompts
      domain: str        — overrides ctx.domain when called directly

    Returns a dict with keys:
      issues: list[dict]  — {fn_name, type, description} per issue
      fixed:  list[str]   — function names that were rewritten
      script_path: Path
    """
    name = "script_review"

    def run(
        self,
        *,
        script_path: Path,
        fix: bool = True,
        kb_context: str = "",
        domain: str = "",
    ) -> dict:
        script_path = Path(script_path)
        if not script_path.exists():
            return {"issues": [], "fixed": [], "script_path": script_path}

        source = script_path.read_text(encoding="utf-8")
        effective_domain = domain or self.ctx.domain

        issues, fn_info = self._audit(source, effective_domain)

        if not fix or not issues or not self.client:
            return {"issues": issues, "fixed": [], "script_path": script_path}

        fixed: list[str] = []
        new_source = source

        for fn_name, info in fn_info.items():
            fixable = [t for t in info["issues"] if t in _LLM_FIXABLE]
            if not fixable:
                continue
            rewritten = self._rewrite_fn(
                fn_name, info["source"], fixable, kb_context, effective_domain
            )
            if rewritten:
                new_source = new_source.replace(info["source"], rewritten, 1)
                fixed.append(fn_name)

        if fixed:
            try:
                ast.parse(new_source)
                script_path.write_text(new_source, encoding="utf-8")
                self._log.info(
                    "ScriptReview: rewrote %d function(s) in %s", len(fixed), script_path
                )
            except SyntaxError as exc:
                self._log.warning(
                    "ScriptReview: LLM rewrite introduced syntax error — discarding (%s)", exc
                )
                fixed = []

        return {"issues": issues, "fixed": fixed, "script_path": script_path}

    # ── audit ─────────────────────────────────────────────────────────────────

    def _audit(
        self, source: str, domain: str
    ) -> tuple[list[dict], dict[str, dict]]:
        """
        Returns (issues, fn_info).
        fn_info maps fn_name → {source: str, issues: list[str]}.
        """
        issues: list[dict] = []
        fn_info: dict[str, dict] = {}

        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            issues.append({
                "fn_name": "<module>",
                "type": "syntax_error",
                "description": f"Syntax error at line {exc.lineno}: {exc.msg}",
            })
            return issues, fn_info

        # Duplicate test function names
        all_test_names = [
            n.name for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        seen: dict[str, int] = {}
        for name in all_test_names:
            seen[name] = seen.get(name, 0) + 1
        for name, count in seen.items():
            if count > 1:
                issues.append({
                    "fn_name": name,
                    "type": "duplicate_test_name",
                    "description": f"'{name}' defined {count} times in same file",
                })

        expected_marker = _domain_marker(domain)
        lines = source.splitlines(keepends=True)

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("test_"):
                continue

            fn_src = _extract_fn_source(lines, node)
            fn_issues: list[str] = []

            # 1. Hardcoded URL
            for child in ast.walk(node):
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    if _URL_RE.search(child.value):
                        issues.append({
                            "fn_name": node.name,
                            "type": "hardcoded_url",
                            "description": f"Hardcoded URL '{child.value[:60]}' — use config fixture",
                        })
                        fn_issues.append("hardcoded_url")
                        break

            # 2. Hardcoded credential assignment in function body
            if _CRED_ASSIGN_RE.search(fn_src):
                issues.append({
                    "fn_name": node.name,
                    "type": "hardcoded_credential",
                    "description": "Hardcoded credential literal — use credentials fixture",
                })
                fn_issues.append("hardcoded_credential")

            # 3. time.sleep()
            if _SLEEP_RE.search(fn_src):
                issues.append({
                    "fn_name": node.name,
                    "type": "time_sleep",
                    "description": "time.sleep() — use wait_for() from utils.wait or page.wait_for_timeout()",
                })
                fn_issues.append("time_sleep")

            # 4. Missing domain marker
            if expected_marker and expected_marker not in _get_markers(node):
                issues.append({
                    "fn_name": node.name,
                    "type": "missing_marker",
                    "description": f"Missing @pytest.mark.{expected_marker}",
                })
                fn_issues.append("missing_marker")

            # 5. Assertion quality
            asserts = _collect_asserts(node)
            if not asserts:
                issues.append({
                    "fn_name": node.name,
                    "type": "missing_assertion",
                    "description": "No assert statements in test function",
                })
                fn_issues.append("missing_assertion")
            else:
                weak_descs = _detect_weak_asserts(asserts)
                for desc in weak_descs:
                    issues.append({
                        "fn_name": node.name,
                        "type": "weak_assertion",
                        "description": desc,
                    })
                if weak_descs:
                    fn_issues.append("weak_assertion")

            # 6. API/security: HTTP call without status-code assertion
            if domain in ("api", "security") and asserts:
                if _has_http_call(node) and not _STATUS_CODE_RE.search(fn_src):
                    issues.append({
                        "fn_name": node.name,
                        "type": "missing_status_assert",
                        "description": "HTTP call made but no status-code assertion found",
                    })
                    fn_issues.append("missing_status_assert")

            # 7. Web/mobile: POM missing base_url
            if domain in ("web", "a11y", "mobile"):
                pom_issue = _check_pom_base_url(node)
                if pom_issue:
                    issues.append({
                        "fn_name": node.name,
                        "type": "pom_missing_base_url",
                        "description": pom_issue,
                    })
                    fn_issues.append("pom_missing_base_url")

            # 8. AI-based exact equality assertion
            ai_issues = _check_ai_exact_match(node)
            for ai_desc in ai_issues:
                issues.append({
                    "fn_name": node.name,
                    "type": "ai_exact_match",
                    "description": ai_desc,
                })
            if ai_issues:
                fn_issues.append("ai_exact_match")

            if fn_src and fn_issues:
                fn_info[node.name] = {"source": fn_src, "issues": fn_issues}

        return issues, fn_info

    # ── rewriting ─────────────────────────────────────────────────────────────

    def _rewrite_fn(
        self,
        fn_name: str,
        fn_src: str,
        issue_types: list[str],
        kb_context: str,
        domain: str,
    ) -> str | None:
        if not self.client:
            return None
        issues_summary = "; ".join(_ISSUE_LABELS.get(t, t) for t in issue_types)
        prompt = _REWRITE_PROMPT.format(
            domain=domain,
            issues_summary=issues_summary,
            kb_context=kb_context or "(No KB context — use framework conventions only)",
            fn_source=fn_src.strip(),
        )
        try:
            result = self.client.generate(prompt, max_tokens=1200, temperature=0.1).strip()
            # Strip accidental markdown fences
            if result.startswith("```"):
                lines = result.splitlines()
                end = -1 if lines[-1].strip() == "```" else len(lines)
                result = "\n".join(lines[1:end]).strip()
            # Sanity check: must contain the function name and look like Python
            if fn_name in result and result.lstrip().startswith(("@", "def ")):
                return result
            self._log.warning(
                "ScriptReview: rewrite for %s doesn't look like a function — skipping", fn_name
            )
            return None
        except Exception as exc:
            self._log.warning("ScriptReview: rewrite failed for %s: %s", fn_name, exc)
            return None


# ── module-level helpers (pure functions, no state) ───────────────────────────

def _domain_marker(domain: str) -> str:
    return {"api": "api", "web": "web", "mobile": "mobile",
            "security": "security", "a11y": "web"}.get(domain, "")


def _extract_fn_source(lines: list[str], node: ast.FunctionDef) -> str:
    """Full function source including decorators (decorator_list lineno < def lineno)."""
    start = node.lineno - 1  # 0-indexed
    if node.decorator_list:
        start = min(d.lineno for d in node.decorator_list) - 1
    end = node.end_lineno  # 1-indexed inclusive
    return "".join(lines[start:end])


def _get_markers(node: ast.FunctionDef) -> list[str]:
    """Extract @pytest.mark.X names from function decorators."""
    markers: list[str] = []
    for dec in node.decorator_list:
        # @pytest.mark.web
        if (
            isinstance(dec, ast.Attribute)
            and isinstance(dec.value, ast.Attribute)
            and isinstance(dec.value.value, ast.Name)
            and dec.value.value.id == "pytest"
            and dec.value.attr == "mark"
        ):
            markers.append(dec.attr)
        # @pytest.mark.xfail(...), @pytest.mark.parametrize(...)
        elif (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and isinstance(dec.func.value, ast.Attribute)
            and isinstance(dec.func.value.value, ast.Name)
            and dec.func.value.value.id == "pytest"
            and dec.func.value.attr == "mark"
        ):
            markers.append(dec.func.attr)
    return markers


def _collect_asserts(fn: ast.FunctionDef) -> list[ast.Assert]:
    """Collect assert statements, not descending into nested function defs."""
    result: list[ast.Assert] = []

    def _walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(child, ast.Assert):
                result.append(child)
            _walk(child)

    _walk(fn)
    return result


def _detect_weak_asserts(asserts: list[ast.Assert]) -> list[str]:
    """Return human-readable descriptions of weak assertion patterns."""
    weak: list[str] = []
    for a in asserts:
        test = a.test
        # assert True
        if isinstance(test, ast.Constant) and test.value is True:
            weak.append("assert True — always passes, not a real assertion")
        # assert False
        elif isinstance(test, ast.Constant) and test.value is False:
            weak.append("assert False — use pytest.fail('reason') instead")
        # assert x is not None
        elif (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.IsNot)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value is None
        ):
            try:
                left_str = ast.unparse(test.left)
            except Exception:
                left_str = "value"
            weak.append(
                f"assert {left_str} is not None — assert a meaningful property or type instead"
            )
        # assert bare_variable (not a call, not a comparison)
        elif isinstance(test, ast.Name):
            weak.append(
                f"assert {test.id} — asserts truthy only; add specific field or status check"
            )
    return weak


def _has_http_call(fn: ast.FunctionDef) -> bool:
    """Return True if any call in the function looks like an HTTP method call."""
    _http_methods = frozenset({"get", "post", "put", "patch", "delete", "request"})
    for child in ast.walk(fn):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
            if child.func.attr in _http_methods:
                return True
    return False


def _check_pom_base_url(fn: ast.FunctionDef) -> str:
    """Detect POM(page) instantiation without a base_url argument."""
    for child in ast.walk(fn):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if not (
            isinstance(func, ast.Name)
            and func.id[0].isupper()
            and func.id.endswith("Page")
        ):
            continue
        has_base_url = len(child.args) >= 2 or any(
            kw.arg == "base_url" for kw in child.keywords
        )
        if not has_base_url:
            return (
                f"{func.id}() called with only {len(child.args)} positional arg(s) — "
                f"use {func.id}(page, base_url_fixture)"
            )
    return ""


def _check_ai_exact_match(fn: ast.FunctionDef) -> list[str]:
    """
    Detect exact string equality assertions on AI-output fields.
    Pattern: assert result["confidence_score"] == "some_string"
    """
    found: list[str] = []
    for child in ast.walk(fn):
        if not isinstance(child, ast.Assert):
            continue
        test = child.test
        if not (
            isinstance(test, ast.Compare)
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Eq)
            and len(test.comparators) == 1
        ):
            continue
        left = test.left
        rhs = test.comparators[0]
        # left side: dict subscript with an AI-sounding field name
        if not isinstance(left, ast.Subscript):
            continue
        key = left.slice
        if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
            continue
        if not _AI_FIELD_RE.match(key.value):
            continue
        # right side: a constant string (exact match)
        if isinstance(rhs, ast.Constant) and isinstance(rhs.value, str):
            found.append(
                f'assert result["{key.value}"] == "{rhs.value}" — '
                f"AI output is non-deterministic; use threshold (>= N) or `in (...)` check"
            )
    return found
