# Test Case Document — API Security

**Product:** Restful Booker  
**Layer:** API  
**Module:** Security — `/booking`, `/auth`

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-SEC-001 | DELETE /booking/{id} without auth returns 401 or 403 | negative | automated | test_security_api.py |
| RB-SEC-002 | PUT /booking/{id} without auth returns 401 or 403 | negative | automated | test_security_api.py |
| RB-SEC-003 | SQL injection in booking search does not cause 500 | negative | automated | test_security_api.py |
| RB-SEC-004 | GET /booking response Content-Type is JSON | positive | automated | test_security_api.py |
| RB-SEC-005 | GET /booking/{nonexistent-id} returns 404 | negative | automated | test_security_api.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

- `DELETE /booking/{id}` — requires auth token cookie
- `PUT /booking/{id}` — requires auth token cookie
- `GET /booking` — public; supports `firstname`/`lastname` filter params

---

## Detailed Test Cases

### RB-SEC-001 — Delete Booking Without Auth Returns 401/403
**Marks:** `api`, `security`, `sanity`  
**Steps:**
1. Create a booking using authenticated client
2. `DELETE /booking/{id}` with no credentials (raw `requests` — no cookie)  
**Expected:** `status_code in (401, 403)`

### RB-SEC-002 — Update Booking Without Auth Returns 401/403
**Marks:** `api`, `security`, `regression`  
**Steps:**
1. Create a booking using authenticated client
2. `PUT /booking/{id}` with full payload but no credentials  
**Expected:** `status_code in (401, 403)`

### RB-SEC-003 — SQL Injection In Search Does Not Cause 500
**Marks:** `api`, `security`, `regression`  
**Test Data:** `firstname = "' OR '1'='1"`, `lastname = "' OR '1'='1"`  
**Steps:** `GET /booking?firstname=...&lastname=...`  
**Expected:** `status_code != 500`; response body does not contain `"sql"` (case-insensitive)

### RB-SEC-004 — API Response Content-Type Is JSON
**Marks:** `api`, `security`, `regression`  
**Steps:** `GET /booking`  
**Expected:** `status_code == 200`; `Content-Type` header contains `application/json` or `json`

### RB-SEC-005 — Nonexistent Booking ID Returns 404
**Marks:** `api`, `security`, `regression`  
**Test Data:** booking ID = `999999999`  
**Steps:** `GET /booking/999999999`  
**Expected:** `status_code == 404`
