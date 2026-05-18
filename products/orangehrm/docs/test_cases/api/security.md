# Test Case Document — API Security

**Product:** OrangeHRM  
**Layer:** API  
**Module:** Security — `/api/v2/`

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-SEC-001 | Unauthenticated GET /admin/users returns 401 | negative | automated | test_security_api.py |
| OH-SEC-002 | Unauthenticated GET /pim/employees returns 401 | negative | automated | test_security_api.py |
| OH-SEC-003 | SQL injection in employee search does not return 500 or expose SQL | negative | automated | test_security_api.py |
| OH-SEC-004 | API response Content-Type is application/json | positive | automated | test_security_api.py |
| OH-SEC-005 | X-Content-Type-Options: nosniff header is present | positive | automated | test_security_api.py |
| OH-SEC-006 | DELETE /pim/employees/{id} without auth is rejected (401 or 405) | negative | automated | test_security_api.py |
| OH-SEC-007 | Arbitrary Origin header is not reflected in CORS response | negative | automated | test_security_api.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

- `GET /api/v2/admin/users` — admin user list (requires auth)
- `GET /api/v2/pim/employees` — employee list (requires auth)
- `DELETE /api/v2/pim/employees/{id}` — delete employee (requires auth)

---

## Detailed Test Cases

### OH-SEC-001 — Unauthenticated Request To Users Returns 401

**Pre-conditions:**
- User Role: None (Unauthenticated)
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2/admin/users
- Required Data State: No Credentials

**Test Data:**
| Field | Value |
|---|---|
| Username | N/A (Unauthenticated) |
| Password | N/A (Unauthenticated) |

**Steps:**
1. Make a GET request to the specified URL without providing credentials.
2. Verify no authentication is provided.
3. Observe the response status code.

**Expected Result:** The response status code is 401 (Unauthorized).

**Validation:** Assert that the HTTP status code is equal to 401.

**Category:** Positive

**Status:** Not Automated

### OH-SEC-002 — Unauthenticated Request To Employees Returns 401

**Pre-conditions:**
- User Role: None, Starting URL: REST API Base URL, Required Data State: No credentials provided

**Test Data:**
| Field | Value |
|---|---|
| HTTP Method | GET |
| Endpoint | /pim/employees |

**Steps:**
1. Send a GET request to the specified endpoint without providing credentials.
2. Check the response status code.

**Expected Result:** The response status code is 401 - Unauthorized.

**Validation:** Verify that the HTTP status code received equals 401.

**Category:** positive

**Status:** not_automated

### OH-SEC-003 — SQL Injection In Search Does Not Return 500

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2
- Required Data State: Authenticated

**Test Data:**
| Field | Value |
|---|---|
| nameOrId | ' OR '1'='1' |

**Steps:**
1. Send GET request to `/pim/employees?nameOrId=%27+OR+%271%27%3D%271`
2. Verify response status code is not 500
3. Check response body does not contain "sql" or "syntax error" (case-insensitive)

**Expected Result:** Response status code is not 500 and response body does not contain "sql" or "syntax error"

**Validation:** Verify response status code and response body content

**Category:** positive

**Status:** not_automated

### OH-SEC-004 — API Response Content-Type Is JSON

**Pre-conditions:**
- User Role: Admin, Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2, Required Data State: Authenticated Session

**Test Data:**
| Field | Value |
|---|---|
| Endpoint | GET /pim/employees |

**Steps:**
1. Send a GET request to the provided endpoint
2. Check if the response status code is 200
3. Verify that the Content-Type header contains application/json

**Expected Result:** Response contains expected data in JSON format

**Validation:** status_code == 200; Content-Type header contains application/json

**Category:** positive

**Status:** not_automated

### OH-SEC-005 — X-Content-Type-Options Header Present

**Pre-conditions:**
- User Role: Admin, Starting URL: /web/index.php/api/v2, Required Data State: Authenticated session

**Test Data:**
| Field | Value |
|---|---|
| API Endpoint | GET /pim/employees |

**Steps:**
1. Send GET request to the specified endpoint
2. Verify response headers

**Expected Result:** The 'X-Content-Type-Options' header value is 'nosniff' (case-insensitive)

**Validation:** Check if the 'X-Content-Type-Options' header exists and its value matches the expected one

**Category:** positive

**Status:** not_automated

### OH-SEC-006 — Delete Employee Without Auth Is Rejected

**Pre-conditions:**
- User Role: Admin or ESS
- Starting URL: /web/index.php/api/v2
- Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| empNumber | 1 |

**Steps:**
1. Send DELETE request to `/api/v2/pim/employees/{empNumber}` without an auth token

**Expected Result:** `status_code in (401, 405)` — server rejects the request before or at auth check

**Validation:** Check the HTTP response status code

**Category:** positive

**Status:** not_automated

### OH-SEC-007 — Arbitrary Origin Not Reflected In CORS

**Pre-conditions:**
- User Role: Admin/API Tester
- Starting URL: https://opensource-demo.orangehrmlive.com/web/index.php/api/v2
- Required Data State: Authenticated Session

**Test Data:**
| Field | Value |
|---|---|
| Origin | https://evil.example.com |

**Steps:**
1. Send authenticated GET request to `/pim/employees` with `Origin` header set to provided value.
2. Verify the response header for `Access-Control-Allow-Origin`.
3. Assert that the response header does not match the provided origin value.

**Expected Result:** The response header for `Access-Control-Allow-Origin` should NOT equal the provided origin value (`https://evil.example.com`).

**Validation:** Check if the response headers contain the correct `Access-Control-Allow-Origin` value, not the provided origin.

**Category:** positive

**Status:** not_automated
