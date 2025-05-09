from fastapi import FastAPI

# Import the router from the routes module
from .routes import router as events_router

# Import initialization functions and global variables for status check
from .db import init_es_client, ensure_events_index_exists, es_client
from .embedding import init_onnx_model, onnx_gte_model
from .config import APP_HOST, APP_PORT # For uvicorn command reference, not used directly here

app = FastAPI(title="Event Ingest Service")

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Initialize Elasticsearch client.
    - Initialize ONNX model.
    - Ensure the Elasticsearch index exists.
    """
    print("Application startup: Initializing resources...")
    # Initialize ES Client (idempotent, checks if already initialized)
    # The db module already calls init_es_client() on import,
    # but calling it here ensures it's done in the async context if needed
    # and serves as a clear startup step.
    # If init_es_client were async, we would await it.
    # For now, assuming synchronous init is fine at module load or here.
    if es_client is None: # Explicitly re-try init if it failed at module load
        init_es_client()

    # Initialize ONNX Model (idempotent, checks if already initialized)
    # Similar to ES client, embedding module calls init_onnx_model() on import.
    if onnx_gte_model is None: # Explicitly re-try init if it failed at module load
        init_onnx_model()

    # Ensure Elasticsearch index exists
    # This is an async function and should be awaited.
    index_ready = await ensure_events_index_exists()
    if not index_ready:
        # This is a critical failure. The application might not function correctly.
        # Consider logging a more severe error or even preventing startup
        # if the index is absolutely essential from the very beginning.
        print("FATAL: Elasticsearch index could not be ensured. Service may be impaired.")
    else:
        print("Elasticsearch index check complete.")
    print("Application startup complete.")


# Include the event processing routes
app.include_router(events_router) # Removed prefix to mount at root

@app.get("/")
async def read_root():
    """
    Root endpoint for health check.
    Provides status of critical components like ONNX model and Elasticsearch.
    """
    # Check ONNX model status (using the imported global variable)
    model_status = "ONNX model loaded" if onnx_gte_model else "ONNX model FAILED to load"

    # Check Elasticsearch client status (using the imported global variable)
    # Perform a ping to ensure connectivity if client exists
    es_status = "Elasticsearch client FAILED to connect"
    if es_client:
        try:
            if await es_client.ping():
                es_status = "Elasticsearch client connected"
            else:
                es_status = "Elasticsearch client ping FAILED"
        except Exception:
            es_status = "Elasticsearch client ping EXCEPTION"


    return {
        "message": "Event Ingest Service is running.",
        "status": {
            "onnx_model": model_status,
            "elasticsearch_client": es_status
        }
    }

# The Uvicorn command in Dockerfile will be:
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
# or using config: CMD ["uvicorn", "src.main:app", "--host", APP_HOST, "--port", str(APP_PORT)]