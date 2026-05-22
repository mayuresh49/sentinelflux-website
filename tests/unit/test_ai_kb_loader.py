"""Unit tests for ai.knowledge_base.kb_loader.KnowledgeBaseLoader."""
from __future__ import annotations

import yaml
import pytest

from ai.knowledge_base.kb_loader import KnowledgeBaseLoader


@pytest.fixture
def kb_dir(tmp_path):
    return tmp_path


@pytest.fixture
def kb(kb_dir):
    return KnowledgeBaseLoader(kb_dir=kb_dir)


def write_yaml(path, data):
    path.write_text(yaml.dump(data), encoding="utf-8")


# ── Loading and caching ───────────────────────────────────────────────────────

class TestKBLoaderLoading:
    def test_load_missing_yaml_returns_empty_dict(self, kb):
        result = kb.load_application_metadata()
        assert result == {}

    def test_load_yaml_file(self, kb, kb_dir):
        write_yaml(kb_dir / "application.yaml", {"name": "TestApp", "version": "1.0"})
        result = kb.load_application_metadata()
        assert result["name"] == "TestApp"
        assert result["version"] == "1.0"

    def test_load_is_cached(self, kb, kb_dir):
        write_yaml(kb_dir / "application.yaml", {"name": "Original"})
        first = kb.load_application_metadata()
        # Overwrite file — should still return cached value
        write_yaml(kb_dir / "application.yaml", {"name": "Modified"})
        second = kb.load_application_metadata()
        assert first is second

    def test_invalidate_clears_cache(self, kb, kb_dir):
        write_yaml(kb_dir / "application.yaml", {"name": "Original"})
        first = kb.load_application_metadata()
        kb.invalidate()
        write_yaml(kb_dir / "application.yaml", {"name": "Modified"})
        second = kb.load_application_metadata()
        assert second["name"] == "Modified"

    def test_load_api_specs(self, kb, kb_dir):
        data = {"rest_api": {"base_url": "http://api.example.com", "version": "v1", "endpoints": []}}
        write_yaml(kb_dir / "api_specs.yaml", data)
        result = kb.load_api_specs()
        assert result["rest_api"]["base_url"] == "http://api.example.com"

    def test_load_ui_pages(self, kb, kb_dir):
        data = {"pages": [{"name": "Login", "url": "/login"}]}
        write_yaml(kb_dir / "ui_pages.yaml", data)
        result = kb.load_ui_pages()
        assert result["pages"][0]["name"] == "Login"

    def test_load_feature_changelog_missing(self, kb):
        assert kb.load_feature_changelog() == ""

    def test_load_feature_changelog_exists(self, kb, kb_dir):
        (kb_dir / "feature_changelog.md").write_text("## Feature A\n\nAdded login")
        result = kb.load_feature_changelog()
        assert "Feature A" in result

    def test_feature_changelog_is_cached(self, kb, kb_dir):
        (kb_dir / "feature_changelog.md").write_text("Original")
        first = kb.load_feature_changelog()
        (kb_dir / "feature_changelog.md").write_text("Modified")
        second = kb.load_feature_changelog()
        assert first == second

    def test_load_product_knowledge(self, kb, kb_dir):
        data = {"product": {"name": "MyApp", "description": "test"}, "modules": []}
        write_yaml(kb_dir / "product_knowledge.yaml", data)
        result = kb.load_product_knowledge()
        assert result["product"]["name"] == "MyApp"

    def test_load_mobile_specs(self, kb, kb_dir):
        data = {"mobile_app": {"name": "MyMobile"}, "screens": []}
        write_yaml(kb_dir / "mobile_specs.yaml", data)
        result = kb.load_mobile_specs()
        assert result["mobile_app"]["name"] == "MyMobile"


# ── Increments loading ────────────────────────────────────────────────────────

class TestKBLoaderIncrements:
    def test_load_increments_empty_when_no_dir(self, kb):
        result = kb.load_increments()
        assert isinstance(result, list)

    def test_load_increments_from_files(self, kb, kb_dir):
        import ai.knowledge_base.kb_loader as kbl
        inc_dir = kb_dir / "increments"
        inc_dir.mkdir()
        write_yaml(inc_dir / "feature_a.yaml", {
            "feature": {"name": "Auth SSO", "version": "1.0", "status": "in_progress"},
            "test_scenarios": {"api": ["Login via SSO"], "ui": []},
        })
        # Patch INCREMENTS_DIR for this loader
        loader = KnowledgeBaseLoader(kb_dir=kb_dir)
        # The loader uses global INCREMENTS_DIR from module, not kb_dir/increments
        # Override via monkeypatch not available here; use a subclass trick
        import ai.knowledge_base.kb_loader as kbl_mod
        original = kbl_mod.INCREMENTS_DIR
        kbl_mod.INCREMENTS_DIR = inc_dir
        try:
            loader.invalidate()
            result = loader.load_increments()
            assert len(result) == 1
            assert result[0]["feature"]["name"] == "Auth SSO"
        finally:
            kbl_mod.INCREMENTS_DIR = original

    def test_load_increments_cached(self, kb, kb_dir):
        import ai.knowledge_base.kb_loader as kbl_mod
        inc_dir = kb_dir / "increments"
        inc_dir.mkdir()
        original = kbl_mod.INCREMENTS_DIR
        kbl_mod.INCREMENTS_DIR = inc_dir
        try:
            kb.invalidate()
            first = kb.load_increments()
            write_yaml(inc_dir / "new.yaml", {"feature": {"name": "New"}})
            second = kb.load_increments()
            assert first is second  # cached
        finally:
            kbl_mod.INCREMENTS_DIR = original


# ── Context formatters ────────────────────────────────────────────────────────

class TestKBContextFormatters:
    def test_get_rest_api_context_empty(self, kb, kb_dir):
        write_yaml(kb_dir / "api_specs.yaml", {"rest_api": {"base_url": "", "version": "", "endpoints": []}})
        result = kb.get_rest_api_context()
        assert "REST API Context" in result

    def test_get_rest_api_context_with_endpoints(self, kb, kb_dir):
        data = {
            "rest_api": {
                "base_url": "http://api.example.com",
                "version": "v1",
                "endpoints": [
                    {"method": "GET", "path": "/users", "description": "List users"},
                    {"method": "POST", "path": "/users", "description": "Create user"},
                ],
            }
        }
        write_yaml(kb_dir / "api_specs.yaml", data)
        result = kb.get_rest_api_context()
        assert "GET /users" in result
        assert "POST /users" in result
        assert "List users" in result

    def test_get_graphql_api_context(self, kb, kb_dir):
        data = {
            "graphql_api": {
                "endpoint": "/graphql",
                "queries": [{"name": "getUser", "description": "Fetch user by id"}],
            }
        }
        write_yaml(kb_dir / "api_specs.yaml", data)
        result = kb.get_graphql_api_context()
        assert "GraphQL API Context" in result
        assert "getUser" in result

    def test_get_ui_context(self, kb, kb_dir):
        data = {"pages": [
            {"name": "Login", "url": "/login"},
            {"name": "Dashboard", "url": "/dashboard"},
        ]}
        write_yaml(kb_dir / "ui_pages.yaml", data)
        result = kb.get_ui_context()
        assert "Login" in result
        assert "/login" in result

    def test_get_feature_context_no_changelog(self, kb):
        result = kb.get_feature_context()
        assert "No feature changelog" in result

    def test_get_feature_context_full(self, kb, kb_dir):
        (kb_dir / "feature_changelog.md").write_text("## Feature A\n\nAdded auth support\n---")
        result = kb.get_feature_context()
        assert "Feature A" in result

    def test_get_feature_context_by_name(self, kb, kb_dir):
        (kb_dir / "feature_changelog.md").write_text(
            "## Feature A\nLogin SSO\n---\n## Feature B\nDashboard redesign\n---"
        )
        result = kb.get_feature_context(feature_name="Feature A")
        assert "Feature A" in result

    def test_get_feature_context_not_found(self, kb, kb_dir):
        (kb_dir / "feature_changelog.md").write_text("## Feature A\nsome content")
        result = kb.get_feature_context(feature_name="Nonexistent")
        assert "not found" in result

    def test_get_product_context(self, kb, kb_dir):
        data = {
            "product": {"name": "MyApp", "description": "An app"},
            "modules": [
                {"name": "Auth", "description": "Authentication", "status": "stable", "business_rules": ["Rule 1"]},
            ],
            "personas": [],
            "use_cases": [],
        }
        write_yaml(kb_dir / "product_knowledge.yaml", data)
        result = kb.get_product_context()
        assert "MyApp" in result
        assert "Auth" in result
        assert "Rule 1" in result

    def test_get_personas_context(self, kb, kb_dir):
        data = {
            "product": {"name": "App"},
            "modules": [],
            "personas": [
                {"name": "Admin", "access_level": 1, "description": "Full access", "features_available": ["config"]},
            ],
            "use_cases": [],
        }
        write_yaml(kb_dir / "product_knowledge.yaml", data)
        result = kb.get_personas_context()
        assert "Admin" in result
        assert "Full access" in result

    def test_get_mobile_context_empty(self, kb):
        result = kb.get_mobile_context()
        assert result == ""

    def test_get_mobile_context_populated(self, kb, kb_dir):
        data = {
            "mobile_app": {
                "name": "MobileApp",
                "platform_versions": {"android": "12", "ios": "16"},
            },
            "screens": [{"name": "Login", "description": "Login screen", "test_scenarios": {"positive": [], "negative": []}}],
            "platform_differences": {"locator_strategy": {"android": "by id", "ios": "by accessibility"}},
        }
        write_yaml(kb_dir / "mobile_specs.yaml", data)
        result = kb.get_mobile_context()
        assert "MobileApp" in result
        assert "Login" in result

    def test_get_increments_context_empty(self, kb, tmp_path, monkeypatch):
        import ai.knowledge_base.kb_loader as kbl_mod
        empty_dir = tmp_path / "empty_inc"
        empty_dir.mkdir()
        monkeypatch.setattr(kbl_mod, "INCREMENTS_DIR", empty_dir)
        kb.invalidate()
        result = kb.get_increments_context()
        assert result == ""

    def test_get_all_context_runs_without_error(self, kb, kb_dir):
        write_yaml(kb_dir / "product_knowledge.yaml", {
            "product": {"name": "T", "description": ""},
            "modules": [],
            "personas": [],
            "use_cases": [],
        })
        write_yaml(kb_dir / "api_specs.yaml", {
            "rest_api": {"base_url": "", "version": "", "endpoints": []},
            "graphql_api": {"endpoint": "/graphql", "queries": []},
        })
        write_yaml(kb_dir / "ui_pages.yaml", {"pages": []})
        result = kb.get_all_context()
        assert "KNOWLEDGE BASE CONTEXT" in result
