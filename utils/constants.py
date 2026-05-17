# AI assertion thresholds — import from here, never hardcode in test scripts.
AI_CONFIDENCE_THRESHOLD = 0.70   # minimum acceptable confidence score for AI outputs
AI_TEXT_SIMILARITY_RATIO = 0.75  # minimum difflib ratio for fuzzy text comparison
AI_RESPONSE_TIMEOUT_S = 30.0     # maximum latency budget for AI endpoint calls (seconds)

LOCATOR_HEAL_TIMEOUT_MS = 2000
DEFAULT_BROWSER_TIMEOUT_MS = 10000
MISTRAL_CLOUD_TIMEOUT_S = 120
MISTRAL_LOCAL_TIMEOUT_S = 300

# Generic polling timeouts for async/scheduler-based test steps (seconds).
# Product-specific timeouts live in products/<product>/constants.py.
REPORT_GEN_TIMEOUT = 120
EMAIL_DELIVERY_TIMEOUT = 30
DATA_SYNC_TIMEOUT = 90
WORKFLOW_STEP_TIMEOUT = 60
POLL_INTERVAL_DEFAULT = 2
