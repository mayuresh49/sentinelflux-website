## API Test Case Document for `/booking`

### Endpoint Scope

#### **POST /booking**
- **Method:** POST
- **Path:** `/booking`
- **Request Fields:**
  - `firstname` (string, required)
  - `lastname` (string, required)
  - `totalprice` (number, required)
  - `depositpaid` (boolean, required)
  - `bookingdates` (object, required)
    - `checkin` (string, date in format YYYY-MM-DD, required)
    - `checkout` (string, date in format YYYY-MM-DD, required)
  - `additionalneeds` (string, optional)
- **Response Codes:**
  - `201 Created`
  - `400 Bad Request`

#### **GET /booking/{id}**
- **Method:** GET
- **Path:** `/booking/{id}`
- **Request Fields:**
  - `id` (integer, required)
- **Response Codes:**
  - `200 OK`
  - `404 Not Found`

#### **PUT /booking/{id}**
- **Method:** PUT
- **Path:** `/booking/{id}`
- **Request Fields:**
  - `firstname` (string, optional)
  - `lastname` (string, optional)
  - `totalprice` (number, optional)
  - `depositpaid` (boolean, optional)
  - `additionalneeds` (string, optional)
  - `bookingdates` (object, optional)
    - `checkin` (string, date in format YYYY-MM-DD, optional)
    - `checkout` (string, date in format YYYY-MM-DD, optional)
- **Response Codes:**
  - `200 OK`
  - `404 Not Found`
  - `400 Bad Request`

#### **DELETE /booking/{id}**
- **Method:** DELETE
- **Path:** `/booking/{id}`
- **Request Fields:**
  - `id` (integer, required)
- **Response Codes:**
  - `201 Created`
  - `404 Not Found`

### Positive Test Cases

#### **POST /booking**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2024-01-15",
    "checkout": "2024-01-20"
  },
  "additionalneeds": "Breakfast"
}
```
**Expected Response:** `201 Created`

#### **GET /booking/{id}**
- Assume the booking ID returned from the POST request is `123`.

**Expected Response:**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2024-01-15",
    "checkout": "2024-01-20"
  },
  "additionalneeds": "Breakfast"
}
```
**Expected Response Code:** `200 OK`

#### **PUT /booking/{id}**
```json
{
  "firstname": "Jane",
  "lastname": "Doe",
  "totalprice": 350,
  "depositpaid": false,
  "bookingdates": {
    "checkin": "2024-01-16",
    "checkout": "2024-01-21"
  },
  "additionalneeds": "Late check-out"
}
```
**Expected Response:** `200 OK`

#### **DELETE /booking/{id}**
- Assume the booking ID returned from the POST request is `123`.

**Expected Response Code:** `201 Created`

### Negative Test Cases

#### **POST /booking**
```json
{
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2024-01-15",
    "checkout": "2024-01-20"
  }
}
```
**Expected Response Code:** `400 Bad Request`

#### **POST /booking**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": "two fifty",
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2024-01-15",
    "checkout": "2024-01-20"
  }
}
```
**Expected Response Code:** `400 Bad Request`

#### **POST /booking**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": "yes",
  "bookingdates": {
    "checkin": "2024-01-15",
    "checkout": "2024-01-20"
  }
}
```
**Expected Response Code:** `400 Bad Request`

#### **POST /booking**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "15/01/2024",
    "checkout": "20/01/2024"
  }
}
```
**Expected Response Code:** `400 Bad Request`

#### **POST /booking**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "totalprice": 250,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2026-01-20",
    "checkout": "2024-01-15"
  }
}
```
**Expected Response Code:** `400 Bad Request`

#### **GET /booking/{id}**
```json
{
  "id": "abc"
}
```
**Expected Response Code:** `404 Not Found`

#### **PUT /booking/{id}**
```json
{
  "totalprice": "three hundred"
}
```
**Expected Response Code:** `400 Bad Request`

### Edge Cases

#### **POST /booking**
```json
{
  "firstname": "A",
  "lastname": "B",
  "totalprice": 0,
  "depositpaid": false,
  "bookingdates": {
    "checkin": "2026-01-01",
    "checkout": "2026-01-02"
  }
}
```
**Expected Response:** `201 Created`

#### **POST /booking**
```json
{
  "firstname": "C",
  "lastname": "D",
  "totalprice": 10000,
  "depositpaid": true,
  "bookingdates": {
    "checkin": "2026-01-01",
    "checkout": "2026-12-31"
  }
}
```
**Expected Response:** `201 Created`

#### **POST /booking**
```json
{
  "firstname": "E",
  "lastname": "F",
  "totalprice": 250,
  "depositpaid": true,
  "additionalneeds": "A very long string that exceeds 500 characters and is intended to test the length limit of additional needs field. This string should be long enough to exceed the maximum allowed character count for this field."
}
```
**Expected Response:** `400 Bad Request`

### Authentication and Authorization Cases

- **Assumption:** No authentication token validation in mock API.

### Validation Rules

1. **Check-out date must be after check-in date**
2. **Booking price must be between 0 and 10000**
3. **Guest first name and last name are mandatory**
4. **Deposit can be optional**
5. **Maximum stay duration is 365 days**
6. **Bookings cannot be created for past dates**
7. **Additional needs field is optional and limited to 500 characters**