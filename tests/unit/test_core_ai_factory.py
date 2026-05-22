"""Unit tests for core.ai_factory — client creation routing."""
from __future__ import annotations

import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures for optional packages ───────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_client_module_cache():
    """Remove cached ai.clients.* modules so fake sys.modules patches take effect."""
    for key in ("ai.clients.anthropic_client", "ai.clients.openai_client"):
        sys.modules.pop(key, None)
    yield
    for key in ("ai.clients.anthropic_client", "ai.clients.openai_client"):
        sys.modules.pop(key, None)


@pytest.fixture
def fake_anthropic():
    mod = types.ModuleType("anthropic")
    mod.Anthropic = MagicMock
    with patch.dict(sys.modules, {"anthropic": mod}):
        yield mod


@pytest.fixture
def fake_openai():
    mod = types.ModuleType("openai")
    mod.OpenAI = MagicMock
    with patch.dict(sys.modules, {"openai": mod}):
        yield mod


# ── create_ai_client ──────────────────────────────────────────────────────────

class TestCreateAIClient:
    def test_disabled_returns_none(self):
        from core.ai_factory import create_ai_client
        assert create_ai_client({"enabled": False}) is None

    def test_enabled_false_even_with_mode(self):
        from core.ai_factory import create_ai_client
        assert create_ai_client({"enabled": False, "mode": "mistral"}) is None

    def test_unknown_mode_returns_none(self):
        from core.ai_factory import create_ai_client
        assert create_ai_client({"enabled": True, "mode": "unsupported_llm"}) is None

    def test_mistral_local_returns_client(self):
        from core.ai_factory import create_ai_client
        from ai.clients.mistral_client import MistralClient
        client = create_ai_client({
            "enabled": True,
            "mode": "mistral",
            "local": True,
            "local_url": "http://localhost:11434",
            "model": "mistral",
        })
        assert isinstance(client, MistralClient)

    def test_mistral_cloud_returns_client(self):
        from core.ai_factory import create_ai_client
        from ai.clients.mistral_client import MistralClient
        client = create_ai_client({
            "enabled": True,
            "mode": "mistral",
            "local": False,
            "api_key": "test-key",
            "model": "mistral-medium",
        })
        assert isinstance(client, MistralClient)

    def test_openai_uses_env_key(self, monkeypatch, fake_openai):
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        from core.ai_factory import create_ai_client
        client = create_ai_client({"enabled": True, "mode": "openai", "model": "gpt-4o-mini"})
        import ai.clients.openai_client as oc
        assert isinstance(client, oc.OpenAIClient)
        assert client.api_key == "env-key"

    def test_openai_default_model(self, monkeypatch, fake_openai):
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        from core.ai_factory import create_ai_client
        client = create_ai_client({"enabled": True, "mode": "openai"})
        assert client.model == "gpt-4o-mini"

    def test_anthropic_uses_env_key(self, monkeypatch, fake_anthropic):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
        from core.ai_factory import create_ai_client
        client = create_ai_client({"enabled": True, "mode": "anthropic"})
        import ai.clients.anthropic_client as ac
        assert isinstance(client, ac.AnthropicClient)
        assert client.api_key == "anth-key"

    def test_anthropic_default_model(self, monkeypatch, fake_anthropic):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
        from core.ai_factory import create_ai_client
        client = create_ai_client({"enabled": True, "mode": "anthropic"})
        assert client.model == "claude-haiku-4-5-20251001"

    def test_anthropic_custom_model(self, monkeypatch, fake_anthropic):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
        from core.ai_factory import create_ai_client
        client = create_ai_client({
            "enabled": True, "mode": "anthropic", "model": "claude-sonnet-4-6"
        })
        assert client.model == "claude-sonnet-4-6"


# ── create_ai_client_from_dashboard ──────────────────────────────────────────

class TestCreateAIClientFromDashboard:
    def test_missing_config_returns_none(self, tmp_path, monkeypatch):
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", tmp_path / "nonexistent.json")
        assert af.create_ai_client_from_dashboard() is None

    def test_ollama_provider(self, tmp_path, monkeypatch):
        cfg = {"provider": "ollama", "model": "mistral", "base_url": "http://localhost:11434"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        from ai.clients.mistral_client import MistralClient
        client = af.create_ai_client_from_dashboard()
        assert isinstance(client, MistralClient)

    def test_openai_provider_no_key_returns_none(self, tmp_path, monkeypatch):
        cfg = {"provider": "openai", "model": "gpt-4o-mini"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert af.create_ai_client_from_dashboard() is None

    def test_openai_provider_with_key(self, tmp_path, monkeypatch, fake_openai):
        cfg = {"provider": "openai", "model": "gpt-4o-mini"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        import ai.clients.openai_client as oc
        client = af.create_ai_client_from_dashboard()
        assert isinstance(client, oc.OpenAIClient)

    def test_anthropic_provider_no_key_returns_none(self, tmp_path, monkeypatch):
        cfg = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert af.create_ai_client_from_dashboard() is None

    def test_anthropic_provider_with_key(self, tmp_path, monkeypatch, fake_anthropic):
        cfg = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
        import ai.clients.anthropic_client as ac
        client = af.create_ai_client_from_dashboard()
        assert isinstance(client, ac.AnthropicClient)

    def test_unknown_provider_returns_none(self, tmp_path, monkeypatch):
        cfg = {"provider": "unknown_ai", "model": "llama"}
        config_file = tmp_path / "chat_config.json"
        config_file.write_text(json.dumps(cfg))
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        assert af.create_ai_client_from_dashboard() is None

    def test_corrupt_config_returns_none(self, tmp_path, monkeypatch):
        config_file = tmp_path / "chat_config.json"
        config_file.write_text("NOT VALID JSON")
        import core.ai_factory as af
        monkeypatch.setattr(af, "_CHAT_CONFIG", config_file)
        assert af.create_ai_client_from_dashboard() is None
