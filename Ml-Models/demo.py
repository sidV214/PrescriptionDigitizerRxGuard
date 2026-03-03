"""
Demo script: Example usage of the complete prescription processing system
Shows how to use each model individually and as part of the pipeline
"""

import logging
from pathlib import Path
from pipeline import PrescriptionProcessor
from models.ocr_model import OCRModel
from models.ner_model import MedicineExtractionModel
from models.correction_model import MedicineCorrectionModel
from models.drug_validation_model import DrugValidationModel
from models.drug_interaction_model import DrugInteractionModel
from utils.data_loader import create_sample_prescription_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_complete_pipeline():
    """
    Demo 1: Complete pipeline processing
    Shows the full workflow from prescription text
    """
    print("\n" + "="*70)
    print("DEMO 1: COMPLETE PRESCRIPTION PROCESSING PIPELINE")
    print("="*70 + "\n")
    
    # Initialize processor with all models
    processor = PrescriptionProcessor(
        enable_ocr=False,  # Skip OCR for this demo
        enable_ner=True,
        enable_correction=True,
        enable_validation=True,
        enable_interaction=True
    )
    
    # Sample prescription text (as if it came from OCR)
    sample_prescription = """
    PRESCRIPTION
    Patient: John Doe | Date: 01/15/2024
    
    MEDICATIONS:
    1. Aspirin 500mg - twice daily for 7 days
    2. Metformin 1000mg - once daily with meals for 30 days
    3. Ibuprfen 400mg - every 6 hours as needed for pain (max 5 days)
    4. Unknown Drug 250mg - three times daily
    """
    
    # Process from text
    result = processor.process_from_text(sample_prescription)
    
    # Generate and print report
    report = processor.generate_report(result)
    print(report)
    
    return result


def demo_ner_model():
    """
    Demo 2: Medicine Extraction (NER) model only
    Shows how to extract medicines, dosages, and durations
    """
    print("\n" + "="*70)
    print("DEMO 2: MEDICINE EXTRACTION (NER) MODEL")
    print("="*70 + "\n")
    
    ner = MedicineExtractionModel()
    
    sample_text = "Take Aspirin 500mg twice daily for 7 days. Also take Metformin 1000mg once daily with food for 30 days."
    
    print(f"Input text: {sample_text}\n")
    
    result = ner.extract_medicines(sample_text)
    
    print(f"Total medicines found: {result['total_medicines']}")
    print("\nExtracted Medicines:")
    for medicine in result["medicines"]:
        print(f"  - {medicine['name']}")
        print(f"    Dosage: {medicine.get('dosage', 'N/A')}")
        print(f"    Frequency: {medicine.get('frequency', 'N/A')}")
        print(f"    Duration: {medicine.get('duration', 'N/A')}\n")
    
    return result


def demo_correction_model():
    """
    Demo 3: Medicine Spelling Correction model
    Shows how to correct OCR spelling errors
    """
    print("\n" + "="*70)
    print("DEMO 3: MEDICINE SPELLING CORRECTION MODEL")
    print("="*70 + "\n")
    
    corrector = MedicineCorrectionModel()
    
    misspelled_medicines = [
        "Asprinh",
        "Metforrmin",
        "Lsinopril",
        "Ibuprfen",
        "Amoxicilin"
    ]
    
    print("Correcting misspelled medicine names:\n")
    
    df_corrections = corrector.correct_medicines_batch(misspelled_medicines)
    
    for _, row in df_corrections.iterrows():
        status = "✓ CORRECTED" if row['is_corrected'] else "✗ NOT CORRECTED"
        print(f"  {row['original']:20} → {row['corrected']:20} [{status}] ({row['score']:.2%})")
    
    # Get statistics
    stats = corrector.get_correction_statistics(df_corrections)
    print(f"\nCorrection Statistics:")
    print(f"  Total: {stats['total_medicines']}")
    print(f"  Corrected: {stats['corrected']}")
    print(f"  Correction Rate: {stats['correction_rate']:.1%}")
    
    return df_corrections


def demo_validation_model():
    """
    Demo 4: Drug Validation model
    Shows how to validate medicines against drug database
    """
    print("\n" + "="*70)
    print("DEMO 4: DRUG VALIDATION MODEL")
    print("="*70 + "\n")
    
    validator = DrugValidationModel()
    
    medicines_to_validate = [
        "Aspirin",
        "Unknown Medicine",
        "Metformin",
        "Fake Drug",
        "Ibuprofen"
    ]
    
    print("Validating medicines against drug database:\n")
    
    df_validations = validator.validate_medicines_batch(medicines_to_validate)
    
    for _, row in df_validations.iterrows():
        status = "✓ VALID" if row['found'] else "✗ NOT FOUND"
        print(f"  {row['medicine']:20} {status:15} [{row['confidence']:.2%}]")
    
    # Get statistics
    stats = validator.get_validation_statistics(df_validations)
    print(f"\nValidation Statistics:")
    print(f"  Total: {stats['total_medicines']}")
    print(f"  Valid: {stats['valid']}")
    print(f"  Found in DB: {stats['found']}")
    print(f"  Validation Rate: {stats['validation_rate']:.1%}")
    
    return df_validations


def demo_interaction_model():
    """
    Demo 5: Drug Interaction Prediction model
    Shows how to predict interactions between medicines
    """
    print("\n" + "="*70)
    print("DEMO 5: DRUG INTERACTION PREDICTION MODEL")
    print("="*70 + "\n")
    
    interaction_model = DrugInteractionModel()
    
    medicines = ["Aspirin", "Ibuprofen", "Metformin"]
    
    print(f"Checking interactions for medicines: {medicines}\n")
    
    # Get interactions
    interactions = interaction_model.predict_interactions_batch(medicines)
    
    # Filter and display
    print("Predicted Interactions:")
    for interaction in interactions:
        if interaction.get("has_interaction") or interaction.get("risk_score", 0) >= 0.5:
            print(f"\n  {interaction['drug1']} + {interaction['drug2']}")
            print(f"    Severity: {interaction.get('severity', 'unknown').upper()}")
            print(f"    Risk Score: {interaction.get('risk_score', 0):.2%}")
            print(f"    Description: {interaction.get('description', 'N/A')}")
    
    # Summary
    summary = interaction_model.get_interaction_summary(interactions)
    print(f"\nInteraction Summary:")
    print(f"  Total Pairs Checked: {summary['total_interactions']}")
    print(f"  High Risk: {summary['high_risk']}")
    print(f"  Moderate Risk: {summary['moderate_risk']}")
    print(f"  Low Risk: {summary['low_risk']}")
    
    return interactions


def demo_batch_processing():
    """
    Demo 6: Batch processing multiple prescriptions
    Shows how to process multiple prescriptions at once
    """
    print("\n" + "="*70)
    print("DEMO 6: BATCH PROCESSING MULTIPLE PRESCRIPTIONS")
    print("="*70 + "\n")
    
    processor = PrescriptionProcessor(enable_ocr=False)
    
    # Sample prescriptions
    prescriptions = [
        "Aspirin 500mg twice daily for 7 days",
        "Metformin 1000mg once daily for 30 days with meals",
        "Ibuprofen 400mg every 6 hours as needed"
    ]
    
    print(f"Processing {len(prescriptions)} prescriptions...\n")
    
    all_results = []
    for i, prescription_text in enumerate(prescriptions, 1):
        result = processor.process_from_text(prescription_text)
        all_results.append(result)
        
        final = result.get("final_result", {})
        medicines = final.get("medicines", [])
        print(f"Prescription {i}: {len(medicines)} medicines found")
        for med in medicines:
            print(f"  - {med.get('name', 'Unknown')}")
        print()
    
    return all_results


def demo_individual_models():
    """
    Demo 7: Individual model usage
    Shows how to use each model independently
    """
    print("\n" + "="*70)
    print("DEMO 7: INDIVIDUAL MODEL USAGE")
    print("="*70 + "\n")
    
    # Model 1: NER
    print("1. NER Model - Extract Medicine Information")
    print("-" * 50)
    ner = MedicineExtractionModel()
    ner_result = ner.extract_medicines("Aspirin 500mg twice daily for 7 days")
    print(f"   Extraction accuracy: {len(ner_result['medicines'])} medicines found")
    
    # Model 2: Correction
    print("\n2. Correction Model - Fix Spelling Errors")
    print("-" * 50)
    corrector = MedicineCorrectionModel()
    correction = corrector.correct_medicine_name("Asprinh")
    print(f"   Corrected: 'Asprinh' → '{correction['corrected']}'")
    
    # Model 3: Validation
    print("\n3. Validation Model - Verify Medicines")
    print("-" * 50)
    validator = DrugValidationModel()
    validation = validator.validate_medicine("Aspirin")
    print(f"   Validation: '{validation['medicine']}' is {'VALID' if validation['valid'] else 'INVALID'}")
    
    # Model 4: Interaction
    print("\n4. Interaction Model - Predict Drug Interactions")
    print("-" * 50)
    interaction_model = DrugInteractionModel()
    interaction = interaction_model.predict_interaction("Aspirin", "Ibuprofen")
    print(f"   Interaction Risk: {interaction['risk_score']:.2%}")


def main():
    """
    Run all demos
    """
    print("\n" + "#"*70)
    print("# PRESCRIPTION PROCESSING SYSTEM - COMPLETE DEMO")
    print("#"*70)
    
    try:
        # Run all demos
        demo_complete_pipeline()
        demo_ner_model()
        demo_correction_model()
        demo_validation_model()
        demo_interaction_model()
        demo_batch_processing()
        demo_individual_models()
        
        print("\n" + "#"*70)
        print("# ALL DEMOS COMPLETED SUCCESSFULLY")
        print("#"*70 + "\n")
        
    except Exception as e:
        logger.error(f"Error running demos: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
