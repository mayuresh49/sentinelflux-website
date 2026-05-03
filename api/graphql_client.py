import json
from pathlib import Path
from typing import Any, Dict, Optional
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent


class GraphQLClient:
    def __init__(self, endpoint: str, logger=None):
        self.endpoint = endpoint
        self.logger = logger

    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        path = ROOT_DIR / relative_path
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)

    def _log(self, message: str):
        if self.logger:
            self.logger.info(message)

    def _load_query(self, query_name: str) -> Dict[str, Any]:
        queries = self._load_json("api/endpoints/graphql_endpoints.json")
        if query_name not in queries:
            raise KeyError(f"GraphQL query not found: {query_name}")
        return queries[query_name]

    def execute(
        self,
        query_name: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        payload_name: Optional[str] = None,
    ) -> requests.Response:
        query_def = self._load_query(query_name)
        payload = {
            "query": query_def["query"],
            "variables": variables or {},
        }

        if payload_name:
            extra_payload = self._load_json(f"api/payloads/graphql/{payload_name}.json")
            payload["variables"].update(extra_payload)

        self._log(f"GraphQL execute: {query_name}")
        response = requests.post(self.endpoint, json=payload, headers=headers)
        self._log(f"Response status: {response.status_code}")
        return response
