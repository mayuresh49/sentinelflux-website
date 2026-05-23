### TC-01 — Successfully Submit a Leave Request

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=1
  - fromDate=2023-12-15
  - toDate=2023-12-16

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 201.

**Expected Result:** HTTP 201 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.data.leaveRequestId == "unique_leave_request_id")
- Schema check (e.g. response.data is an object)

**Category:** positive

**Status:** not_automated

### TC-02 — Attempt to Submit a Leave Request with Invalid Employee ID

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 999 does not exist in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=999
  - leaveTypeId=1
  - fromDate=2023-12-15
  - toDate=2023-12-16

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "Employee not found")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated

### TC-03 — Attempt to Submit a Leave Request with Invalid Leave Type ID

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=999
  - fromDate=2023-12-15
  - toDate=2023-12-16

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "Leave type not found")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated

### TC-04 — Attempt to Submit a Leave Request with Past Dates

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=1
  - fromDate=2022-01-01
  - toDate=2022-01-03

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "Leave dates cannot be in the past")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated

### TC-05 — Attempt to Submit a Leave Request with Invalid Date Range

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=1
  - fromDate=2023-12-16
  - toDate=2023-12-15

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "To date must be on or after from date")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated

### TC-06 — Attempt to Submit a Leave Request with Insufficient Balance

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system
- Employee has insufficient leave balance for requested period

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=1
  - fromDate=2023-12-15
  - toDate=2024-01-14

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "Insufficient leave balance")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated

### TC-07 — Attempt to Submit a Leave Request with Missing Required Fields

**Pre-conditions:**
- Authenticated as Admin via POST /auth/login
- Employee ID 5 exists in the system

**Request:**
- Method: POST
- Path: /api/v2/leave/leave-requests
- Headers:
  - Authorization: Bearer {session_token}
- Body:
  - empNumber=5
  - leaveTypeId=1
  - toDate=2023-12-16

**Steps:**
1. Authenticate and obtain session token/cookie using credentials provided in the Knowledge Base.
2. Send POST /api/v2/leave/leave-requests with the exact request body and headers above.
3. Assert response status code is 400.

**Expected Result:** HTTP 400 — describe what the response body must contain (exact fields and values where applicable).

**Validation:**
- Response field assertions (e.g. response.error == "Missing required field: fromDate")
- Schema check (e.g. response.data is an object)

**Category:** negative

**Status:** not_automated
