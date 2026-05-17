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

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

- `GET /api/v2/admin/users` — admin user list (requires auth)
- `GET /api/v2/pim/employees` — employee list (requires auth)
- `DELETE /api/v2/pim/employees/{id}` — delete employee (requires auth)

---

## Detailed Test Cases

### OH-SEC-001 — Unauthenticated Request To Users Returns 401
**Marks:** `api`, `security`  
**Steps:** `GET /api/v2/admin/users` with no credentials  
**Expected:** `status_code == 401`

### OH-SEC-002 — Unauthenticated Request To Employees Returns 401
**Marks:** `api`, `security`  
**Steps:** `GET /api/v2/pim/employees` with no credentials  
**Expected:** `status_code == 401`

### OH-SEC-003 — SQL Injection In Search Does Not Return 500
**Marks:** `api`, `security`  
**Test Data:** `nameOrId = "' OR '1'='1"`  
**Steps:** Authenticated `GET /pim/employees?nameOrId=%27+OR+%271%27%3D%271`  
**Expected:** `status_code != 500`; response body does not contain `"sql"` or `"syntax error"` (case-insensitive)

### OH-SEC-004 — API Response Content-Type Is JSON
**Marks:** `api`, `security`  
**Steps:** Authenticated `GET /pim/employees`  
**Expected:** `status_code == 200`; `Content-Type` header contains `application/json`

### OH-SEC-005 — X-Content-Type-Options Header Present
**Marks:** `api`, `security`  
**Steps:** Authenticated `GET /pim/employees`  
**Expected:** `X-Content-Type-Options` header value is `nosniff` (case-insensitive)

### OH-SEC-006 — Delete Employee Without Auth Is Rejected
**Marks:** `api`, `security`  
**Steps:** `DELETE /api/v2/pim/employees/1` with no auth token  
**Expected:** `status_code in (401, 405)` — server rejects the request before or at auth check

### OH-SEC-007 — Arbitrary Origin Not Reflected In CORS
**Marks:** `api`, `security`  
**Steps:** Authenticated `GET /pim/employees` with `Origin: https://evil.example.com`  
**Expected:** `Access-Control-Allow-Origin` response header is NOT `https://evil.example.com`
