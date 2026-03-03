"""
Main Pipeline: Orchestrates all 5 models for complete prescription processing
"""

import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from models.ocr_model import OCRModel
from models.ner_model import MedicineExtractionModel
from models.correction_model import MedicineCorrectionModel
from models.drug_validation_model import DrugValidationModel
from models.drug_interaction_model import DrugInteractionModel

logger = logging.getLogger(__name__)


class PrescriptionProcessor:
    """
    Full prescription processing pipeline combining all 5 models
    """

    def __init__(self, enable_ocr: bool = True, enable_ner: bool = True,
                 enable_correction: bool = True, enable_validation: bool = True,
                 enable_interaction: bool = True):
        """
        Initialize prescription processor with all models
        
        Args:
            enable_ocr: Enable OCR model
            enable_ner: Enable NER model
            enable_correction: Enable correction model
            enable_validation: Enable validation model
            enable_interaction: Enable interaction model
        """
        logger.info("Initializing PrescriptionProcessor...")
        
        self.enable_ocr = enable_ocr
        self.enable_ner = enable_ner
        self.enable_correction = enable_correction
        self.enable_validation = enable_validation
        self.enable_interaction = enable_interaction
        
        # Initialize models
        self.ocr_model = OCRModel(use_easy_ocr=True, use_transformer_ocr=False) if enable_ocr else None
        self.ner_model = MedicineExtractionModel() if enable_ner else None
        self.correction_model = MedicineCorrectionModel() if enable_correction else None
        self.validation_model = DrugValidationModel() if enable_validation else None
        self.interaction_model = DrugInteractionModel() if enable_interaction else None
        
        logger.info("PrescriptionProcessor initialized successfully")

    def _normalize_ocr_text(self, text: str) -> str:
        """Apply structural OCR text normalization to repair corrupted tokens"""
        import re
        if not text:
            return ""
            
        try:
            # Phase 1: Character Normalization
            text = re.sub(r'(\d)[Oo](?=\d)', r'\g<1>0', text)
            text = re.sub(r'\b[l1][Oo]\b', '10', text)
            text = re.sub(r'(\d)[Oo](?=\s*(?:mg|g|mcg|ml))', r'\g<1>0', text, flags=re.IGNORECASE)
            
            # Phase 2: Additional OCR Digit Normalization
            text = re.sub(r'(\d)[lI](?=\d)', r'\g<1>1', text)
            text = re.sub(r'(\d)\s+mg', r'\g<1>mg', text, flags=re.IGNORECASE)
            text = re.sub(r'MG', 'mg', text)
            
            # Normalize mixed stray spaces in mg tokens "40 0mg" -> "400mg"
            text = re.sub(r'(\d)\s+(\d+\s*(?:mg|g|mcg|ml))', r'\g<1>\g<2>', text, flags=re.IGNORECASE)

            # Phase 2 & 3: Token Reconstruction for corrupted duration lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                # Check if line contains 'for' and 'day' pattern
                if re.search(r'\bfor\b', line, re.IGNORECASE) and re.search(r'\bdays?\b', line, re.IGNORECASE):
                    # Extract loose mg tokens
                    mg_tokens = re.findall(r'\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml)\b', line, re.IGNORECASE)
                    if mg_tokens:
                        # Remove them from duration parsing
                        new_line = line
                        for mg in mg_tokens:
                            new_line = new_line.replace(mg, "")
                        new_line = re.sub(r'\s+', ' ', new_line).strip()
                        lines[i] = new_line
                        
                        # Re-inject mapped to previous lines (bottom up nearest order)
                        mg_idx = len(mg_tokens) - 1
                        for j in range(i - 1, -1, -1):
                            if mg_idx < 0:
                                break
                            # If the line doesn't already have its own dosage, and has alphabetics
                            if not re.search(r'\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml)\b', lines[j], re.IGNORECASE):
                                if re.search(r'[a-zA-Z]{3,}', lines[j]):
                                    lines[j] = lines[j] + f" {mg_tokens[mg_idx]}"
                                    mg_idx -= 1
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in OCR text normalization: {str(e)}")
            return text

    def process_prescription_image(self, image_path: str) -> Dict:
        """
        Complete prescription processing from image
        
        Args:
            image_path: Path to prescription image
            
        Returns:
            Dictionary with complete processing results
        """
        logger.info(f"Processing prescription image: {image_path}")
        
        result = {
            "image_path": image_path,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: OCR - Extract text from image
            if self.enable_ocr and self.ocr_model:
                import time
                t0 = time.time()
                logger.info("Stage 1: Running OCR...")
                ocr_result = self.ocr_model.extract_text(image_path)
                result["stages"]["ocr"] = ocr_result
                extracted_text = ocr_result.get("extracted_text", "")
                confidence = ocr_result.get('confidence', 0)
                logger.info(f"OCR completed in {time.time()-t0:.2f}s. Confidence: {confidence:.2f}")
                
                if confidence < 0.3:
                    logger.warning("Low OCR confidence detected < 0.3")
                    result.setdefault("warnings", []).append(f"Low OCR confidence ({confidence:.2f})")
            else:
                logger.warning("OCR disabled or model not initialized")
                return result
            
            # Stage 2: NER - Extract medicines
            if self.enable_ner and self.ner_model:
                import time
                t0 = time.time()
                logger.info("Stage 2: Running NER (Medicine Extraction)...")
                
                extracted_text = self._normalize_ocr_text(extracted_text)
                
                ner_result = self.ner_model.extract_medicines(extracted_text)
                medicines = ner_result.get("medicines", [])
                
                for med in medicines:
                    fuzzy = med.get("fuzzy_score", 0)
                    med_conf = (fuzzy / 100.0) * confidence
                    med["confidence"] = round(max(0.0, min(1.0, med_conf)), 2)
                    
                result["stages"]["ner"] = ner_result
                logger.info(f"Extracted {len(medicines)} medicines in {time.time()-t0:.2f}s")
            else:
                logger.warning("NER disabled or model not initialized")
                return result
            
            # Stage 3: Correction - Fix spelling errors
            if self.enable_correction and self.correction_model and medicines:
                logger.info("Stage 3: Running Correction (Spelling fix)...")
                medicines = self.correction_model.correct_extracted_medicines(medicines)
                result["stages"]["correction"] = {
                    "corrected_medicines": medicines,
                    "method": "RapidFuzz fuzzy matching"
                }
                logger.info(f"Spelling correction completed")
            
            if self.enable_validation and self.validation_model and medicines:
                logger.info("Stage 4: Running Validation...")
                medicines = self.validation_model.validate_extracted_medicines(medicines)
                
                for med in medicines:
                    if "dosage_warning" in med:
                        msg = f"Unusual dosage detected for {med['name']}: {med['dosage']}"
                        if msg not in result.setdefault("warnings", []):
                            result["warnings"].append(msg)
                            
                result["stages"]["validation"] = {
                    "validated_medicines": medicines,
                    "method": "Drug database lookup"
                }
                logger.info(f"Drug validation completed")
            
            # Stage 5: Interaction Prediction - Check drug interactions
            if self.enable_interaction and self.interaction_model and medicines:
                import time
                t0 = time.time()
                logger.info("Stage 5: Running Interaction Prediction...")
                interactions = self.interaction_model.predict_interactions_from_medicines(medicines)
                result["stages"]["interaction"] = interactions
                logger.info(f"Found {len(interactions.get('significant_interactions', []))} interactions in {time.time()-t0:.2f}s")
            
            # Final results assembly
            warnings = result.get("warnings", [])
            if not medicines:
                warnings.append("No valid medicines matched against database.")
                
            result["final_result"] = {
                "medicines": medicines,
                "total_medicines": len(medicines),
                "status": "success",
                "warnings": warnings
            }
            
            if "interaction" in result["stages"]:
                result["final_result"]["interactions"] = result["stages"]["interaction"].get(
                    "significant_interactions", []
                )
            
            logger.info("Prescription processing completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing prescription: {str(e)}", exc_info=True)
            result["final_result"] = {
                "status": "error",
                "error": str(e)
            }
        
        return result

    def process_from_text(self, text: str) -> Dict:
        """
        Process prescription from OCR text (skip OCR stage)
        
        Args:
            text: OCR-extracted prescription text
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing prescription from text (OCR text provided)...")
        
        result = {
            "source": "text",
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Skip OCR, start from NER
            text = self._normalize_ocr_text(text)
            
            result["stages"]["ocr"] = {
                "extracted_text": text,
                "method": "Text input (OCR skipped, but normalized)"
            }
            
            # Stage 2: NER
            if self.enable_ner and self.ner_model:
                import time
                t0 = time.time()
                logger.info("Stage 2: Running NER...")
                ner_result = self.ner_model.extract_medicines(text)
                medicines = ner_result.get("medicines", [])
                
                for med in medicines:
                    fuzzy = med.get("fuzzy_score", 100)
                    med["confidence"] = round(max(0.0, min(1.0, fuzzy / 100.0)), 2)
                    
                result["stages"]["ner"] = ner_result
                logger.info(f"Extracted {len(medicines)} medicines in {time.time()-t0:.2f}s")
            else:
                return result
            
            # Stages 3-5 follow same pattern as image processing
            if self.enable_correction and self.correction_model and medicines:
                medicines = self.correction_model.correct_extracted_medicines(medicines)
                result["stages"]["correction"] = {"corrected_medicines": medicines}
            
            if self.enable_validation and self.validation_model and medicines:
                medicines = self.validation_model.validate_extracted_medicines(medicines)
                result["stages"]["validation"] = {"validated_medicines": medicines}
            
            if self.enable_interaction and self.interaction_model and medicines:
                import time
                t0 = time.time()
                logger.info("Stage 5: Running Interaction Prediction...")
                interactions = self.interaction_model.predict_interactions_from_medicines(medicines)
                result["stages"]["interaction"] = interactions
                logger.info(f"Found {len(interactions.get('significant_interactions', []))} interactions in {time.time()-t0:.2f}s")
            
            warnings = result.get("warnings", [])
            if not medicines:
                warnings.append("No valid medicines matched against database.")
                
            result["final_result"] = {
                "medicines": medicines,
                "total_medicines": len(medicines),
                "status": "success",
                "warnings": warnings
            }
            
            if "interaction" in result["stages"]:
                result["final_result"]["interactions"] = result["stages"]["interaction"].get(
                    "significant_interactions", []
                )
            
            logger.info("Text processing completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}", exc_info=True)
            result["final_result"] = {"status": "error", "error": str(e)}
        
        return result

    def batch_process_images(self, image_paths: List[str]) -> List[Dict]:
        """
        Process multiple prescription images
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of processing results
        """
        logger.info(f"Batch processing {len(image_paths)} prescription images...")
        
        results = []
        for image_path in image_paths:
            result = self.process_prescription_image(image_path)
            results.append(result)
        
        logger.info(f"Batch processing completed")
        
        return results

    def export_results(self, result: Dict, output_path: str) -> None:
        """
        Export processing results to JSON
        
        Args:
            result: Processing result dictionary
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results exported to: {output_path}")
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")

    def generate_report(self, result: Dict) -> str:
        """
        Generate human-readable report from processing result
        
        Args:
            result: Processing result dictionary
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("PRESCRIPTION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {result.get('timestamp', 'N/A')}")
        report.append("")
        
        if result.get("final_result", {}).get("status") == "error":
            report.append(f"ERROR: {result['final_result'].get('error', 'Unknown error')}")
            return "\n".join(report)
        
        final = result.get("final_result", {})
        report.append(f"Total Medicines Found: {final.get('total_medicines', 0)}")
        report.append("")
        
        # Medicines section
        report.append("MEDICINES:")
        report.append("-" * 60)
        medicines = final.get("medicines", [])
        for i, med in enumerate(medicines, 1):
            report.append(f"{i}. {med.get('name', 'Unknown')}")
            if med.get('dosage'):
                report.append(f"   Dosage: {med.get('dosage')}")
            if med.get('frequency'):
                report.append(f"   Frequency: {med.get('frequency')}")
            if med.get('duration'):
                report.append(f"   Duration: {med.get('duration')}")
            if med.get('is_valid') is False:
                report.append(f"   ⚠️  WARNING: Not found in drug database")
            report.append("")
        
        # Interactions section
        interactions = final.get("interactions", [])
        if interactions:
            report.append("DRUG INTERACTIONS:")
            report.append("-" * 60)
            for i, interaction in enumerate(interactions, 1):
                report.append(f"{i}. {interaction['drug1']} + {interaction['drug2']}")
                report.append(f"   Severity: {interaction.get('severity', 'unknown').upper()}")
                report.append(f"   Risk Score: {interaction.get('risk_score', 0):.2%}")
                report.append(f"   Description: {interaction.get('description', 'N/A')}")
                report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize processor
    processor = PrescriptionProcessor()
    
    # Example 1: Process from text (no image needed for testing)
    sample_text = """
    Take Aspirin 500mg twice daily for 7 days.
    Also take Metformin 1000mg once daily with food for 30 days.
    Use Ibuprofen 400mg three times daily as needed for pain.
    """
    
    result = processor.process_from_text(sample_text)
    
    # Generate and print report
    report = processor.generate_report(result)
    print(report)
    
    # Export results
    # processor.export_results(result, "prescription_result.json")
