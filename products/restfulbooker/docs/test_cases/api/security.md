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
**Pre-conditions:**
- User Role: Unauthenticated
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required Data State: Auth Token is not present

**Test Data:**
| Field | Value |
|---|---|
| bookingId | any valid existing booking id |

**Steps:**
1. Perform a POST request to `https://restful-booker.herokuapp.com/auth` with incorrect credentials (admin / invalid password)
2. Obtain an auth token using the response from step 1
3. Replace `{id}` in `DELETE /booking/{id}` with the obtained booking id from test data
4. Send a DELETE request to the modified endpoint without including the auth token

**Expected Result:** Response status code is either 401 or 403

**Validation:** Verify that the response status code is within (401, 403) range

**Category:** positive
**Status:** not_automated### RB-SEC-002 — Update Booking Without Auth Returns 401/403
**Pre-conditions:**
- User role: Authenticated
- Starting URL: https://restful-booker.herokuapp.com/#/wrap
- Required data state: Existing booking with valid ID
**Test Data:**
| Field | Value |
|---|---|
| Booking ID | (existent bookings' ID from KB) |
**Steps:**
1. Send a PUT request to `/booking/{id}` with full payload but without credentials
2. Verify the response status code is either 401 or 403
**Expected Result:** Response status code is either 401 or 403
**Validation:** Check the HTTP status code from the response
**Category:** negative
**Status:** not_automated### RB-SEC-003 — SQL Injection In Search Does Not Cause 500
**Pre-conditions:**
- User Role: Unauthenticated
- Starting URL: https://restful-booker.herokuapp.com/booking?firstname=...&lastname=...
- Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| firstname | "' OR '1'='1" |
| lastname | "' OR '1'='1" |

**Steps:**
1. Perform a GET request on the specified URL with the provided test data.
2. Check the response status code.

**Expected Result:** The response status code is not equal to 500.

**Validation:** The response body does not contain "sql" (case-insensitive).

**Category:** positive
**Status:** not_automated### RB-SEC-004 — API Response Content-Type Is JSON
**Pre-conditions:**
- User role: None (anonymous user)
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required data state: No authentication required for GET operations

**Test Data:**
| Field | Value |
|---|---|
| Endpoint | GET /booking |

**Steps:**
1. Perform the GET /booking request without authentication
2. Check the response headers

**Expected Result:** The response should contain a status code of 200 and a `Content-Type` header containing either 'application/json' or 'json'.

**Validation:** Assert that the status code is 200, and that the `Content-Type` header contains either 'application/json' or 'json'.

**Category:** positive
**Status:** not_automated### RB-SEC-005 — Nonexistent Booking ID Returns 404
**Pre-conditions:**
- User Role: Not Applicable (API Request)
- Starting URL: https://restful-booker.herokuapp.com/auth (for obtaining token if needed)
- Required Data State: Auth Token (if applicable)

**Test Data:**
| Field | Value |
|---|---|
| Booking ID | 999999999 |

**Steps:**
1. Make a GET request to `https://restful-booker.herokuapp.com/booking/{BookingID}` with the provided Auth Token if required.
2. Verify the response status code.

**Expected Result:** Status Code: 404 Not Found

**Validation:** Verify that the status code equals 404.

**Category:** positive
**Status:** not_automated