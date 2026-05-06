```markdown
# Test Case Document - PIM Employee List Page

## Page Details
- Page: PIM - Employee List (/web/index.php/pim/viewEmployeeList)
- Description: List of all employees with search and filter functionality
- Fields (explicit list from KB):
  - Employee Name (optional)
  - Employee Id (optional)
  - Search (optional)
  - Add (optional)
  - Employee table (optional)
  - Record count (optional)
  - Row checkbox (optional)

## Test Scenarios
### Positive Tests
1. **[positive]** Employee list loads with all employees on page load
2. **[positive]** Search by employee name filters results correctly
3. **[positive]** Search by employee ID filters to exact match
4. **[positive]** Clicking Add navigates to add employee form
5. **[positive]** Record count updates after search
6. **[positive]** 'No Records Found' is displayed when searching with a non-existent name
7. **[positive]** Special characters are handled gracefully during searches
8. **[edge_cases]** Search is case-insensitive
9. **[edge_cases]** Partial name search returns all matching employees

### Negative Tests
10. **[negative]** Search with non-existent employee ID does not filter the results

## Test Case - Employee List Loads Correctly

### Pre-conditions
- The user is authenticated and has appropriate permissions to access the PIM - Employee List page.

### Step-by-step actions
1. Navigate to /web/index.php/pim/viewEmployeeList
2. Observe the employee list displayed on the page.

### Expected results
- The employee list should load with all employees present in the system.

## Test Case - Search by Employee Name

### Pre-conditions
- The user is authenticated and has appropriate permissions to access the PIM - Employee List page.
- Multiple employees with different names are present in the system.

### Step-by-step actions
1. In the search bar, enter a valid employee name.
2. Press Enter or click 'Search'.
3. Observe the updated employee list displayed on the page.

### Expected results
- The updated employee list should only contain employees with the entered name.

## Test Case - Search by Employee ID

### Pre-conditions
- The user is authenticated and has appropriate permissions to access the PIM - Employee List page.
- Multiple employees with different IDs are present in the system.

### Step-by-step actions
1. In the search bar, enter a valid employee ID.
2. Press Enter or click 'Search'.
3. Observe the updated employee list displayed on the page.

### Expected results
- The updated employee list should only contain the employee with the exact entered ID.
```

```markdown
# Test Case Document - PIM Add Employee Form

## Page Details
- Page: PIM - Add Employee (/web/index.php/pim/addEmployee)
- Description: Form to create a new employee record
- Fields (explicit list from KB):
  - First Name (required), max_length=30
  - Middle Name (optional), max_length=30
  - Last Name (required), max_length=30
  - Employee Id (optional)
  - Create Login Details (optional)
  - Save (optional)
  - Cancel (optional)

## Test Scenarios
### Positive Tests
1. **[positive]** Save with first name and last name creates employee and redirects to profile
2. **[positive]** Save with all fields populates employee record correctly
3. **[positive]** Enable Create Login Details shows username/password fields
4. **[positive]** Cancel navigates back to employee list without saving
5. **[positive]** Auto-generated employee ID is unique
6. **[edge_cases]** First name with only spaces shows validation error
7. **[edge_cases]** Employee ID with special characters is rejected
8. **[edge_cases]** First name with accented characters is accepted

### Negative Tests
9. **[negative]** Save without first name shows required field error
10. **[negative]** Save without last name shows required field error
11. **[negative]** First name exceeding 30 characters shows validation error
12. **[negative]** Duplicate employee ID shows error
```

This markdown document provides test case descriptions for the PIM - Employee List and PIM - Add Employee pages, following the strict rules as specified.