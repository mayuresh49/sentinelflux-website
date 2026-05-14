# Test Case Document — Leave API

**Product:** OrangeHRM  
**Layer:** API  
**Module:** Leave (`/api/v2/leave/`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-API-006 | GET /leave/leave-types returns 200 with data array | positive | automated | test_orangehrm_leave.py |
| OH-API-007 | Each leave type item contains id and name fields | positive | automated | test_orangehrm_leave.py |
| OH-API-008 | GET /leave/leave-types without auth returns 401 | negative | automated | test_orangehrm_leave.py |
| OH-API-009 | POST /leave/leave-requests with non-existent leaveTypeId returns 400 | negative | automated | test_orangehrm_leave.py |
| OH-API-010 | POST /leave/leave-requests with toDate before fromDate returns 400 | negative | automated | test_orangehrm_leave.py |
| OH-API-011 | POST /leave/leave-requests with valid data creates request | positive | not_automated | — |
| OH-API-012 | POST /leave/leave-requests missing required field returns 400 | negative | not_automated | — |
| OH-API-013 | GET /leave/leave-requests lists submitted requests | positive | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Details
- **Base:** `https://opensource-demo.orangehrmlive.com/web/index.php/api/v2`
- **Auth:** Session cookie (obtained via POST `/auth/validateCredentials`)

## Endpoints Covered
- `GET /leave/leave-types` — List all leave types
- `POST /leave/leave-requests` — Submit a leave request

## Field Validation Rules
- `leaveTypeId`: integer, must reference an existing leave type, required
- `fromDate`: string YYYY-MM-DD, required
- `toDate`: string YYYY-MM-DD, required, must be >= fromDate
- `comment`: string, optional

---

## Detailed Test Cases

### OH-API-006 — List Leave Types Returns 200
**Steps:** GET /leave/leave-types with valid session  
**Expected:** 200, body has `data` array

### OH-API-007 — Leave Type Items Have id and name
**Steps:** GET /leave/leave-types, inspect first item  
**Expected:** `id` and `name` keys present, at least 1 item

### OH-API-008 — List Leave Types Without Auth Returns 401
**Steps:** GET /leave/leave-types without any auth cookie  
**Expected:** 401 Unauthorized

### OH-API-009 — Leave Request With Invalid leaveTypeId
**Payload:** `{"leaveTypeId": 99999, "fromDate": "2099-01-01", "toDate": "2099-01-02"}`  
**Expected:** 400 or 422

### OH-API-010 — Leave Request With Invalid Date Range
**Pre-conditions:** At least one leave type exists  
**Steps:** GET leave types, extract first id; POST request with fromDate > toDate  
**Expected:** 400 or 422

### OH-API-011 — Create Leave Request With Valid Data (not_automated)
**Pre-conditions:** Valid leaveTypeId obtained from GET /leave/leave-types  
**Payload:** `{"leaveTypeId": <valid_id>, "fromDate": "2099-03-01", "toDate": "2099-03-02"}`  
**Expected:** 200 or 201; created request reflected in list

### OH-API-012 — Missing Required Field (not_automated)
**Payload:** Omit `leaveTypeId`  
**Expected:** 400 with field-specific error

### OH-API-013 — List Leave Requests (not_automatable)
**Note:** GET /leave/leave-requests may require specific employee context and may not return data on the shared demo unless a request was submitted in the same session. State-dependent; difficult to automate reliably.
