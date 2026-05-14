"""Backward-compat shim — re-exports everything from the config subpackage."""
from dashboard.routers.config import (  # noqa: F401
    router,
    _load_config,
    _save_config,
    _load_assignments,
    _save_assignments,
    _all_tests,
    assignments_summary_by_feature,
    get_test_type_for_index,
    get_generation_categories_instruction,
    get_generation_type_instruction,
)
