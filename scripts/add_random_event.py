import httpx
import json
import uuid
import random
import string
import time
from datetime import datetime, timedelta

# URL of the running event-ingest service (development)
SERVICE_URL = "http://localhost:8080/events"
EVENT_SCHEMA_VERSION = "1.0.0" # From openapi.yml

def generate_random_string(length=10):
    """Generates a random string of fixed length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_event():
    """Generates a dictionary representing a valid random event."""
    now = datetime.utcnow()
    # Ensure start_time is in the future
    start_time_dt = now + timedelta(days=random.randint(1, 30), hours=random.randint(0,23), minutes=random.randint(0,59))
    event_id = f"evt_{uuid.uuid4()}"

    event = {
        "version": EVENT_SCHEMA_VERSION,
        "id": event_id,
        "title": f"Random Event {generate_random_string(5)}",
        "description": f"This is a randomly generated event: {generate_random_string(20)}.",
        "start_time": start_time_dt.isoformat() + "Z",
        # Optional: end_time
        "end_time": (start_time_dt + timedelta(hours=random.randint(1,5))).isoformat() + "Z",
        "location": {
            "name": f"Random Location {random.randint(1,100)}",
            # Optional: address
            "address": f"{random.randint(1,1000)} Random St, City {generate_random_string(3)}",
            "geo": { # Geo is optional in Location, but if present, lat/lon are required
                "lat": random.uniform(-90, 90),
                "lon": random.uniform(-180, 180)
            }
        },
        "organizer_info": {
            "name": f"Random Org {generate_random_string(3)}",
            # Optional: contact_email, website
            "contact_email": f"{generate_random_string(5)}@example.com",
            "website": f"http://{generate_random_string(8)}.example.com"
        },
        # Optional: action_link
        "action_link": {
            "url": f"http://example.com/action/{generate_random_string(6)}",
            "text": f"Click Here {generate_random_string(4)}",
            "type": random.choice(["purchase", "rsvp", "register", "info", None]) # type is optional
        },
        "signature": f"0x{generate_random_string(64)}", # Placeholder for actual signature
        # Optional: related_links
        "related_links": [
            {
                "url": f"http://example.com/related/{generate_random_string(6)}",
                "text": f"More Info {generate_random_string(4)}",
                "type": random.choice(["website", "social", "video", None]) # type is optional
            }
            for _ in range(random.randint(0, 2)) # 0 to 2 related links
        ],
        # vector_embedding is optional at creation
    }
    # Remove None type from action_link.type if it was chosen
    if event["action_link"] and event["action_link"]["type"] is None:
        del event["action_link"]["type"]

    # Remove None type from related_links.type if chosen
    for link in event["related_links"]:
        if link["type"] is None:
            del link["type"]

    return event

if __name__ == "__main__":
    print(f"Attempting to add a random event to {SERVICE_URL}...")
    random_event_data = generate_random_event()

    print("\nGenerated Event Data:")
    print(json.dumps(random_event_data, indent=2))

    event_json_str = json.dumps(random_event_data)

    # The 'event' part of the multipart form should be a tuple: (filename, content, content_type)
    # For a JSON string, filename can be None.
    files = {'event': (None, event_json_str, 'application/json')}

    print("Waiting 5 seconds for services to initialize...")
    time.sleep(5) # Add delay here

    try:
        # Using a context manager for the client is good practice
        with httpx.Client() as client:
            response = client.post(SERVICE_URL, files=files)

        print(f"\n--- Response ---")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text:")
            print(response.text)

    except httpx.RequestError as exc:
        print(f"\nAn error occurred while requesting {exc.request.url!r}: {exc}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")