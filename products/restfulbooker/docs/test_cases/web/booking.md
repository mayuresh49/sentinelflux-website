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
| RB-WEB-010 | Booking form date picker prevents checkout before checkin | edge | not_automated | — |
| RB-WEB-011 | Booking confirmation email is sent after successful booking | positive | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details
- **URL:** `/` (home page)
- **Key Elements:** Room list, Book Room button, booking form (Firstname, Lastname, Email, Phone, date range)

---

## Test Cases

### RB-WEB-001 — Home Page Shows Rooms
**Pre-conditions:**
- User Role: Not Specified
- Starting URL: https://automationintesting.online
- Required Data State: No data required

**Test Data:**
| Field | Value |
|---|---|
| None | - |

**Steps:**
1. Navigate to Home Page
2. Verify that at least one room card is listed

**Expected Result:** At least one room card is displayed on the home page

**Validation:** Count of visible room cards is greater than zero

**Category:** positive
**Status:** not_automated### RB-WEB-002 — Room Count Is Positive
**Pre-conditions:**
- User Role: Anonymous (Unauthenticated)
- Starting URL: Home Page (https://automationintesting.online)
- Required Data State: No data required for this test case

**Test Data:**
| Field | Value |
|---|---|
| Room Count | Must be positive and retrievable from the Home Page |

**Steps:**
1. Navigate to the Home Page (https://automationintesting.online)
2. Read the room count displayed on the Home Page
3. Verify that the read room count is a positive number

**Expected Result:** The read room count should be a positive number

**Validation:** Assert that the retrieved room count is greater than zero

**Category:** positive
**Status:** not_automated### RB-WEB-003 — Booking Form Opens On Click
**Pre-conditions:**
- User role: regular user
- Starting URL: https://automationintesting.online
- Required data state: None

**Test Data:**
| Field | Value |
|---|---|
| none | none |

**Steps:**
1. Navigate to the Home Page.
2. Click on the "Book Room" button inline on the home page for the first room.
3. Verify that the Booking Form is displayed.

**Expected Result:** The Booking Form is visible.

**Validation:** Check if the Firstname input field is present and editable.

**Category:** positive
**Status:** not_automated### RB-WEB-004 — Submit With Valid Data
**Pre-conditions:**
- User role: anonymous, Starting URL: https://automationintesting.online, Required data state: Firstname=John, Lastname=Smith, Email=john.smith@example.com, Phone=01234567890
**Test Data:**
| Field | Value |
|---|---|
| firstname | John |
| lastname | Smith |
| email | john.smith@example.com |
| phone | 01234567890 |
**Steps:**
1. Navigate to Home Page
2. Access the Booking Form
3. Fill in all fields with provided data
4. Click on "Book" button
**Expected Result:** Booking confirmed OR validation error displayed (demo site may have date restrictions)
**Validation:** Check if booking is successfully created or validation error message is displayed
**Category:** positive
**Status:** not_automated### RB-WEB-005 — Submit With No Fields
**Pre-conditions:**
- User role: anonymous
- Starting URL: https://automationintesting.online

**Test Data:**
| Field | Value |
|---|---|
| Firstname | - |
| Lastname | - |
| Email | - |
| Phone | - |
| Check-in date | - |
| Check-out date | - |

**Steps:**
1. Navigate to the Booking Form inline on Home Page
2. Click on "Book" button without filling any fields
3. Verify validation error is shown

**Expected Result:** Validation error message is displayed

**Validation:** The validation error message matches the expected validation rules for Web Booking

**Category:** positive
**Status:** not_automated### RB-WEB-010 — Date Picker Prevents Checkout Before Checkin
**Pre-conditions:**
- User role: Regular user
- Starting URL: Home Page (https://automationintesting.online)
- Required data state: Booking Form is displayed and open

**Test Data:**
| Field | Value |
|---|---|
| Check-in date | Select a future date from the calendar picker |
| Checkout date | A date earlier than the selected check-in date from the calendar picker |

**Steps:**
1. Navigate to the Booking Form on the Home Page.
2. Input valid data for the required fields: firstname, lastname, email (optional), phone (optional).
3. Select a future check-in date using the calendar picker.
4. Try to select an earlier checkout date using the calendar picker.
5. Click on the 'Book Now' button.

**Expected Result:** The user is unable to select a checkout date before the check-in date.

**Validation:** Check that the checkout date input field is disabled when selecting a date before the check-in date.

**Category:** positive
**Status:** not_automated### RB-WEB-011 — Confirmation Email Sent (not_automatable)
**Pre-conditions:**
- User role: Any registered user, Starting URL: Home Page, Required data state: Firstname, Lastname, Email, Phone, Check-in date, Check-out date
**Test Data:**
| Field | Value |
|---|---|
| Firstname | any valid first name from KB |
| Lastname | any valid last name from KB |
| Email | valid email format from KB |
| Phone | 11+ characters phone number from KB |
| Check-in date | valid check-in date from KB |
| Check-out date | valid check-out date (after check-in date) from KB |
**Steps:**
1. Navigate to Home Page and fill out the booking form with provided test data.
2. Submit the booking form.
3. Verify a confirmation email is sent to the provided email address.
**Expected Result:** Email is received in the user's inbox.
**Validation:** Confirmation email subject contains "Booking Confirmation".
**Category:** positive
**Status:** not_automated