# Test Case Document — Mobile Booking

**Product:** Restful Booker  
**Layer:** Mobile  
**Module:** Booking

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-MOB-001 | Create booking with all fields shows confirmation | positive | automated | test_booking_mobile.py |
| RB-MOB-002 | Create booking without firstname shows error | negative | automated | test_booking_mobile.py |
| RB-MOB-003 | Create booking without lastname shows error | negative | automated | test_booking_mobile.py |
| RB-MOB-004 | Checkout date before checkin date shows error | negative | automated | test_booking_mobile.py |
| RB-MOB-005 | Booking list is visible on home screen | positive | automated | test_booking_mobile.py |
| RB-MOB-006 | Create booking parametrized (Alice/Smith, Bob/Jones) | positive | automated | test_booking_mobile.py |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Screen / Component Details
- **Screen:** Booking screen (via `booking_screen` fixture)
- **Fields:** `firstname`, `lastname`, `total_price`, `checkin`, `checkout`, `deposit_paid` (optional)
- **Confirmation:** `booking_screen.is_confirmed()`
- **Error indicator:** `booking_screen.is_error_shown()`

---

## Detailed Test Cases

### RB-MOB-001 — Create Booking Shows Confirmation
**Test Data:** firstname=John, lastname=Doe, price=150.0, checkin=2026-06-01, checkout=2026-06-05, deposit_paid=True  
**Steps:** Call `booking_screen.create_booking(...)` with all fields  
**Expected:** `is_confirmed()` returns `True`

### RB-MOB-002 — Create Booking Without Firstname Shows Error
**Steps:** Fill lastname, price, checkin, checkout; omit firstname; call `submit()`  
**Expected:** `is_error_shown()` returns `True`

### RB-MOB-003 — Create Booking Without Lastname Shows Error
**Steps:** Fill firstname, price, checkin, checkout; omit lastname; call `submit()`  
**Expected:** `is_error_shown()` returns `True`

### RB-MOB-004 — Checkout Before Checkin Shows Error
**Test Data:** checkin=2026-06-10, checkout=2026-06-05 (checkout is before checkin)  
**Steps:** Call `create_booking(...)` with inverted dates  
**Expected:** `is_error_shown()` returns `True`

### RB-MOB-005 — Booking List Visible On Home
**Steps:** Navigate to home screen via `booking_screen`  
**Expected:** `is_booking_list_visible()` returns `True`

### RB-MOB-006 — Create Booking Parametrized
**Test Data:** [("Alice", "Smith", 200.0, "2026-07-01", "2026-07-03"), ("Bob", "Jones", 99.0, "2026-08-15", "2026-08-16")]  
**Steps:** For each data set, call `create_booking(...)`  
**Expected:** `is_confirmed()` returns `True` for each
