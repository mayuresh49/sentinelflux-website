# Timesheets Test Case Document

## Fields on the Timesheets Form

- Employee ID (employee_id): Unique across the system, auto-generated if not provided
- From Date (timesheet_from_date): Represents start date of the timesheet
- To Date (timesheet_to_date): Represents end date of the timesheet
- Hours Worked (timesheet_hours_worked): Represents total hours worked during the specified timesheet period

## Test Case Titles

1. Verify Timesheet Form Access Based on User Role
2. Valid Timesheet Submission with Correct Data
3. Mandatory Fields Validation for Timesheet Form
4. Input Restriction Checks for Timesheet Hours Worked
5. Negative Scenarios for Timesheet From Date and To Date
6. Validate Employee ID Uniqueness
7. Test Session Expiry and Inactivity Timeout
8. Test Password Complexity Rules
9. Test Admin Cannot Delete Their Own Account
10. Test ESS Users Can Only Edit Their Own Profile
11. Test Supervisor Can View Direct Reports' Timesheets

## Pre-conditions

- Authenticated user with valid credentials (admin, ess_user or supervisor)
- Correct permissions for the user role
- Active employee record associated with the ESS user or supervisor account

## Test Data

Use actual test credentials and data from the Knowledge Base Context:
- admin username: Admin, password: admin123
- ess_user username: Kris.Chapman, password: Admin123

Other required data will be generated as part of the tests (e.g., employee ID, timesheet dates, hours worked).

## Step-by-step actions

Details for each test case are described in their corresponding sections below.

## Expected results

Expected results will be based on documented business rules and validation rules:
- Timesheets can be submitted, viewed, edited or deleted based on user role and permissions
- Mandatory fields are required (employee ID, from date, to date)
- Hours worked should be within input restriction limits if provided (minimum hours per day, maximum hours per week, etc.)
- Employee ID must be unique across the system
- Session expires after configured inactivity timeout
- Password meets complexity requirements: min 8 chars, uppercase, lowercase, number, special char
- Admin cannot delete their own account
- ESS users can only edit their own profile
- Supervisor can view direct reports' timesheets

## Negative scenarios for mandatory fields

1. Employee ID not provided (system should generate one automatically)
2. From Date is left blank or is in the past
3. To Date is left blank or is before From Date
4. Hours Worked is left blank or has a value outside of the input restriction limits

## Input restriction checks (only for limits documented in KB)

- Timesheet Hours Worked: Minimum hours per day, maximum hours per week

## Notes on optional fields and edge cases

- Hours Worked is not required if the user's employment status indicates "On Leave" during the timesheet period
- If a timesheet contains no entries (i.e., all days off), it can still be saved without errors
- Timesheets can span across multiple weeks, as long as the input restriction limits for hours worked per week are met