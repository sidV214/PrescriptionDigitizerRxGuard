"""
Model 1: OCR Model for extracting text from handwritten prescription images
Uses EasyOCR, TrOCR (Transformers), OpenCV, and Pillow
"""

import cv2
import numpy as np
from PIL import Image
import easyocr
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import logging
from typing import Tuple, Dict, List
from utils.config import OCR_CONFIG, TRANSFORMER_OCR_CONFIG

logger = logging.getLogger(__name__)


class OCRModel:
    """
    Optical Character Recognition model for prescription images
    Combines EasyOCR and TrOCR for robust text extraction
    """

    def __init__(self, use_easy_ocr: bool = True, use_transformer_ocr: bool = True):
        """
        Initialize OCR models
        
        Args:
            use_easy_ocr: Whether to use EasyOCR
            use_transformer_ocr: Whether to use TrOCR (Transformer-based OCR)
        """
        self.use_easy_ocr = use_easy_ocr
        self.use_transformer_ocr = use_transformer_ocr
        
        if self.use_easy_ocr:
            logger.info("Initializing EasyOCR...")
            self.easy_ocr_reader = easyocr.Reader(
                OCR_CONFIG["languages"],
                gpu=OCR_CONFIG["gpu"],
                model_storage_directory=OCR_CONFIG["model_storage_directory"]
            )
        
        if self.use_transformer_ocr:
            logger.info("Initializing TrOCR (Transformer-based)...")
            self.trocr_model = VisionEncoderDecoderModel.from_pretrained(  # type: ignore
                TRANSFORMER_OCR_CONFIG["model_name"]
            )
            self.image_processor = ViTImageProcessor.from_pretrained(  # type: ignore
                TRANSFORMER_OCR_CONFIG["model_name"]
            )
            self.tokenizer = AutoTokenizer.from_pretrained(  # type: ignore
                TRANSFORMER_OCR_CONFIG["model_name"]
            )

    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, Image.Image]:
        """
        Preprocess prescription image for OCR
        
        Args:
            image_path: Path to the prescription image
            
        Returns:
            Tuple of (OpenCV image, PIL image)
        """
        logger.info(f"Preprocessing image: {image_path}")
        
        # Read with OpenCV
        cv_image = cv2.imread(image_path)
        
        # Convert BGR to RGB for processing
        cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # Downscale input image to max width 1000px before OCR
        h, w = cv_image_rgb.shape[:2]
        if w > 1000:
            scale = 1000 / w
            new_w, new_h = 1000, int(h * scale)
            cv_image_rgb = cv2.resize(cv_image_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Image enhancement techniques
        cv_image_rgb = self._enhance_image(cv_image_rgb)
        
        # Convert to PIL for transformer model
        pil_image = Image.fromarray(cv_image_rgb)
        
        return cv_image_rgb, pil_image

    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image for better OCR results
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Enhanced image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        
        # Convert back to RGB (no thresholding)
        result = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
        
        return result

    def extract_text_easyocr(self, image: np.ndarray) -> Dict:
        """
        Extract text using EasyOCR and reconstruct spatial lines
        
        Args:
            image: OpenCV image
            
        Returns:
            Dictionary with extracted text structurally aligned to multi-line strings
            and averaged confidence scores.
        """
        logger.info("Extracting text using EasyOCR with spatial line reconstruction...")
        
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        results = self.easy_ocr_reader.readtext(gray_image)
        
        confidences = []
        tokens = []
        
        img_h = image.shape[0]
        # Dynamic Y-threshold for line clustering: ~1.5% of image height, minimum 10px
        y_threshold = max(10, int(img_h * 0.015))
        
        for detection in results:
            bbox = detection[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            text = detection[1]  # type: ignore
            confidence = detection[2]  # type: ignore
            
            # Calculate geometric centroids
            x_center = sum(pt[0] for pt in bbox) / 4.0
            y_center = sum(pt[1] for pt in bbox) / 4.0
            
            tokens.append({
                "text": text,
                "x": x_center,
                "y": y_center
            })
            confidences.append(confidence)
            
        # Cluster tokens functionally into horizontal lines by Y coordinate
        lines_clusters = []
        for token in tokens:
            placed = False
            for cluster in lines_clusters:
                cluster_y_avg = sum(t["y"] for t in cluster) / len(cluster)
                if abs(token["y"] - cluster_y_avg) <= y_threshold:
                    cluster.append(token)
                    placed = True
                    break
            
            if not placed:
                lines_clusters.append([token])
                
        # Sort logical lines from top-to-bottom
        lines_clusters.sort(key=lambda cluster: sum(t["y"] for t in cluster) / len(cluster))
        
        # Sort internal tokens from left-to-right and generate string lines
        reconstructed_lines = []
        for cluster in lines_clusters:
            cluster.sort(key=lambda t: t["x"])
            line_str = " ".join(t["text"] for t in cluster)
            reconstructed_lines.append(line_str)
            
        # Assemble perfectly structured 2D array matrix into a multiline string
        full_text = "\n".join(reconstructed_lines)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        return {
            "text": full_text,
            "lines": reconstructed_lines,
            "confidence": float(avg_confidence),
            "method": "EasyOCR"
        }

    def extract_text_trocr(self, pil_image: Image.Image) -> Dict:
        """
        Extract text using TrOCR (Transformer-based OCR)
        
        Args:
            pil_image: PIL image
            
        Returns:
            Dictionary with extracted text
        """
        logger.info("Extracting text using TrOCR...")
        
        try:
            pixel_values = self.image_processor(images=pil_image, return_tensors="pt").pixel_values  # type: ignore
            
            generated_ids = self.trocr_model.generate(  # type: ignore
                pixel_values,
                max_length=128,
                num_beams=5,
                early_stopping=True
            )
            
            generated_text = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return {
                "text": generated_text,
                "lines": [generated_text],
                "confidence": 0.95,  # TrOCR doesn't provide confidence
                "method": "TrOCR"
            }
        except Exception as e:
            logger.error(f"TrOCR extraction failed: {str(e)}")
            return {"text": "", "lines": [], "confidence": 0, "method": "TrOCR"}

    def extract_text(self, image_path: str) -> Dict:
        """
        Extract text from prescription image using both OCR methods
        
        Args:
            image_path: Path to the prescription image
            
        Returns:
            Dictionary with extracted text and metadata
        """
        logger.info(f"Starting OCR extraction from: {image_path}")
        
        cv_image = cv2.imread(image_path)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv_image)
        
        results = {
            "image_path": image_path,
            "methods": []
        }
        
        if self.use_easy_ocr:
            easyocr_result = self.extract_text_easyocr(cv_image)
            results["methods"].append(easyocr_result)
        
        if self.use_transformer_ocr:
            trocr_result = self.extract_text_trocr(pil_image)
            results["methods"].append(trocr_result)
        
        # Combine results - use the method with higher confidence
        best_result = max(results["methods"], key=lambda x: x["confidence"])
        results["extracted_text"] = best_result["text"]
        results["best_method"] = best_result["method"]
        results["confidence"] = best_result["confidence"]
        
        logger.info(f"OCR extraction completed. Confidence: {results['confidence']:.2f}")
        logger.info(f"RAW OCR TEXT: {results['extracted_text']}")
        
        return results

    def batch_extract(self, image_paths: List[str]) -> List[Dict]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of paths to prescription images
            
        Returns:
            List of extraction results
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.extract_text(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {image_path}: {str(e)}")
                results.append({"image_path": image_path, "error": str(e)})
        
        return results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    ocr = OCRModel(use_easy_ocr=True, use_transformer_ocr=False)
    # result = ocr.extract_text("path/to/prescription_image.jpg")
    # print(result)
