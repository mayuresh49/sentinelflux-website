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
**Pre-conditions:**
- User role: anonymous, Starting URL: Home Page, Required data state: None
**Test Data:**
| Field | Value |
|---|---|
| firstname | John |
| lastname | Doe |
| totalprice | 150.0 |
| checkin | 2026-06-01 |
| checkout | 2026-06-05 |
| depositpaid | True |
**Steps:**
1. Navigate to Home Page and access the Booking Form
2. Fill out the booking form with provided test data
3. Click on 'Submit' button
4. Verify that the booking confirmation message appears
**Expected Result:** Booking confirmation message is displayed
**Validation:** The submitted booking can be retrieved using its ID
**Category:** positive
**Status:** not_automated### RB-MOB-002 — Create Booking Without Firstname Shows Error
**Pre-conditions:**
- User Role: Anonymous
- Starting URL: https://automationintesting.online/booking-form
- Required Data State: Lastname, Price, Checkin, Checkout are provided, Firstname is missing

**Test Data:**
| Field | Value |
|---|---|
| Firstname | (missing) |
| Lastname | admin |
| Price | any valid total price |
| Checkin | any valid check-in date |
| Checkout | any valid check-out date |

**Steps:**
1. Navigate to the booking form
2. Fill lastname, price, checkin, checkout; omit firstname
3. Call `submit()`

**Expected Result:** "is_error_shown()" returns True

**Validation:** Verify that the error message related to missing firstname is displayed

**Category:** positive
**Status:** not_automated### RB-MOB-003 — Create Booking Without Lastname Shows Error
**Pre-conditions:**
- User role: regular user
- Starting URL: https://automationintesting.online/booking-form
- Required data state: firstname, price, checkin, checkout

**Test Data:**
| Field | Value |
|---|---|
| First Name | any valid first name |
| Price | any valid total price |
| Checkin Date | any valid check-in date |
| Checkout Date | any valid check-out date |
| Last Name | (omitted) |

**Steps:**
1. Navigate to the Booking Form.
2. Fill in the First Name, Price, Checkin Date, and Checkout Date fields.
3. Omit the Last Name field.
4. Call `submit()`.

**Expected Result:** The "is_error_shown()" returns True.

**Validation:** Verify that an error message is displayed regarding the missing last name.

**Category:** positive
**Status:** not_automated### RB-MOB-004 — Checkout Before Checkin Shows Error
**Pre-conditions:**
- User Role: Anonymous (not logged in)
- Starting URL: <https://automationintesting.online>
- Required Data State: Navigate to the Booking Form

**Test Data:**
| Field | Value |
|---|---|
| Checkin Date | 2026-06-10 |
| Checkout Date | 2026-06-05 |

**Steps:**
1. Navigate to the Booking Form on the Home Page
2. Fill out the Booking Form with the provided test data
3. Submit the form
4. Verify if an error message is shown

**Expected Result:** A warning message is displayed stating that checkout date must be after checkin date.

**Validation:** Check that the error message is displayed and no booking is created in the REST API.

**Category:** positive
**Status:** not_automated### RB-MOB-005 — Booking List Visible On Home
**Pre-conditions:**
- User role: Anonymous
- Starting URL: https://automationintesting.online
- Required data state: No specific data required

**Test Data:**
| Field | Value |
|---|---|
| None | - |

**Steps:**
1. Navigate to the home page via clicking on the Booking Form inline on the Home Page.
2. Verify that the booking list is displayed.

**Expected Result:** The booking list is visible on the home page.

**Validation:** Assert that the booking list is present and visible on the home page.

**Category:** positive
**Status:** not_automated```
### RB-MOB-006 — Create Booking Parametrized
**Pre-conditions:**
- (User Role: unauthenticated, Starting URL: Home Page, Required Data State: none)

**Test Data:**
| Field         | Value                   |
|---------------|-------------------------|
| firstname     | Alice                   |
| lastname      | Smith                   |
| totalprice    | 200.0                   |
| checkin_date  | 2026-07-01              |
| checkout_date | 2026-07-03              |
| additionalneeds| None                     |

**Steps:**
1. Navigate to Home Page
2. Click on Booking Form
3. Fill out the form with provided data
4. Click on Create Booking button
5. Check for successful booking confirmation message
6. Verify that `is_confirmed()` returns True

**Expected Result:** Confirmation message appears and `is_confirmed()` returns True
**Validation:** Confirmation message is displayed and the correct booking details are returned by GET /booking/{id}
**Category:** positive
**Status:** not_automated
```