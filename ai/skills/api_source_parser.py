"""ApiSourceParser — loads an API spec, service code, or URL and returns
a structured context string suitable for injection into test-gen prompts.

Detection order (auto):
  - Starts with http(s)://           → fetch, then detect content
  - .yaml / .yml / .json             → try OpenAPI/Swagger parse
  - .py / .js / .ts / .java / .go / .rb → code route extraction
  - anything else                     → read as plain text
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import yaml

_CODE_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rb", ".php", ".cs", ".kt"}
_SPEC_EXTENSIONS = {".yaml", ".yml", ".json"}

SourceType = Literal["openapi", "code", "url", "text"]


class ApiSourceParser:

    def parse(self, source: str) -> str:
        """Return a structured context string extracted from *source*."""
        src_type = self._detect_type(source)
        if src_type == "url":
            return self._parse_url(source)
        if src_type == "openapi":
            return self._parse_openapi(Path(source))
        if src_type == "code":
            return self._parse_code(Path(source))
        return self._parse_text(Path(source))

    # ── detection ──────────────────────────────────────────────────────────

    def _detect_type(self, source: str) -> SourceType:
        if source.startswith(("http://", "https://")):
            return "url"
        path = Path(source)
        if path.suffix.lower() in _SPEC_EXTENSIONS:
            return "openapi"
        if path.suffix.lower() in _CODE_EXTENSIONS:
            return "code"
        return "text"

    # ── OpenAPI / Swagger ──────────────────────────────────────────────────

    def _parse_openapi(self, path: Path) -> str:
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw) if path.suffix == ".json" else yaml.safe_load(raw)
        except Exception as exc:
            return f"=== Source (could not parse as OpenAPI: {exc}) ===\n{path.read_text(encoding='utf-8')[:3000]}"

        if not isinstance(data, dict) or "paths" not in data:
            # Not an OpenAPI spec — treat as plain text YAML
            return f"=== Source Context (YAML document: {path.name}) ===\n{path.read_text(encoding='utf-8')[:4000]}"

        return self._format_openapi(data, path.name)

    def _format_openapi(self, spec: dict, filename: str) -> str:
        info = spec.get("info", {})
        title = info.get("title", filename)
        version = info.get("version", "")
        base = spec.get("servers", [{}])[0].get("url", "") or spec.get("basePath", "")
        lines = [
            f"=== API Source Context (OpenAPI Spec: {title} {version}) ===",
            f"Base URL: {base}" if base else "",
            "",
            "Endpoints:",
        ]
        for path, methods in spec.get("paths", {}).items():
            for method, op in methods.items():
                if method.startswith("x-") or not isinstance(op, dict):
                    continue
                summary = op.get("summary") or op.get("description") or ""
                lines.append(f"  {method.upper()} {path} — {summary}")
                # Parameters
                params = op.get("parameters", [])
                if params:
                    param_desc = ", ".join(
                        f"{p.get('name')} ({p.get('in','?')}, {'required' if p.get('required') else 'optional'})"
                        for p in params if isinstance(p, dict)
                    )
                    lines.append(f"    Parameters: {param_desc}")
                # Request body
                rb = op.get("requestBody", {})
                if rb:
                    content_types = list(rb.get("content", {}).keys())
                    schema_ref = ""
                    for ct in content_types:
                        schema = rb["content"][ct].get("schema", {})
                        schema_ref = schema.get("$ref", schema.get("title", ""))
                        if schema_ref:
                            schema_ref = schema_ref.split("/")[-1]
                            break
                    lines.append(f"    Request body: {', '.join(content_types)}" + (f", schema: {schema_ref}" if schema_ref else ""))
                # Responses
                for code, resp in op.get("responses", {}).items():
                    desc = resp.get("description", "") if isinstance(resp, dict) else ""
                    lines.append(f"    Response {code}: {desc}")
                # Security
                security = op.get("security", spec.get("security", []))
                if security:
                    lines.append(f"    Auth: {security}")

        # Components / schemas summary
        schemas = spec.get("components", {}).get("schemas", {}) or spec.get("definitions", {})
        if schemas:
            lines += ["", "Schemas:"]
            for name, schema in list(schemas.items())[:15]:
                props = list(schema.get("properties", {}).keys()) if isinstance(schema, dict) else []
                lines.append(f"  {name}: {', '.join(props[:8])}" + (" …" if len(props) > 8 else ""))

        return "\n".join(line for line in lines if line is not None)

    # ── Source code ────────────────────────────────────────────────────────

    def _parse_code(self, path: Path) -> str:
        try:
            code = path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"=== Source (read error: {exc}) ==="

        routes = self._extract_routes(code, path.suffix.lower())
        if not routes:
            # No routes found — return first 3 KB of code as-is
            return f"=== Source Context (Service Code: {path.name}) ===\n{code[:3000]}"

        lines = [f"=== API Source Context (Service Code: {path.name}) ===", "", "Detected Routes:"]
        lines.extend(f"  {r}" for r in routes)
        return "\n".join(lines)

    def _extract_routes(self, code: str, ext: str) -> list[str]:
        routes: list[str] = []

        if ext == ".py":
            # FastAPI / Flask / Django patterns
            patterns = [
                r'@(?:app|router|blueprint)\.(get|post|put|patch|delete|options|head)\s*\(\s*["\']([^"\']+)["\']',
                r'path\s*\(\s*["\']([^"\']+)["\']',
                r'url\s*\(\s*r?["\']([^"\']+)["\']',
            ]
            for pat in patterns:
                for m in re.finditer(pat, code, re.IGNORECASE):
                    groups = m.groups()
                    if len(groups) == 2:
                        routes.append(f"{groups[0].upper()} {groups[1]}")
                    else:
                        routes.append(f"PATH {groups[0]}")

        elif ext in (".js", ".ts"):
            # Express.js patterns
            for m in re.finditer(
                r'(?:router|app)\.(get|post|put|patch|delete)\s*\(\s*["\`]([^"\`]+)["\`]',
                code, re.IGNORECASE
            ):
                routes.append(f"{m.group(1).upper()} {m.group(2)}")

        elif ext == ".java":
            # Spring MVC / JAX-RS
            for m in re.finditer(
                r'@(?:Get|Post|Put|Patch|Delete|Request)Mapping\s*(?:\(.*?value\s*=\s*)?["\']([^"\']+)["\']',
                code, re.IGNORECASE
            ):
                routes.append(f"ROUTE {m.group(1)}")

        elif ext == ".go":
            for m in re.finditer(
                r'(?:Handle|HandleFunc|GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"',
                code
            ):
                routes.append(f"ROUTE {m.group(1)}")

        return routes

    # ── URL ────────────────────────────────────────────────────────────────

    def _parse_url(self, url: str) -> str:
        try:
            import requests
            resp = requests.get(url, timeout=15, headers={"Accept": "application/json,text/html,*/*"})
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "")
        except Exception as exc:
            return f"=== Source (URL fetch failed: {exc}) ==="

        # JSON → try OpenAPI
        if "json" in ct:
            try:
                data = resp.json()
                if isinstance(data, dict) and "paths" in data:
                    return self._format_openapi(data, url)
                # Generic JSON — dump truncated
                return f"=== API Source Context (URL: {url}) ===\n{json.dumps(data, indent=2)[:4000]}"
            except Exception:
                pass

        # YAML content type
        if "yaml" in ct:
            try:
                data = yaml.safe_load(resp.text)
                if isinstance(data, dict) and "paths" in data:
                    return self._format_openapi(data, url)
            except Exception:
                pass

        # HTML — strip tags, keep readable text
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return f"=== API Source Context (URL: {url}) ===\n{text[:4000]}"

    # ── Plain text / markdown / other ─────────────────────────────────────

    def _parse_text(self, path: Path) -> str:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"=== Source (read error: {exc}) ==="
        return f"=== API Source Context ({path.name}) ===\n{content[:4000]}"
