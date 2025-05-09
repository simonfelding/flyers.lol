from elasticsearch import Elasticsearch, ApiError
from .config import ELASTICSEARCH_URL, ES_REQUEST_TIMEOUT, ES_MAX_RETRIES, ES_RETRY_ON_TIMEOUT, INDEX_NAME, VECTOR_DIMENSIONS
from typing import Dict, Any
from generated_models import Event

es_client: Elasticsearch | None = None

def init_es_client():
    global es_client
    try:
        es_client = Elasticsearch(
            ELASTICSEARCH_URL,
            request_timeout=ES_REQUEST_TIMEOUT,
            max_retries=ES_MAX_RETRIES,
            retry_on_timeout=ES_RETRY_ON_TIMEOUT
        )
        if not es_client.ping():
            raise ConnectionError("Elasticsearch ping failed")
        print("Elasticsearch client connected successfully.")
    except ConnectionError as e:
        print(f"FATAL: Could not connect to Elasticsearch: {e}")
        es_client = None # Allow app to start but endpoints will fail
    except Exception as e:
        print(f"FATAL: An unexpected error occurred during Elasticsearch client initialization: {e}")
        es_client = None

async def ensure_events_index_exists():
    if not es_client or not es_client.ping(): # Check ping again in case connection dropped
        print("Cannot ensure index exists: Elasticsearch client not available or connection lost.")
        # Attempt to re-initialize, could be a transient issue
        init_es_client()
        if not es_client or not es_client.ping():
             print("Re-initialization failed. Elasticsearch client still not available.")
             return False # Still not available after re-init attempt

    try:
        if not es_client.indices.exists(index=INDEX_NAME):
            mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "start_time": {"type": "date"},
                        "end_time": {"type": "date"},
                        "location": {
                            "properties": {
                                "name": {"type": "text"},
                                "address": {"type": "text"},
                                "geo": {"type": "geo_point"}
                            }
                        },
                        "organizer_info": {
                            "properties": {
                                "name": {"type": "keyword"},
                                "contact_email": {"type": "keyword"},
                                "website": {"type": "keyword"}
                            }
                        },
                        "action_link": {
                            "properties": {
                                "url": {"type": "keyword"},
                                "text": {"type": "text"},
                                "type": {"type": "keyword"}
                            }
                        },
                        "signature": {"type": "keyword"},
                        "media": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "value": {"type": "keyword"}
                            }
                        },
                        "related_links": {
                            "type": "nested",
                            "properties": {
                                "url": {"type": "keyword"},
                                "text": {"type": "text"},
                                "type": {"type": "keyword"}
                            }
                        },
                        "vector_embedding": {
                            "type": "dense_vector",
                            "dims": VECTOR_DIMENSIONS
                        }
                    }
                }
            }
            es_client.indices.create(index=INDEX_NAME, body=mapping)
            print(f"Index '{INDEX_NAME}' created with mapping.")
        return True
    except ApiError as e:
        print(f"Error ensuring Elasticsearch index '{INDEX_NAME}' exists: {e}")
        return False
    except Exception as e: # Catch any other unexpected error
        print(f"Unexpected error in ensure_events_index_exists: {e}")
        return False

async def index_event(event_model: Event): # Changed signature to accept Event model
    if not es_client:
        print(f"Cannot index event {event_model.id}: Elasticsearch client not available.")
        return False # Or raise an exception
    try:
        # Use model_dump(mode='json') for the document body
        await es_client.index(
            index=INDEX_NAME,
            id=event_model.id,
            document=event_model.model_dump(mode='json') # Use mode='json'
        )
        print(f"Event {event_model.id} indexed successfully.")
        return True
    except ApiError as e:
        print(f"Error indexing event {event_model.id} to Elasticsearch: {e}")
        # Potentially raise a custom exception here to be handled by the route
        raise  # Re-raise the exception to be caught by the caller
    except Exception as e:
        print(f"Unexpected error indexing event {event_model.id}: {e}")
        raise # Re-raise for visibility

# Call init_es_client when the module is loaded.
# Alternatively, this can be called in a FastAPI startup event.
# For simplicity here, we initialize it at module load.
# If the app structure allows for async startup, that's preferred.
init_es_client()