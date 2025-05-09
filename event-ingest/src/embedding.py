import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from typing import List, Optional

from .config import ONNX_MODEL_DIRECTORY, MAX_SEQ_LENGTH

# Global variable to hold the loaded ONNX model instance
onnx_gte_model = None

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

def init_onnx_model():
    global onnx_gte_model
    try:
        if not os.path.exists(ONNX_MODEL_DIRECTORY):
             print(f"FATAL: ONNX model directory {ONNX_MODEL_DIRECTORY} not found.")
             onnx_gte_model = None
             return
        onnx_gte_model = GTEOnnxModel(model_dir=ONNX_MODEL_DIRECTORY, max_seq_length=MAX_SEQ_LENGTH)
        print(f"ONNX GTE model loaded successfully from {ONNX_MODEL_DIRECTORY}")
    except FileNotFoundError as fnf_error:
        print(f"FATAL: Could not load ONNX GTE model due to missing file: {fnf_error}")
        onnx_gte_model = None
    except Exception as e:
        print(f"FATAL: Could not load ONNX GTE model: {e}")
        onnx_gte_model = None

def get_embedding(text_input: str) -> Optional[List[float]]:
    if onnx_gte_model is None:
        print("Error: ONNX model is not available for embedding.")
        # Optionally, try to initialize it again if it's None
        # init_onnx_model()
        # if onnx_gte_model is None: # Check again after trying to init
        #     return None
        return None # Return None if model is still not available
    if not text_input:
        print("Error: text_input for embedding cannot be empty.")
        return None
    try:
        embedding_np = onnx_gte_model.encode(text_input)
        return embedding_np.tolist()
    except Exception as e:
        print(f"Error during embedding generation: {e}")
        # Depending on desired behavior, you might re-raise or return None
        # For now, returning None to indicate failure.
        return None

# Initialize the model when this module is loaded.
# This can also be done in a FastAPI startup event for more control.
init_onnx_model()