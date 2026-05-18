# Test Case Document — Booking API

**Product:** Restful Booker  
**Layer:** API  
**Module:** Booking (`/booking`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-API-001 | GET /booking returns list with bookingid entries | positive | automated | test_booking_api.py |
| RB-API-002 | POST /booking returns bookingid and booking details | positive | automated | test_booking_api.py |
| RB-API-003 | GET /booking/{id} returns correct booking details | positive | automated | test_booking_api.py |
| RB-API-004 | PUT /booking/{id} updates firstname and totalprice | positive | automated | test_booking_api.py |
| RB-API-005 | PATCH /booking/{id} updates additionalneeds only | positive | automated | test_booking_api.py |
| RB-API-006 | DELETE /booking/{id} removes booking (GET returns 404) | positive | automated | test_booking_api.py |
| RB-API-007 | GET /booking/{nonexistent} returns 404 | negative | automated | test_booking_api.py |
| RB-API-008 | GET /booking filtered by firstname returns matching records | positive | automated | test_booking_api.py |
| RB-API-009 | POST /booking missing firstname returns 400/422/500 | negative | automated | test_booking_api.py |
| RB-API-010 | POST /booking without additionalneeds (optional) succeeds | positive | automated | test_booking_api.py |
| RB-API-011 | POST /booking returns 200 with bookingid (alt dataset) | positive | automated | test_booking.py |
| RB-API-012 | GET /booking/{id} returns all stored fields correctly | positive | automated | test_booking.py |
| RB-API-013 | PUT /booking/{id} returns updated firstname and price | positive | automated | test_booking.py |
| RB-API-014 | DELETE /booking/{id} returns 201 Created | positive | automated | test_booking.py |
| RB-API-015 | GET /booking returns non-empty list with bookingid keys | positive | automated | test_booking.py |
| RB-API-016 | GET /booking/{nonexistent-id} returns 404 | negative | automated | test_booking.py |
| RB-API-017 | PATCH /booking/{id} updates firstname field | positive | automated | test_booking.py |
| RB-API-018 | POST /booking with single-char names returns 200 | edge | automated | test_booking.py |
| RB-API-019 | GET /booking filtered by unique firstname returns subset | positive | automated | test_booking.py |
| RB-API-020 | Authenticate with valid credentials returns non-empty token | positive | automated | test_auth_api.py |
| RB-API-021 | Authenticate with invalid credentials returns null/bad response | negative | automated | test_auth_api.py |
| RB-API-022 | Delete booking without auth token is rejected (401/403) | negative | automated | test_auth_api.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

### POST /booking
- 
**Request Fields:** `firstname`, `lastname`, `totalprice` (number), `depositpaid` (boolean), `bookingdates.checkin`, `bookingdates.checkout`, `additionalneeds` (optional)
- **Success:** `200 OK` with `{"bookingid": <int>, "booking": {...}}`

### GET /booking
- **Query Params (optional):** `firstname`, `lastname` — filter by name
- **Response:** Array of `{"bookingid": <int>}`

### GET /booking/{id}
- **Response Codes:** `200 OK` (details) · `404 Not Found`

### PUT /booking/{id}
- **Auth required:** Cookie `token=<token>`
- **Response Codes:** `200 OK` (updated object) · `403` (no auth)

### PATCH /booking/{id}
- **Auth required:** Cookie `token=<token>`
- **Response Codes:** `200 OK` (partial update) · `403` (no auth)

### DELETE /booking/{id}
- **Auth required:** Cookie `token=<token>`
- **Response Codes:** `201 Created` (deleted) · `403` (no auth)

---

## Detailed Test Cases

### RB-API-001 — Get All Bookings

**Pre-conditions:**
- User Role: None (GET request does not require authentication)
- Starting URL: https://restful-booker.herokuapp.com/booking
- Required Data State: N/A

**Test Data:**
| Field | Value |
|---|---|
| bookingid (first element in response body) | - |

**Steps:**
1. Navigate to the specified URL for GET request
2. Execute the GET /booking request
3. Verify that the HTTP status code is 200 OK
4. Check if the response body contains a non-empty list
5. Get the first element from the response body
6. Verify that the first element has a key "bookingid"

**Expected Result:** The response body contains a non-empty list with the first element having a key "bookingid"

**Validation:** Check HTTP status code, presence of a list in the response body, existence of the key "bookingid" in the first element of the list

**Category:** positive

**Status:** not_automated

### RB-API-002 — Create Booking Returns ID

**Pre-conditions:**
- User: Unauthenticated
- Starting URL: https://restful-booker.herokuapp.com
- Required Data State: token is not required

**Test Data:**
| Field | Value |
|---|---|
| firstname | James |
| lastname | Brown |
| totalprice | 150 |
| depositpaid | True |
| checkin | 2026-08-01 |
| checkout | 2026-08-07 |
| additionalneeds | Breakfast |

**Steps:**
1. Send POST request to `/booking` with VALID_BOOKING data
2. Verify response status code is 200
3. Extract bookingid from response body
4. Verify booking.firstname == "James" in the response body

**Expected Result:** Response contains bookingid and booking.firstname == "James"

**Validation:** Assert response status code is 200, assert bookingid is an integer, assert booking.firstname == "James"

**Category:** positive

**Status:** not_automated

### RB-API-003 — Get Booking By ID

**Pre-conditions:**
- User Role: Admin or Guest
- Starting URL: https://restful-booker.herokuapp.com
- Required Data State: Existing Booking ID

**Test Data:**
| Field | Value |
|---|---|
| BookingID | (any existing booking id from knowledge base) |

**Steps:**
1. Send GET request to `/booking/{id}` with the provided BookingID
2. Verify response status code is 200
3. Compare response fields (firstname, lastname, totalprice, depositpaid, dates) with the creation payload

**Expected Result:** Response contains all expected booking details

**Validation:** Assert that response status code is 200 and that all response fields match the creation payload

**Category:** positive

**Status:** not_automated

### RB-API-004 — Update Booking

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Auth Token

**Test Data:**
| Field | Value |
|---|---|
| Firstname | Updated |
| Totalprice | 200 |

**Steps:**
1. Log in with credentials admin / password
2. Get auth token using POST /auth
3. Navigate to REST API Context
4. Use PUT /booking/{id} with input values from Test Data
5. Check response status code is 200
6. Verify response body has updated values

**Expected Result:** Response body has updated values

**Validation:** Response status code is 200 and response body reflects updated values

**Category:** positive

**Status:** not_automated

### RB-API-005 — Partial Update Booking

**Pre-conditions:**
- User role: Authenticated user
- Starting URL: https://restful-booker.herokuapp.com
- Required data state: valid token, existing booking with id

**Test Data:**
| Field | Value |
|---|---|
| FieldName | additionalneeds |
| Value | "Lunch" |

**Steps:**
1. Send a POST request to `/auth` with credentials (admin, password) and receive token
2. Set authorization header with received token in future requests
3. Send a PATCH request to `/booking/{id}` with body `{"additionalneeds": "Lunch"}`

**Expected Result:** Response status code 200

**Validation:** Check response body contains field additionalneeds equal to "Lunch"

**Category:** positive

**Status:** not_automated

### RB-API-006 — Delete Booking

**Pre-conditions:**
- User Role: Authenticated
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required Data State: auth token obtained

**Test Data:**
| Field | Value |
|---|---|
| username | admin |
| password | password |

**Steps:**
1. Send POST request to `/auth` with username 'admin' and password 'password'
2. Store the received auth token in a cookie header
3. Send DELETE request to `/booking/{id}` with the appropriate booking ID and auth token included in the cookie header
4. Send GET request to `/booking/{id}` with the same ID as in step 3, but without including the auth token

**Expected Result:** DELETE returns 200 or 201; subsequent GET returns 404

**Validation:** Verify that the booking is deleted and not found by checking the response codes

**Category:** positive

**Status:** not_automated

### RB-API-007 — Get Nonexistent Booking Returns 404

**Pre-conditions:**
- User role: Not applicable (no authentication required)
- Starting URL: https://restful-booker.herokuapp.com/booking/{id}
- Required data state: booking_id = `999999999`

**Test Data:**
| Field | Value |
|---|---|
| booking_id | 999999999 |

**Steps:**
1. Replace {id} in the starting URL with the provided booking_id (999999999)
2. Perform GET request to the modified URL
3. Check the response status code

**Expected Result:** HTTP 404 Not Found

**Validation:** Verify that the server responds with HTTP 404 status code.

**Category:** positive

**Status:** not_automated

### RB-API-008 — Filter Bookings By Name

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Token obtained via POST /auth using credentials admin / password

**Test Data:**
| Field | Value |
|---|---|
| Firstname | FilterTest |

**Steps:**
1. Access Admin Panel
2. Enter token in Cookie header
3. Use API GET /booking?firstname=FilterTest

**Expected Result:** HTTP status code 200 and a list length >= 1

**Validation:** Verify that the list contains at least one booking with firstname FilterTest

**Category:** positive

**Status:** not_automated

### RB-API-009 — Create Booking Missing Required Field

**Pre-conditions:**
- User Role: None
- Starting URL: https://restful-booker.herokuapp.com
- Required Data State: Valid_BOOKING without `firstname`

**Test Data:**
| Field | Value |
|---|---|
| firstname | (empty) |
| lastname | (valid value from KB) |
| totalprice | (valid value from KB) |
| depositpaid | (valid value from KB) |
| bookingdates | (valid value from KB) |
| additionalneeds | (optional value from KB) |

**Steps:**
1. Send a POST request to `/booking` with the provided incomplete payload
2. Check the response status code

**Expected Result:**
`status_code in (400, 422, 500)`

**Validation:**
- Verify that the response status code matches the expected values

**Category:** positive

**Status:** not_automated

### RB-API-010 — Create Booking Without Optional Field

**Pre-conditions:**
- User role: Not Applicable (REST API)
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required data state: valid credentials

**Test Data:**
| Field | Value |
|---|---|
| firstname | VALID_FIRSTNAME |
| lastname | VALID_LASTNAME |
| totalprice | VALID_TOTALPRICE |
| depositpaid | VALID_DEPOSITPAID |
| bookingdates | VALID_BOOKINGDATES |

**Steps:**
1. Send POST request to /auth with valid credentials
2. Store the returned token in a variable
3. Send POST request to /booking with provided test data and the stored token in the Authorization header

**Expected Result:** Status code 200; body has `bookingid`

**Validation:** Check that status code is 200, that the response contains a 'bookingid' field

**Category:** positive

**Status:** not_automated

### RB-API-011 — Create Booking Returns OK (alt dataset)

**Pre-conditions:**
- User Role: Anonymous
- Starting URL: https://restful-booker.herokuapp.com
- Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| firstname | John |
| lastname | Doe |
| totalprice | 250 |
| depositpaid | True |
| checkin | 2024-01-15 |
| checkout | 2024-01-20 |

**Steps:**
1. Send a POST request to `/booking` with the provided test data.
2. Check the response status code is 200.
3. Verify the response body contains a `bookingid` (int).

**Expected Result:** The server responds with a 200 status code and the booking id in the response body.

**Validation:** Check the server's response for the correct status code and the presence of a booking id.

**Category:** positive

**Status:** not_automated

### RB-API-012 — Get Booking Returns Details

**Pre-conditions:**
- User Role: None (as GET does not require authentication)
- Starting URL: https://restful-booker.herokuapp.com/booking/{id}
- Required Data State: A valid booking ID

**Test Data:**
| Field | Value |
|---|---|
| Booking ID | 12345 (exact value from KB) |

**Steps:**
1. Navigate to the specified URL with the provided booking ID
2. Send a GET request to retrieve booking details

**Expected Result:**
- Response status code: 200 OK
- firstname: John
- lastname: Doe
- totalprice: 250
- depositpaid: True
- checkin: 2024-01-15
- checkout: 2024-01-20

**Validation:**
- Verify the response status code is 200 OK
- Verify the returned booking details match the expected values (firstname, lastname, totalprice, depositpaid, checkin, checkout)

**Category:** positive

**Status:** not_automated

### RB-API-013 — Update Booking Returns Updated

**Pre-conditions:**
- User Role: Authenticated
- Starting URL: https://restful-booker.herokuapp.com/#/auth
- Required Data State: Auth token obtained

**Test Data:**
| Field | Value |
|---|---|
| id | {relevant ID from KB} |
| firstname | Jane |
| totalprice | 350 |

**Steps:**
1. Send POST request to `/auth` with valid credentials (admin / password)
2. Store the obtained token for later use in Cookie header
3. Update booking details using PUT request to `/booking/{id}` with provided data
4. Check response status code: 200 OK
5. Verify updated fields in response: firstname=Jane, totalprice=350

**Expected Result:** No error message, valid response body

**Validation:** Response contains expected values for the updated fields

**Category:** positive

**Status:** not_automated

### RB-API-014 — Delete Booking Returns 201

**Pre-conditions:**
- User Role: Authenticated Admin
- URL: https://restful-booker.herokuapp.com/auth
- Token: returned auth token
- Starting URL: https://restful-booker.herokuapp.com/booking/{id} (replace {id} with a specific booking ID)

**Test Data:**
| Field | Value |
|---|---|
| Token | Authenticated Admin's token |
| ID | Specific Booking ID |

**Steps:**
1. Send POST request to /auth endpoint with admin credentials and receive auth token.
2. Set the Authorization header with the received token in the HTTP headers.
3. Send DELETE request to the specified booking URL.

**Expected Result:** Response status code: 201 Created

**Validation:** Check if response status code is equal to 201.

**Category:** positive

**Status:** not_automated

### RB-API-015 — Get Booking IDs Returns List

**Pre-conditions:**
- User Role: Not Applicable (REST API)
- Starting URL: https://restful-booker.herokuapp.com/booking
- Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| Response Body | Not Applicable (REST API) |

**Steps:**
1. Send a GET request to the `/booking` endpoint

**Expected Result:**
200 HTTP status code and a JSON response containing a list of booking IDs with length greater than 0

**Validation:**
- Verify that the response has a 200 HTTP status code
- Verify that the response body is a JSON array with a minimum of 5 objects, each containing a `bookingid` key

**Category:** positive

**Status:** not_automated

### RB-API-016 — Get Nonexistent Booking Returns Not Found

**Pre-conditions:**
- User role: None (anonymous)
- Starting URL: https://restful-booker.herokuapp.com/booking/{id}
- Required data state: booking_id = `9999999`

**Test Data:**
| Field | Value |
|---|---|
| booking_id | 9999999 |

**Steps:**
1. Navigate to the specified URL with the provided booking ID
2. Execute a GET request for the nonexistent booking
3. Check the response status code

**Expected Result:** Response status code is 404 (Not Found)

**Validation:** Verify that the response status code equals 404

**Category:** positive

**Status:** not_automated

### RB-API-017 — Partial Update Returns OK

**Pre-conditions:**
- User Role: Admin
- Starting URL: https://restful-booker.herokuapp.com/#/auth
- Required Data State: Auth Token

**Test Data:**
| Field | Value |
|---|---|
| ID | Existing Booking ID |
| Firstname | UpdatedName |

**Steps:**
1. Send POST request to `/auth` with credentials (admin, password)
2. Store the received token for future use
3. Send PATCH request to `/booking/{id}` with headers containing the stored token and body: {"firstname": "UpdatedName"}
4. Verify response status code is 200
5. Verify response body contains "firstname == "UpdatedName""

**Expected Result:** Successful partial update of booking with new first name

**Validation:** Check that the booking record has been updated in the database and the API returns the expected response

**Category:** positive

**Status:** not_automated

### RB-API-018 — Create Booking With Min Names Returns OK

**Pre-conditions:**
- User Role: Unauthenticated
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required Data State: None

**Test Data:**
| Field | Value |
|---|---|
| firstname | A |
| lastname | B |

**Steps:**
1. Send POST request to /auth with admin/password as credentials. Save returned token for later use.
2. Use saved token in the Authorization header and send POST request to /booking with the test data provided.
3. Check response status code is 200.
4. Extract bookingid from response body.

**Expected Result:** Response has 200 status code and includes bookingid.

**Validation:** Verify that bookingid is a valid numeric value.

**Category:** positive

**Status:** not_automated

### RB-API-019 — Filter By Name Returns Subset

**Pre-conditions:**
- User Role: Unspecified
- Starting URL: https://restful-booker.herokuapp.com
- Required Data State: A valid auth token (if required for the specific endpoint)

**Test Data:**
| Field | Value |
|---|---|
| firstname | UniqueFilterTest |

**Steps:**
1. Perform authentication using admin credentials if needed
2. Send GET request to `/booking` with query parameter `firstname=UniqueFilterTest`
3. Check the response status code is 200
4. Verify that the response is a list containing at least one booking where the firstname field matches 'UniqueFilterTest'

**Expected Result:** The requested bookings are returned as a list in the response body

**Validation:** Assert the number of bookings in the list and check if the 'UniqueFilterTest' appears in the list of firstnames

**Category:** positive

**Status:** not_automated

### RB-API-020 — Authenticate With Valid Credentials

**Pre-conditions:**
- User role: Admin
- Starting URL: https://restful-booker.herokuapp.com/auth
- Required data state: None

**Test Data:**
| Field | Value |
|---|---|
| username | admin |
| password | password |

**Steps:**
1. Perform a POST request to the specified URL with the provided test data in the request body.
2. Extract the auth token from the response.
3. Verify that the auth token is a non-empty string and not "Bad credentials".

**Expected Result:** Auth token returned as a non-empty string.

**Validation:** Check that the extracted auth token matches the expected format.

**Category:** positive

**Status:** not_automated

### RB-API-021 — Authenticate With Invalid Credentials

**Pre-conditions:**
- User role: Admin
- Starting URL: https://restful-booker.herokuapp.com/#/auth
- Required data state: None

**Test Data:**
| Field | Value |
|---|---|
| username | wrong_user |
| password | wrong_pass |

**Steps:**
1. Navigate to the authentication endpoint (`POST /auth`)
2. Provide invalid credentials `wrong_user` and `wrong_pass`
3. Verify the response body contains `{"reason": "Bad credentials"}`
4. Verify no `token` key exists in the response

**Expected Result:** Response with a 200 status code, containing `{"reason": "Bad credentials"}`, and no `token` key

**Validation:** Check the HTTP response status, response body content, and absence of the `token` key

**Category:** positive

**Status:** not_automated

### RB-API-022 — Delete Without Auth Token Is Rejected

**Pre-conditions:**
- User Role: Unauthenticated Client
- Starting URL: https://restful-booker.herokuapp.com/booking/{id}
- Required Data State: A booking exists

**Test Data:**
| Field | Value |
|---|---|
| id | (Existing booking ID) |

**Steps:**
1. Send a DELETE request to the provided endpoint without authentication

**Expected Result:** HTTP status code 401 or 403

**Validation:** Check the response status code

**Category:** positive

**Status:** not_automated
