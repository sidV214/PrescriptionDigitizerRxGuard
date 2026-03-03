# Quick Start Guide

Get the prescription processing system up and running in 5 minutes.

## Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd s:\Ml-Models

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download NER model
python -m spacy download en_core_web_sm
```

## First Run (2 minutes)

```bash
# Run demo to verify installation
python demo.py
```

## Basic Usage (1 minute)

### Option A: Simple Python Script

Create `quick_test.py`:

```python
from pipeline import PrescriptionProcessor

# Initialize
processor = PrescriptionProcessor(enable_ocr=False)

# Process prescription text
result = processor.process_from_text("""
    Take Aspirin 500mg twice daily for 7 days.
    Take Metformin 1000mg once daily for 30 days.
""")

# Print results
print(processor.generate_report(result))
```

Run it:
```bash
python quick_test.py
```

### Option B: Interactive Python

```bash
python

# Inside Python:
>>> from pipeline import PrescriptionProcessor
>>> processor = PrescriptionProcessor(enable_ocr=False)
>>> result = processor.process_from_text("Take Aspirin 500mg twice daily for 7 days")
>>> print(processor.generate_report(result))
```

## Common Tasks

### Task 1: Extract Medicines from Text

```python
from models.ner_model import MedicineExtractionModel

ner = MedicineExtractionModel()
result = ner.extract_medicines("Take Aspirin 500mg twice daily for 7 days")

for medicine in result['medicines']:
    print(f"{medicine['name']}: {medicine['dosage']} {medicine['frequency']}")
```

### Task 2: Fix Spelling Errors

```python
from models.correction_model import MedicineCorrectionModel

corrector = MedicineCorrectionModel()
correction = corrector.correct_medicine_name("Asprinh")
print(f"Corrected: {correction['corrected']}")
```

### Task 3: Check if Medicine is Valid

```python
from models.drug_validation_model import DrugValidationModel

validator = DrugValidationModel()
result = validator.validate_medicine("Aspirin")
print(f"Valid: {result['valid']}, Confidence: {result['confidence']:.0%}")
```

### Task 4: Check Drug Interactions

```python
from models.drug_interaction_model import DrugInteractionModel

interaction_model = DrugInteractionModel()
result = interaction_model.predict_interaction("Aspirin", "Ibuprofen")
print(f"Risk: {result['risk_score']:.0%}, Severity: {result['severity']}")
```

### Task 5: Process Multiple Medicines at Once

```python
from pipeline import PrescriptionProcessor
import pandas as pd

processor = PrescriptionProcessor(enable_ocr=False)

prescription = """
1. Aspirin 500mg - twice daily for 7 days
2. Metformin 1000mg - once daily for 30 days
3. Ibuprofen 400mg - every 6 hours as needed
"""

result = processor.process_from_text(prescription)
print(processor.generate_report(result))
```

## Output Examples

### Example 1: Single Medicine Check
```
Input: "Aspirin 500mg"

Output:
  Medicine: Aspirin
  Dosage: 500mg
  Valid: ✓
  Interactions: None detected
```

### Example 2: Multiple Medicines
```
Input: "Take Aspirin and Ibuprofen"

Output:
  Medicines: 2
  - Aspirin
  - Ibuprofen
  
  Interactions Found: 1
  - Aspirin + Ibuprofen (HIGH RISK)
```

### Example 3: Complete Report
```
========== PRESCRIPTION ANALYSIS ==========
Medicines: 3
- Aspirin 500mg (twice daily, 7 days)
- Metformin 1000mg (once daily, 30 days)
- Ibuprofen 400mg (every 6 hours, as needed)

Drug Interactions:
🔴 Aspirin + Ibuprofen (High Risk - 85% risk)
   Increased GI bleeding risk

✓ Validation Complete
==========================================
```

## Troubleshooting

### Issue: "Module not found" error
```bash
# Solution: Verify virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### Issue: "No module named spacy"
```bash
# Solution: Install spaCy models
pip install spacy
python -m spacy download en_core_web_sm
```

### Issue: "EasyOCR failed to download"
```bash
# Solution: Pre-download models manually
python -c "import easyocr; reader = easyocr.Reader(['en'])"
```

### Issue: Memory error or slow processing
```bash
# Solution in pipeline.py:
processor = PrescriptionProcessor(
    enable_ocr=False,  # Skip OCR if not needed
    enable_interaction=False  # Disable interaction if not needed
)
```

## Next Steps

1. **Read INSTALLATION.md** for detailed setup options
2. **Check examples.py** for practical use cases
3. **Review API documentation** in individual model files
4. **Customize your drug database** in `data/drugs_database.csv`
5. **Train interaction model** with your own data

## Getting Help

- Check the README.md for documentation
- Look at demo.py for working examples
- Review individual model docstrings: `help(OCRModel)`, `help(DrugInteractionModel)`, etc.
- Check utils/config.py to customize settings

## Key Files Reference

```
pipeline.py              - Main processing pipeline
models/ocr_model.py      - Image text extraction
models/ner_model.py      - Medicine name extraction
models/correction_model.py - Spelling correction
models/drug_validation_model.py - Drug database lookup
models/drug_interaction_model.py - Interaction prediction

demo.py                  - Full demonstrations
examples.py              - Practical use cases
INSTALLATION.md          - Detailed setup
utils/config.py          - Configuration
utils/data_loader.py     - Data utilities
```

## Performance Tips

1. **Disable unused models**: Turn off models you don't need
2. **Use text input**: Skip OCR stage when text is already available
3. **Batch processing**: Process multiple prescriptions together
4. **Cache results**: Save validation results to avoid re-processing

## API Endpoints (If Using as Service)

```python
# Example: Using with Flask or FastAPI
from pipeline import PrescriptionProcessor

processor = PrescriptionProcessor()

@app.post("/process")
def process_prescription(text: str):
    result = processor.process_from_text(text)
    return result
```

---

**Ready to process prescriptions!** 🎉

Start with: `python demo.py`
