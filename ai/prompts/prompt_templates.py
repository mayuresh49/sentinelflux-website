class PromptTemplate:
    def __init__(self, template: str):
        self.template = template

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)


LOCATOR_HEALING_PROMPT = PromptTemplate("""
A UI locator is broken. Suggest a replacement CSS selector.

HTML: {html}
Broken Locator: {broken_locator}
Page URL: {url}

STRICT RULES:
1. ONLY suggest a selector that matches an element present in the HTML above.
   If the element cannot be found, respond with exactly: NOT_FOUND
2. Do NOT invent attributes, IDs, or class names not present in the HTML.
3. Prefer stable attributes in this order: id > name > data-testid > aria-label > role > class.
4. Respond with the selector string only — no explanation, no markdown, no JSON.
""")

TEST_GENERATION_PROMPT = PromptTemplate("""
Generate a pytest test for the following scenario.

Scenario: {scenario}
Type: {test_type}
Target: {target}
Expected outcome: {expected_outcome}

Include positive, edge-case, and negative-path coverage.
Return valid pytest test code only.
""")

API_TEST_GENERATION_PROMPT = PromptTemplate("""
Generate a pytest API test suite for the following endpoint.

API Name: {api_name}
Endpoint: {endpoint}
Method: {method}
Description: {description}
Payload: {payload_description}
Expected status codes: {expected_status}

{kb_context}

The suite should include:
- standard success case
- edge cases for boundary values and optional inputs
- negative scenarios for invalid payloads, missing fields, and non-existing resource IDs
- response schema and status validation
- error-handling assertions

Return valid pytest test functions only.
""")

TEST_CASE_DOC_PROMPT = PromptTemplate("""
Generate a detailed test case document for the form located at {page_url}.

Knowledge Base Context:
{kb_context}
{exploration_context}
STRICT RULES — violating these will produce incorrect documentation:
1. ONLY test fields that are explicitly listed in the Knowledge Base Context or the Live Exploration Context above.
   If a Live Exploration Context is present, it overrides KB on field names, selectors, and validation messages — it is ground truth.
   Do NOT invent fields from training data.
2. Do NOT use knowledge from your training data about this application. Rely solely on the KB and exploration contexts.
3. If a field is not listed in either context, it does not exist on this form — do not include it.
4. Use exact test credentials and data from the KB (e.g. actual usernames, passwords, known field values).
5. Describe expected results based only on documented business rules, not assumptions.
6. Begin the document with a "Fields in Scope" section listing every KB-documented field, its type, whether it is required, and its validation rule.
7. NEVER write a heading that spans multiple TCs (e.g. "### PREFIX-036 to PREFIX-043"). Each test case MUST have its own numbered heading and complete content — no placeholders, no "see index above".
8. NEVER write a one-liner as the full test case body. Every section listed below is mandatory for each TC.
9. Minimum 3 numbered Steps per test case. Never collapse multiple actions into a single step.
10. Pre-conditions must list at minimum: the user role, the application URL, and any prerequisite data state.
{tc_id_instruction}
Format EVERY test case using EXACTLY this structure:

### TC_ID — Test Case Title

**Pre-conditions:**
- User role (e.g. Admin, ESS)
- Starting URL
- Any required data state

**Test Data:**
| Field | Value |
|---|---|
| FieldName | exact value (from KB — never invented) |

**Steps:**
1. Navigate to the exact URL
2. Perform the specific user action with exact input values
3. (add more steps — minimum 3 total)

**Expected Result:** Explicit pass criteria. Not just "Success" — state what the user sees, what persists, what message appears.

**Validation:** List specific field-level or page-level assertions to verify.

**Category:** positive | negative | edge | security

**Status:** not_automated

Form Description:
{form_description}

Output full markdown documentation suitable for version control.
""")

API_TEST_CASE_DOC_PROMPT = PromptTemplate("""
Generate a detailed API test case document for the endpoint {endpoint} ({method}).

Knowledge Base Context:
{kb_context}

API Context:
{api_context}
{source_context}
STRICT RULES — violating these will produce incorrect documentation:
1. If Source Context is provided above, treat it as the authoritative specification. Use exact endpoint paths, methods, parameters, schemas, and status codes from it.
2. If no Source Context, rely solely on KB/API Context — do NOT invent fields or codes from training data.
3. Do NOT invent request fields, error codes, or behaviors not present in any provided context.
4. Begin the document with an explicit "Endpoint Scope" section listing: HTTP method, full path, all request fields (name / type / required or optional / constraints), and every documented response code with its meaning.
5. When Source Context is an OpenAPI spec, generate one test case per documented response code.
6. NEVER write a heading that spans multiple TCs (e.g. "### PREFIX-010 to PREFIX-015"). Each test case MUST have its own numbered heading and complete content — no placeholders, no "see index above".
7. NEVER write a one-liner as the full test case body. Every section listed below is mandatory for each TC.
8. Minimum 3 numbered Steps per test case: (1) setup/auth step, (2) send-request step with exact payload, (3) assertion step.
9. Expected Result must state the exact status code AND the key fields to assert in the response body.
{tc_id_instruction}
{categories_instruction}

Generate test cases only for the enabled categories above. Do not include excluded categories.

Format EVERY test case using EXACTLY this structure:

### TC_ID — Test Case Title

**Pre-conditions:**
- Auth state (e.g. "Authenticated as Admin via POST /auth/login")
- Any prerequisite data (e.g. "Employee ID 5 exists in the system")

**Request:**
- Method: HTTP_METHOD
- Path: /api/v2/resource/{{id}}
- Headers: key: value
- Body: field1=value1, field2=value2 (list each field explicitly)

**Steps:**
1. Authenticate and obtain session token/cookie using exact credentials from KB
2. Send METHOD /path with the exact request body and headers above
3. Assert response status code is NNN

**Expected Result:** HTTP NNN — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data[0].userName == "Admin")
- Schema check (e.g. response.data is an array)

**Category:** positive | negative | edge | security

**Status:** not_automated

Output full markdown documentation suitable for version control.
""")

TEST_SCRIPT_GEN_PROMPT = PromptTemplate("""
You are a test automation engineer. Convert the following test case document into a runnable pytest file.

Domain: {domain}
Feature: {feature_name}

--- FRAMEWORK CONVENTIONS ---
{conventions}

--- AVAILABLE PAGE OBJECTS ---
{page_catalog}
{exploration_context}
--- TEST CASE DOCUMENT ---
{test_case_doc}

--- RULES ---
- Output ONLY valid Python code. No markdown, no explanations, no code fences.
- Follow the conventions above exactly (fixtures, imports, markers, assertion style).
- ONLY import page objects listed in the "AVAILABLE PAGE OBJECTS" section above.
  Do NOT invent page class names or module paths not listed there.
  If no page object is listed, use only the fixtures and patterns from FRAMEWORK CONVENTIONS.
- One pytest function per test case. Name: test_{{action}}_{{expected_outcome}}.
- If a test case has an ID in the document (format PRODUCT-LAYER-NNN, e.g. RB-API-001), use it as a prefix in the function name: test_{{ID_underscored}}_{{description}} (hyphens → underscores). Example: "RB-API-001" → test_RB_API_001_create_booking.{tc_prefix_hint}
- SKIP any test case with status `not_automatable` — do not generate a pytest function for it.
- For test cases with status `async_dependent`: generate the function, add `@pytest.mark.async_wait` and `@pytest.mark.dependency` markers, and use `wait_for()` from `utils.wait` for polling steps.
- Use parametrize only when test data sets share identical steps.
- Do not add comments unless a business rule is non-obvious.
- Do not import anything not in the conventions, AVAILABLE PAGE OBJECTS, or standard library.
- NEVER hardcode URLs or credentials in test scripts. All URLs and credentials MUST come from product config fixtures (e.g. orangehrm_base_url, orangehrm_api_base_url, orangehrm_credentials, rb_api_base, rb_web_base, rb_credentials). These fixtures are loaded from config/env_{{env}}.yaml at runtime based on the --env pytest option.
- NEVER write an authenticate() helper that takes hardcoded username/password strings. For authenticated API calls use the {{product}}_client fixture (e.g. orangehrm_client). For unauthenticated API calls use {{product}}_api_base_url + requests. Pass {{product}}_credentials fixture when credentials are needed as test input.
- NEVER use rest_client for product-specific tests — it reads a generic config. Use {{product}}_client for authenticated calls and {{product}}_api_base_url for raw requests.
- All page object constructors require base_url as the second argument. Never instantiate a page object without passing the URL fixture: PageClass(page, {{product}}_base_url).
- If a LIVE APPLICATION EXPLORATION CONTEXT section is present above: every page.fill(), page.click(), and page.locator() call MUST use a selector from that context. Do NOT invent CSS selectors — if no page object exists for this feature, call page methods directly using the selectors from the exploration context.
{test_type_instruction}
{categories_instruction}
Output the complete Python file content starting with imports.
""")

FEATURE_DOC_PROMPT = PromptTemplate("""
Generate a comprehensive test case document for the feature described below.

Feature Context:
{feature_context}

Knowledge Base Context:
{kb_context}

STRICT RULES — violating these will produce incorrect documentation:
1. ONLY test fields and behaviors explicitly listed in Feature Context or Knowledge Base Context.
2. Do NOT invent fields, endpoints, or behaviors from training data knowledge of the application.
3. If a field is not listed in the KB, it does not exist in scope — do not reference it.
4. Use exact credentials, field names, and values from the KB. Do not substitute generic placeholders.
5. Base expected results only on documented business rules, not assumptions or generic HRMS patterns.
6. Begin the document with an explicit "Fields in Scope" section listing only KB-documented fields.

{categories_instruction}

Document must cover only the enabled categories above. Do not generate test cases for excluded categories.
Remaining required sections (for enabled categories only):
- Fields in Scope (explicit list from KB only — no invented fields)
- All positive (happy path) scenarios
- Negative scenarios (invalid input, missing fields, boundary violations) for KB-documented rules only
- Edge cases from the business rules
- Security-relevant cases (auth, access control) if applicable
- Integration scenarios with dependent modules

Begin the document with a Test Case Index table:
| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| {ID_PREFIX}-NNN | ... | positive/negative/edge | not_automated | — |

For each test case, use:
### {ID_PREFIX}-NNN — <title>
**Pre-conditions:** ...
**Test Data:** ...
**Steps:** numbered list
**Expected Result:** ...
**Category:** positive | negative | edge | security
**Status:** not_automated (human sets to: `automated` when script exists · `not_automatable` to exclude from script generation · `async_dependent` when the test requires a running scheduler/background job and cannot run standalone)

Output full markdown documentation.
""")