import pytest
import pytest_asyncio
import httpx
import uuid
import json
import time
from elasticsearch import AsyncElasticsearch
# Assuming generated_models is accessible, adjust path if needed
# Might need to add event-ingest to PYTHONPATH when running tests
from event_ingest.generated_models import Event, Location, Geo, OrganizerInfo, Media

SERVICE_URL = "http://localhost:8081"  # event-ingest-test service
ES_URL = "http://localhost:9201"       # elasticsearch-test service
INDEX_NAME = "events"

@pytest.mark.asyncio
async def test_create_event_successful():
    event_id = str(uuid.uuid4())
    test_event = Event(
        id=event_id,
        title="Integration Test Event",
        description="Testing the event creation pipeline.",
        start_time="2025-06-01T10:00:00Z",
        end_time="2025-06-01T12:00:00Z", # Added based on typical event structure
        event_source_url="http://example.com/event", # Added based on typical event structure
        location=Location(
            name="Test Location",
            address="123 Test St, Test City", # Added for completeness
            geo=Geo(lat=0.0, lon=0.0)
        ),
        organizer_info=OrganizerInfo(
            name="Test Org",
            description="A test organizer.", # Added for completeness
            email="org@example.com" # Added for completeness
        ),
        tags=["test", "integration"],
        media=[Media(url="http://example.com/image.jpg", type="image")],
        # Ensure all required fields from openapi.yml schema are included
        # For example, if 'category' or 'status' are required, add them.
        # Assuming 'action_links' and 'related_links' are optional for now.
        category="Test Category", # Added example required field
        status="confirmed" # Added example required field
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URL}/events", json=test_event.model_dump(by_alias=True))

    assert response.status_code == 200  # Or 201 if your API returns that
    response_data = response.json()
    assert response_data["message"] == "Event created successfully"
    assert response_data["event_id"] == event_id

    # Allow time for indexing
    time.sleep(2)

    es_client = AsyncElasticsearch([ES_URL])
    try:
        es_response = await es_client.get(index=INDEX_NAME, id=event_id)
        assert es_response["found"] is True
        assert es_response["_id"] == event_id
        assert es_response["_source"]["title"] == test_event.title
        assert es_response["_source"]["id"] == event_id
        assert es_response["_source"]["location"]["name"] == test_event.location.name
        assert es_response["_source"]["vector_embedding"] is not None # Check embedding exists
        # Add more assertions for other fields as needed
        assert es_response["_source"]["category"] == test_event.category
        assert es_response["_source"]["organizerInfo"]["name"] == test_event.organizer_info.name

    finally:
        await es_client.close()
@pytest.mark.asyncio
async def test_create_event_invalid_data():
    invalid_event_dict = {
        # Missing 'title', 'description', etc.
        "id": str(uuid.uuid4()),
        "start_time": "not-a-date"
    }
    event_json_str = json.dumps(invalid_event_dict)

    # Prepare multipart data
    files = {'event': (None, event_json_str, 'application/json')}

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{SERVICE_URL}/events", files=files)

    # FastAPI typically returns 422 for Pydantic validation errors
    assert response.status_code == 422
    response_data = response.json()
    assert "detail" in response_data # Check for FastAPI's error detail structure
    # Optionally, assert specific details about the validation error
    # print(response_data) # For debugging the exact error structure