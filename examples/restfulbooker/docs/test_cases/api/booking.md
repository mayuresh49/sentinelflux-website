# API Test Case Document for /booking

## Endpoint Scope

### POST /booking: Create a new booking record
- **Method:** POST
- **Path:** /booking
- **Request Fields:**
  - `firstname` (string) - Required
  - `lastname` (string) - Required
  - `totalprice` (number) - Required
  - `depositpaid` (boolean) - Required
  - `bookingdates` (object) - Required
    - `checkin` (date) - Required
    - `checkout` (date) - Required
  - `additionalneeds` (string, optional) - Limited to 500 characters
- **Response Codes:**
  - 201 Created

### GET /booking/{id}: Retrieve a booking by ID
- **Method:** GET
- **Path:** /booking/{id}
- **Request Fields:**
  - `id` (number) - Required
- **Response Codes:**
  - 200 OK
  - 404 Not Found

### PUT /booking/{id}: Update an existing booking
- **Method:** PUT
- **Path:** /booking/{id}
- **Request Fields:**
  - `firstname` (string, optional)
  - `lastname` (string, optional)
  - `totalprice` (number, optional)
  - `depositpaid` (boolean, optional)
  - `additionalneeds` (string, optional) - Limited to 500 characters
  - `bookingdates` (object, optional)
    - `checkin` (date, optional)
    - `checkout` (date, optional)
- **Response Codes:**
  - 200 OK
  - 404 Not Found

### DELETE /booking/{id}: Delete a booking
- **Method:** DELETE
- **Path:** /booking/{id}
- **Request Fields:**
  - `id` (number) - Required
- **Response Codes:**
  - 201 Created

## Positive Test Cases

### POST /booking
- **Description:** Create a new booking with valid data
- **Input Data:**
  ```json
  {
    "firstname": "John",
    "lastname": "Doe",
    "totalprice": 100,
    "depositpaid": true,
    "bookingdates": {
      "checkin": "2024-01-01",
      "checkout": "2024-01-02"
    },
    "additionalneeds": "Breakfast included"
  }
  ```
- **Expected Response Code:** 201 Created

### GET /booking/{id}
- **Description:** Retrieve a booking by valid ID
- **Input Data:**
  - `id` (integer) - Assume valid ID returned from POST request
- **Expected Response Code:** 200 OK

### PUT /booking/{id}
- **Description:** Update an existing booking with valid partial data
- **Input Data:**
  - `id` (integer) - Assume valid ID returned from POST request
  ```json
  {
    "firstname": "Jane",
    "totalprice": 150,
    "additionalneeds": ""
  }
  ```
- **Expected Response Code:** 200 OK

### DELETE /booking/{id}
- **Description:** Delete a booking by valid ID
- **Input Data:**
  - `id` (integer) - Assume valid ID returned from POST request
- **Expected Response Code:** 201 Created

## Negative Test Cases

### POST /booking
- **Description:** Missing required fields
  - **Field Missing:** `firstname`
  - **Expected Response Code:** Error response with appropriate error message
- **Description:** Invalid data types
  - **Invalid Field:** `totalprice` as string ("100")
  - **Expected Response Code:** Error response with appropriate error message
- **Description:** Date validation failure
  - **Invalid Field:** `checkin` after `checkout`
  - **Expected Response Code:** Error response with appropriate error message

### GET /booking/{id}
- **Description:** Non-existing booking ID
  - **Input Data:**
    - `id` (integer) - 999999999 (assumed non-existent)
  - **Expected Response Code:** 404 Not Found

### PUT /booking/{id}
- **Description:** Update non-existing booking
  - **Input Data:**
    - `id` (integer) - 999999999 (assumed non-existent)
  - **Expected Response Code:** 404 Not Found

### DELETE /booking/{id}
- **Description:** Non-existing booking ID
  - **Input Data:**
    - `id` (integer) - 999999999 (assumed non-existent)
  - **Expected Response Code:** Error response with appropriate error message

## Edge Cases

### POST /booking
- **Description:** Maximum stay duration
  - **Input Data:**
    ```json
    {
      "firstname": "Edge",
      "lastname": "Case",
      "totalprice": 100,
      "depositpaid": true,
      "bookingdates": {
        "checkin": "2024-01-01",
        "checkout": "2025-01-01"
      },
      "additionalneeds": ""
    }
    ```
  - **Expected Response Code:** Error response with appropriate error message

### PUT /booking/{id}
- **Description:** Update with empty string for `firstname`
  - **Input Data:**
    - `id` (integer) - Assume valid ID returned from POST request
    ```json
    {
      "firstname": ""
    }
    ```
  - **Expected Response Code:** Error response with appropriate error message

### GET /booking/{id}
- **Description:** Very large booking ID
  - **Input Data:**
    - `id` (integer) - 9223372036854775807 (max integer value)
  - **Expected Response Code:** Error response with appropriate error message

## Authentication and Authorization Cases

- **Description:** No authentication token validation in mock API
- **Input Data:**
  - N/A (no token required for mock testing)
- **Expected Response Code:** Appropriate response code based on endpoint logic

## Validation Rules

1. **Check-out date must be after check-in date**
   - **Validation Rule:** Ensure `checkout` > `checkin`
   - **Error Message:** "Checkout date must be after check-in date"

2. **Booking price must be between 0 and 10000**
   - **Validation Rule:** Ensure `totalprice` within range
   - **Error Message:** "Total price must be between 0 and 10000"

3. **Guest first name and last name are mandatory**
   - **Validation Rule:** Ensure both `firstname` and `lastname` are present
   - **Error Message:** "First name and last name are required"

4. **Deposit can be optional**
   - **Validation Rule:** Allow `depositpaid` to be omitted or boolean

5. **Maximum stay duration is 365 days**
   - **Validation Rule:** Ensure `checkout` within 1 year of `checkin`
   - **Error Message:** "Maximum stay duration is 365 days"

6. **Bookings cannot be created for past dates**
   - **Validation Rule:** Ensure `checkin` not in the past
   - **Error Message:** "Bookings cannot be made for past dates"

7. **Additional needs field is optional and limited to 500 characters**
   - **Validation Rule:** Allow empty or string with max length 500
   - **Error Message:** "Additional needs must be less than 500 characters"