```markdown
# Login Page Test Case Document

## PAGE DETAILS

Page: Login Page (/web/index.php/auth/login)
Description: Application entry point - username/password authentication

Fields (these are the ONLY fields on this form):
  - Username (required)
  - Password (required)
  - Login (optional)
  - Error message (optional)

## DEFINED TEST SCENARIOS

1. [positive] Admin user logs in with valid credentials and lands on dashboard
2. [positive] ESS user logs in and sees limited navigation menu
3. [negative] Wrong password shows 'Invalid credentials' error
4. [negative] Empty username shows validation error
5. [negative] Empty password shows validation error
6. [negative] Both fields empty shows validation error
7. [negative] SQL injection in username shows error, not 500
8. [edge_cases] Username is case-sensitive (Admin != admin)
9. [edge_cases] Browser back button after login does not expose session
10. [edge_cases] Session expires after inactivity

## BUSINESS RULES AND VALIDATIONS

Authentication:
  - Username is case-sensitive
  - Account locks after 5 consecutive failed login attempts (if configured)
  - Session expires after configured inactivity timeout
  - Password must meet complexity: min 8 chars, uppercase, lowercase, number, special char
  - Admin cannot delete their own account

## FIELD VALIDATION RULES

username: {'required': True, 'type': 'string', 'min_length': 5, 'max_length': 40, 'unique': True, 'pattern': 'alphanumeric and underscores only'}
password: {'required': True, 'min_length': 8, 'rules': ['At least one uppercase letter', 'At least one lowercase letter', 'At least one number', 'At least one special character']}

## NEGATIVE SCENARIOS FOR MANDATORY FIELDS

1. Test case title: Empty username
   Pre-conditions: User is on the login page
   Test data: Leave username field empty
   Step-by-step actions: Fill in only the password field, leaving the username field blank; click "Login" button
   Expected results: Error message displays, informing that the username field is required

2. Test case title: Empty password
   Pre-conditions: User is on the login page
   Test data: Leave password field empty
   Step-by-step actions: Fill in only the username field, leaving the password field blank; click "Login" button
   Expected results: Error message displays, informing that the password field is required

3. Test case title: Both fields empty
   Pre-conditions: User is on the login page
   Test data: Leave both fields empty
   Step-by-step actions: Click "Login" button
   Expected results: Error message displays, informing that either the username or password field is required

## INPUT RESTRICTION CHECKS

1. SQL injection test case title: SQL injection in username
   Pre-conditions: User is on the login page
   Test data: Input a malicious string with SQL syntax (e.g., `admin'--`) into the username field
   Step-by-step actions: Fill in the password and click "Login" button
   Expected results: Error message or an application error is displayed, but not a 500 internal server error

## NOTES ON OPTIONAL FIELDS AND EDGE CASES

1. Login field (optional): This field may be used to auto-login the user if a session cookie exists. It's not necessary for manual login.
2. Error message field (optional): Displays error messages related to failed login attempts or validation issues.
3. Username case-sensitivity (edge case): Ensure that username "Admin" and "admin" are treated as separate users.
4. Browser back button after login (edge case): After successful login, the user should be redirected to the dashboard, not be able to access the previous page by clicking the browser's back button.
5. Session expiration (edge case): The session should expire after a configured inactivity timeout.
```