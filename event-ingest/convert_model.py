import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
import os

print("Starting model conversion to ONNX format...")

# Define model name and output path
MODEL_NAME = "Alibaba-NLP/gte-multilingual-base"
OUTPUT_MODEL_PATH = "gte-multilingual-base-onnx"

# Create output directories if they don't exist
os.makedirs(OUTPUT_MODEL_PATH, exist_ok=True)
tokenizer_output_path = os.path.join(OUTPUT_MODEL_PATH, "tokenizer")
os.makedirs(tokenizer_output_path, exist_ok=True)

print(f"Loading original model '{MODEL_NAME}' from Hugging Face...")
# As per your script, using AutoModelForTokenClassification.
# trust_remote_code=True is important for GTE models.
model_original = AutoModelForTokenClassification.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer_original = AutoTokenizer.from_pretrained(MODEL_NAME)
print("Original model and tokenizer loaded.")

# Create dummy input for ONNX export
dummy_text = "This is a test for ONNX Runtime!"
dummy_model_input = tokenizer_original(dummy_text, return_tensors="pt")
print(f"Created dummy input for text: '{dummy_text}'")

# Export the model to ONNX
onnx_file_path = f"{OUTPUT_MODEL_PATH}/model.onnx"
print(f"Exporting model to ONNX at '{onnx_file_path}'...")
torch.onnx.export(
    model_original,
    tuple(dummy_model_input.values()),
    onnx_file_path,
    input_names=['input_ids', 'attention_mask'],
    output_names=['last_hidden_state'], # As per your script, one output named 'last_hidden_state'
    dynamic_axes={
        'input_ids': {0: 'batch_size', 1: 'sequence'},
        'attention_mask': {0: 'batch_size', 1: 'sequence'},
        'last_hidden_state': {0: 'batch_size', 1: 'sequence'} # This implies shape [batch, seq, features]
    },
    do_constant_folding=True,
    opset_version=14,
)
print("Model successfully exported to ONNX.")

# Save the tokenizer
print(f"Saving tokenizer to '{tokenizer_output_path}'...")
tokenizer_original.save_pretrained(tokenizer_output_path)
print("Tokenizer successfully saved.")
print("Model conversion script finished.")