
# brain_tumor_detection/api/

import torch
import numpy as np
from typing import Dict, List, Any, Tuple
import time
import json
import os
import logging

from brain_tumor_detection.Backend.models.unet_segmentation import UNetModel
from brain_tumor_detection.Backend.preprocessing.dicom_processor import MRIPreprocessor

import hashlib

class BrainTumorInferenceService:
    """Service for performing brain tumor detection inference"""

    def __init__(self, model_path: str, device: str = None):
        self._verify_model_integrity(model_path)
        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        # ... rest of your initialization code ...

    def _verify_model_integrity(self, model_path):
        expected_hash = "a1b2c3d4..."
        with open(model_path, 'rb') as f:
            assert hashlib.sha256(f.read()).hexdigest() == expected_hash

        logging.info(f"Initializing inference service on {self.device}")
        
        # Load model
        self.model = UNetModel(num_classes=1)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        
        # Initialize preprocessor
        self.preprocessor = MRIPreprocessor(target_size=(256, 256))
        
        logging.info("Inference service initialized successfully")
    
    def process_scan(self, scan_path: str) -> Dict[str, Any]:
        """
        Process a single MRI scan with optimized batch inference and accurate volume calculation.
        Args:
            scan_path: Path to DICOM directory or NIfTI file
        Returns:
            Dictionary containing segmentation results and metadata
        """
        start_time = time.time()
        logging.info(f"Processing scan: {scan_path}")
        try:
            # Preprocess the scan
            volume = self.preprocessor.preprocess(scan_path)
            # Extract 2D slices for prediction
            slices = self.preprocessor.extract_2d_slices(volume, axis=2)
            # Batch processing
            with torch.no_grad():
                slices_tensor = torch.stack([torch.from_numpy(s).float() for s in slices]).to(self.device)
                if slices_tensor.ndim == 3:
                    slices_tensor = slices_tensor.unsqueeze(1)
                preds = self.model(slices_tensor)
                probs = torch.sigmoid(preds).cpu().numpy()
                masks = (probs > 0.5).astype(np.uint8)
            if masks.ndim == 4 and masks.shape[1] == 1:
                masks = masks[:, 0]
                probs = probs[:, 0]
            segmentation_masks = list(masks)
            tumor_probabilities = list(probs)
            # Reconstruct 3D volume from slices
            segmentation_volume = np.stack(segmentation_masks, axis=0)
            probability_volume = np.stack(tumor_probabilities, axis=0)
            # Accurate tumor statistics using voxel size
            tumor_size_voxels = np.sum(segmentation_volume)
            voxel_volume = np.prod(self.preprocessor.metadata['spacing'])
            tumor_volume_ml = tumor_size_voxels * voxel_volume / 1000  # mm³ to ml
            # Find tumor coordinates (center of mass)
            if tumor_size_voxels > 0:
                tumor_indices = np.where(segmentation_volume > 0)
                tumor_center = [
                    np.mean(tumor_indices[0]),
                    np.mean(tumor_indices[1]),
                    np.mean(tumor_indices[2])
                ]
            else:
                tumor_center = [0, 0, 0]
            # Calculate max probability
            max_probability = np.max(probability_volume)
            # Prepare results
            results = {
                "prediction": {
                    "tumor_detected": tumor_size_voxels > 100,  # Threshold to avoid noise
                    "confidence": float(max_probability),
                    "tumor_size_ml": float(tumor_volume_ml),
                    "tumor_center": tumor_center,
                },
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "model_version": "unet_resnet50_v1.0",
                    "preprocessing_steps": ["skull_stripping", "normalization", "resizing"]
                }
            }
            logging.info(f"Scan processed successfully in {results['metadata']['processing_time']:.2f} seconds")
            return results
        except Exception as e:
            logging.error(f"Error processing scan: {str(e)}")
            return {
                "error": str(e),
                "metadata": {
                    "processing_time": time.time() - start_time
                }
            }

    
    def generate_heatmap(self, probability_map: np.ndarray) -> np.ndarray:
        """
        Generate a colored heatmap from probability map
        
        Args:
            probability_map: 2D probability map from model
            
        Returns:
            RGB heatmap image
        """
        # Create a colormap (red for higher probabilities)
        heatmap = np.zeros((probability_map.shape[0], probability_map.shape[1], 3))
        
        # Red channel - higher intensity for higher probabilities
        heatmap[:, :, 0] = probability_map
        
        # Alpha blending factor based on probability
        alpha = probability_map * 0.7
        
        return heatmap, alpha
    
    def overlay_segmentation(self, original_slice: np.ndarray, 
                            segmentation_mask: np.ndarray) -> np.ndarray:
        """
        Overlay segmentation mask on original image
        
        Args:
            original_slice: Original MRI slice
            segmentation_mask: Binary segmentation mask
            
        Returns:
            Slice with overlay
        """
        # Convert original to RGB if grayscale
        if len(original_slice.shape) == 2:
            rgb_slice = np.stack([original_slice] * 3, axis=2)
        else:
            rgb_slice = original_slice.copy()
        
        # Create mask for overlay
        mask = segmentation_mask > 0
        
        # Create colored overlay (red for tumor)
        rgb_slice[mask, 0] = 1.0  # Red channel
        rgb_slice[mask, 1] *= 0.3  # Reduce green
        rgb_slice[mask, 2] *= 0.3  # Reduce blue
        
        return rgb_slice

    def calculate_metrics(self, segmentation_volume, probability_volume, ground_truth):
        """
        Compute critical performance metrics for segmentation results.
        Args:
            segmentation_volume: Predicted segmentation (3D numpy array)
            probability_volume: Model probability output (3D numpy array)
            ground_truth: Ground truth segmentation (3D numpy array)
        Returns:
            Dictionary with Dice, Hausdorff, and Surface Dice metrics
        """
        return {
            "dice_score": self.dice_coeff(segmentation_volume, ground_truth),
            "hausdorff_distance": self.hd_distance(segmentation_volume, ground_truth),
            "surface_dice": self.surface_dice(segmentation_volume, ground_truth)
        }

    # Security & Compliance: Model integrity verification
    def _verify_model_integrity(self, model_path):
        import hashlib
        expected_hash = "a1b2c3d4..."  # Replace with real hash
        with open(model_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()
            assert actual_hash == expected_hash, f"Model file integrity check failed! Expected {expected_hash}, got {actual_hash}"