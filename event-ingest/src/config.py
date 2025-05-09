import os

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ONNX_MODEL_DIRECTORY = os.getenv("ONNX_MODEL_DIRECTORY", "/app/gte-multilingual-base-onnx")
# Dimensions for the GTE multilingual base model.
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "768"))
INDEX_NAME = os.getenv("INDEX_NAME", "events")

# FastAPI app settings
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# ONNX Model settings
MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "512"))

# Elasticsearch client settings
ES_REQUEST_TIMEOUT = int(os.getenv("ES_REQUEST_TIMEOUT", "30"))
ES_MAX_RETRIES = int(os.getenv("ES_MAX_RETRIES", "3"))
ES_RETRY_ON_TIMEOUT = os.getenv("ES_RETRY_ON_TIMEOUT", "True").lower() == "true"