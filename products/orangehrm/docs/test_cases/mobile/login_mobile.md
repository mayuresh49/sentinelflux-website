### OH-MOB-017 | Scenario | Type | Status | Script  
--- | --- | --- | --- | ---  
OH-MOB-017 | Admin user logs in with valid credentials and lands on dashboard | positive | not_automated | OH-MOB-017_script.py  
OH-MOB-018 | ESS user logs in and sees limited navigation menu | positive | not_automated | OH-MOB-018_script.py  
OH-MOB-019 | Wrong password shows 'Invalid credentials' error | negative | not_automated | OH-MOB-019_script.py  
OH-MOB-020 | Empty username shows validation error | negative | not_automated | OH-MOB-020_script.py  
OH-MOB-021 | Empty password shows validation error | negative | not_automated | OH-MOB-021_script.py  
OH-MOB-022 | Both fields empty shows validation error | negative | not_automated | OH-MOB-022_script.py  
OH-MOB-023 | SQL injection in username shows error, not 500 | negative | not_automated | OH-MOB-023_script.py  
OH-MOB-024 | Username is case-sensitive (Admin != admin) | edge | not_automated | OH-MOB-024_script.py  
OH-MOB-025 | Browser back button after login does not expose session | edge | not_automated | OH-MOB-025_script.py  
OH-MOB-026 | Session expires after inactivity | edge | not_automated | OH-MOB-026_script.py  

---

### Fields in Scope

| Field      | Type     | Required | Validation Rule                                                                 |
|------------|----------|----------|---------------------------------------------------------------------------------|
| Username   | string   | Yes      | min_length: 5, max_length: 40, unique: True, pattern: alphanumeric and underscores only |
| Password   | string   | Yes      | min_length: 8, rules: At least one uppercase letter, At least one lowercase letter, At least one number, At least one special character |

---

### OH-MOB-017 — Admin user logs in with valid credentials and lands on dashboard

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value       |
|----------|-------------|
| Username | Admin       |
| Password | admin123    |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Admin` and password `admin123`.
3. Click on the Login button.

**Expected Result:** The user should be redirected to the dashboard page with full system access.

**Validation:** 
- Assert that the URL redirects to the dashboard.
- Verify that all available modules are displayed (e.g., User management, System configuration).

**Category:** positive

**Status:** not_automated

---

### OH-MOB-018 — ESS user logs in and sees limited navigation menu

**Pre-conditions:**
- User role: ESS
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value          |
|----------|----------------|
| Username | Kris.Chapman   |
| Password | Admin123       |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Kris.Chapman` and password `Admin123`.
3. Click on the Login button.

**Expected Result:** The user should be redirected to a page with limited navigation options, specifically: My Info, Apply for leave, View own leave balance.

**Validation:** 
- Assert that the URL redirects to the ESS dashboard.
- Verify that only the allowed modules are displayed (e.g., My Info, Apply for leave, View own leave balance).

**Category:** positive

**Status:** not_automated

---

### OH-MOB-019 — Wrong password shows 'Invalid credentials' error

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value       |
|----------|-------------|
| Username | Admin       |
| Password | wrong123    |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Admin` and password `wrong123`.
3. Click on the Login button.

**Expected Result:** The user should see an error message stating 'Invalid credentials'.

**Validation:** 
- Assert that an error message is displayed with the text 'Invalid credentials'.
- Verify that the login form remains populated with the entered username.

**Category:** negative

**Status:** not_automated

---

### OH-MOB-020 — Empty username shows validation error

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value |
|----------|-------|
| Username |       |
| Password | admin123 |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Leave the username field empty and enter the password `admin123`.
3. Click on the Login button.

**Expected Result:** The user should see a validation error message indicating that the username is required.

**Validation:** 
- Assert that an error message is displayed with the text 'Username is required'.
- Verify that the login form remains populated with the entered password.

**Category:** negative

**Status:** not_automated

---

### OH-MOB-021 — Empty password shows validation error

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value       |
|----------|-------------|
| Username | Admin       |
| Password |             |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Admin` and leave the password field empty.
3. Click on the Login button.

**Expected Result:** The user should see a validation error message indicating that the password is required.

**Validation:** 
- Assert that an error message is displayed with the text 'Password is required'.
- Verify that the login form remains populated with the entered username.

**Category:** negative

**Status:** not_automated

---

### OH-MOB-022 — Both fields empty shows validation error

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value |
|----------|-------|
| Username |       |
| Password |       |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Leave both the username and password fields empty.
3. Click on the Login button.

**Expected Result:** The user should see a validation error message indicating that both username and password are required.

**Validation:** 
- Assert that an error message is displayed with the text 'Username and Password are required'.
- Verify that the login form remains blank.

**Category:** negative

**Status:** not_automated

---

### OH-MOB-023 — SQL injection in username shows error, not 500

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value         |
|----------|---------------|
| Username | ' OR '1'='1    |
| Password | admin123      |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `' OR '1'='1` and password `admin123`.
3. Click on the Login button.

**Expected Result:** The user should see a validation error message instead of a 500 server error, indicating that SQL injection is not allowed.

**Validation:** 
- Assert that an error message is displayed with the text 'Invalid credentials' or similar.
- Verify that no sensitive information about the database structure is revealed in the error message.

**Category:** negative

**Status:** not_automated

---

### OH-MOB-024 — Username is case-sensitive (Admin != admin)

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value   |
|----------|---------|
| Username | admin   |
| Password | admin123|

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `admin` (in lowercase) and password `admin123`.
3. Click on the Login button.

**Expected Result:** The user should see a validation error message indicating that the credentials are incorrect due to case sensitivity.

**Validation:** 
- Assert that an error message is displayed with the text 'Invalid credentials'.
- Verify that the login form remains populated with the entered username.

**Category:** edge

**Status:** not_automated

---

### OH-MOB-025 — Browser back button after login does not expose session

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value       |
|----------|-------------|
| Username | Admin       |
| Password | admin123    |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Admin` and password `admin123`.
3. Click on the Login button.
4. After being redirected to the dashboard, click the browser back button.

**Expected Result:** The user should be redirected to the login page again or see a message indicating that they need to log in to continue.

**Validation:** 
- Assert that the URL redirects to the login page or displays a message requiring re-login.
- Verify that sensitive information from the dashboard is not accessible when navigating back.

**Category:** edge

**Status:** not_automated

---

### OH-MOB-026 — Session expires after inactivity

**Pre-conditions:**
- User role: Admin
- Starting URL: /web/index.php/auth/login
- No prerequisite data state required

**Test Data:**
| Field    | Value       |
|----------|-------------|
| Username | Admin       |
| Password | admin123    |

**Steps:**
1. Navigate to the exact URL: `/web/index.php/auth/login`
2. Enter the username `Admin` and password `admin123`.
3. Click on the Login button.
4. Keep the browser open but do not perform any actions for a period longer than the session timeout duration.

**Expected Result:** After the session expires, the user should be automatically logged out and redirected to the login page.

**Validation:** 
- Assert that the URL redirects to the login page.
- Verify that no sensitive information from the dashboard is accessible after session expiration.

**Category:** edge

**Status:** not_automated
