"""Unit tests for ai.clients — BaseClient, AnthropicClient, OpenAIClient, MistralClient."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fake_anthropic():
    """Return a minimal fake `anthropic` module + Anthropic callable mock."""
    mod = types.ModuleType("anthropic")
    mod.Anthropic = MagicMock()  # instance so .return_value works as expected
    return mod


def _make_fake_openai():
    mod = types.ModuleType("openai")
    mod.OpenAI = MagicMock()
    return mod


# ── BaseClient ────────────────────────────────────────────────────────────────

class TestBaseClient:
    def test_is_abstract(self):
        from ai.clients.base_client import AIClient
        with pytest.raises(TypeError):
            AIClient(api_key="key", model="m")  # type: ignore[abstract]

    def test_stores_api_key_and_model(self):
        from ai.clients.base_client import AIClient

        class ConcreteClient(AIClient):
            def generate(self, prompt, **kwargs): return ""
            def chat(self, messages, **kwargs): return ""

        client = ConcreteClient(api_key="test-key", model="my-model")
        assert client.api_key == "test-key"
        assert client.model == "my-model"

    def test_default_model(self):
        from ai.clients.base_client import AIClient

        class ConcreteClient(AIClient):
            def generate(self, prompt, **kwargs): return ""
            def chat(self, messages, **kwargs): return ""

        client = ConcreteClient(api_key="key")
        assert client.model == "mistral"


# ── AnthropicClient ───────────────────────────────────────────────────────────

@pytest.fixture
def fake_anthropic_mod():
    """Inject a fake `anthropic` module into sys.modules for the test."""
    mod = _make_fake_anthropic()
    with patch.dict(sys.modules, {"anthropic": mod}):
        # Force a fresh import of anthropic_client using the fake module
        sys.modules.pop("ai.clients.anthropic_client", None)
        yield mod
    sys.modules.pop("ai.clients.anthropic_client", None)


class TestAnthropicClient:
    def test_init_stores_model(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod
        client = mod.AnthropicClient(api_key="test-key", model="claude-sonnet-4-6")
        assert client.model == "claude-sonnet-4-6"
        assert client.api_key == "test-key"

    def test_default_model(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod
        client = mod.AnthropicClient(api_key="test-key")
        assert client.model == "claude-haiku-4-5-20251001"

    def test_generate_delegates_to_chat(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod
        client = mod.AnthropicClient(api_key="key")

        captured = {}
        def fake_chat(messages, **kwargs):
            captured["messages"] = messages
            return "AI response"
        client.chat = fake_chat

        result = client.generate("hello world")
        assert result == "AI response"
        assert captured["messages"] == [{"role": "user", "content": "hello world"}]

    def test_chat_extracts_text_block(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod

        class Block:
            text = "response text"

        class FakeMessages:
            def create(self, **kwargs):
                class Resp:
                    content = [Block()]
                return Resp()

        fake_anthropic_mod.Anthropic.return_value.messages = FakeMessages()
        client = mod.AnthropicClient(api_key="key")
        result = client.chat([{"role": "user", "content": "hi"}])
        assert result == "response text"

    def test_chat_returns_empty_when_no_text_block(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod

        class BlockNoText:
            pass  # no .text attribute

        class FakeMessages:
            def create(self, **kwargs):
                class Resp:
                    content = [BlockNoText()]
                return Resp()

        fake_anthropic_mod.Anthropic.return_value.messages = FakeMessages()
        client = mod.AnthropicClient(api_key="key")
        result = client.chat([{"role": "user", "content": "hi"}])
        assert result == ""

    def test_chat_passes_max_tokens(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod

        captured = {}

        class FakeMessages:
            def create(self, **kwargs):
                captured.update(kwargs)
                class Block:
                    text = ""
                class Resp:
                    content = [Block()]
                return Resp()

        fake_anthropic_mod.Anthropic.return_value.messages = FakeMessages()
        client = mod.AnthropicClient(api_key="key")
        client.chat([{"role": "user", "content": "hi"}], max_tokens=512)
        assert captured["max_tokens"] == 512

    def test_chat_default_max_tokens(self, fake_anthropic_mod):
        import ai.clients.anthropic_client as mod

        captured = {}

        class FakeMessages:
            def create(self, **kwargs):
                captured.update(kwargs)
                class Block:
                    text = ""
                class Resp:
                    content = [Block()]
                return Resp()

        fake_anthropic_mod.Anthropic.return_value.messages = FakeMessages()
        client = mod.AnthropicClient(api_key="key")
        client.chat([{"role": "user", "content": "hi"}])
        assert captured.get("max_tokens", 4096) == 4096


# ── MistralClient ─────────────────────────────────────────────────────────────

class TestMistralClientInit:
    def test_local_client_stores_config(self):
        from ai.clients.mistral_client import MistralClient
        client = MistralClient(model="mistral", local=True, local_url="http://localhost:11434")
        assert client.model == "mistral"
        assert client.local is True

    def test_cloud_client_stores_model(self):
        from ai.clients.mistral_client import MistralClient
        client = MistralClient(api_key="key", model="mistral-medium", local=False)
        assert client.model == "mistral-medium"

    def test_default_model_used_when_not_specified(self):
        from ai.clients.mistral_client import MistralClient
        client = MistralClient(local=True, local_url="http://localhost:11434")
        assert client.model is not None


# ── OpenAIClient ──────────────────────────────────────────────────────────────

@pytest.fixture
def fake_openai_mod():
    mod = _make_fake_openai()
    with patch.dict(sys.modules, {"openai": mod}):
        sys.modules.pop("ai.clients.openai_client", None)
        yield mod
    sys.modules.pop("ai.clients.openai_client", None)


class TestOpenAIClientInit:
    def test_stores_api_key_and_model(self, fake_openai_mod):
        import ai.clients.openai_client as mod
        client = mod.OpenAIClient(api_key="test-key", model="gpt-4o-mini")
        assert client.api_key == "test-key"
        assert client.model == "gpt-4o-mini"
