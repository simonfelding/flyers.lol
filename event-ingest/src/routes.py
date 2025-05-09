from elasticsearch import ApiError
from elasticsearch import ApiError
import json
from fastapi import APIRouter, HTTPException, status, Form, UploadFile, File
from pydantic import ValidationError
from typing import Optional

# Assuming generated_models.py is in a location accessible by Python's import system.
# If generated_models.py is at the root of the /app directory (alongside src/),
# and the working directory is /app, this import should work.
# If PYTHONPATH issues arise, this might need adjustment in the Dockerfile or runtime environment.
from generated_models import Event

from .embedding import get_embedding
from .db import index_event, ensure_events_index_exists, es_client

router = APIRouter()

@router.post("/events", status_code=status.HTTP_201_CREATED, response_model=Event)
async def create_event_endpoint(
    event_json_str: str = Form(..., alias='event', description="JSON string representing the Event object"),
    imageFile: UploadFile | None = File(None, description="Optional event image file")
):
    if es_client is None:
        # This check might be redundant if db.init_es_client() ensures es_client is always initialized
        # or raises an error that prevents the app from starting/handling requests.
        # However, it's a good safeguard.
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Elasticsearch service not available.")

    # 1. Parse and Validate Event Data
    try:
        parsed_dict = json.loads(event_json_str)
        validated_event = Event.model_validate(parsed_dict)
        # Use .model_dump() for preparing data for ES, ensuring aliases and excluding unset/none
        validated_event_dict = validated_event.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON format for event data: {e}")
    except ValidationError as e:
        # Provide detailed validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Event data validation failed: {e.errors()}")

    # 2. Handle Image File (Placeholder - actual processing not implemented here)
    if imageFile:
        print(f"Received image: {imageFile.filename}, type: {imageFile.content_type}, size: {imageFile.size}")
        # TODO: Implement image saving/processing logic.
        # For now, we just log. If you read the file, ensure to await imageFile.close()
        # Example: validated_event_dict['image_filename'] = imageFile.filename
        # await imageFile.close() # Important if you read from it.

    # 3. Generate Embedding
    # Ensure 'title' and 'description' are present or handle their absence gracefully.
    # The Event model should define these fields.
    description_text = validated_event_dict.get("description", "")
    title_text = validated_event_dict.get("title", "")
    text_to_embed = f"{title_text} {description_text}".strip()

    event_id = validated_event_dict.get("id", "UNKNOWN_ID") # Get ID for logging and ES document ID

    embedding = None
    if not text_to_embed:
        print(f"Warning: Empty text for embedding for event ID {event_id}. Skipping embedding generation.")
    else:
        try:
            embedding = get_embedding(text_to_embed) # Call the refactored function
            if embedding is None:
                 print(f"Warning: Embedding generation returned None for event ID {event_id}.")
        except Exception as e: # Catching broad exception from get_embedding if it raises one
            print(f"Error during embedding generation for event ID {event_id}: {e}")
            # Decide if this should be a 500 error or just a warning.
            # For now, we'll let it be indexed without embedding if generation fails.
            embedding = None

    # Add embedding to the document if generated
    if embedding:
        validated_event_dict['vector_embedding'] = embedding
    else:
        # Ensure the field exists with a null value if no embedding,
        # if your ES mapping expects it or for consistency.
        validated_event_dict['vector_embedding'] = None


    # 4. Ensure Index Exists
    try:
        if not await ensure_events_index_exists():
            # This function now handles its own logging for failure.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to ensure Elasticsearch index exists.")
    except Exception as e: # Catch any exception from ensure_events_index_exists itself
        print(f"Critical error during ensure_events_index_exists call: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ensure Elasticsearch index exists: {str(e)}")


    # 5. Index to Elasticsearch
    try:
        await index_event(event_model=validated_event) # Pass the Pydantic model instance
        # Return the Pydantic model instance for response_model serialization
        return validated_event
    except ApiError as e: # Correct exception type
        print(f"Elasticsearch API Error indexing event {validated_event.id}: {e}") # Use validated_event.id
        raise HTTPException(status_code=500, detail="Error storing event data.")
    except Exception as e: # Catch any other unexpected errors during indexing
        print(f"Unexpected error indexing event {event_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while indexing the event: {str(e)}")