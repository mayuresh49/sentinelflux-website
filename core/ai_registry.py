"""Module-level AI client registry — lets BasePage access the session AI client without constructor injection."""


_client = None


def set_ai_client(client) -> None:
    global _client
    _client = client


def get_ai_client():
    return _client
