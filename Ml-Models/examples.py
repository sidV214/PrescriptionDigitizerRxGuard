"""
Practical Usage Examples
Real-world scenarios and common use cases
"""

import json
from pipeline import PrescriptionProcessor
from models.ner_model import MedicineExtractionModel
from models.correction_model import MedicineCorrectionModel
from models.drug_validation_model import DrugValidationModel
from models.drug_interaction_model import DrugInteractionModel
from utils.data_loader import save_results_to_csv


# =============================================================================
# EXAMPLE 1: Process a Real Prescription Text
# =============================================================================

def example_1_basic_prescription_processing():
    """
    Most common use case: Process a prescription from OCR output
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Prescription Processing")
    print("="*70 + "\n")
    
    # Initialize processor
    processor = PrescriptionProcessor(enable_ocr=False)
    
    # Prescription text from OCR
    prescription_text = """
    PRESCRIPTION
    Patient: Jane Smith
    Date: January 15, 2024
    Doctor: Dr. Robert Johnson
    
    MEDICATION INSTRUCTIONS:
    
    1. Aspirin 500mg - Take twice daily with meals for 7 days
    2. Metformin 1000mg - Take once daily in the morning for 30 days
    3. Ibuprfen 400mg - Take every 6 hours as needed for pain (not to exceed 5 days)
    4. Omeprazole 20mg - Take once daily before breakfast for 14 days
    
    NOTES: Take with water. Contact doctor if symptoms persist.
    """
    
    # Process
    result = processor.process_from_text(prescription_text)
    
    # Print the report
    report = processor.generate_report(result)
    print(report)
    
    # Save results
    processor.export_results(result, 'example1_results.json')
    
    return result


# =============================================================================
# EXAMPLE 2: Handle spelling errors in medicine names
# =============================================================================

def example_2_correct_misspelled_medicines():
    """
    Handle OCR errors with spelling correction
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Correcting Misspelled Medicine Names")
    print("="*70 + "\n")
    
    corrector = MedicineCorrectionModel()
    
    # Misspelled medicines from OCR
    misspelled = [
        "Asprihn",      # Aspirin
        "Metforrmin",   # Metformin
        "Ibuprofin",    # Ibuprofen
        "Lisinoprol",   # Lisinopril
        "Omeprazle"     # Omeprazole
    ]
    
    print("Correcting misspelled medicines:\n")
    
    corrections = corrector.correct_medicines_batch(misspelled)
    
    print("Results:")
    print("-" * 70)
    for _, row in corrections.iterrows():
        symbol = "✓" if row['is_corrected'] else "✗"
        print(f"  {symbol} {row['original']:15} → {row['corrected']:15} ({row['score']:.1%})")
    
    # Export
    corrections.to_csv('example2_corrections.csv', index=False)
    print("\nResults saved to: example2_corrections.csv")
    
    return corrections


# =============================================================================
# EXAMPLE 3: Validate medicines against drug database
# =============================================================================

def example_3_validate_medicines():
    """
    Validate if extracted medicines exist in database
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Validating Medicines Against Database")
    print("="*70 + "\n")
    
    validator = DrugValidationModel()
    
    # Medicines to validate
    medicines_to_check = [
        "Aspirin",
        "Unknown Medicine",
        "Metformin",
        "Fake Drug XYZ",
        "Lisinopril",
        "Not A Real Medicine"
    ]
    
    print(f"Validating {len(medicines_to_check)} medicines:\n")
    
    validations = validator.validate_medicines_batch(medicines_to_check)
    
    print("Results:")
    print("-" * 70)
    for _, row in validations.iterrows():
        status = "✓ FOUND" if row['found'] else "✗ NOT FOUND"
        valid = "VALID" if row['valid'] else "INVALID"
        print(f"  {row['medicine']:20} {status:12} {valid:10} ({row['confidence']:.0%})")
    
    # Show what was validated successfully
    print("\n\nSuccessfully validated medicines:")
    valid_medicines = validations[validations['found']]
    for _, med in valid_medicines.iterrows():
        db_info = med['database_match']
        if isinstance(db_info, dict):
            print(f"\n  {med['medicine']}")
            print(f"    Generic: {db_info.get('generic_name', 'N/A')}")
            print(f"    Category: {db_info.get('category', 'N/A')}")
            print(f"    Side Effects: {db_info.get('side_effects', 'N/A')}")
    
    # Export
    validations.to_csv('example3_validations.csv', index=False)
    print("\n\nResults saved to: example3_validations.csv")
    
    return validations


# =============================================================================
# EXAMPLE 4: Check for drug interactions
# =============================================================================

def example_4_check_interactions():
    """
    Predict harmful drug interactions
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Checking Drug Interactions")
    print("="*70 + "\n")
    
    interaction_model = DrugInteractionModel()
    
    # Patient's medications
    medications = [
        "Aspirin",
        "Ibuprofen",
        "Metformin",
        "Lisinopril"
    ]
    
    print(f"Checking interactions for patient with {len(medications)} medications:\n")
    for i, med in enumerate(medications, 1):
        print(f"  {i}. {med}")
    
    # Check all interactions
    interactions = interaction_model.predict_interactions_batch(medications)
    
    # Filter significant interactions
    print("\n\nSignificant Interactions Found:")
    print("-" * 70)
    
    high_risk = [i for i in interactions if i.get('severity') == 'high']
    moderate_risk = [i for i in interactions if i.get('severity') == 'moderate']
    low_risk = [i for i in interactions if i.get('severity') == 'low']
    
    if high_risk:
        print("\n🔴 HIGH RISK:")
        for i in high_risk:
            print(f"\n  {i['drug1']} + {i['drug2']}")
            print(f"  Risk Score: {i.get('risk_score', 0):.1%}")
            print(f"  Description: {i.get('description', 'N/A')}")
    
    if moderate_risk:
        print("\n🟡 MODERATE RISK:")
        for i in moderate_risk:
            print(f"\n  {i['drug1']} + {i['drug2']}")
            print(f"  Risk Score: {i.get('risk_score', 0):.1%}")
            print(f"  Description: {i.get('description', 'N/A')}")
    
    if low_risk:
        print("\n🟢 LOW RISK:")
        for i in low_risk:
            print(f"  {i['drug1']} + {i['drug2']} ({i.get('risk_score', 0):.1%})")
    
    # Summary
    summary = interaction_model.get_interaction_summary(interactions)
    print("\n\nSummary:")
    print("-" * 70)
    print(f"  Total Pairs Checked: {summary['total_interactions']}")
    print(f"  High Risk: {summary['high_risk']}")
    print(f"  Moderate Risk: {summary['moderate_risk']}")
    print(f"  Low Risk: {summary['low_risk']}")
    
    # Export
    import pandas as pd
    df_interactions = pd.DataFrame(interactions)
    df_interactions.to_csv('example4_interactions.csv', index=False)
    print("\n\nResults saved to: example4_interactions.csv")
    
    return interactions


# =============================================================================
# EXAMPLE 5: End-to-end workflow for a patient
# =============================================================================

def example_5_complete_patient_workflow():
    """
    Complete workflow: Extract → Correct → Validate → Check Interactions
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Complete Patient Medication Workflow")
    print("="*70 + "\n")
    
    # Initialize all models
    processor = PrescriptionProcessor(enable_ocr=False)
    
    # Patient's prescription
    patient_prescription = """
    Rx for: John Doe
    Date: 01/15/2024
    
    1. Aspirin 500 mg - twice daily for 1 week
    2. Metforrmin 1000 mg - once daily for 30 days
    3. Ibuprfen 400 mg - every 6 hours as needed
    """
    
    print(f"Patient Prescription:\n{patient_prescription}\n")
    
    # Process through complete pipeline
    print("Processing through complete pipeline...")
    print("-" * 70 + "\n")
    
    result = processor.process_from_text(patient_prescription)
    
    # Extract information
    final_result = result.get('final_result', {})
    medicines = final_result.get('medicines', [])
    interactions = final_result.get('interactions', [])
    
    print(f"✓ Extracted {len(medicines)} medicines")
    print(f"✓ Validated medications")
    print(f"✓ Found {len(interactions)} significant interactions\n")
    
    # Detailed patient summary
    print("PATIENT MEDICATION SUMMARY")
    print("=" * 70)
    
    for i, med in enumerate(medicines, 1):
        print(f"\n{i}. {med.get('name', 'Unknown')}")
        print(f"   Dosage: {med.get('dosage', 'N/A')}")
        print(f"   Frequency: {med.get('frequency', 'N/A')}")
        print(f"   Duration: {med.get('duration', 'N/A')}")
        
        if med.get('spelling_corrected'):
            print(f"   ⚠️ Auto-corrected from: {med.get('original_name', 'N/A')}")
        
        if not med.get('is_valid'):
            print(f"   ⚠️ WARNING: Not found in drug database!")
    
    # Interactions
    if interactions:
        print("\n\nMEDICATION INTERACTIONS")
        print("=" * 70)
        
        for interaction in interactions:
            severity_symbol = "🔴" if interaction['severity'] == 'high' else "🟡"
            print(f"\n{severity_symbol} {interaction['drug1']} + {interaction['drug2']}")
            print(f"   Risk Level: {interaction['severity'].upper()}")
            print(f"   Risk Score: {interaction.get('risk_score', 0):.1%}")
            print(f"   Details: {interaction.get('description', 'N/A')}")
    
    # Save complete patient report
    report = processor.generate_report(result)
    with open('example5_patient_report.txt', 'w') as f:
        f.write(report)
    
    print("\n\nReport saved to: example5_patient_report.txt")
    
    return result


# =============================================================================
# EXAMPLE 6: Batch processing for clinic usage
# =============================================================================

def example_6_batch_processing_clinic():
    """
    Process multiple prescriptions for clinic usage
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Batch Processing for Clinic")
    print("="*70 + "\n")
    
    processor = PrescriptionProcessor(enable_ocr=False)
    
    # Multiple prescriptions from clinic
    prescriptions = [
        {
            "patient_id": "P001",
            "text": "Aspirin 500mg twice daily for 7 days. Metformin 1000mg once daily for 30 days."
        },
        {
            "patient_id": "P002",
            "text": "Ibuprfen 400mg every 6 hours as needed. Omeprazole 20mg once daily for 14 days."
        },
        {
            "patient_id": "P003",
            "text": "Lisinopril 10mg once daily for 60 days. Atorvastatin 20mg once daily for 90 days."
        }
    ]
    
    print(f"Processing {len(prescriptions)} patient prescriptions...\n")
    
    clinic_results = {
        "total_patients": len(prescriptions),
        "total_medicines": 0,
        "warnings": [],
        "patients": []
    }
    
    for prescription in prescriptions:
        patient_id = prescription['patient_id']
        result = processor.process_from_text(prescription['text'])
        
        final = result.get('final_result', {})
        medicines = final.get('medicines', [])
        interactions = final.get('interactions', [])
        
        patient_data = {
            "patient_id": patient_id,
            "medicines": medicines,
            "interactions": interactions
        }
        
        clinic_results['patients'].append(patient_data)
        clinic_results['total_medicines'] += len(medicines)
        
        # Track warnings
        for med in medicines:
            if not med.get('is_valid'):
                clinic_results['warnings'].append(
                    f"{patient_id}: Unknown medicine '{med.get('name')}'"
                )
        
        if interactions:
            for inter in interactions:
                if inter.get('severity') == 'high':
                    clinic_results['warnings'].append(
                        f"{patient_id}: High-risk interaction - {inter['drug1']} + {inter['drug2']}"
                    )
    
    # Print summary
    print(f"✓ Processed {clinic_results['total_patients']} patients")
    print(f"✓ Found {clinic_results['total_medicines']} total medicines")
    print(f"✓ Identified {len(clinic_results['warnings'])} warnings\n")
    
    if clinic_results['warnings']:
        print("⚠️ WARNINGS:")
        for warning in clinic_results['warnings']:
            print(f"  - {warning}")
    
    # Export results
    with open('example6_clinic_results.json', 'w') as f:
        json.dump(clinic_results, f, indent=2)
    
    print("\nResults saved to: example6_clinic_results.json")
    
    return clinic_results


# =============================================================================
# Run Examples
# =============================================================================

def run_all_examples():
    """Run all practical examples"""
    print("\n" + "#"*70)
    print("# PRACTICAL USAGE EXAMPLES")
    print("#"*70)
    
    try:
        example_1_basic_prescription_processing()
        example_2_correct_misspelled_medicines()
        example_3_validate_medicines()
        example_4_check_interactions()
        example_5_complete_patient_workflow()
        example_6_batch_processing_clinic()
        
        print("\n" + "#"*70)
        print("# ALL EXAMPLES COMPLETED")
        print("#"*70 + "\n")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    run_all_examples()
