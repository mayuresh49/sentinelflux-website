# API Test Case Documentation

No generated docs yet — run the pipeline to populate this directory:

```bash
python3 -m ai.generate_api_test_doc --endpoint /booking --method POST \
    --output docs/test_cases/api/booking_create.md

python3 -m ai.generate_api_test_doc --endpoint /booking --method GET \
    --output docs/test_cases/api/booking_get.md
```

See [API Test Generation Guide](../../api_test_generation.md) for full options and GraphQL support.
