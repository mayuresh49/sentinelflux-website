# API Test Case Coverage

## Booking REST API

### Positive scenarios
- Create booking with valid payload and expected 200/201 response.
- Retrieve booking details for a created booking ID and verify response data.
- Update booking with valid optional fields and verify persistence.

### Edge cases
- Create booking with minimum required fields only.
- Create booking with maximum allowed field lengths and verify acceptance.
- Update booking with partial payload and confirm unchanged fields remain intact.
- Retrieve booking using a valid booking ID at boundary values if supported.

### Negative scenarios
- Create booking with missing required fields and expect 400 validation error.
- Create booking with invalid data types for fields like `totalPrice` or `depositPaid`.
- Create booking with unsupported date formats and verify error response.
- Retrieve booking using a non-existing booking ID and expect 404.
- Update booking with invalid or malformed payload and expect appropriate error.

### Validation focus
- Response schema validation against `booking_schema.json`.
- Required field presence and type checks.
- Status code assertions for success and failure paths.
- Error message content when invalid inputs are submitted.

## GraphQL API

### Positive scenarios
- Query country by code and verify returned `name` and `code`.
- Validate GraphQL response structure and data fields.

### Edge cases
- Query with optional arguments omitted if supported.
- Request a single field only and verify minimal response.

### Negative scenarios
- Query with missing required variables and expect GraphQL error.
- Query with invalid country code and verify error or empty response handling.
- Validate response to malformed query syntax if the client supports it.

### Validation focus
- GraphQL error handling and status assertions.
- Response payload content and schema checks.
- Negative input handling for invalid variables.
