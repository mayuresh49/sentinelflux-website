from utils.assertions import assert_status_code


def test_countries_query(graphql_client):
    response = graphql_client.execute(
        query_name="countries_list",
        payload_name="countries_variables",
    )
    assert_status_code(response, 200)
    payload = response.json()
    assert payload["data"]["country"]["code"] == "US"
    assert payload["data"]["country"]["name"] == "United States"
