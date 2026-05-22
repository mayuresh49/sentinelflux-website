### Endpoint Scope

**HTTP Method:** POST  
**Full Path:** /api/v2/auth/login  

**Request Fields:**
- `username` (string, required)
- `password` (string, required)

**Allowed Response Codes:**
- 200 - Successful login
- 401 - Unauthorized (invalid credentials)
- 429 - Too Many Requests (account locked after 5 failed attempts)

### TC_001 — Successful Login with Valid Credentials

**Pre-conditions:**
- User "admin" exists with valid password "admin123"

**Request:**
- Method: POST
- Path: /api/v2/auth/login
- Headers: Content-Type: application/json
- Body: 
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```

**Steps:**
1. No additional setup required as this is a login.
2. Send POST /api/v2/auth/login with the exact request body and headers above.
3. Assert response status code is 200.

**Expected Result:** HTTP 200 — The response should contain session token or cookie.

**Validation:**
- Response field assertions (e.g., check for presence of a valid session token/cookie)
- Schema check (e.g., response.data.sessionToken)

**Category:** positive

**Status:** not_automated

### TC_002 — Failed Login with Invalid Credentials

**Pre-conditions:**
- User "admin" exists with valid password "admin123"

**Request:**
- Method: POST
- Path: /api/v2/auth/login
- Headers: Content-Type: application/json
- Body: 
  ```json
  {
    "username": "admin",
    "password": "wrongpassword"
  }
  ```

**Steps:**
1. No additional setup required as this is a login.
2. Send POST /api/v2/auth/login with the exact request body and headers above.
3. Assert response status code is 401.

**Expected Result:** HTTP 401 — The response should indicate unauthorized access.

**Validation:**
- Response field assertions (e.g., check for error message "Invalid username or password")
- Schema check (e.g., response.data.errorCode == "INVALID_CREDENTIALS")

**Category:** negative

**Status:** not_automated

### TC_003 — Account Lockout After 5 Failed Login Attempts

**Pre-conditions:**
- User "admin" exists with valid password "admin123"
- User has attempted to login 4 times with incorrect credentials previously.

**Request:**
- Method: POST
- Path: /api/v2/auth/login
- Headers: Content-Type: application/json
- Body: 
  ```json
  {
    "username": "admin",
    "password": "wrongpassword"
  }
  ```

**Steps:**
1. No additional setup required as this is a login.
2. Send POST /api/v2/auth/login with the exact request body and headers above.
3. Assert response status code is 429.

**Expected Result:** HTTP 429 — The response should indicate account lockout due to too many requests.

**Validation:**
- Response field assertions (e.g., check for error message "Account locked")
- Schema check (e.g., response.data.errorCode == "ACCOUNT_LOCKED")

**Category:** negative

**Status:** not_automated

### TC_004 — Successful Login with Case-Sensitive Username

**Pre-conditions:**
- User "Admin" exists with valid password "admin123"

**Request:**
- Method: POST
- Path: /api/v2/auth/login
- Headers: Content-Type: application/json
- Body: 
  ```json
  {
    "username": "Admin",
    "password": "admin123"
  }
  ```

**Steps:**
1. No additional setup required as this is a login.
2. Send POST /api/v2/auth/login with the exact request body and headers above.
3. Assert response status code is 200.

**Expected Result:** HTTP 200 — The response should contain session token or cookie.

**Validation:**
- Response field assertions (e.g., check for presence of a valid session token/cookie)
- Schema check (e.g., response.data.sessionToken)

**Category:** positive

**Status:** not_automated
