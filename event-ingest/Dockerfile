# Stage 1: Model Converter
FROM python:3.13 AS converter

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r converter_requirements.txt

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
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ONNX model and tokenizer from the converter stage
COPY --from=converter /app/gte-multilingual-base-onnx /app/gte-multilingual-base-onnx

# Add the openapi schema to the container - but note that this is only there as a backup in case github is unavailable.
ADD https://raw.githubusercontent.com/simonfelding/flyers.lol/refs/heads/main/openapi.yml /app/openapi.yml

# Copy the application code (main.py)
COPY main.py .
# If there are other necessary files for main.py (like pydantic models in a separate file), copy them too.

# Expose port and set command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]