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

### RB-WEB-006 — Admin Login Valid
**Test Data:** username=admin, password=password  
**Steps:** Navigate to admin, fill credentials, submit  
**Expected:** Admin panel is visible

### RB-WEB-007 — Admin Login Invalid
**Test Data:** username=wronguser, password=wrongpassword  
**Steps:** Navigate to admin, fill bad credentials, submit  
**Expected:** Admin panel not visible; error indicator shown

### RB-WEB-008 — Admin Panel Shows Rooms Menu
**Pre-conditions:** Logged in as admin  
**Steps:** Verify Rooms nav link exists  
**Expected:** "Rooms" link is visible in navigation

### RB-WEB-009 — Admin Logout
**Pre-conditions:** Logged in as admin  
**Steps:** Click logout  
**Expected:** Redirected to home/login; admin panel no longer accessible

### RB-WEB-012 — Create Room
**Steps:** Navigate to Rooms, fill room details, save  
**Expected:** New room appears in rooms list

### RB-WEB-013 — Delete Room
**Steps:** Select a room, delete  
**Expected:** Room is removed from list

### RB-WEB-014 — Session Persists Across Refresh (not_automatable)
**Note:** Requires verifying browser session state across hard refresh. Behavior differs by browser and cannot be reliably automated in all CI environments without specific session mocking.
