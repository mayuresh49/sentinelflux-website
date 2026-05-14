# Test Case Document — Auth API

**Product:** Restful Booker  
**Layer:** API  
**Module:** Authentication (`/auth`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-API-020 | Authenticate with valid credentials returns non-empty token | positive | automated | test_auth_api.py |
| RB-API-021 | Authenticate with invalid credentials returns null/bad response | negative | automated | test_auth_api.py |
| RB-API-022 | Delete booking without auth token is rejected (401/403) | negative | automated | test_auth_api.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

### **POST /auth**
- **Request Fields:**
  - `username` (string, required)
  - `password` (string, required)
- **Response:** `{"token": "<string>"}` on success; `{"reason": "Bad credentials"}` on failure
- **Response Codes:** `200 OK` (always; check body for success/failure)

---

## Test Cases

### RB-API-020 — Authenticate With Valid Credentials
**Test Data:** username=`admin`, password=`password123`  
**Steps:** POST /auth with valid credentials  
**Expected:** 200, token is non-empty string, not "Bad credentials"

### RB-API-021 — Authenticate With Invalid Credentials
**Test Data:** username=`wrong_user`, password=`wrong_pass`  
**Steps:** POST /auth  
**Expected:** 200, body contains `{"reason": "Bad credentials"}`, no `token` key

### RB-API-022 — Delete Without Auth Token Is Rejected
**Pre-conditions:** A booking exists  
**Steps:**
1. Create booking with authenticated client
2. Attempt DELETE /booking/{id} with unauthenticated client (empty credentials)  
**Expected:** 401 or 403
