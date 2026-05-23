"""
AppExplorationSkill — Playwright-based discovery of real UI structure.

Eliminates locator hallucination by extracting actual DOM selectors from a running
application instead of letting the LLM guess from training-data knowledge.

Requires playwright (already a dependency via accessibility testing).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

_log = logging.getLogger(__name__)

# JS snippet that extracts all interactive inputs from the DOM
_JS_EXTRACT_INPUTS = """() => {
    const inputs = [];
    document.querySelectorAll('input:not([type=hidden]):not([type=submit]), select, textarea').forEach(el => {
        let label = '';
        if (el.id) {
            const lbl = document.querySelector('label[for="' + el.id + '"]');
            if (lbl) label = lbl.innerText.trim().replace('*', '').trim();
        }
        if (!label) {
            const grp = el.closest('.oxd-input-group, .oxd-form-row, .form-group, [class*="field"]');
            if (grp) {
                const lbl = grp.querySelector('label, .oxd-label, .label');
                if (lbl) label = lbl.innerText.trim().replace('*', '').trim();
            }
        }
        inputs.push({
            tag: el.tagName.toLowerCase(),
            type: el.type || el.tagName.toLowerCase(),
            id: el.id || '',
            name: el.name || '',
            placeholder: el.placeholder || '',
            ariaLabel: el.getAttribute('aria-label') || '',
            dataTestId: el.getAttribute('data-testid') || '',
            required: el.required || el.getAttribute('aria-required') === 'true',
            label: label,
            options: el.tagName === 'SELECT'
                ? Array.from(el.options).map(o => o.value).filter(v => v)
                : [],
        });
    });
    return inputs;
}"""

_JS_EXTRACT_BUTTONS = """() => {
    const btns = [];
    const seen = new Set();
    document.querySelectorAll('button, [role="button"], input[type="submit"]').forEach(el => {
        if (!el.offsetParent) return;
        const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
        if (!text || text.length > 100 || seen.has(text)) return;
        seen.add(text);
        btns.push({
            tag: el.tagName.toLowerCase(),
            type: el.type || 'button',
            id: el.id || '',
            name: el.name || '',
            text: text,
            dataTestId: el.getAttribute('data-testid') || '',
            ariaLabel: el.getAttribute('aria-label') || '',
        });
    });
    return btns;
}"""

_JS_EXTRACT_NAV = """() => {
    const links = [];
    document.querySelectorAll('nav a, [role="navigation"] a, .oxd-main-menu a, .main-menu a').forEach(el => {
        const text = el.innerText.trim();
        const href = el.getAttribute('href') || '';
        if (text && href && !href.startsWith('javascript')) links.push({text, href});
    });
    return links.slice(0, 20);
}"""

_JS_EXTRACT_ERRORS = """() => {
    const errors = {};
    document.querySelectorAll(
        '.oxd-input-field-error-message, span.oxd-text--span.--required, .error-message, [class*="error-msg"], [role="alert"]'
    ).forEach(el => {
        const text = el.innerText.trim();
        if (!text || text.length > 150) return;
        const grp = el.closest('.oxd-input-group, .form-group, [class*="field"]');
        if (grp) {
            const inp = grp.querySelector('input, select, textarea');
            if (inp) {
                const key = inp.name || inp.id || inp.getAttribute('aria-label') || 'unknown';
                if (!errors[key]) errors[key] = text;
                return;
            }
        }
        errors['_msg_' + Object.keys(errors).length] = text;
    });
    return errors;
}"""


def _to_snake(name: str) -> str:
    s = re.sub(r"[^\w\s]", "", name.lower()).strip()
    s = re.sub(r"\s+", "_", s)
    return re.sub(r"_+", "_", s) or "element"


def _best_selector(attrs: dict) -> tuple[str, list[str]]:
    """Return (primary_selector, alternatives) ranked by stability."""
    candidates: list[str] = []

    tid = attrs.get("dataTestId", "").strip()
    if tid:
        candidates.append(f"[data-testid='{tid}']")

    el_id = attrs.get("id", "").strip()
    # Skip React auto-IDs like :r0: or numeric-only
    if el_id and not re.match(r"^[:\d]", el_id):
        candidates.append(f"#{el_id}")

    tag = attrs.get("tag", "input").lower()
    name = attrs.get("name", "").strip()
    if name and tag in ("input", "select", "textarea"):
        candidates.append(f"{tag}[name='{name}']")

    aria = attrs.get("ariaLabel", "").strip()
    if aria:
        candidates.append(f"[aria-label='{aria}']")

    ph = attrs.get("placeholder", "").strip()
    if ph and tag == "input":
        candidates.append(f"input[placeholder='{ph}']")

    text = attrs.get("text", "").strip()
    if text and tag in ("button", "a") and not candidates:
        candidates.append(f"button:has-text('{text[:50]}')")

    return (candidates[0], candidates[1:]) if candidates else ("", [])


def _url_to_slug(url: str) -> str:
    """Convert URL to a filesystem-safe slug for file naming."""
    path = re.sub(r"https?://[^/]+", "", url).strip("/")
    slug = re.sub(r"[^\w/]", "_", path).replace("/", "_")
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "page"


def _slug_to_class(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("_")) + "Page"


@dataclass
class DiscoveredField:
    name: str
    label: str
    field_type: str
    required: bool
    placeholder: str
    primary_selector: str
    alternative_selectors: list[str] = field(default_factory=list)
    validation_message: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class DiscoveredPage:
    url: str
    title: str
    fields: list[DiscoveredField] = field(default_factory=list)
    buttons: list[DiscoveredField] = field(default_factory=list)
    navigation: list[dict] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        def _f(f: DiscoveredField) -> dict:
            d = {
                "name": f.name,
                "label": f.label,
                "type": f.field_type,
                "required": f.required,
                "primary_selector": f.primary_selector,
                "alternative_selectors": f.alternative_selectors,
            }
            if f.placeholder:
                d["placeholder"] = f.placeholder
            if f.validation_message:
                d["validation_message"] = f.validation_message
            if f.options:
                d["options"] = f.options
            return d

        return {
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp,
            "headings": self.headings,
            "fields": [_f(f) for f in self.fields],
            "buttons": [_f(b) for b in self.buttons],
            "navigation": self.navigation,
        }

    def to_locator_json(self) -> dict:
        """Produce locators/{platform}/{page}.json-compatible dict."""
        result = {}
        for f in self.fields + self.buttons:
            result[f.name] = {
                "primary": f.primary_selector,
                "alternatives": f.alternative_selectors,
            }
        return result

    def to_exploration_context(self) -> str:
        """
        Format as a LIVE APPLICATION EXPLORATION CONTEXT block for prompt injection.
        The LLM is constrained to only reference elements listed here.
        """
        lines = [
            "=== LIVE APPLICATION EXPLORATION CONTEXT ===",
            "Verified against the actual running application — all selectors and field names below",
            "are confirmed to exist in the DOM. Do NOT reference any element not listed here.",
            "",
            f"Page Title: {self.title}",
            f"URL: {self.url}",
        ]

        if self.headings:
            lines.append(f"Page Headings: {' | '.join(self.headings)}")

        if self.fields:
            lines += ["", "Form Fields (DOM-verified):"]
            for f in self.fields:
                req_tag = " [REQUIRED]" if f.required else ""
                lines.append(f"  • {f.name}{req_tag}")
                lines.append(f"      label:    \"{f.label}\"")
                lines.append(f"      type:     {f.field_type}")
                lines.append(f"      selector: {f.primary_selector}")
                if f.alternative_selectors:
                    lines.append(f"      alt:      {', '.join(f.alternative_selectors[:2])}")
                if f.placeholder:
                    lines.append(f"      placeholder: \"{f.placeholder}\"")
                if f.validation_message:
                    lines.append(f"      error msg: \"{f.validation_message}\"")
                if f.options:
                    lines.append(f"      options: {f.options[:6]}")

        if self.buttons:
            lines += ["", "Buttons / Actions (DOM-verified):"]
            for b in self.buttons:
                lines.append(f"  • \"{b.label}\"  →  {b.primary_selector}")
                if b.alternative_selectors:
                    lines.append(f"      alt: {', '.join(b.alternative_selectors[:2])}")

        if self.navigation:
            lines += ["", "Navigation Links:"]
            for nav in self.navigation[:12]:
                lines.append(f"  • \"{nav['text']}\"  →  {nav['href']}")

        lines += [
            "",
            "CONSTRAINT: Every field name, selector, button label, and URL path in the test cases",
            "or test script MUST come from this exploration context. Do not invent anything.",
            "=== END EXPLORATION CONTEXT ===",
        ]
        return "\n".join(lines)

    def to_page_object_code(self, class_name: str, product: str) -> str:
        """Generate a page object skeleton with DOM-verified selectors."""
        import re as _re
        # Extract path only from the URL for the navigate method
        url_path = _re.sub(r"https?://[^/]+", "", self.url) or self.url

        def _sel(selector: str) -> str:
            # Return selector as a Python string literal (repr handles escaping)
            return repr(selector)

        lines = [
            '"""Page object for {} — selectors verified against live app."""'.format(self.title),
            "from __future__ import annotations",
            "",
            "from pages.base_page import BasePage",
            "",
            "",
            f"class {class_name}(BasePage):",
            f'    URL = "{url_path}"',
            "",
            "    def navigate(self) -> None:",
            "        self.page.goto(f\"{self.base_url}" + url_path + "\")",
            "",
        ]

        for f in self.fields:
            mname = _to_snake(f.name)
            sel = _sel(f.primary_selector)
            if f.field_type in ("text", "password", "email", "number", "search", "textarea", "url"):
                lines += [
                    f"    def fill_{mname}(self, value: str) -> None:",
                    f"        self.page.fill({sel}, value)",
                    "",
                ]
            elif f.field_type == "checkbox":
                lines += [
                    f"    def set_{mname}(self, checked: bool = True) -> None:",
                    f"        el = self.page.locator({sel})",
                    "        if checked != el.is_checked():",
                    "            el.click()",
                    "",
                ]
            elif f.field_type in ("select", "select-one", "select-multiple"):
                lines += [
                    f"    def select_{mname}(self, value: str) -> None:",
                    f"        self.page.select_option({sel}, value)",
                    "",
                ]

        for b in self.buttons:
            mname = _to_snake(b.label or b.name)
            sel = _sel(b.primary_selector)
            lines += [
                f"    def click_{mname}(self) -> None:",
                f"        self.page.click({sel})",
                "",
            ]

        lines += [
            "    def get_validation_error(self, field_name: str) -> str:",
            '        """Return visible validation message for field_name, or empty string."""',
            "        try:",
            "            sel = f\"[data-testid='{field_name}-error'], .oxd-input-field-error-message, .error-message\"",
            "            return self.page.locator(sel).first.inner_text().strip()",
            "        except Exception:",
            '            return ""',
            "",
        ]

        return "\n".join(lines)

    def to_kb_yaml_entry(self) -> dict:
        """Produce a ui_pages.yaml-compatible page entry from this exploration result."""
        elements: list[str] = []
        for f in self.fields:
            label = f.label or f.name
            elements.append(f"{label} ({f.primary_selector})")
        for b in self.buttons:
            elements.append(f"[Button] {b.label} ({b.primary_selector})")

        positive = [f"Verify {self.title} loads and all elements are visible"]
        for f in self.fields:
            if f.required:
                label = f.label or f.name
                positive.append(f"Fill {label} with valid data and submit successfully")

        negative: list[str] = []
        for f in self.fields:
            if f.validation_message:
                label = f.label or f.name
                negative.append(f"{label} empty: {f.validation_message}")
            elif f.required:
                label = f.label or f.name
                negative.append(f"Leave {label} empty — expect required-field error")

        entry: dict = {
            "name": self.title,
            "url": self.url,
            "description": (
                f"Discovered via AppExplorerAgent on {self.timestamp[:10] if self.timestamp else 'unknown date'}"
            ),
            "elements": elements,
        }
        if positive or negative:
            scenarios: dict = {}
            if positive:
                scenarios["positive"] = positive
            if negative:
                scenarios["negative"] = negative
            entry["test_scenarios"] = scenarios
        return entry

    def to_increment_entry(self, feature_name: str, product: str, domain: str = "web") -> dict:
        """Produce an increment YAML-compatible dict for this single page."""
        scenarios: list[dict] = [
            {
                "name": "page_loads",
                "type": "happy_path",
                "description": f"Verify {self.title} loads without errors",
            }
        ]
        for f in self.fields:
            if f.required:
                label = f.label or f.name
                scenarios.append({
                    "name": f"fill_{f.name}",
                    "type": "happy_path",
                    "description": f"Fill {label} with valid data",
                })
        if any(f.validation_message for f in self.fields):
            scenarios.append({
                "name": "validation_errors",
                "type": "error",
                "description": "Submit empty form — required-field errors appear for all mandatory fields",
            })

        return {
            "product": product,
            "feature": feature_name,
            "domain": domain,
            "description": f"UI exploration of {self.title} at {self.url}\n",
            "ui_changes": [{
                "component": self.title,
                "url": self.url,
                "fields": [f"{f.label or f.name} ({f.primary_selector})" for f in self.fields],
                "buttons": [b.label for b in self.buttons],
            }],
            "scenarios": scenarios,
        }


class AppExplorationSkill:
    """Playwright-based page structure discovery."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    def explore_page(self, url: str, *, browser_context=None) -> DiscoveredPage:
        """Explore a single page. Pass browser_context for authenticated sessions."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "playwright is required for AppExplorationSkill. "
                "Run: pip install playwright && playwright install chromium"
            )

        if browser_context is not None:
            page = browser_context.new_page()
            try:
                page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                self._wait_for_spa(page)
                return self._extract(page, url)
            finally:
                page.close()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            ctx = browser.new_context()
            page = ctx.new_page()
            try:
                page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                self._wait_for_spa(page)
                return self._extract(page, url)
            finally:
                browser.close()

    def explore_with_auth(
        self,
        pages: list[str],
        base_url: str,
        login_url: str,
        credentials: dict,
    ) -> list[DiscoveredPage]:
        """Authenticate once then explore all target pages."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "playwright is required. Run: pip install playwright && playwright install chromium"
            )

        results: list[DiscoveredPage] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            ctx = browser.new_context()
            page = ctx.new_page()
            try:
                self._login(page, login_url, credentials)
                for url in pages:
                    full_url = url if url.startswith("http") else f"{base_url.rstrip('/')}{url}"
                    try:
                        page.goto(full_url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                        self._wait_for_spa(page)
                        dp = self._extract(page, full_url)
                        results.append(dp)
                        _log.info("Explored %s — %d fields, %d buttons", full_url, len(dp.fields), len(dp.buttons))
                    except Exception as exc:
                        _log.warning("Failed to explore %s: %s", full_url, exc)
            finally:
                browser.close()
        return results

    def _wait_for_spa(self, page, extra_ms: int = 500) -> None:
        """Wait for a SPA to settle after navigation: networkidle then a short DOM-settle pause."""
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(extra_ms)

    def _login(self, page, login_url: str, credentials: dict) -> None:
        page.goto(login_url, timeout=self.timeout_ms, wait_until="domcontentloaded")
        page.wait_for_timeout(500)

        username = credentials.get("username", "")
        password = credentials.get("password", "")

        for sel in ["input[name='username']", "input[type='text']:visible", "#username",
                    "input[placeholder*='sername' i]", "input[autocomplete='username']"]:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.fill(username)
                    break
            except Exception:
                pass

        for sel in ["input[name='password']", "input[type='password']", "#password",
                    "input[autocomplete='current-password']"]:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.fill(password)
                    break
            except Exception:
                pass

        for sel in ["button[type='submit']", "button:has-text('Login')",
                    "button:has-text('Sign in')", "input[type='submit']"]:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click()
                    try:
                        page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
                    except Exception:
                        page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        current_url = page.url
        login_base = login_url.split("?")[0].rstrip("/")
        if current_url.rstrip("/").endswith(login_base.split("/")[-1]):
            _log.warning(
                "Login may have failed — still on login page after submit. "
                "Check credentials or login URL: %s", login_url
            )
        else:
            _log.info("Login succeeded — redirected to %s", current_url)

    def _extract(self, page, url: str) -> DiscoveredPage:
        title = page.title() or url.rsplit("/", 1)[-1]

        try:
            headings = page.eval_on_selector_all(
                "h1, h2, h3",
                "els => els.map(e => e.innerText.trim()).filter(t => t.length > 0 && t.length < 80).slice(0, 5)"
            )
        except Exception:
            headings = []

        try:
            input_data: list[dict] = page.evaluate(_JS_EXTRACT_INPUTS)
        except Exception as exc:
            _log.warning("Input extraction failed on %s: %s", url, exc)
            input_data = []

        try:
            button_data: list[dict] = page.evaluate(_JS_EXTRACT_BUTTONS)
        except Exception as exc:
            _log.warning("Button extraction failed on %s: %s", url, exc)
            button_data = []

        try:
            nav_data: list[dict] = page.evaluate(_JS_EXTRACT_NAV)
        except Exception:
            nav_data = []

        fields: list[DiscoveredField] = []
        for i, inp in enumerate(input_data):
            primary, alternatives = _best_selector(inp)
            if not primary:
                continue
            name = _to_snake(inp.get("name") or inp.get("id") or inp.get("ariaLabel") or f"field_{i}")
            fields.append(DiscoveredField(
                name=name,
                label=inp.get("label", ""),
                field_type=inp.get("type", "text"),
                required=bool(inp.get("required", False)),
                placeholder=inp.get("placeholder", ""),
                primary_selector=primary,
                alternative_selectors=alternatives,
                options=inp.get("options", []),
            ))

        buttons: list[DiscoveredField] = []
        for btn in button_data:
            primary, alternatives = _best_selector(btn)
            text = btn.get("text", "")
            if not primary:
                primary = f"button:has-text('{text[:50]}')" if text else ""
            if not primary:
                continue
            name = _to_snake(text or btn.get("id") or f"btn_{len(buttons)}")
            buttons.append(DiscoveredField(
                name=name,
                label=text,
                field_type="button",
                required=False,
                placeholder="",
                primary_selector=primary,
                alternative_selectors=alternatives,
            ))

        # Capture validation messages — submit empty form, collect errors
        validation = self._capture_validation(page)
        for f in fields:
            for key in [f.name, f.primary_selector]:
                if key in validation:
                    f.validation_message = validation[key]
                    break

        return DiscoveredPage(
            url=url,
            title=title,
            fields=fields,
            buttons=buttons,
            navigation=nav_data,
            headings=[h for h in headings if h],
            timestamp=datetime.utcnow().isoformat(),
        )

    def _capture_validation(self, page) -> dict[str, str]:
        """Click submit with no input to reveal required-field validation messages."""
        messages: dict[str, str] = {}
        try:
            submit = page.locator("button[type='submit'], input[type='submit']").first
            if submit.count() and submit.is_visible():
                submit.click()
                page.wait_for_timeout(800)
                messages = page.evaluate(_JS_EXTRACT_ERRORS) or {}
        except Exception as exc:
            _log.debug("Validation capture skipped (non-fatal): %s", exc)
        return messages
