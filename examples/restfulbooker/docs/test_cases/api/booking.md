# Test Case Document — Booking API

**Product:** Restful Booker  
**Layer:** API  
**Module:** Booking (`/booking`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-API-001 | Get all booking IDs returns non-empty list | positive | automated | test_booking_api.py |
| RB-API-002 | Create booking with full valid payload returns booking ID | positive | automated | test_booking_api.py |
| RB-API-003 | Get booking by ID returns correct all fields | positive | automated | test_booking_api.py |
| RB-API-004 | Full update booking returns updated data | positive | automated | test_booking_api.py |
| RB-API-005 | Partial update booking returns 200 with new value | positive | automated | test_booking_api.py |
| RB-API-006 | Delete booking removes it (GET returns 404 after) | positive | automated | test_booking_api.py |
| RB-API-007 | Get non-existent booking ID returns 404 | negative | automated | test_booking_api.py |
| RB-API-008 | Filter bookings by firstname returns subset | positive | automated | test_booking_api.py |
| RB-API-009 | Create booking missing required field returns 400/422/500 | negative | automated | test_booking_api.py |
| RB-API-010 | Create booking without optional additionalneeds field succeeds | positive | automated | test_booking_api.py |
| RB-API-011 | Create booking returns 200 status (legacy coverage) | positive | automated | test_booking.py |
| RB-API-012 | Get booking returns all fields (legacy coverage) | positive | automated | test_booking.py |
| RB-API-013 | Update booking returns updated firstname and price | positive | automated | test_booking.py |
| RB-API-014 | Delete booking returns 201 status | positive | automated | test_booking.py |
| RB-API-015 | Get all booking IDs returns list with bookingid key | positive | automated | test_booking.py |
| RB-API-016 | Get non-existent booking returns 404 | negative | automated | test_booking.py |
| RB-API-017 | Partial update booking returns 200 with changed field | positive | automated | test_booking.py |
| RB-API-018 | Create booking with single-char firstname and lastname | edge | automated | test_booking.py |
| RB-API-019 | Filter bookings by unique firstname returns matching subset | positive | automated | test_booking.py |
| RB-API-020 | Create booking with invalid totalprice type (string) returns 400 | negative | not_automated | — |
| RB-API-021 | Create booking with invalid depositpaid type (string) returns 400 | negative | not_automated | — |
| RB-API-022 | Create booking with wrong date format (DD/MM/YYYY) returns 400 | negative | not_automated | — |
| RB-API-023 | Create booking with checkout date before checkin returns 400 | negative | not_automated | — |
| RB-API-024 | Update booking with invalid totalprice type returns 400 | negative | not_automated | — |
| RB-API-025 | Create booking with totalprice = 0 (boundary) returns 201 | edge | not_automated | — |
| RB-API-026 | Create booking with totalprice = 10000 (max boundary) returns 201 | edge | not_automated | — |
| RB-API-027 | Create booking with additionalneeds > 500 chars returns 400 | edge | not_automated | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Endpoint Scope

### **POST /booking**
- **Request Fields:**
  - `firstname` (string, required)
  - `lastname` (string, required)
  - `totalprice` (number, required)
  - `depositpaid` (boolean, required)
  - `bookingdates` (object, required)
    - `checkin` (string, YYYY-MM-DD, required)
    - `checkout` (string, YYYY-MM-DD, required)
  - `additionalneeds` (string, optional)
- **Response Codes:** `200 OK`, `400 Bad Request`

### **GET /booking/{id}**
- **Request Fields:** `id` (integer, required)
- **Response Codes:** `200 OK`, `404 Not Found`

### **PUT /booking/{id}**
- All booking fields (optional for partial update via PATCH)
- **Response Codes:** `200 OK`, `400 Bad Request`, `404 Not Found`

### **DELETE /booking/{id}**
- **Request Fields:** `id` (integer, required)
- **Response Codes:** `201 Created`, `404 Not Found`

---

## Positive Test Cases

### RB-API-001 — Get All Booking IDs
**Steps:** GET /booking  
**Expected:** 200, body is list, `bookingid` present in each item

### RB-API-002 — Create Booking (Full Payload)
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": { "checkin": "2024-01-15", "checkout": "2024-01-20" },
  "additionalneeds": "Breakfast"
}
```
**Expected:** `200 OK`, body has `bookingid` (integer) and `booking` object matching input

### RB-API-003 — Get Booking By ID
**Pre-conditions:** booking created via POST  
**Steps:** GET /booking/{id}  
**Expected:** `200 OK`, all fields match POST payload

### RB-API-004 — Full Update Booking
**Pre-conditions:** booking exists  
**Steps:** PUT /booking/{id} with changed firstname + totalprice  
**Expected:** `200 OK`, response reflects updated values

### RB-API-005 — Partial Update Booking
**Steps:** PATCH /booking/{id} with `{"additionalneeds": "Lunch"}`  
**Expected:** `200 OK`, `additionalneeds` = "Lunch"

### RB-API-006 — Delete Booking
**Steps:** DELETE /booking/{id}, then GET /booking/{id}  
**Expected:** DELETE returns 200/201; GET returns `404`

### RB-API-008 — Filter By Name
**Steps:** GET /booking?firstname=FilterTest  
**Expected:** `200 OK`, list contains at least 1 result

### RB-API-010 — Create Without Optional Field
**Steps:** POST without `additionalneeds`  
**Expected:** `200 OK`, `bookingid` present

---

## Negative Test Cases

### RB-API-007 — Get Non-Existent Booking
**Steps:** GET /booking/999999999  
**Expected:** `404 Not Found`

### RB-API-009 — Create Missing Required Field (firstname)
**Steps:** POST payload without `firstname`  
**Expected:** `400`, `422`, or `500`

### RB-API-020 — Invalid totalprice Type
```json
{ "firstname": "John", "lastname": "Doe", "totalprice": "two fifty", ... }
```
**Expected:** `400 Bad Request`

### RB-API-021 — Invalid depositpaid Type
```json
{ ..., "depositpaid": "yes" }
```
**Expected:** `400 Bad Request`

### RB-API-022 — Wrong Date Format
```json
{ ..., "bookingdates": { "checkin": "15/01/2024", "checkout": "20/01/2024" } }
```
**Expected:** `400 Bad Request`

### RB-API-023 — Checkout Before Checkin
```json
{ ..., "bookingdates": { "checkin": "2026-01-20", "checkout": "2024-01-15" } }
```
**Expected:** `400 Bad Request`

### RB-API-024 — PUT With Invalid totalprice
```json
{ "totalprice": "three hundred" }
```
**Expected:** `400 Bad Request`

---

## Edge Cases

### RB-API-018 — Min Name Length
```json
{ "firstname": "A", "lastname": "B", "totalprice": 250, "depositpaid": true, "bookingdates": {...} }
```
**Expected:** `200 OK`

### RB-API-025 — Zero Price
```json
{ ..., "totalprice": 0 }
```
**Expected:** `200 OK` (boundary value)

### RB-API-026 — Max Price
```json
{ ..., "totalprice": 10000 }
```
**Expected:** `200 OK` (upper boundary)

### RB-API-027 — Long additionalneeds (>500 chars)
**Expected:** `400 Bad Request`

---

## Validation Rules
1. Checkout date must be after checkin date
2. Booking price must be between 0 and 10000
3. firstname and lastname are mandatory
4. additionalneeds is optional, max 500 characters
5. Maximum stay duration is 365 days
6. Bookings cannot be created for past dates
