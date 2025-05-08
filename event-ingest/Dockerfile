# Stage 1: Model Converter
FROM python:3.13 AS converter

WORKDIR /app

COPY convert_model.py converter_requirements.txt ./


RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -r converter_requirements.txt

# Copy the conversion script

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

# Copy the generated Pydantic models
COPY ./generated_models.py /app/generated_models.py

# Copy the application code (main.py)
COPY main.py .
# If there are other necessary files for main.py, copy them too.

# Expose port and set command
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]