"""Knowledge Base Loader — loads base YAML files + feature increment drops for AI context."""

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

_log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
INCREMENTS_DIR = BASE_DIR / "increments"


class KnowledgeBaseLoader:
    def __init__(self, kb_dir: Path = None):
        self.kb_dir = kb_dir or BASE_DIR
        self._cache: Dict[str, Any] = {}

    # --- loaders ---

    def load_application_metadata(self) -> Dict[str, Any]:
        return self._load_cached("application", self.kb_dir / "application.yaml")

    def load_api_specs(self) -> Dict[str, Any]:
        return self._load_cached("api_specs", self.kb_dir / "api_specs.yaml")

    def load_ui_pages(self) -> Dict[str, Any]:
        return self._load_cached("ui_pages", self.kb_dir / "ui_pages.yaml")

    def load_feature_changelog(self) -> str:
        key = "feature_changelog"
        if key not in self._cache:
            path = self.kb_dir / "feature_changelog.md"
            self._cache[key] = path.read_text(encoding="utf-8") if path.exists() else ""
        return self._cache[key]

    def load_product_knowledge(self) -> Dict[str, Any]:
        return self._load_cached("product_knowledge", self.kb_dir / "product_knowledge.yaml")

    def load_mobile_specs(self) -> Dict[str, Any]:
        return self._load_cached("mobile_specs", self.kb_dir / "mobile_specs.yaml")

    def load_increments(self) -> list[Dict[str, Any]]:
        """Load all feature increment YAMLs from increments/ directory."""
        key = "increments"
        if key not in self._cache:
            increments = []
            if INCREMENTS_DIR.exists():
                for path in sorted(INCREMENTS_DIR.glob("*.yaml")):
                    data = self._load_yaml(path)
                    if data:
                        increments.append(data)
                        _log.debug("Loaded increment: %s", path.name)
            self._cache[key] = increments
        return self._cache[key]

    def invalidate(self):
        """Clear cache — call after adding new increment files."""
        self._cache.clear()

    # --- context formatters ---

    def get_rest_api_context(self) -> str:
        specs = self.load_api_specs()
        rest = specs.get("rest_api", {})
        endpoints_info = [
            f"- {e['method']} {e['path']}: {e['description']}"
            for e in rest.get("endpoints", [])
        ]
        return (
            f"REST API Context:\nBase URL: {rest.get('base_url', 'N/A')}\n"
            f"Version: {rest.get('version', '1.0')}\n\nEndpoints:\n"
            + "\n".join(endpoints_info)
        )

    def get_graphql_api_context(self) -> str:
        specs = self.load_api_specs()
        graphql = specs.get("graphql_api", {})
        queries_info = [f"- {q['name']}: {q['description']}" for q in graphql.get("queries", [])]
        return (
            f"GraphQL API Context:\nEndpoint: {graphql.get('endpoint', '/graphql')}\n\n"
            f"Available Queries:\n" + "\n".join(queries_info)
        )

    def get_ui_context(self) -> str:
        ui = self.load_ui_pages()
        pages_info = [f"- {p['name']}: {p['url']}" for p in ui.get("pages", [])]
        return "UI Pages Context:\n" + "\n".join(pages_info)

    def get_feature_context(self, feature_name: str = None) -> str:
        changelog = self.load_feature_changelog()
        if not changelog:
            return "No feature changelog available."
        if feature_name:
            lines = changelog.split("\n")
            section, in_section = [], False
            for line in lines:
                if feature_name.lower() in line.lower():
                    in_section = True
                if in_section:
                    section.append(line)
                    if line.startswith("---"):
                        break
            return "\n".join(section[:50]) if section else "Feature not found"
        return changelog[:1000]

    def get_product_context(self) -> str:
        product = self.load_product_knowledge()
        ctx = [
            "\n=== PRODUCT KNOWLEDGE ===",
            f"Product: {product.get('product', {}).get('name', 'Unknown')}",
            f"Description: {product.get('product', {}).get('description', '')}\n",
            "=== MODULES AND FEATURES ===",
        ]
        for module in product.get("modules", []):
            ctx.append(f"\n- {module['name']}: {module['description']}")
            ctx.append(f"  Status: {module.get('status', 'Unknown')}")
            for rule in module.get("business_rules", [])[:5]:
                ctx.append(f"    • {rule}")
        return "\n".join(ctx)

    def get_personas_context(self) -> str:
        product = self.load_product_knowledge()
        ctx = ["\n=== USER PERSONAS AND ACCESS CONTROL ==="]
        for p in product.get("personas", []):
            ctx.append(f"\n- {p['name']} (Level {p.get('access_level', '?')})")
            ctx.append(f"  {p['description']}")
            for f in p.get("features_available", [])[:3]:
                ctx.append(f"    • {f}")
        return "\n".join(ctx)

    def get_use_cases_context(self) -> str:
        product = self.load_product_knowledge()
        ctx = ["\n=== USE CASES AND SCENARIOS ==="]
        for uc in product.get("use_cases", []):
            ctx.append(f"\n- {uc['name']}: {uc['description']}")
            ctx.append(f"  Actors: {', '.join(uc.get('actors', []))}")
            for s in uc.get("test_scenarios", [])[:3]:
                ctx.append(f"    • {s}")
        return "\n".join(ctx)

    def get_business_rules_context(self) -> str:
        product = self.load_product_knowledge()
        ctx = ["\n=== BUSINESS RULES AND VALIDATIONS ==="]
        for module in product.get("modules", []):
            ctx.append(f"\n{module['name']}:")
            for rule in module.get("business_rules", []):
                ctx.append(f"  • {rule}")
        return "\n".join(ctx)

    def get_mobile_context(self) -> str:
        mobile = self.load_mobile_specs()
        if not mobile:
            return ""
        ctx = ["\n=== MOBILE APP CONTEXT ==="]
        app = mobile.get("mobile_app", {})
        ctx.append(f"App: {app.get('name', 'Unknown')}")
        ctx.append(f"Platforms: Android {app.get('platform_versions', {}).get('android', '?')} / iOS {app.get('platform_versions', {}).get('ios', '?')}")
        ctx.append("\nScreens:")
        for screen in mobile.get("screens", []):
            ctx.append(f"  - {screen['name']}: {screen['description']}")
            for s in screen.get("test_scenarios", {}).get("positive", [])[:2]:
                ctx.append(f"      [+] {s}")
            for s in screen.get("test_scenarios", {}).get("negative", [])[:2]:
                ctx.append(f"      [-] {s}")
        ctx.append("\nPlatform differences:")
        for platform, detail in mobile.get("platform_differences", {}).get("locator_strategy", {}).items():
            ctx.append(f"  {platform}: {detail}")
        return "\n".join(ctx)

    def get_increments_context(self) -> str:
        increments = self.load_increments()
        if not increments:
            return ""
        ctx = ["\n=== FEATURE INCREMENTS ==="]
        for inc in increments:
            feature = inc.get("feature", {})
            if isinstance(feature, str):
                feature = {"name": feature}
            feature_name = feature.get("name", "Unnamed")
            ctx.append(f"\n- {feature_name} (v{feature.get('version', '?')})")
            ctx.append(f"  Status: {feature.get('status', 'unknown')}")
            # Emit endpoint constraints so the LLM cannot fabricate paths
            endpoints = inc.get("endpoints", [])
            if endpoints:
                ctx.append(f"\n  API CONSTRAINTS FOR {feature_name} — ONLY these paths are valid:")
                for ep in endpoints:
                    codes = ep.get("response_codes", [])
                    ctx.append(f"    {ep.get('method','GET')} {ep.get('path','')} → codes {codes}")
                ctx.append("  NEVER use any path not listed above.")
            for scenario in inc.get("test_scenarios", {}).get("api", [])[:3]:
                ctx.append(f"    • [api] {scenario}")
            for scenario in inc.get("scenarios", [])[:4]:
                ctx.append(f"    • {scenario.get('type','scenario')}: {scenario.get('name','')} — {scenario.get('description','')}")
            for scenario in inc.get("test_scenarios", {}).get("ui", [])[:2]:
                ctx.append(f"    • [ui] {scenario}")
        return "\n".join(ctx)

    def get_all_context(self) -> str:
        parts = [
            "=== KNOWLEDGE BASE CONTEXT ===\n",
            self.get_product_context(),
            self.get_personas_context(),
            self.get_business_rules_context(),
            self.get_use_cases_context(),
            self.get_ui_context(),
            self.get_rest_api_context(),
            self.get_graphql_api_context(),
            self.get_mobile_context(),
            "\n=== RECENT FEATURES ===\n",
            self.get_feature_context(),
            self.get_increments_context(),
        ]
        return "\n".join(parts)

    # --- internals ---

    def _load_cached(self, key: str, path: Path) -> Dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = self._load_yaml(path)
        return self._cache[key]

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            _log.warning("KB file not found, skipping: %s", path)
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
