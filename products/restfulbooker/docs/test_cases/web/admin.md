# Test Case Document — Admin Web

**Product:** Restful Booker  
**Layer:** Web  
**Module:** Admin Panel (`/#/admin`)

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-WEB-006 | Admin login with valid credentials shows admin panel | positive | automated | test_admin_web.py |
| RB-WEB-007 | Admin login with invalid credentials does not show panel | negative | automated | test_admin_web.py |
| RB-WEB-008 | Admin panel shows Rooms navigation link after login | positive | automated | test_admin_web.py |
| RB-WEB-009 | Admin logout returns to login/home page | positive | automated | test_admin_web.py |
| RB-WEB-012 | Create new room with valid data appears in rooms list | positive | not_automated | — |
| RB-WEB-013 | Delete room removes it from rooms list | negative | not_automated | — |
| RB-WEB-014 | Session persists across page refresh | edge | not_automatable | — |

> **Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Page Details
- **URL:** `/#/admin`
- **Credentials:** username=`admin`, password=`password` (web panel)
- **Key Elements:** Login form, Rooms link, logout

---

## Test Cases

```
### RB-WEB-006 — Admin Login Valid
**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Logged out

**Test Data:**
| Field | Value |
|---|---|
| Username | admin |
| Password | password |

**Steps:**
1. Navigate to the Admin Panel URL.
2. Enter the provided credentials and submit.
3. Verify that the Admin Panel is visible.

**Expected Result:** The Admin Panel is accessible after providing valid credentials.

**Validation:** Check if the Admin Panel UI is rendered with the user logged in.

**Category:** positive
**Status:** not_automated### RB-WEB-007 — Admin Login Invalid
**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Not logged in

**Test Data:**
| Field | Value |
|---|---|
| username | wronguser |
| password | wrongpassword |

**Steps:**
1. Navigate to the Admin Panel at https://automationintesting.online/#/admin
2. Enter incorrect credentials (wronguser, wrongpassword) and submit the login form
3. Check for an error indicator indicating invalid credentials

**Expected Result:** Error indicator shown instead of access to Admin Panel

**Validation:** Verify that the error message "Bad Credentials" is displayed

**Category:** positive
**Status:** not_automated### RB-WEB-008 — Admin Panel Shows Rooms Menu
**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Logged in

**Test Data:**
| Field | Value |
|---|---|
| Credentials | admin / password |

**Steps:**
1. Login using the provided credentials.
2. Navigate to Admin Panel.
3. Verify the presence of a "Rooms" navigation link.

**Expected Result:** The "Rooms" link is visible in the navigation.

**Validation:** Verify that the "Rooms" link is present in the navigation bar.

**Category:** positive
**Status:** not_automated### RB-WEB-009 — Admin Logout
**Pre-conditions:**
- User role: admin
- Starting URL: https://automationintesting.online/#/admin (Admin Panel)
- Required data state: logged in as admin
**Test Data:**
| Field | Value |
|---|---|
| Credentials | admin / password |
**Steps:**
1. Navigate to Admin Panel and log in with provided credentials.
2. Click on the 'Logout' button.
3. Verify that the user is redirected to the Home Page (https://automationintesting.online).
4. Attempt to access Admin Panel and ensure it is no longer accessible.
**Expected Result:** User is redirected to the Home Page and Admin Panel becomes inaccessible.
**Validation:** User is on Home Page, Admin Panel URL returns a 401 error.
**Category:** positive
**Status:** not_automated### RB-WEB-012 — Create Room
**Pre-conditions:**
- User Role: Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Login credentials (admin / password)

**Test Data:**
| Field | Value |
|---|---|
| Room Number | Any unique number |
| Room Type | Any valid room type |
| Description | Any description for the room |
| Max Guests | Any valid number of guests |
| Room Price | Any valid price |

**Steps:**
1. Navigate to Admin Panel and login with provided credentials.
2. Navigate to Rooms section.
3. Fill out the room details form with the test data.
4. Click on the 'Save' button.

**Expected Result:** The new room appears in the rooms list in the Admin Panel.

**Validation:** Verify that the room appears in the rooms list and matches the entered values.

**Category:** positive
**Status:** not_automated### RB-WEB-013 — Delete Room
**Pre-conditions:**
- User Role: Logged in Admin
- Starting URL: https://automationintesting.online/#/admin
- Required Data State: Authenticated user with admin credentials

**Test Data:**
| Field | Value |
|---|---|
| RoomID | (to be defined) |

**Steps:**
1. Navigate to Admin Panel
2. Select the room to delete from the list
3. Click on 'Delete Room' button for the selected room
4. Enter the RoomID in the confirmation dialog
5. Confirm deletion by clicking 'Yes'

**Expected Result:** The selected room is removed from the list of available rooms

**Validation:** The deleted room no longer appears in the list of available rooms

**Category:** positive
**Status:** not_automated### RB-WEB-014 — Session Persists Across Refresh (not_automatable)
**Pre-conditions:**
- User role: Authenticated user
- Starting URL: https://automationintesting.online
- Required data state: Successful login

**Test Data:**
| Field | Value |
|---|---|
| Username | admin |
| Password | password |

**Steps:**
1. Navigate to the Home Page.
2. Click on the "Login" button and enter the credentials in the provided form.
3. Submit the login form.
4. Refresh the page.

**Expected Result:** The authenticated user remains logged in after refreshing the page.

**Validation:** Verify that the user is still logged in by checking for the presence of the auth token in the Cookie header.

**Category:** positive
**Status:** not_automated