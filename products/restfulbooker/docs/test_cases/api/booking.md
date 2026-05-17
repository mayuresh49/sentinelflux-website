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

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

### POST /booking
- **Request Fields:** `firstname`, `lastname`, `totalprice` (number), `depositpaid` (boolean), `bookingdates.checkin`, `bookingdates.checkout`, `additionalneeds` (optional)
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
**Marks:** `api`, `sanity`  
**Steps:** `GET /booking`  
**Expected:** 200; body is a non-empty list; first element has key `bookingid`

### RB-API-002 — Create Booking Returns ID
**Test Data:** firstname=James, lastname=Brown, totalprice=150, depositpaid=True, checkin=2026-08-01, checkout=2026-08-07, additionalneeds=Breakfast  
**Steps:** `POST /booking` with VALID_BOOKING  
**Expected:** 200; body has `bookingid` (int); `booking.firstname` == "James"

### RB-API-003 — Get Booking By ID
**Steps:** Create booking → `GET /booking/{id}`  
**Expected:** 200; all fields match creation payload (firstname, lastname, totalprice, depositpaid, dates)

### RB-API-004 — Update Booking
**Steps:** Create → `PUT /booking/{id}` with firstname=Updated, totalprice=200  
**Expected:** 200; response body has updated values

### RB-API-005 — Partial Update Booking
**Steps:** Create → `PATCH /booking/{id}` with `{"additionalneeds": "Lunch"}`  
**Expected:** 200; `additionalneeds == "Lunch"`

### RB-API-006 — Delete Booking
**Steps:** Create → `DELETE /booking/{id}` → `GET /booking/{id}`  
**Expected:** DELETE returns 200 or 201; subsequent GET returns 404

### RB-API-007 — Get Nonexistent Booking Returns 404
**Test Data:** booking_id = `999999999`  
**Steps:** `GET /booking/999999999`  
**Expected:** 404

### RB-API-008 — Filter Bookings By Name
**Steps:** Create booking with firstname=FilterTest → `GET /booking?firstname=FilterTest`  
**Expected:** 200; list length >= 1

### RB-API-009 — Create Booking Missing Required Field
**Test Data:** VALID_BOOKING without `firstname`  
**Steps:** `POST /booking` with incomplete payload  
**Expected:** `status_code in (400, 422, 500)`

### RB-API-010 — Create Booking Without Optional Field
**Test Data:** VALID_BOOKING without `additionalneeds`  
**Steps:** `POST /booking`  
**Expected:** 200; body has `bookingid`

### RB-API-011 — Create Booking Returns OK (alt dataset)
**Test Data:** firstname=John, lastname=Doe, totalprice=250, depositpaid=True, checkin=2024-01-15, checkout=2024-01-20  
**Steps:** `POST /booking`  
**Expected:** 200; body has `bookingid` (int)

### RB-API-012 — Get Booking Returns Details
**Steps:** Create → `GET /booking/{id}`  
**Expected:** 200; firstname=John, lastname=Doe, totalprice=250, depositpaid=True, checkin=2024-01-15, checkout=2024-01-20

### RB-API-013 — Update Booking Returns Updated
**Steps:** Create → `PUT /booking/{id}` with firstname=Jane, totalprice=350  
**Expected:** 200; response has firstname=Jane, totalprice=350

### RB-API-014 — Delete Booking Returns 201
**Steps:** Create → `DELETE /booking/{id}`  
**Expected:** 201 Created

### RB-API-015 — Get Booking IDs Returns List
**Steps:** `GET /booking`  
**Expected:** 200; body is a list; length > 0; all first 5 items have `bookingid` key

### RB-API-016 — Get Nonexistent Booking Returns Not Found
**Test Data:** booking_id = `9999999`  
**Steps:** `GET /booking/9999999`  
**Expected:** 404

### RB-API-017 — Partial Update Returns OK
**Steps:** Create → `PATCH /booking/{id}` with `{"firstname": "UpdatedName"}`  
**Expected:** 200; response `firstname == "UpdatedName"`

### RB-API-018 — Create Booking With Min Names Returns OK
**Test Data:** firstname=A, lastname=B (single characters)  
**Steps:** `POST /booking`  
**Expected:** 200; body has `bookingid`

### RB-API-019 — Filter By Name Returns Subset
**Steps:** Create booking with firstname=UniqueFilterTest → `GET /booking?firstname=UniqueFilterTest`  
**Expected:** 200; response is a list

### RB-API-020 — Authenticate With Valid Credentials
**Test Data:** username=admin, password=password123  
**Steps:** `POST /auth`  
**Expected:** 200; token is non-empty string, not "Bad credentials"

### RB-API-021 — Authenticate With Invalid Credentials
**Test Data:** username=wrong_user, password=wrong_pass  
**Steps:** `POST /auth`  
**Expected:** 200; body contains `{"reason": "Bad credentials"}`; no `token` key

### RB-API-022 — Delete Without Auth Token Is Rejected
**Pre-conditions:** A booking exists  
**Steps:** Create booking with authenticated client → DELETE with unauthenticated client  
**Expected:** 401 or 403
