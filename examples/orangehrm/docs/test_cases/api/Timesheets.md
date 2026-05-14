# API Test Case Document: /Timesheets (ALL)

## Endpoint Scope

### **Method:** GET  
**Path:** `/timesheets`  
**Request Fields:** None  
**Response Codes from KB:**  
- 200 OK: Successful retrieval of timesheets.  
- 401 Unauthorized: Authentication required.  
- 403 Forbidden: Access denied due to insufficient permissions.  

### **Method:** POST  
**Path:** `/timesheets`  
**Request Fields:**  
- `empNumber`: Employee ID (required)  
- `date`: Date of the timesheet entry (YYYY-MM-DD, required)  
- `hours`: Number of hours worked (required)  
- `description`: Description of work done (optional)  

**Response Codes from KB:**  
- 201 Created: Timesheet successfully created.  
- 400 Bad Request: Invalid input data.  
- 401 Unauthorized: Authentication required.  
- 403 Forbidden: Access denied due to insufficient permissions.  

### **Method:** PUT  
**Path:** `/timesheets/{timesheetId}`  
**Request Fields:**  
- `hours`: Number of hours worked (optional)  
- `description`: Description of work done (optional)  

**Response Codes from KB:**  
- 200 OK: Timesheet successfully updated.  
- 400 Bad Request: Invalid input data.  
- 401 Unauthorized: Authentication required.  
- 403 Forbidden: Access denied due to insufficient permissions.  
- 404 Not Found: The specified timesheet entry does not exist.  

### **Method:** DELETE  
**Path:** `/timesheets/{timesheetId}`  
**Request Fields:** None  

**Response Codes from KB:**  
- 204 No Content: Timesheet successfully deleted.  
- 401 Unauthorized: Authentication required.  
- 403 Forbidden: Access denied due to insufficient permissions.  
- 404 Not Found: The specified timesheet entry does not exist.  

## Positive Test Cases

### **GET /timesheets**

1. **Test Case:** Retrieve all timesheets
   - **Description:** Verify that the API returns a list of timesheets with valid data.
   - **Input:** None  
   - **Expected Output:** 200 OK, JSON array containing timesheet entries.

### **POST /timesheets**

1. **Test Case:** Create a new timesheet entry
   - **Description:** Verify that the API successfully creates a new timesheet entry with valid data.
   - **Input:**  
     ```json
     {
       "empNumber": 1,
       "date": "2023-04-15",
       "hours": 8.0,
       "description": "Worked on project XYZ"
     }
     ```  
   - **Expected Output:** 201 Created, JSON object with the newly created timesheet details.

### **PUT /timesheets/{timesheetId}**

1. **Test Case:** Update an existing timesheet entry
   - **Description:** Verify that the API successfully updates an existing timesheet entry.
   - **Input:**  
     ```json
     {
       "hours": 8.5,
       "description": "Updated description for project XYZ"
     }
     ```  
   - **Expected Output:** 200 OK, JSON object with updated timesheet details.

### **DELETE /timesheets/{timesheetId}**

1. **Test Case:** Delete an existing timesheet entry
   - **Description:** Verify that the API successfully deletes an existing timesheet entry.
   - **Input:** None  
   - **Expected Output:** 204 No Content, no response body.

## Negative Test Cases

### **GET /timesheets**

1. **Test Case:** Unauthenticated access to retrieve timesheets
   - **Description:** Verify that the API returns an unauthorized error when accessed without authentication.
   - **Input:** None  
   - **Expected Output:** 401 Unauthorized, JSON object with error details.

2. **Test Case:** Access denied due to insufficient permissions
   - **Description:** Verify that the API returns a forbidden error when a user attempts to access timesheets without proper permissions.
   - **Input:** None  
   - **Expected Output:** 403 Forbidden, JSON object with error details.

### **POST /timesheets**

1. **Test Case:** Missing empNumber
   - **Description:** Verify that the API returns a bad request error when creating a timesheet entry without an empNumber.
   - **Input:**  
     ```json
     {
       "date": "2023-04-15",
       "hours": 8.0,
       "description": "Worked on project XYZ"
     }
     ```  
   - **Expected Output:** 400 Bad Request, JSON object with error details.

2. **Test Case:** Invalid date format
   - **Description:** Verify that the API returns a bad request error when creating a timesheet entry with an invalid date format.
   - **Input:**  
     ```json
     {
       "empNumber": 1,
       "date": "15-04-2023",
       "hours": 8.0,
       "description": "Worked on project XYZ"
     }
     ```  
   - **Expected Output:** 400 Bad Request, JSON object with error details.

### **PUT /timesheets/{timesheetId}**

1. **Test Case:** Update a non-existent timesheet entry
   - **Description:** Verify that the API returns a not found error when attempting to update a non-existent timesheet entry.
   - **Input:**  
     ```json
     {
       "hours": 8.5,
       "description": "Updated description for project XYZ"
     }
     ```  
   - **Expected Output:** 404 Not Found, JSON object with error details.

### **DELETE /timesheets/{timesheetId}**

1. **Test Case:** Delete a non-existent timesheet entry
   - **Description:** Verify that the API returns a not found error when attempting to delete a non-existent timesheet entry.
   - **Input:** None  
   - **Expected Output:** 404 Not Found, JSON object with error details.

## Edge Cases

### **GET /timesheets**

1. **Test Case:** Retrieve timesheets with no entries
   - **Description:** Verify that the API returns an empty array when there are no timesheet entries.
   - **Input:** None  
   - **Expected Output:** 200 OK, JSON array with zero elements.

### **POST /timesheets**

1. **Test Case:** Create a timesheet entry with minimum required fields
   - **Description:** Verify that the API successfully creates a timesheet entry with only the minimum required fields.
   - **Input:**  
     ```json
     {
       "empNumber": 1,
       "date": "2023-04-15",
       "hours": 8.0
     }
     ```  
   - **Expected Output:** 201 Created, JSON object with the newly created timesheet details.

### **PUT /timesheets/{timesheetId}**

1. **Test Case:** Update a timesheet entry without any fields
   - **Description:** Verify that the API successfully updates an existing timesheet entry without changing any fields.
   - **Input:** None  
   - **Expected Output:** 200 OK, JSON object with unchanged timesheet details.

## Authentication and Authorization Cases

### **GET /timesheets**

1. **Test Case:** Authorized access to retrieve timesheets
   - **Description:** Verify that the API successfully retrieves timesheets when accessed by a user with proper authentication.
   - **Input:** None  
   - **Expected Output:** 200 OK, JSON array containing timesheet entries.

### **POST /timesheets**

1. **Test Case:** Authorized access to create a new timesheet entry
   - **Description:** Verify that the API successfully creates a new timesheet entry when accessed by a user with proper authentication.
   - **Input:**  
     ```json
     {
       "empNumber": 1,
       "date": "2023-04-15",
       "hours": 8.0,
       "description": "Worked on project XYZ"
     }
     ```  
   - **Expected Output:** 201 Created, JSON object with the newly created timesheet details.

### **PUT /timesheets/{timesheetId}**

1. **Test Case:** Authorized access to update an existing timesheet entry
   - **Description:** Verify that the API successfully updates an existing timesheet entry when accessed by a user with proper authentication.
   - **Input:**  
     ```json
     {
       "hours": 8.5,
       "description": "Updated description for project XYZ"
     }
     ```  
   - **Expected Output:** 200 OK, JSON object with updated timesheet details.

### **DELETE /timesheets/{timesheetId}**

1. **Test Case:** Authorized access to delete an existing timesheet entry
   - **Description:** Verify that the API successfully deletes an existing timesheet entry when accessed by a user with proper authentication.
   - **Input:** None  
   - **Expected Output:** 204 No Content, no response body.

## Validation Rules

### **POST /timesheets**

1. **Test Case:** Validate empNumber uniqueness
   - **Description:** Verify that the API returns an error when attempting to create a timesheet entry for an employee with a non-existent empNumber.
   - **Input:**  
     ```json
     {
       "empNumber": 9999,
       "date": "2023-04-15",
       "hours": 8.0,
       "description": "Worked on project XYZ"
     }
     ```  
   - **Expected Output:** 400 Bad Request, JSON object with error details.

### **PUT /timesheets/{timesheetId}**

1. **Test Case:** Validate hours range
   - **Description:** Verify that the API returns an error when attempting to update a timesheet entry with invalid hours (e.g., negative or zero).
   - **Input:**  
     ```json
     {
       "hours": -5,
       "description": "Updated description for project XYZ"
     }
     ```  
   - **Expected Output:** 400 Bad Request, JSON object with error details.

This document provides a comprehensive set of test cases to ensure the robustness and correctness of the `/timesheets` API endpoint. Each test case is designed to validate different scenarios, including positive functionality, negative inputs, edge cases, authentication requirements, and validation rules as specified in the provided knowledge base context.