# Test Case Document — Booking Web (Home Page)

**Product:** Restful Booker  
**Layer:** Web  
**Module:** Booking (Home Page — `/#/`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-WEB-001 | Home page loads and shows room listings | positive | automated | test_booking_web.py |
| RB-WEB-002 | Room count on home page is at least 1 | positive | automated | test_booking_web.py |
| RB-WEB-003 | Clicking Book Room opens booking form | positive | automated | test_booking_web.py |
| RB-WEB-004 | Submit booking form with valid data shows confirmation or error | positive | automated | test_booking_web.py |
| RB-WEB-005 | Submit booking form with no fields filled shows validation error | negative | automated | test_booking_web.py |
| RB-WEB-006 | Booking form date picker prevents checkout before checkin | edge | not_automated | — |
| RB-WEB-007 | Booking confirmation email is sent after successful booking | positive | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details
- **URL:** `/` (home page)
- **Key Elements:** Room list, Book Room button, booking form (Firstname, Lastname, Email, Phone, date range)

---

## Test Cases

### RB-WEB-001 — Home Page Shows Rooms
**Steps:** Navigate to home page  
**Expected:** At least one room card is listed

### RB-WEB-002 — Room Count Is Positive
**Steps:** Navigate to home page, read room count  
**Expected:** `room_count >= 1`

### RB-WEB-003 — Booking Form Opens On Click
**Steps:** Navigate, click Book Room on first room  
**Expected:** Firstname input field is visible

### RB-WEB-004 — Submit With Valid Data
**Test Data:** Firstname=John, Lastname=Smith, Email=john.smith@example.com, Phone=01234567890  
**Steps:** Fill all fields, click Book  
**Expected:** Booking confirmed OR validation error displayed (demo site may have date restrictions)

### RB-WEB-005 — Submit With No Fields
**Steps:** Open booking form, click Book without filling anything  
**Expected:** Validation error is shown

### RB-WEB-006 — Date Picker Prevents Checkout Before Checkin
**Steps:** Set checkout date earlier than checkin date in calendar picker  
**Expected:** Checkout date is constrained; cannot select a date before checkin

### RB-WEB-007 — Confirmation Email Sent (not_automatable)
**Note:** Requires email inbox verification. Cannot be automated without email testing tooling (e.g., Mailhog, SendGrid API access).
