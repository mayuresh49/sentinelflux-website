# Test Case Documentation - Login Page (/web/index.php/auth/login)

## Fields in Scope

| Field Name      | Type         | Required  | Validation Rule                                             |
|-----------------|--------------|-----------|------------------------------------------------------------|
| Username        | string       | Yes       | Alphanumeric and underscores only, min 5 chars, max 40 chars, unique |
| Password        | string       | Yes       | Min 8 chars, contains uppercase, lowercase, number, special char |
| Login           | optional     | -         | Not applicable                                             |
| Error Message   | string       | optional  | Varies based on business rules and validation errors       |

## Test Cases

### TC_001 - [positive] Admin user logs in with valid credentials and lands on dashboard

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: Correct admin username and password

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `Admin`      |
| Password  | `admin123`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter the admin username and password in their respective fields.
3. Click the 'Login' button.

**Expected Result:** The user is redirected to the dashboard (e.g., /web/index.php) after a successful login, with no error messages displayed.

**Validation:** Verify that the user is on the correct page (dashboard), and that there are no error messages visible.

**Category:** positive

---

### TC_002 - [positive] ESS user logs in and sees limited navigation menu

**Pre-conditions:**
- User role: ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: Correct ESS username and password

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `Kris.Chapman`      |
| Password  | `Admin123`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter the ESS username and password in their respective fields.
3. Click the 'Login' button.

**Expected Result:** The user is redirected to a page with a limited navigation menu, reflecting ESS access rights. No error messages should be displayed.

**Validation:** Verify that the user is on the correct page (with limited navigation menu), and that there are no error messages visible.

**Category:** positive

---

### TC_003 - [negative] Wrong password shows 'Invalid credentials' error

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: Incorrect username and correct password for either Admin or ESS user

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `Admin`      |
| Password  | `wrong_password`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter an incorrect admin username and correct password in their respective fields.
3. Click the 'Login' button.

**Expected Result:** A message stating "Invalid credentials" should be displayed, with no redirection.

**Validation:** Verify that the "Invalid credentials" error message is displayed, and the user remains on the login page.

**Category:** negative

---

### TC_004 - [negative] Empty username shows validation error

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: No input in the username field

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `""`         |
| Password  | `Admin123`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Leave the username field empty and enter a correct password in the password field.
3. Click the 'Login' button.

**Expected Result:** A validation error message should be displayed next to or below the username field, with no redirection.

**Validation:** Verify that a validation error message is displayed next to the username field, and the user remains on the login page.

**Category:** negative

---

### TC_005 - [negative] Empty password shows validation error

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: No input in the password field

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `Admin`      |
| Password  | `""`         |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter an incorrect username and leave the password field empty.
3. Click the 'Login' button.

**Expected Result:** A validation error message should be displayed next to or below the password field, with no redirection.

**Validation:** Verify that a validation error message is displayed next to the password field, and the user remains on the login page.

**Category:** negative

---

### TC_006 - [negative] Both fields empty shows validation error

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: No input in either field

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `""`         |
| Password  | `""`         |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Leave both fields empty.
3. Click the 'Login' button.

**Expected Result:** Validation error messages should be displayed for both the username and password fields, with no redirection.

**Validation:** Verify that validation error messages are displayed for both the username and password fields, and the user remains on the login page.

**Category:** negative

---

### TC_007 - [negative] SQL injection in username shows error, not 500

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: A user with a valid username (e.g., `Admin`)

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `Admin'; DROP TABLE users; --`      |
| Password  | `Admin123`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter a username with an SQL injection attempt in the username field.
3. Enter a correct password in the password field.
4. Click the 'Login' button.

**Expected Result:** A message stating "Invalid credentials" should be displayed, with no redirection or 500 error.

**Validation:** Verify that the "Invalid credentials" error message is displayed, and there are no signs of a SQL injection vulnerability exploited (e.g., no tables deleted).

**Category:** negative

---

### TC_008 - [edge_cases] Username is case-sensitive (Admin != admin)

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- Prerequisite data state: Correct uppercase username and incorrect lowercase equivalent

**Test Data:**
| Field | Value        |
|---|---|
| Username  | `admin`      |
| Password  | `admin123`   |

**Steps:**
1. Navigate to the login page at `/web/index.php/auth/login`.
2. Enter an incorrect lowercase username and the correct password in their respective fields.
3. Click the 'Login' button.

**Expected Result:** A message stating "Invalid credentials" should be displayed, with no redirection.

**Validation:** Verify that the "Invalid credentials" error message is displayed, and the user remains on the login page.

**Category:** edge

---

### TC_009 - [security] Check for secure storage of passwords

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: Not applicable (This is an architectural test, not a functional one)
- Prerequisite data state: N/A

**Test Data:**
N/A

**Steps:**
1. Investigate the storage mechanism for passwords in the application's database.
2. Verify that passwords are hashed and salted, and not stored as plain text.

**Expected Result:** Passwords should be hashed and salted, with no signs of being stored as plain text.

**Validation:** This validation will require a deep understanding of the application's codebase and data storage mechanisms. Consult with security experts or perform penetration testing if necessary.

**Category:** security

---

### TC_010 - [security] Check for rate limiting on login attempts

**Pre-conditions:**
- User role: Admin or ESS
- Starting URL: Not applicable (This is an architectural test, not a functional one)
- Prerequisite data state: N/A

**Test Data:**
N/A

**Steps:**
1. Investigate the login mechanism in the application to see if it includes rate limiting for preventing brute force attacks.
2. Perform multiple login attempts with incorrect credentials to test if rate limiting is applied.

**Expected Result:** After a certain number of failed attempts, further attempts should be blocked or delayed for a set period of time to prevent brute force attacks.

**Validation:** This validation will require a deep understanding of the application's codebase and security mechanisms. Consult with security experts or perform penetration testing if necessary.

**Category:** security

---
