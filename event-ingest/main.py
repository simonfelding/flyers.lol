from fastapi import FastAPI, HTTPException, status, Request
# Pydantic BaseModel, Field, HttpUrl will come from generated_models or be standard types
import onnxruntime as ort
import numpy as np
from tokenizers import Tokenizer # From the 'tokenizers' library by Hugging Face
import os
from typing import List, Dict, Any, Optional, Union
import json
# Removed yaml, jsonschema, validate, jsonschema_exceptions
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from generated_models import Event # Assuming this will be the generated model name

app = FastAPI()

# --- Elasticsearch Client ---
try:
    es_client = Elasticsearch(
        "http://elasticsearch:9200",
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )
    if not es_client.ping():
        raise ConnectionError("Elasticsearch ping failed")
    print("Elasticsearch client connected successfully.")
except ConnectionError as e:
    print(f"FATAL: Could not connect to Elasticsearch: {e}")
    es_client = None # Allow app to start but endpoints will fail

# Define the ONNX Model Class
class GTEOnnxModel:
    def __init__(self, model_dir: str, max_seq_length: int = 512):
        """
        ONNX model for GTE.
        Assumes model_dir contains 'model.onnx' and 'tokenizer/tokenizer.json'.
        """
        opt = ort.SessionOptions()
        opt.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        opt.log_severity_level = 3  # Suppress info/warning messages unless error
        opt.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        onnx_model_path = os.path.join(model_dir, "model.onnx")
        tokenizer_path = os.path.join(model_dir, "tokenizer/tokenizer.json")

        if not os.path.exists(onnx_model_path):
            raise FileNotFoundError(f"ONNX model not found at {onnx_model_path}")
        if not os.path.exists(tokenizer_path):
            raise FileNotFoundError(f"Tokenizer file not found at {tokenizer_path}")

        self.sess = ort.InferenceSession(onnx_model_path, opt, providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(tokenizer_path)

        # Configure tokenizer for padding and truncation
        self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id("[PAD]") or 0, length=max_seq_length)
        self.tokenizer.enable_truncation(max_length=max_seq_length)
        self.max_seq_length = max_seq_length

    def encode(self, text: str) -> np.ndarray:
        """
        Encodes a single text string into a normalized sentence embedding.
        """
        # Tokenize the input text
        encoded_inputs = self.tokenizer.encode(text) # add_special_tokens=True is default

        # Prepare model input for ONNX Runtime
        # Input names must match those used during ONNX export: 'input_ids', 'attention_mask'
        model_input = {
            'input_ids': np.atleast_2d(encoded_inputs.ids).astype(np.int64),
            'attention_mask': np.atleast_2d(encoded_inputs.attention_mask).astype(np.int64)
        }

        # Run inference
        # The ONNX model was exported with one output named 'last_hidden_state'
        outputs = self.sess.run(None, model_input)
        last_hidden_state = outputs[0]  # Shape: (batch_size, sequence_length, hidden_size)

        # Get the CLS token embedding (first token of the first sequence)
        # GTE models use the embedding of the [CLS] token (at index 0)
        # Ensure batch dimension is handled, even if it's 1
        cls_embedding = last_hidden_state[0, 0, :]

        # Normalize the CLS embedding to get the final sentence embedding
        norm = np.linalg.norm(cls_embedding)
        if norm == 0: # Avoid division by zero
            return cls_embedding
        normalized_embedding = cls_embedding / norm

        return normalized_embedding

# --- FastAPI Application ---
ONNX_MODEL_DIRECTORY = "/app/gte-multilingual-base-onnx" # Path inside the Docker container's runner stage
try:
    onnx_gte_model = GTEOnnxModel(model_dir=ONNX_MODEL_DIRECTORY)
    print(f"ONNX GTE model loaded successfully from {ONNX_MODEL_DIRECTORY}")
except Exception as e:
    print(f"FATAL: Could not load ONNX GTE model: {e}")
    # In a real scenario, you might want the app to not start or enter a degraded state.
    # For now, if it fails, endpoints will raise errors.
    onnx_gte_model = None


# --- Internal Embedding Function ---
def _generate_embedding(text_input: str) -> Optional[List[float]]:
    if onnx_gte_model is None:
        print("Error: ONNX model is not available for embedding.")
        return None
    if not text_input:
        print("Error: text_input for embedding cannot be empty.")
        return None
    try:
        embedding_np = onnx_gte_model.encode(text_input)
        return embedding_np.tolist()
    except Exception as e:
        print(f"Error during internal embedding generation: {e}")
        return None

# Pydantic models are now imported from generated_models.py
# The Event model (and its sub-models like Geo, Location, etc.) are expected to be in generated_models.EventPayload


# --- Elasticsearch Index Management ---
INDEX_NAME = "events"
# Dimensions for the GTE multilingual base model. Verify if different.
VECTOR_DIMENSIONS = 768

async def ensure_events_index_exists():
    if not es_client or not es_client.ping():
        print("Cannot ensure index exists: Elasticsearch client not available.")
        return False
    try:
        if not await es_client.indices.exists(index=INDEX_NAME):
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
                                "value": {"type": "keyword"} # Assuming URL/CID, not for full text search
                            }
                        },
                        "related_links": { # Storing as nested to allow querying on specific link properties
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
            await es_client.indices.create(index=INDEX_NAME, body=mapping)
            print(f"Index '{INDEX_NAME}' created with mapping.")
        return True
    except es_exceptions.ElasticsearchException as e:
        print(f"Error ensuring Elasticsearch index '{INDEX_NAME}' exists: {e}")
        return False

# --- API Endpoints ---

@app.post("/events", status_code=status.HTTP_201_CREATED, response_model=Event) # Use generated model for response
async def ingest_event(event_data: Event): # Use generated model for request body
    if es_client is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Elasticsearch service not available.")

    # Schema validation is now handled by FastAPI using the Pydantic model EventPayload

    # 1. Pydantic model (event_data) is already validated and parsed by FastAPI.

    # 2. Generate Embedding
    # Ensure event_data has title and description attributes as expected by generated_models.EventPayload
    description_text = event_data.description if event_data.description else ""
    # Make sure title is not None. If it can be, handle appropriately.
    title_text = event_data.title if event_data.title else ""
    text_to_embed = f"{title_text} {description_text}".strip()


    if not text_to_embed:
        embedding = None
        print(f"Warning: Empty text for embedding for event ID {event_data.id}. Skipping embedding generation.")
    else:
        embedding = _generate_embedding(text_to_embed)

    if embedding is None and text_to_embed:
        print(f"Warning: Failed to generate event embedding for event ID {event_data.id}. Event will be indexed without embedding.")
        # Assuming EventPayload has a vector_embedding field that can be None
        event_data.vector_embedding = None
    elif embedding:
        # Assuming EventPayload has a vector_embedding field
        event_data.vector_embedding = embedding

    # 3. Ensure Index Exists
    if not await ensure_events_index_exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to ensure Elasticsearch index exists.")

    # 4. Index to Elasticsearch
    # Use model_dump(by_alias=True) as requested
    event_data_for_es = event_data.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)

    try:
        await es_client.index(index=INDEX_NAME, id=event_data.id, document=event_data_for_es)
        return event_data
    except es_exceptions.ElasticsearchException as e:
        print(f"Error indexing event {event_data.id} to Elasticsearch: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to index event in Elasticsearch: {str(e)}")

@app.get("/")
def read_root():
    model_status = "ONNX model loaded" if onnx_gte_model else "ONNX model FAILED to load"
    es_status = "Elasticsearch client connected" if es_client and es_client.ping() else "Elasticsearch client FAILED to connect"
    # openapi_schema_status no longer relevant here as schema is handled by Pydantic models
    return {"message": f"NLP service is running. Model: {model_status}. Elasticsearch: {es_status}."}