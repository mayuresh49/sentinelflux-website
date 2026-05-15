# Test Case Document for Login Page (/web/index.php/auth/login)

## Overview
This document outlines the test scenarios for the login page of the application. The form includes two required fields: Username and Password, and an optional field for the Login button. Error messages are also displayed as needed.

### Fields on this Form:
1. **Username**
2. **Password**
3. **Login** (optional)
4. **Error message** (optional)

## Test Cases

### Positive Scenarios
1. **Test Case Title:** Admin User Logs In with Valid Credentials and Lands on Dashboard  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = Admin  
     - Password = admin123  
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'Admin' in the username field.
     3. Enter 'admin123' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - The user should be redirected to the dashboard.
   **Validation Rules and Constraints:**
     - Username is case-sensitive.
     - Password must meet complexity requirements (min 8 chars, uppercase, lowercase, number, special char).
   **Notes:**
     - Ensure that the session cookie has the HttpOnly flag set for security.

2. **Test Case Title:** ESS User Logs In and Sees Limited Navigation Menu  
   **Pre-conditions:**
     - The ESS user credentials are known (username=Kris.Chapman, password=Admin123).  
   **Test Data:**
     - Username = Kris.Chapman
     - Password = Admin123
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'Kris.Chapman' in the username field.
     3. Enter 'Admin123' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - The user should be redirected to a limited navigation menu with options like 'My Info', 'Apply for leave', and 'View own leave balance'.
   **Validation Rules and Constraints:**
     - Username is case-sensitive.
     - Password must meet complexity requirements (min 8 chars, uppercase, lowercase, number, special char).
   **Notes:**
     - Ensure that the session cookie has the HttpOnly flag set for security.

### Negative Scenarios
3. **Test Case Title:** Wrong Password Shows 'Invalid Credentials' Error  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = Admin
     - Password = wrongpassword
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'Admin' in the username field.
     3. Enter 'wrongpassword' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - The error message 'Invalid credentials' should be displayed.
   **Validation Rules and Constraints:**
     - Username is case-sensitive.
     - Password must meet complexity requirements (min 8 chars, uppercase, lowercase, number, special char).
   **Notes:**
     - Ensure that no sensitive information is exposed in the error message.

4. **Test Case Title:** Empty Username Shows Validation Error  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = (empty)
     - Password = admin123
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Leave the username field empty.
     3. Enter 'admin123' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - A validation error message should be displayed indicating that the username is required.
   **Validation Rules and Constraints:**
     - Username must not be empty.
     - Password must meet complexity requirements (min 8 chars, uppercase, lowercase, number, special char).
   **Notes:**
     - Ensure that no sensitive information is exposed in the error message.

5. **Test Case Title:** Empty Password Shows Validation Error  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = Admin
     - Password = (empty)
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'Admin' in the username field.
     3. Leave the password field empty.
     4. Click on the Login button.
   **Expected Results:**
     - A validation error message should be displayed indicating that the password is required.
   **Validation Rules and Constraints:**
     - Password must not be empty.
     - Username must meet complexity requirements (min 5 chars, alphanumeric and underscores only).
   **Notes:**
     - Ensure that no sensitive information is exposed in the error message.

6. **Test Case Title:** Both Fields Empty Shows Validation Error  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = (empty)
     - Password = (empty)
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Leave both username and password fields empty.
     3. Click on the Login button.
   **Expected Results:**
     - A validation error message should be displayed indicating that both fields are required.
   **Validation Rules and Constraints:**
     - Username must not be empty.
     - Password must not be empty.
   **Notes:**
     - Ensure that no sensitive information is exposed in the error message.

7. **Test Case Title:** SQL Injection in Username Shows Error, Not 500  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = ' OR '1'='1
     - Password = admin123
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter "' OR '1'='1" in the username field.
     3. Enter 'admin123' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - An error message should be displayed, but not a server error (500).
   **Validation Rules and Constraints:**
     - Username is case-sensitive.
     - Password must meet complexity requirements (min 8 chars, uppercase, lowercase, number, special char).
   **Notes:**
     - Ensure that the application does not expose sensitive information or database errors.

### Edge Cases
8. **Test Case Title:** Username is Case-Sensitive (Admin != admin)  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = admin
     - Password = admin123
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'admin' in the username field.
     3. Enter 'admin123' in the password field.
     4. Click on the Login button.
   **Expected Results:**
     - An error message should be displayed indicating that the credentials are invalid.
   **Validation Rules and Constraints:**
     - Username is case-sensitive.
   **Notes:**
     - Ensure that case sensitivity is correctly enforced.

9. **Test Case Title:** Browser Back Button After Login Does Not Expose Session  
   **Pre-conditions:**
     - The admin user credentials are known (username=Admin, password=admin123).  
   **Test Data:**
     - Username = Admin
     - Password = admin123
   **Step-by-step Actions:**
     1. Navigate to the login page.
     2. Enter 'Admin' in the username field.
     3. Enter 'admin123' in the password field.
     4. Click on the Login button and land on the dashboard.
     5. Press the browser back button.
   **Expected Results:**
     - The login page should not be accessible, or a session expired message should appear if attempting to log in again.
   **Validation Rules and Constraints:**
     - Session management rules apply.
   **Notes:**
     - Ensure that session cookies are properly managed.

10. **Test Case Title:** Session Expires After Inactivity  
    **Pre-conditions:**
      - The admin user credentials are known (username=Admin, password=admin123).  
    **Test Data:**
      - Username = Admin
      - Password = admin123
    **Step-by-step Actions:**
      1. Navigate to the login page.
      2. Enter 'Admin' in the username field.
      3. Enter 'admin123' in the password field.
      4. Click on the Login button and land on the dashboard.
      5. Wait for the configured inactivity timeout period (e.g., 30 minutes).
    **Expected Results:**
      - The user should be automatically logged out, or a session expired message should appear if attempting to perform any action.
    **Validation Rules and Constraints:**
      - Session management rules apply.
    **Notes:**
      - Ensure that session expiration is correctly enforced.

## Known Issues
- **[medium]** Session cookie not marked HttpOnly in some configurations  
  **Hint:** Check response headers for Set-Cookie: HttpOnly flag

- **[high]** IDOR possible if empNumber is guessable — ESS users may access other records via direct URL  
  **Hint:** ESS user accessing /pim/employees/{other_empNumber} should return 403

- **[low]** Username enumeration possible via login error message timing difference  
  **Hint:** Time login responses for valid vs invalid usernames

## Conclusion
This test case document covers the necessary scenarios to ensure that the login page functions correctly, adhering to business rules and security guidelines. It includes positive, negative, and edge-case scenarios to validate user authentication and access control mechanisms.