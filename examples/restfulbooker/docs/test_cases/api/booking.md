# API Test Case Document

## Endpoint Scope

### POST /booking
**Method:** POST  
**Path:** /booking  
**Request Fields:**
- `firstname` (string): Guest's first name
- `lastname` (string): Guest's last name
- `totalprice` (number): Total price of the booking
- `depositpaid` (boolean): Whether deposit is paid or not
- `bookingdates` (object):
  - `checkin` (date): Check-in date in YYYY-MM-DD format
  - `checkout` (date): Check-out date in YYYY-MM-DD format
- `additionalneeds` (string, optional): Additional needs of the guest

**Response Codes:**
- 201 Created: Booking successfully created
- 400 Bad Request: Invalid or missing fields

### GET /booking/{id}
**Method:** GET  
**Path:** /booking/{id}  
**Request Fields:**
- `id` (number): Booking ID

**Response Codes:**
- 200 OK: Booking details retrieved successfully
- 404 Not Found: Booking not found
- 400 Bad Request: Invalid booking ID format

### PUT /booking/{id}
**Method:** PUT  
**Path:** /booking/{id}  
**Request Fields:**
- `firstname` (string, optional): Guest's first name
- `lastname` (string, optional): Guest's last name
- `totalprice` (number, optional): Total price of the booking
- `depositpaid` (boolean, optional): Whether deposit is paid or not
- `bookingdates` (object, optional):
  - `checkin` (date, optional): Check-in date in YYYY-MM-DD format
  - `checkout` (date, optional): Check-out date in YYYY-MM-DD format
- `additionalneeds` (string, optional): Additional needs of the guest

**Response Codes:**
- 200 OK: Booking updated successfully
- 404 Not Found: Booking not found
- 400 Bad Request: Invalid booking ID format or invalid data types

### DELETE /booking/{id}
**Method:** DELETE  
**Path:** /booking/{id}  
**Request Fields:**
- `id` (number): Booking ID

**Response Codes:**
- 201 Created: Booking successfully deleted
- 404 Not Found: Booking not found
- 400 Bad Request: Invalid booking ID format

## Positive Test Cases

### POST /booking
1. **Create a valid booking**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": true,
       "bookingdates": {
         "checkin": "2024-10-01",
         "checkout": "2024-10-07"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 201 Created

### GET /booking/{id}
1. **Retrieve booking by valid ID**
   - Request:
     ```json
     {
       "id": 1
     }
     ```
   - Expected Response: 200 OK, Booking details

### PUT /booking/{id}
1. **Update a valid booking**
   - Request:
     ```json
     {
       "totalprice": 600,
       "depositpaid": false
     }
     ```
   - Expected Response: 200 OK

### DELETE /booking/{id}
1. **Delete a valid booking**
   - Request:
     ```json
     {
       "id": 1
     }
     ```
   - Expected Response: 201 Created

## Negative Test Cases

### POST /booking
1. **Missing firstname field**
   - Request:
     ```json
     {
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": true,
       "bookingdates": {
         "checkin": "2024-10-01",
         "checkout": "2024-10-07"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

2. **totalPrice as string instead of number**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": "five hundred",
       "depositpaid": true,
       "bookingdates": {
         "checkin": "2024-10-01",
         "checkout": "2024-10-07"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

3. **depositpaid as non-boolean**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": "yes",
       "bookingdates": {
         "checkin": "2024-10-01",
         "checkout": "2024-10-07"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

4. **Invalid date format (DD/MM/YYYY instead of YYYY-MM-DD)**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": true,
       "bookingdates": {
         "checkin": "01/10/2024",
         "checkout": "07/10/2024"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

5. **Checkin date after checkout date**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": true,
       "bookingdates": {
         "checkin": "2024-10-07",
         "checkout": "2024-10-01"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

6. **Historical dates (past)**
   - Request:
     ```json
     {
       "firstname": "John",
       "lastname": "Doe",
       "totalprice": 500,
       "depositpaid": true,
       "bookingdates": {
         "checkin": "2023-10-01",
         "checkout": "2023-10-07"
       },
       "additionalneeds": "Breakfast included"
     }
     ```
   - Expected Response: 400 Bad Request

### GET /booking/{id}
1. **Non-existing booking ID**
   - Request:
     ```json
     {
       "id": 999999
     }
     ```
   - Expected Response: 404 Not Found

2. **Negative booking ID**
   - Request:
     ```json
     {
       "id": -1
     }
     ```
   - Expected Response: 400 Bad Request

3. **Alphabetic characters as ID**
   - Request:
     ```json
     {
       "id": "abc"
     }
     ```
   - Expected Response: 400 Bad Request

4. **Very large ID number**
   - Request:
     ```json
     {
       "id": 9999999999999999999999999999999