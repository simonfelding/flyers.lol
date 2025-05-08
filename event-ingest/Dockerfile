# Stage 1: Model Converter
FROM python:3.13 AS converter

WORKDIR /app

# Install dependencies for model conversion
# We need transformers, torch (for export), and onnx (though torch.onnx handles it)
# sentencepiece is often a dependency for tokenizers
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    pip install transformers torch onnx sentencepiece

# Copy the conversion script
COPY convert_model.py .

# Run the conversion script
# This will download the original model and save the ONNX version and tokenizer
RUN python convert_model.py

# Stage 2: Application Runner
FROM python:3.13-slim AS runner

WORKDIR /app

# Install dependencies for the FastAPI app with ONNX runtime
# onnxruntime for running the model, tokenizers for loading the HF tokenizer
# Install build tools needed for some pip packages (e.g., onnxruntime, tokenizers might have C/C++ extensions)

COPY requirements.txt .
# requirements.txt now includes elasticsearch and jsonschema
# onnxruntime and tokenizers are also essential for the app
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir onnxruntime tokenizers

# Copy the ONNX model and tokenizer from the converter stage
COPY --from=converter /app/gte-multilingual-base-onnx /app/gte-multilingual-base-onnx

# Copy the event schema from the host into the image
# Ensure this path matches EVENT_SCHEMA_PATH in main.py
COPY ./event_schema.json /app/event_schema.json

# Copy the application code (main.py)
COPY main.py .
# If there are other necessary files for main.py (like pydantic models in a separate file), copy them too.

# Expose port and set command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]