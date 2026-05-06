"""Tier-3 escalation: Skyvern vision agent REST client."""

import logging
import time
from typing import Optional

_log = logging.getLogger(__name__)


class SkyvernClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        poll_interval_s: int = 5,
        max_wait_s: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.poll_interval_s = poll_interval_s
        self.max_wait_s = max_wait_s
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["x-api-key"] = api_key

    def run_task(
        self,
        url: str,
        navigation_goal: str,
        data_extraction_goal: Optional[str] = None,
    ) -> dict:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError("httpx not installed — run: pip install httpx") from exc

        payload: dict = {"url": url, "navigation_goal": navigation_goal}
        if data_extraction_goal:
            payload["data_extraction_goal"] = data_extraction_goal

        resp = httpx.post(
            f"{self.base_url}/api/v1/tasks",
            json=payload,
            headers=self._headers,
            timeout=30,
        )
        resp.raise_for_status()
        task_id = resp.json()["task_id"]
        _log.info("[Skyvern] task created: %s", task_id)
        return self._poll(task_id)

    def _poll(self, task_id: str) -> dict:
        import httpx

        deadline = time.time() + self.max_wait_s
        while time.time() < deadline:
            resp = httpx.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")
            if status in ("completed", "failed", "terminated"):
                _log.info("[Skyvern] task %s finished → %s", task_id, status)
                return data
            time.sleep(self.poll_interval_s)

        raise TimeoutError(
            f"Skyvern task {task_id} did not complete within {self.max_wait_s}s"
        )
