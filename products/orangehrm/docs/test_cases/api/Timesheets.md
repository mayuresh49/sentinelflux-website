# Test Case Document — API Timesheets

**Product:** OrangeHRM
**Layer:** API
**Module:** Timesheets

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| OH-API-014 | GET /timesheets returns 200 with list | positive | automated | test_Timesheets.py |
| OH-API-015 | POST /timesheets with valid data returns 201 | positive | automated | test_Timesheets.py |
| OH-API-016 | PUT /timesheets/{id} with valid data returns 200 | positive | automated | test_Timesheets.py |
| OH-API-017 | DELETE /timesheets/{id} with valid id returns 204 | positive | automated | test_Timesheets.py |
| OH-API-018 | GET /timesheets unauthenticated returns 401 | security | automated | test_Timesheets.py |
| OH-API-019 | GET /timesheets insufficient permissions returns 403 | security | automated | test_Timesheets.py |
| OH-API-020 | POST /timesheets missing empNumber returns 400 | negative | automated | test_Timesheets.py |
| OH-API-021 | POST /timesheets invalid date format returns 400 | negative | automated | test_Timesheets.py |
| OH-API-022 | PUT /timesheets non-existent id returns 404 | negative | automated | test_Timesheets.py |
| OH-API-023 | DELETE /timesheets non-existent id returns 404 | negative | automated | test_Timesheets.py |
| OH-API-024 | GET /timesheets with no entries returns empty array | edge | automated | test_Timesheets.py |
| OH-API-025 | POST /timesheets with minimum required fields returns 201 | positive | automated | test_Timesheets.py |
| OH-API-026 | PUT /timesheets with empty body returns 200 | edge | automated | test_Timesheets.py |
| OH-API-027 | POST /timesheets with non-existent empNumber returns 400 | negative | automated | test_Timesheets.py |
| OH-API-028 | PUT /timesheets invalid hours value returns 400 | negative | automated | test_Timesheets.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

| Method | Path | Description |
|---|---|---|
| GET | /api/v2/timesheets | List all timesheets |
| POST | /api/v2/timesheets | Create a timesheet entry |
| PUT | /api/v2/timesheets/{timesheetId} | Update a timesheet entry |
| DELETE | /api/v2/timesheets/{timesheetId} | Delete a timesheet entry |

**Request Fields (POST/PUT):**

| Field | Type | Required | Description |
|---|---|---|---|
| empNumber | Integer | Yes (POST) | Employee ID; must reference an existing employee |
| date | String | Yes (POST) | Date in YYYY-MM-DD format |
| hours | Float | Yes (POST) | Hours worked; must be positive |
| description | String | No | Optional work description |

**Response Codes:** 200 OK · 201 Created · 204 No Content · 400 Bad Request · 401 Unauthorized · 403 Forbidden · 404 Not Found

---

## Detailed Test Cases

### OH-API-014 — GET /timesheets Returns 200 With List

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login (username=Admin, password=admin123)
- At least one timesheet record exists

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers: Authorization: Bearer {token}

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send GET /api/v2/timesheets with Authorization header
3. Assert response status code is 200 and body is a list

**Expected Result:** HTTP 200 — response body is a JSON array (list) of timesheet objects.

**Category:** positive

**Status:** automated

---

### OH-API-015 — POST /timesheets With Valid Data Returns 201

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee with empNumber=1 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/timesheets
- Body: empNumber=1, date=2023-04-15, hours=8.0, description="Worked on project XYZ"

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send POST /api/v2/timesheets with valid payload
3. Assert response status is 201 and body contains empNumber, date, hours fields

**Expected Result:** HTTP 201 — response body contains empNumber, date, and hours fields matching the submitted values.

**Category:** positive

**Status:** automated

---

### OH-API-016 — PUT /timesheets/{id} With Valid Data Returns 200

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=1 exists in the system

**Request:**
- Method: PUT
- Path: /api/v2/timesheets/1
- Body: hours=8.5, description="Updated description for project XYZ"

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send PUT /api/v2/timesheets/1 with update payload
3. Assert response status is 200 and body contains updated hours and description

**Expected Result:** HTTP 200 — response body reflects the updated hours and description values.

**Category:** positive

**Status:** automated

---

### OH-API-017 — DELETE /timesheets/{id} With Valid ID Returns 204

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=1 exists in the system

**Request:**
- Method: DELETE
- Path: /api/v2/timesheets/1

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send DELETE /api/v2/timesheets/1
3. Assert response status is 204 and body is empty

**Expected Result:** HTTP 204 — empty response body; timesheet record is removed.

**Category:** positive

**Status:** automated

---

### OH-API-018 — GET /timesheets Unauthenticated Returns 401

**Pre-conditions:**
- No Authorization header provided

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers: (no Authorization)

**Steps:**
1. Send GET /api/v2/timesheets with no Authorization header
2. Assert response status is 401
3. Assert response body contains an authentication error message

**Expected Result:** HTTP 401 — request rejected with unauthorized error. No timesheet data exposed.

**Category:** security

**Status:** automated

---

### OH-API-019 — GET /timesheets Insufficient Permissions Returns 403

**Pre-conditions:**
- Authenticated as a user with insufficient permissions (non-admin role)

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers: Authorization: Bearer {restricted_token}

**Steps:**
1. Authenticate as a restricted user and obtain Bearer token
2. Send GET /api/v2/timesheets with that token
3. Assert response status is 403

**Expected Result:** HTTP 403 — request rejected with forbidden error. No timesheet data exposed.

**Category:** security

**Status:** automated

---

### OH-API-020 — POST /timesheets Missing empNumber Returns 400

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login

**Request:**
- Method: POST
- Path: /api/v2/timesheets
- Body: date=2023-04-15, hours=8.0, description="Worked on project XYZ" (no empNumber)

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send POST /api/v2/timesheets with payload missing empNumber
3. Assert response status is 400

**Expected Result:** HTTP 400 — response body contains a validation error indicating empNumber is required.

**Category:** negative

**Status:** automated

---

### OH-API-021 — POST /timesheets Invalid Date Format Returns 400

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login

**Request:**
- Method: POST
- Path: /api/v2/timesheets
- Body: empNumber=1, date=15-04-2023 (DD-MM-YYYY instead of YYYY-MM-DD), hours=8.0

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send POST /api/v2/timesheets with date in wrong format (15-04-2023)
3. Assert response status is 400

**Expected Result:** HTTP 400 — response body indicates invalid date format. Timesheet is not created.

**Category:** negative

**Status:** automated

---

### OH-API-022 — PUT /timesheets Non-existent ID Returns 404

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=9999 does not exist

**Request:**
- Method: PUT
- Path: /api/v2/timesheets/9999
- Body: hours=8.5, description="Updated"

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send PUT /api/v2/timesheets/9999 (non-existent ID)
3. Assert response status is 404

**Expected Result:** HTTP 404 — response body indicates the timesheet was not found.

**Category:** negative

**Status:** automated

---

### OH-API-023 — DELETE /timesheets Non-existent ID Returns 404

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=9999 does not exist

**Request:**
- Method: DELETE
- Path: /api/v2/timesheets/9999

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send DELETE /api/v2/timesheets/9999 (non-existent ID)
3. Assert response status is 404

**Expected Result:** HTTP 404 — response body indicates the timesheet was not found.

**Category:** negative

**Status:** automated

---

### OH-API-024 — GET /timesheets With No Entries Returns Empty Array

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- No timesheet records exist in the system

**Request:**
- Method: GET
- Path: /api/v2/timesheets
- Headers: Authorization: Bearer {token}

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send GET /api/v2/timesheets when no records exist
3. Assert response status is 200 and body is an empty list

**Expected Result:** HTTP 200 — response body is an empty JSON array (`[]`).

**Category:** edge

**Status:** automated

---

### OH-API-025 — POST /timesheets With Minimum Required Fields Returns 201

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee with empNumber=1 exists

**Request:**
- Method: POST
- Path: /api/v2/timesheets
- Body: empNumber=1, date=2023-04-15, hours=8.0 (no description)

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send POST /api/v2/timesheets with only the required fields (no description)
3. Assert response status is 201

**Expected Result:** HTTP 201 — timesheet created successfully with only the minimum required fields provided.

**Category:** positive

**Status:** automated

---

### OH-API-026 — PUT /timesheets With Empty Body Returns 200

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=1 exists

**Request:**
- Method: PUT
- Path: /api/v2/timesheets/1
- Body: {} (empty object)

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send PUT /api/v2/timesheets/1 with an empty JSON body
3. Assert response status is 200

**Expected Result:** HTTP 200 — no-op update; existing timesheet values unchanged.

**Category:** edge

**Status:** automated

---

### OH-API-027 — POST /timesheets With Non-existent empNumber Returns 400

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- No employee with empNumber=9999 exists

**Request:**
- Method: POST
- Path: /api/v2/timesheets
- Body: empNumber=9999, date=2023-04-15, hours=8.0, description="Worked on project XYZ"

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send POST /api/v2/timesheets with empNumber=9999 (non-existent employee)
3. Assert response status is 400

**Expected Result:** HTTP 400 — response body indicates the employee does not exist. Timesheet is not created.

**Category:** negative

**Status:** automated

---

### OH-API-028 — PUT /timesheets Invalid Hours Value Returns 400

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Timesheet with ID=1 exists

**Request:**
- Method: PUT
- Path: /api/v2/timesheets/1
- Body: hours=-5, description="Updated description"

**Steps:**
1. Authenticate as Admin and obtain Bearer token
2. Send PUT /api/v2/timesheets/1 with hours=-5 (negative value)
3. Assert response status is 400

**Expected Result:** HTTP 400 — response body indicates the hours value is invalid (must be positive). Record is not updated.

**Category:** negative

**Status:** automated
