import os
import torch
import pytest
from brain_tumor_detection.Backend.api.inference_service import BrainTumorInferenceService

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/brain_tumor_model.pt'))

def test_model_load():
    """Test that the model loads without error and is not None."""
    service = BrainTumorInferenceService(model_path=MODEL_PATH)
    assert service.model is not None

def test_model_inference():
    """Test that the model can perform a dummy inference."""
    service = BrainTumorInferenceService(model_path=MODEL_PATH)
    dummy_input = torch.randn(1, 10)  # Adjust shape as needed for your model
    try:
        output = service.model(dummy_input)
        assert output is not None
    except Exception as e:
        pytest.fail(f"Model inference failed: {e}")
