"""
Image Validation Module for PneumoScan AI
Detects and rejects non-medical images
"""

import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageValidator:
    """Advanced image validation for chest X-ray detection"""
    
    def __init__(self):
        self.validation_rules = {
            'grayscale': {'weight': 1.5, 'threshold': 0.7},
            'aspect_ratio': {'weight': 1.0, 'threshold': 0.6},
            'size': {'weight': 0.8, 'threshold': 0.5},
            'contrast': {'weight': 1.2, 'threshold': 0.6},
            'edge_density': {'weight': 1.3, 'threshold': 0.6},
            'saturation': {'weight': 1.4, 'threshold': 0.7},
            'texture': {'weight': 1.0, 'threshold': 0.5}
        }
    
    def quick_validate(self, img: Image.Image) -> Tuple[bool, str]:
        """
        Quick pre-validation before deep processing
        Returns: (is_valid, message)
        """
        try:
            # Check if image is color
            if img.mode in ['RGB', 'RGBA', 'CMYK']:
                img_array = np.array(img.convert('RGB'))
                if not np.all(img_array[:, :, 0] == img_array[:, :, 1]) or \
                   not np.all(img_array[:, :, 1] == img_array[:, :, 2]):
                    return False, "Color images are not valid chest X-rays. Please upload grayscale X-ray images."
            
            # Check dimensions
            width, height = img.size
            if width < 100 or height < 100:
                return False, f"Image too small ({width}x{height}). Minimum size is 100x100 pixels."
            
            if width > 5000 or height > 5000:
                return False, f"Image too large ({width}x{height}). Maximum size is 5000x5000 pixels."
            
            # Check aspect ratio
            aspect_ratio = width / height if height > 0 else 0
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                return False, f"Unusual aspect ratio: {aspect_ratio:.2f}. Chest X-rays typically have aspect ratio between 0.7-1.3."
            
            return True, "Quick validation passed"
            
        except Exception as e:
            logger.error(f"Quick validation error: {e}")
            return False, f"Error validating image: {str(e)}"
    
    def is_chest_xray(self, image_array) -> Tuple[bool, float, str, List[str]]:
        """
        Advanced validation to check if uploaded image is a chest X-ray
        
        Returns:
            is_valid: Boolean indicating if image is valid
            confidence: Confidence score (0-100)
            message: Summary message
            details: List of detailed validation results
        """
        try:
            # Convert to numpy array if needed
            if isinstance(image_array, Image.Image):
                img = image_array
                img_array = np.array(img)
            else:
                img_array = image_array
            
            # Initialize scores
            validation_scores = []
            validation_details = []
            weights_sum = 0
            
            # 1. GRAYSCALE CHECK
            weight = self.validation_rules['grayscale']['weight']
            
            if len(img_array.shape) == 2:
                validation_scores.append(1.0 * weight)
                validation_details.append(f"✓ Grayscale image")
            elif len(img_array.shape) == 3:
                if img_array.shape[2] == 1:
                    validation_scores.append(1.0 * weight)
                    validation_details.append(f"✓ Grayscale image")
                else:
                    if np.all(img_array[:, :, 0] == img_array[:, :, 1]) and \
                       np.all(img_array[:, :, 1] == img_array[:, :, 2]):
                        validation_scores.append(0.9 * weight)
                        validation_details.append(f"✓ RGB but grayscale content")
                    else:
                        validation_scores.append(0.0 * weight)
                        validation_details.append(f"✗ Color image detected")
            weights_sum += weight
            
            # 2. ASPECT RATIO CHECK
            weight = self.validation_rules['aspect_ratio']['weight']
            h, w = img_array.shape[:2]
            aspect_ratio = w / h if h > 0 else 0
            
            if 0.7 <= aspect_ratio <= 1.3:
                validation_scores.append(1.0 * weight)
                validation_details.append(f"✓ Good aspect ratio: {aspect_ratio:.2f}")
            elif 0.5 <= aspect_ratio <= 1.5:
                validation_scores.append(0.6 * weight)
                validation_details.append(f"⚠ Acceptable aspect ratio: {aspect_ratio:.2f}")
            else:
                validation_scores.append(0.2 * weight)
                validation_details.append(f"✗ Unusual aspect ratio: {aspect_ratio:.2f}")
            weights_sum += weight
            
            # 3. IMAGE SIZE CHECK
            weight = self.validation_rules['size']['weight']
            max_dim = max(h, w)
            min_dim = min(h, w)
            
            if max_dim >= 500 and min_dim >= 400:
                validation_scores.append(1.0 * weight)
                validation_details.append(f"✓ Good image size: {max_dim}px")
            elif max_dim >= 300 and min_dim >= 200:
                validation_scores.append(0.7 * weight)
                validation_details.append(f"⚠ Acceptable image size: {max_dim}px")
            else:
                validation_scores.append(0.3 * weight)
                validation_details.append(f"✗ Small image size: {max_dim}px")
            weights_sum += weight
            
            # 4. CONTRAST/HISTOGRAM ANALYSIS
            weight = self.validation_rules['contrast']['weight']
            
            if len(img_array.shape) == 3:
                gray_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray_img = img_array
            
            hist = cv2.calcHist([gray_img], [0], None, [256], [0, 256])
            hist_normalized = hist / hist.sum()
            non_zero_bins = np.sum(hist_normalized > 0.005)
            
            if non_zero_bins > 100:
                validation_scores.append(1.0 * weight)
                validation_details.append(f"✓ Excellent contrast: {non_zero_bins} levels")
            elif non_zero_bins > 50:
                validation_scores.append(0.8 * weight)
                validation_details.append(f"✓ Good contrast: {non_zero_bins} levels")
            elif non_zero_bins > 20:
                validation_scores.append(0.5 * weight)
                validation_details.append(f"⚠ Moderate contrast: {non_zero_bins} levels")
            else:
                validation_scores.append(0.1 * weight)
                validation_details.append(f"✗ Poor contrast: only {non_zero_bins} levels")
            weights_sum += weight
            
            # 5. EDGE DETECTION
            weight = self.validation_rules['edge_density']['weight']
            
            edges = cv2.Canny(gray_img, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            
            if 0.04 <= edge_density <= 0.12:
                validation_scores.append(1.0 * weight)
                validation_details.append(f"✓ Normal edge density: {edge_density:.4f}")
            elif 0.02 <= edge_density <= 0.18:
                validation_scores.append(0.7 * weight)
                validation_details.append(f"⚠ Acceptable edge density: {edge_density:.4f}")
            elif edge_density > 0.25:
                validation_scores.append(0.2 * weight)
                validation_details.append(f"✗ Too many edges - likely natural image")
            elif edge_density < 0.01:
                validation_scores.append(0.2 * weight)
                validation_details.append(f"✗ Too few edges - blank/solid image")
            else:
                validation_scores.append(0.4 * weight)
                validation_details.append(f"⚠ Unusual edge density: {edge_density:.4f}")
            weights_sum += weight
            
            # 6. COLOR SATURATION CHECK
            weight = self.validation_rules['saturation']['weight']
            
            if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
                hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
                saturation = hsv[:, :, 1]
                avg_saturation = np.mean(saturation)
                
                if avg_saturation < 10:
                    validation_scores.append(1.0 * weight)
                    validation_details.append(f"✓ Very low saturation (X-ray)")
                elif avg_saturation < 20:
                    validation_scores.append(0.8 * weight)
                    validation_details.append(f"✓ Low saturation")
                elif avg_saturation < 50:
                    validation_scores.append(0.3 * weight)
                    validation_details.append(f"⚠ Moderate saturation")
                else:
                    validation_scores.append(0.0 * weight)
                    validation_details.append(f"✗ High saturation - color photo")
                weights_sum += weight
            
            # CALCULATE FINAL VALIDATION SCORE
            if weights_sum > 0:
                final_score = (sum(validation_scores) / weights_sum) * 100
            else:
                final_score = 0
            
            # Determine result
            if final_score >= 75:
                is_valid = True
                message = f"✓ Valid chest X-ray detected (confidence: {final_score:.1f}%)"
                confidence = final_score
            elif final_score >= 60:
                is_valid = True
                message = f"⚠ Possible chest X-ray, but unusual features (confidence: {final_score:.1f}%)"
                confidence = final_score
            else:
                is_valid = False
                message = f"✗ NOT a valid chest X-ray! (confidence: {final_score:.1f}%)"
                confidence = final_score
            
            logger.info(f"Image validation complete: {message}")
            return is_valid, confidence, message, validation_details
            
        except Exception as e:
            logger.error(f"Error in deep validation: {e}")
            return False, 0, f"✗ Error validating image: {str(e)}", []


# Global instance
validator = ImageValidator()