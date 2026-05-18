# Test Case Document — Web Security

**Product:** Restful Booker  
**Layer:** Web  
**Module:** Security — Home Page & Admin Panel

---

## Test Case Index

| ID | Scenario | Type | Status | Script |
|---|---|---|---|---|
| RB-SEC-006 | XSS payload in contact form does not execute | negative | automated | test_security_web.py |
| RB-SEC-007 | Admin panel requires login credentials to access | negative | automated | test_security_web.py |
| RB-SEC-008 | XSS payload in booking firstname field does not execute | negative | automated | test_security_web.py |
| RB-SEC-009 | Home page does not expose web server version in headers | negative | automated | test_security_web.py |

> 
**Status values:** `automated` = script exists · `not_automated` = not yet scripted · `not_automatable` = human must mark; skipped by script generator

---

## Scope

Client-side security checks on the Restful Booker web layer: XSS prevention in user-input forms, access control on the admin panel, and response header hygiene.

---

## Detailed Test Cases

### RB-SEC-006 — XSS In Contact Form Does Not Execute

**Pre-conditions:**
- User Role: Anonymous
- Starting URL: Home Page (https://automationintesting.online)
- Required Data State: Contact form fields are accessible and empty

**Test Data:**
| Field | Value |
|---|---|
| Name | `<script>window.__xss_fired=true</script>` |
| Email | Valid email format |
| Phone | Not applicable (if required) |
| Check-in Date | Not applicable (if required) |
| Check-out Date | Not applicable (if required) |

**Steps:**
1. Navigate to home page
2. Fill contact form fields with provided test data
3. Submit the form
4. Check for JS dialog events and `window.__xss_fired`

**Expected Result:** No dialog fires; `window.__xss_fired` is not `true`

**Validation:** `window.__xss_fired` is checked and compared to a false value

**Category:** positive

**Status:** not_automated

### RB-SEC-007 — Admin Panel Requires Login

**Pre-conditions:**
- User role: Anonymous
- Starting URL: https://automationintesting.online/#/admin
- Required data state: No active admin session

**Test Data:**
| Field | Value |
|---|---|
| username | admin |
| password | password (from KB) |

**Steps:**
1. Navigate directly to `https://automationintesting.online/#/admin`
2. Enter the credentials `admin` and `password` into the login form
3. Submit the login form

**Expected Result:** The admin panel content is not shown; a login form is present.

**Validation:** Verify that the login form is present and that the user cannot access the admin panel without entering valid credentials.

**Category:** positive

**Status:** not_automated

### RB-SEC-008 — XSS In Booking Firstname Does Not Execute

**Pre-conditions:**
- User Role: Any
- Starting URL: https://automationintesting.online
- Required Data State: Booking Form open

**Test Data:**
| Field | Value |
|---|---|
| Firstname | `<script>window.__xss_fired=true</script>` |

**Steps:**
1. Navigate to the Booking Form by clicking the first available Book button on Home Page
2. Enter `<script>window.__xss_fired=true</script>` in the Firstname field
3. Submit the booking form
4. Check for JS dialog events and `window.__xss_fired`

**Expected Result:** No dialog fires; `window.__xss_fired` is not `true`

**Validation:** Verify that `window.__xss_fired` is not `true` using a JavaScript assertion or console log.

**Category:** positive

**Status:** not_automated

### RB-SEC-009 — Home Page Does Not Expose Server Version

**Pre-conditions:**
- User role: Unauthenticated
- Starting URL: <https://automationintesting.online>
- Required data state: No server version in response headers

**Test Data:**
| Field | Value |
|---|---|
| Server Header | apache/, nginx/, or iis/ (to be extracted from response headers) |

**Steps:**
1. Navigate to home page
2. Intercept all responses via Playwright `page.on("response", ...)`
3. Collect `Server` response headers
4. Check if `Server` header contains a version string for apache/, nginx/, or iis/

**Expected Result:** No server version found in the `Server` header

**Validation:** Verify that the `Server` header does not contain a version string for apache/, nginx/, or iis/

**Category:** positive

**Status:** not_automated
