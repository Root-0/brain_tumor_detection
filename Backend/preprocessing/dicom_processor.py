import os
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from scipy import ndimage
import pydicom
from typing import List, Tuple, Dict, Any

class MRIPreprocessor:
    """Handles preprocessing of MRI scans from DICOM/NIfTI formats"""
    
    def __init__(self, target_size=(256, 256), normalize=True, skull_strip=True):
        """
        Initialize the preprocessor
        
        Args:
            target_size: Tuple defining the target dimensions for slices
            normalize: Whether to apply intensity normalization
            skull_strip: Whether to apply skull stripping
        """
        self.target_size = target_size
        self.normalize = normalize
        self.skull_strip = skull_strip
    
    def load_dicom_series(self, dicom_dir: str) -> np.ndarray:
        """
        Load a DICOM series from a directory
        
        Args:
            dicom_dir: Directory containing DICOM files
            
        Returns:
            3D numpy array of the scan
        """
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(dicom_dir)
        reader.SetFileNames(dicom_names)
        image = reader.Execute()
        
        # Convert to numpy array
        array = sitk.GetArrayFromImage(image)
        
        # Get metadata for later use
        self.metadata = {
            'spacing': image.GetSpacing(),
            'origin': image.GetOrigin(),
            'direction': image.GetDirection()
        }
        
        return array
    
    def load_nifti(self, nifti_path: str) -> np.ndarray:
        """
        Load a NIfTI file
        
        Args:
            nifti_path: Path to NIfTI file
            
        Returns:
            3D numpy array of the scan
        """
        nifti_img = nib.load(nifti_path)
        array = nifti_img.get_fdata()
        
        # Store metadata
        self.metadata = {
            'affine': nifti_img.affine,
            'header': nifti_img.header
        }
        
        return array
    
    def apply_skull_stripping(self, volume: np.ndarray) -> np.ndarray:
        """
        Apply a basic skull stripping algorithm
        
        Note: In production, use dedicated libraries like HD-BET
        This is a simplified placeholder function
        
        Args:
            volume: 3D MRI volume
            
        Returns:
            Skull-stripped volume
        """
        # This is a simplified placeholder - in a real system, use HD-BET or other specialized tools
        # Example of a basic thresholding approach (not clinically accurate):
        threshold = np.percentile(volume, 99) * 0.5
        binary_mask = volume > threshold
        
        # Apply morphological operations to clean up the mask
        binary_mask = ndimage.binary_erosion(binary_mask, iterations=2)
        binary_mask = ndimage.binary_dilation(binary_mask, iterations=5)
        binary_mask = ndimage.binary_fill_holes(binary_mask)
        
        # Apply the mask to the original volume
        stripped_volume = volume * binary_mask
        
        return stripped_volume
    
    def normalize_intensity(self, volume: np.ndarray) -> np.ndarray:
        """
        Apply intensity normalization to the volume
        
        Args:
            volume: 3D MRI volume
            
        Returns:
            Normalized volume
        """
        # Z-score normalization (mean=0, std=1)
        # Only consider non-zero voxels
        mask = volume > 0
        if np.sum(mask) > 0:
            mean = np.mean(volume[mask])
            std = np.std(volume[mask])
            if std > 0:
                volume[mask] = (volume[mask] - mean) / std
        
        # Clip outliers
        volume = np.clip(volume, -5, 5)
        
        # Rescale to [0, 1]
        volume = (volume - volume.min()) / (volume.max() - volume.min() + 1e-8)
        
        return volume
    
    def resize_volume(self, volume: np.ndarray) -> tuple:
        """
        Resize the volume to target dimensions and update voxel size (spacing)
        
        Args:
            volume: 3D MRI volume
        Returns:
            Tuple of (resized volume, new_spacing)
        """
        # Get original spacing from metadata
        original_spacing = self.metadata['spacing'] if hasattr(self, 'metadata') and 'spacing' in self.metadata else (1.0, 1.0, 1.0)
        depth, height, width = volume.shape
        # Determine resize factors
        height_factor = self.target_size[0] / height
        width_factor = self.target_size[1] / width
        # Resize using scipy's zoom
        resized_volume = ndimage.zoom(volume, (1, height_factor, width_factor), order=1)
        # Calculate new spacing
        new_spacing = (
            original_spacing[0] * (height / self.target_size[0]),
            original_spacing[1] * (width / self.target_size[1]),
            original_spacing[2]
        )
        if hasattr(self, 'metadata'):
            self.metadata['spacing'] = new_spacing
        else:
            self.metadata = {'spacing': new_spacing}
        return resized_volume, new_spacing

    def apply_skull_stripping(self, volume: np.ndarray) -> np.ndarray:
        """
        Apply advanced skull stripping using HD-BET if available
        Args:
            volume: 3D MRI volume
        Returns:
            Skull-stripped volume
        """
        try:
            import hd_bet
            stripped_volume = hd_bet.run_hd_bet(volume)
            return stripped_volume
        except ImportError:
            # Fallback to basic skull stripping if hd_bet is not installed
            threshold = np.percentile(volume, 99) * 0.5
            binary_mask = volume > threshold
            binary_mask = ndimage.binary_erosion(binary_mask, iterations=2)
            binary_mask = ndimage.binary_dilation(binary_mask, iterations=5)
            binary_mask = ndimage.binary_fill_holes(binary_mask)
            stripped_volume = volume * binary_mask
            return stripped_volume

    
    def preprocess(self, input_path: str) -> np.ndarray:
        """
        Main preprocessing function
        
        Args:
            input_path: Path to DICOM directory or NIfTI file
            
        Returns:
            Preprocessed volume ready for model input
        """
        # Load data
        if os.path.isdir(input_path):
            volume = self.load_dicom_series(input_path)
        else:
            volume = self.load_nifti(input_path)
        
        # Apply skull stripping if enabled
        if self.skull_strip:
            volume = self.apply_skull_stripping(volume)
        
        # Resize volume
        volume = self.resize_volume(volume)
        
        # Apply intensity normalization if enabled
        if self.normalize:
            volume = self.normalize_intensity(volume)
        
        return volume
    
    def extract_2d_slices(self, volume: np.ndarray, axis=0, return_spacing=False) -> List[np.ndarray]:
        """
        Extract 2D slices from 3D volume along specified axis, optionally returning voxel spacing per slice
        Args:
            volume: 3D MRI volume
            axis: Axis along which to extract slices (0=sagittal, 1=coronal, 2=axial)
            return_spacing: If True, return (slice, spacing) tuples
        Returns:
            List of 2D slices, or list of (slice, spacing) tuples if return_spacing=True
        """
        slices = []
        spacing = self.metadata['spacing'] if hasattr(self, 'metadata') and 'spacing' in self.metadata else (1.0, 1.0, 1.0)
        # Determine spacing for each axis
        if axis == 0:
            slice_spacing = (spacing[1], spacing[2])
        elif axis == 1:
            slice_spacing = (spacing[0], spacing[2])
        else:
            slice_spacing = (spacing[0], spacing[1])
        # Extract slices along the specified axis
        for i in range(volume.shape[axis]):
            if axis == 0:
                slice_2d = volume[i, :, :]
            elif axis == 1:
                slice_2d = volume[:, i, :]
            else:  # axis == 2
                slice_2d = volume[:, :, i]
            # Ensure slice has the target dimensions
            if slice_2d.shape != self.target_size:
                slice_2d = ndimage.zoom(slice_2d, 
                                       (self.target_size[0]/slice_2d.shape[0], 
                                        self.target_size[1]/slice_2d.shape[1]), 
                                       order=1)
            # Add channel dimension for model input
            slice_2d = np.expand_dims(slice_2d, axis=0)
            if return_spacing:
                slices.append((slice_2d, slice_spacing))
            else:
                slices.append(slice_2d)
        return slices

