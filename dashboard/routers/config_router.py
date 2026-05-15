"""Backward-compat shim — re-exports everything from the config subpackage."""
from dashboard.routers.config import (  # noqa: F401
    _all_tests,
    _load_assignments,
    _load_config,
    _save_assignments,
    _save_config,
    assignments_summary_by_feature,
    get_generation_categories_instruction,
    get_generation_type_instruction,
    get_test_type_for_index,
    router,
)
