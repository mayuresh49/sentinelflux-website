from typing import Any, Mapping


def assert_equal(actual: Any, expected: Any, message: str = ""):
    assert actual == expected, message or f"Expected {expected!r}, got {actual!r}"


def assert_contains(container: Any, member: Any, message: str = ""):
    assert member in container, message or f"Expected {member!r} to be in {container!r}"


def assert_status_code(response, expected: int):
    actual = getattr(response, "status_code", None)
    assert actual == expected, f"Expected status code {expected}, got {actual}"


def assert_schema(response_json: Mapping[str, Any], schema: Mapping[str, Any]):
    from jsonschema import validate

    validate(instance=response_json, schema=schema)
