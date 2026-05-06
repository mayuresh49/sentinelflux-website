"""Tier-2 fallback: Browser-Use LLM agent via local Ollama."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

_log = logging.getLogger(__name__)


@dataclass
class AgentResult:
    success: bool
    message: str


class BrowserUseAgent:
    def __init__(
        self,
        model: str = "qwen2.5:7b",
        ollama_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.ollama_url = ollama_url

    def act(self, task: str, start_url: Optional[str] = None) -> AgentResult:
        """Synchronous entry point — runs async agent in a new event loop."""
        try:
            return asyncio.run(self._async_act(task, start_url))
        except Exception as exc:
            _log.warning("[BrowserUse] agent failed: %s", exc)
            return AgentResult(success=False, message=str(exc))

    async def _async_act(self, task: str, start_url: Optional[str]) -> AgentResult:
        try:
            from browser_use import Agent
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise RuntimeError(
                "browser-use not installed — run: pip install browser-use langchain-ollama"
            ) from exc

        llm = ChatOllama(model=self.model, base_url=self.ollama_url)
        full_task = f"Go to {start_url} and then: {task}" if start_url else task
        agent = Agent(task=full_task, llm=llm)
        result = await agent.run()
        return AgentResult(success=True, message=str(result))
