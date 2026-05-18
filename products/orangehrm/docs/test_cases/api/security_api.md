### TC Index Table
| ID       | Scenario                                 | Type     | Status           | Script      |
|----------|--------------------------------------------|----------|------------------|-------------|
| OH-API-029  | Authenticate user and create session        | positive | not_automated    |             |
| OH-API-030  | Attempt to authenticate with invalid credentials | negative | not_automated    |             |
| OH-API-031  | List all employees                         | positive | not_automated    |             |
| OH-API-032  | Create a new employee record               | positive | not_automated    |             |
| OH-API-033  | Retrieve a specific employee by empNumber   | positive | not_automated    |             |
| OH-API-034  | Update employee personal details           | positive | not_automated    |             |
| OH-API-035  | Delete an employee                         | positive | not_automated    |             |
| OH-API-036  | List all configured leave types            | positive | not_automated    |             |
| OH-API-037  | Submit a leave request                     | positive | not_automated    |             |
| OH-API-038  | List system users (Admin role only)        | positive | not_automated    |             |
| OH-API-039  | Create a new system user                   | positive | not_automated    |             |

### OH-API-029 — Authenticate user and create session
**Pre-conditions:**
- Admin role with access to API server
- API server is running

**Test Data:**
| Field | Value |
|---|---|
| username | admin |
| password | Admin123! |

**Steps:**
1. Send POST /auth/login with the exact request body and headers above
2. Assert response status code is 200

**Expected Result:** HTTP 200 — Response body must contain a sessionToken field.

**Validation:**
- Response field assertions (e.g. response.data.sessionToken is present)
- Schema check (e.g. response.data contains a sessionToken)

**Category:** positive
**Status:** not_automated### OH-API-030 — Attempt to authenticate with invalid credentials
**Pre-conditions:**
- API server is running
- Invalid username and password
**Test Data:**
| Field | Value |
|---|---|
| username | invalid |
| password | Invalid123! |
**Steps:**
1. Send POST /auth/login with the exact request body and headers above.
2. Assert response status code is 401.
**Expected Result:** HTTP 401 — describe what the response body must contain (exact fields and values where applicable).
**Validation:** 
- Response field assertions (e.g. response.error.message == "Invalid credentials")
- Schema check (e.g. response.error contains a message)
**Category:** negative
**Status:** not_automated### OH-API-031 — List all employees

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: GET
- Path: /pim/employees
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send GET /pim/employees with the exact request headers above
3. Assert response status code is 200

**Expected Result:** HTTP 200 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.length > 0)
- Schema check (e.g. response.data is an array of employee records)

**Category:** positive

**Status:** not_automated

### OH-API-032 — Create a new employee record

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: POST
- Path: /pim/employees
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json
- Body: firstName=John, lastName=Doe, middleName=William, dateOfBirth=1980-05-24

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send POST /pim/employees with the exact request body and headers above
3. Assert response status code is 201

**Expected Result:** HTTP 201 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.empNumber is present)
- Schema check (e.g. response.data contains an empNumber)

**Category:** positive

**Status:** not_automated

### OH-API-033 — Retrieve a specific employee by empNumber

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: GET
- Path: /pim/employees/5
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send GET /pim/employees/5 with the exact request headers above
3. Assert response status code is 200

**Expected Result:** HTTP 200 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.empNumber == 5)
- Schema check (e.g. response.data contains an empNumber)

**Category:** positive

**Status:** not_automated

### OH-API-034 — Update employee personal details

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: PUT
- Path: /pim/employees/5/personal-details
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json
- Body: firstName=Johnny, lastName=Doe

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send PUT /pim/employees/5/personal-details with the exact request body and headers above
3. Assert response status code is 200

**Expected Result:** HTTP 200 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.firstName == "Johnny")
- Schema check (e.g. response.data contains firstName)

**Category:** positive

**Status:** not_automated

### OH-API-035 — Delete an employee

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: DELETE
- Path: /pim/employees?empNumber=5
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send DELETE /pim/employees?empNumber=5 with the exact request headers above
3. Assert response status code is 204

**Expected Result:** HTTP 204 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. no content)
- Schema check (e.g. response has no data)

**Category:** positive

**Status:** not_automated

### OH-API-036 — List all configured leave types

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: GET
- Path: /leave/leave-types
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send GET /leave/leave-types with the exact request headers above
3. Assert response status code is 200

**Expected Result:** HTTP 200 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.length > 0)
- Schema check (e.g. response.data is an array of leave types)

**Category:** positive

**Status:** not_automated

### OH-API-037 — Submit a leave request

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: POST
- Path: /leave/leave-requests
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json
- Body: employeeId=5, leaveTypeId=1, fromDate=2023-10-01, toDate=2023-10-07

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send POST /leave/leave-requests with the exact request body and headers above
3. Assert response status code is 201

**Expected Result:** HTTP 201 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.requestId is present)
- Schema check (e.g. response.data contains a requestId)

**Category:** positive

**Status:** not_automated

### OH-API-038 — List system users (Admin role only)

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: GET
- Path: /admin/users
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send GET /admin/users with the exact request headers above
3. Assert response status code is 200

**Expected Result:** HTTP 200 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.length > 0)
- Schema check (e.g. response.data is an array of user records)

**Category:** positive

**Status:** not_automated

### OH-API-039 — Create a new system user

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- API server is running

**Request:**
- Method: POST
- Path: /admin/users
- Headers: Authorization: Bearer <sessionToken>, Content-Type: application/json
- Body: username=newuser, password=NewUser123!, role=admin

**Steps:**
1. Authenticate and obtain session token using exact credentials from KB
2. Send POST /admin/users with the exact request body and headers above
3. Assert response status code is 201

**Expected Result:** HTTP 201 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.userId is present)
- Schema check (e.g. response.data contains a userId)

**Category:** positive

**Status:** not_automated
