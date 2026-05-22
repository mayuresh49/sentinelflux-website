"""Unit tests for utils.assertions, utils.ai_assertions, utils.wait, utils.step."""
from __future__ import annotations

import pytest


# ── utils.assertions ──────────────────────────────────────────────────────────

class TestAssertions:
    def test_assert_equal_pass(self):
        from utils.assertions import assert_equal
        assert_equal("hello", "hello")

    def test_assert_equal_fail(self):
        from utils.assertions import assert_equal
        with pytest.raises(AssertionError, match="Expected 2"):
            assert_equal(1, 2)

    def test_assert_equal_custom_message(self):
        from utils.assertions import assert_equal
        with pytest.raises(AssertionError, match="custom msg"):
            assert_equal(1, 2, "custom msg")

    def test_assert_contains_list(self):
        from utils.assertions import assert_contains
        assert_contains([1, 2, 3], 2)

    def test_assert_contains_string(self):
        from utils.assertions import assert_contains
        assert_contains("hello world", "world")

    def test_assert_contains_fail(self):
        from utils.assertions import assert_contains
        with pytest.raises(AssertionError):
            assert_contains([1, 2], 99)

    def test_assert_status_code_pass(self):
        from utils.assertions import assert_status_code
        resp = type("R", (), {"status_code": 200})()
        assert_status_code(resp, 200)

    def test_assert_status_code_fail(self):
        from utils.assertions import assert_status_code
        resp = type("R", (), {"status_code": 404})()
        with pytest.raises(AssertionError, match="Expected status code 200, got 404"):
            assert_status_code(resp, 200)


# ── utils.ai_assertions ───────────────────────────────────────────────────────

class TestAIAssertions:
    def test_confidence_above_pass(self):
        from utils.ai_assertions import assert_confidence_above
        assert_confidence_above(0.9, 0.7)

    def test_confidence_above_fail(self):
        from utils.ai_assertions import assert_confidence_above
        with pytest.raises(AssertionError, match="below minimum"):
            assert_confidence_above(0.5, 0.7)

    def test_confidence_above_with_label(self):
        from utils.ai_assertions import assert_confidence_above
        with pytest.raises(AssertionError, match=r"\[mytest\]"):
            assert_confidence_above(0.1, 0.7, label="mytest")

    def test_confidence_below_pass(self):
        from utils.ai_assertions import assert_confidence_below
        assert_confidence_below(0.3, 0.5)

    def test_confidence_below_fail(self):
        from utils.ai_assertions import assert_confidence_below
        with pytest.raises(AssertionError, match="exceeds ceiling"):
            assert_confidence_below(0.8, 0.5)

    def test_category_in_pass(self):
        from utils.ai_assertions import assert_category_in
        assert_category_in("positive", {"positive", "negative"})

    def test_category_in_fail(self):
        from utils.ai_assertions import assert_category_in
        with pytest.raises(AssertionError, match="not in expected set"):
            assert_category_in("unknown", {"positive", "negative"})

    def test_text_contains_any_pass(self):
        from utils.ai_assertions import assert_text_contains_any
        assert_text_contains_any("the error occurred", ["error", "warning"])

    def test_text_contains_any_case_insensitive(self):
        from utils.ai_assertions import assert_text_contains_any
        assert_text_contains_any("The ERROR was found", ["error"])

    def test_text_contains_any_fail(self):
        from utils.ai_assertions import assert_text_contains_any
        with pytest.raises(AssertionError, match="contains none of"):
            assert_text_contains_any("all good", ["error", "warning"])

    def test_text_contains_all_pass(self):
        from utils.ai_assertions import assert_text_contains_all
        assert_text_contains_all("login and logout flow", ["login", "logout"])

    def test_text_contains_all_fail(self):
        from utils.ai_assertions import assert_text_contains_all
        with pytest.raises(AssertionError, match="missing required keywords"):
            assert_text_contains_all("only login", ["login", "logout"])

    def test_text_similarity_pass(self):
        from utils.ai_assertions import assert_text_similarity
        assert_text_similarity("hello world", "hello world", min_ratio=1.0)

    def test_text_similarity_fail(self):
        from utils.ai_assertions import assert_text_similarity
        with pytest.raises(AssertionError, match="below minimum"):
            assert_text_similarity("cat", "completely different text here", min_ratio=0.9)

    def test_response_within_pass(self):
        from utils.ai_assertions import assert_response_within
        assert_response_within(1.0, max_seconds=5.0)

    def test_response_within_fail(self):
        from utils.ai_assertions import assert_response_within
        with pytest.raises(AssertionError, match="exceeded limit"):
            assert_response_within(10.0, max_seconds=5.0)

    def test_field_present_pass(self):
        from utils.ai_assertions import assert_field_present
        assert_field_present({"score": 0.9, "label": "ok"}, "score", "label")

    def test_field_present_fail(self):
        from utils.ai_assertions import assert_field_present
        with pytest.raises(AssertionError, match="missing field"):
            assert_field_present({"score": 0.9}, "score", "label")

    def test_soft_assertions_collects_failures(self):
        from utils.ai_assertions import SoftAssertions, assert_confidence_above
        with pytest.raises(AssertionError, match="2 soft assertion"):
            with SoftAssertions() as soft:
                soft.assert_confidence_above(0.1, 0.7)
                soft.assert_confidence_above(0.2, 0.8)

    def test_soft_assertions_passes_when_all_pass(self):
        from utils.ai_assertions import SoftAssertions
        with SoftAssertions() as soft:
            soft.assert_confidence_above(0.9, 0.7)
            soft.assert_category_in("positive", {"positive", "negative"})
        assert soft.passed
        assert soft.failure_count == 0

    def test_soft_assertions_hard_exception_propagates(self):
        from utils.ai_assertions import SoftAssertions
        with pytest.raises(RuntimeError, match="hard error"):
            with SoftAssertions():
                raise RuntimeError("hard error")

    def test_soft_text_contains_any(self):
        from utils.ai_assertions import SoftAssertions
        with pytest.raises(AssertionError, match="1 soft assertion"):
            with SoftAssertions() as soft:
                soft.assert_text_contains_any("all good", ["error"])

    def test_soft_field_present(self):
        from utils.ai_assertions import SoftAssertions
        with SoftAssertions() as soft:
            soft.assert_field_present({"a": 1, "b": 2}, "a", "b")
        assert soft.passed


# ── utils.wait ────────────────────────────────────────────────────────────────

class TestWaitFor:
    def test_returns_true_on_immediate_condition(self):
        from utils.wait import wait_for
        result = wait_for(lambda: True, timeout=5, interval=1)
        assert result is True

    def test_raises_timeout_error(self, monkeypatch):
        import utils.wait as wait_mod
        import time as _time

        tick = {"n": 0}

        def fake_monotonic():
            tick["n"] += 1
            return tick["n"] * 10  # each call is 10 units ahead → quickly past deadline

        monkeypatch.setattr(wait_mod.time, "monotonic", fake_monotonic)
        monkeypatch.setattr(wait_mod.time, "sleep", lambda x: None)

        with pytest.raises(TimeoutError, match="wait_for timed out after 5s waiting for: my cond"):
            wait_mod.wait_for(lambda: False, timeout=5, interval=1, description="my cond")

    def test_resolves_on_second_poll(self, monkeypatch):
        import utils.wait as wait_mod

        counter = {"n": 0}
        start = [None]

        calls = {"mono": 0}

        def fake_monotonic():
            calls["mono"] += 1
            return calls["mono"] * 0.001  # tiny increments, never hits 100

        monkeypatch.setattr(wait_mod.time, "monotonic", fake_monotonic)
        monkeypatch.setattr(wait_mod.time, "sleep", lambda x: None)

        call_count = {"n": 0}
        def cond():
            call_count["n"] += 1
            return call_count["n"] >= 3

        result = wait_mod.wait_for(cond, timeout=100, interval=0)
        assert result is True
        assert call_count["n"] == 3

    def test_description_in_error(self, monkeypatch):
        import utils.wait as wait_mod
        tick = {"n": 0}
        def fake_monotonic():
            tick["n"] += 1
            return tick["n"] * 10
        monkeypatch.setattr(wait_mod.time, "monotonic", fake_monotonic)
        monkeypatch.setattr(wait_mod.time, "sleep", lambda x: None)
        with pytest.raises(TimeoutError, match="scheduler job"):
            wait_mod.wait_for(lambda: False, timeout=1, description="scheduler job")


# ── utils.step ────────────────────────────────────────────────────────────────

class TestStep:
    def setup_method(self):
        import utils.step as s
        s.reset()

    def test_step_records_success(self):
        import utils.step as s
        with s.step("login to app"):
            pass
        assert s.snapshot() == [("login to app", True)]

    def test_step_records_failure_and_reraises(self):
        import utils.step as s
        with pytest.raises(ValueError, match="boom"):
            with s.step("failing action"):
                raise ValueError("boom")
        assert s.snapshot() == [("failing action", False)]

    def test_multiple_steps_ordered(self):
        import utils.step as s
        with s.step("step 1"):
            pass
        with pytest.raises(RuntimeError):
            with s.step("step 2"):
                raise RuntimeError("fail")
        assert s.snapshot() == [("step 1", True), ("step 2", False)]

    def test_reset_clears_all(self):
        import utils.step as s
        with s.step("x"):
            pass
        s.reset()
        assert s.snapshot() == []

    def test_snapshot_returns_copy(self):
        import utils.step as s
        with s.step("a"):
            pass
        snap = s.snapshot()
        snap.clear()
        assert len(s.snapshot()) == 1

    def test_step_method_decorator_records(self):
        import utils.step as s

        class FakePage:
            def action(self):
                pass

        decorated = s.step_method("click submit")(FakePage.action)
        page = FakePage()
        decorated(page)
        steps = s.snapshot()
        assert any("click submit" in desc for desc, _ in steps)

    def test_step_method_decorator_on_failure(self):
        import utils.step as s

        class FakePage:
            def action(self):
                raise RuntimeError("click failed")

        decorated = s.step_method("click button")(FakePage.action)
        page = FakePage()
        with pytest.raises(RuntimeError):
            decorated(page)
        steps = s.snapshot()
        assert any(desc == "click button" and not ok for desc, ok in steps)
