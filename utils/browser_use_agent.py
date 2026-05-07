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

    def act(
        self,
        task: str,
        start_url: Optional[str] = None,
        cookies: Optional[list] = None,
    ) -> AgentResult:
        """Synchronous entry point — runs async agent in a new event loop.

        cookies: Playwright context.cookies() list — injected into the agent's
        browser so it inherits the existing auth session. Without this the agent
        would start unauthenticated and land on the login page.
        """
        try:
            return asyncio.run(self._async_act(task, start_url, cookies or []))
        except Exception as exc:
            _log.warning("[BrowserUse] agent failed: %s", exc)
            return AgentResult(success=False, message=str(exc))

    async def _async_act(
        self,
        task: str,
        start_url: Optional[str],
        cookies: list,
    ) -> AgentResult:
        try:
            from browser_use import Agent
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise RuntimeError(
                "browser-use not installed — run: pip install browser-use langchain-ollama"
            ) from exc

        llm = ChatOllama(model=self.model, base_url=self.ollama_url)
        full_task = f"Go to {start_url} and then: {task}" if start_url else task

        agent = self._build_agent(full_task, llm, cookies)
        result = await agent.run()
        return AgentResult(success=True, message=str(result))

    def _build_agent(self, task: str, llm, cookies: list):
        """Build Agent with cookie-seeded context when cookies are available."""
        from browser_use import Agent

        if not cookies:
            return Agent(task=task, llm=llm)

        # browser-use uses Playwright internally — inject cookies via BrowserContextConfig
        # so the agent inherits the existing authenticated session.
        try:
            from browser_use.browser.browser import Browser, BrowserConfig
            from browser_use.browser.context import BrowserContextConfig

            pw_cookies = [
                {k: v for k, v in c.items() if k in ("name", "value", "domain", "path", "secure", "httpOnly", "sameSite", "expires")}
                for c in cookies
            ]
            browser = Browser(config=BrowserConfig(
                headless=True,
                new_context_config=BrowserContextConfig(cookies=pw_cookies),
            ))
            _log.info("[BrowserUse] injecting %d cookies into agent browser context", len(pw_cookies))
            return Agent(task=task, llm=llm, browser=browser)
        except Exception as exc:
            _log.warning("[BrowserUse] cookie injection failed (%s) — running unauthenticated", exc)
            return Agent(task=task, llm=llm)
