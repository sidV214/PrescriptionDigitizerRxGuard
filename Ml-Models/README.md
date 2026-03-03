# Prescription Processing ML System

A comprehensive machine learning system for processing handwritten prescription images with models for OCR, medicine extraction, spelling correction, drug validation, and drug interaction prediction.

## Project Structure

```
prescription-ml/
├── models/
│   ├── ocr_model.py              # Model 1: Text extraction from images
│   ├── ner_model.py              # Model 2: Medicine extraction (NER)
│   ├── correction_model.py        # Model 3: Spelling correction
│   ├── drug_validation_model.py   # Model 4: Drug validation
│   └── drug_interaction_model.py  # Model 5: Drug interaction prediction
├── data/
│   ├── drugs_database.csv         # Drug database for validation
│   ├── drug_interactions.csv      # Drug interactions reference data
│   └── sample_prescriptions/      # Sample prescription images
├── utils/
│   ├── config.py                  # Configuration settings
│   └── data_loader.py             # Data loading utilities
├── pipeline.py                    # Main pipeline orchestrator
├── requirements.txt               # Python dependencies
└── README.md                      # Documentation
```

## Models Overview

### 1. OCR Model (Optical Character Recognition)
- Extracts text from handwritten prescription images
- Uses EasyOCR for primary OCR and TrOCR for transformer-based recognition
- Employs OpenCV for image preprocessing
- Built with Pillow for image handling

### 2. NER Model (Named Entity Recognition)
- Identifies medicine names, dosages, and duration
- Uses spaCy for NLP processing
- Extracts structured entities from OCR text

### 3. Medicine Correction Model
- Corrects OCR spelling errors
- Uses RapidFuzz for fuzzy string matching
- Matches against a medicine database

### 4. Drug Validation Model
- Validates extracted medicines against a drug database
- Uses CSV-based drug reference data
- Confirms medicines exist in real datasets

### 5. Drug Interaction Prediction Model
- Predicts harmful interactions between medicines
- Uses XGBoost for classification
- Trained on medicine interaction patterns
- Provides risk scoring

## Installation

```bash
cd prescription-ml
pip install -r requirements.txt
python -m spacy download en_core_sci_md
```

## Usage

```python
from pipeline import PrescriptionProcessor

processor = PrescriptionProcessor()
result = processor.process_prescription('prescription_image.jpg')
print(result)
```

## Output Format

```json
{
  "extracted_text": "...",
  "medicines": [
    {
      "name": "Aspirin",
      "dosage": "500mg",
      "duration": "7 days",
      "corrected": true,
      "valid": true
    }
  ],
  "interactions": [
    {
      "medicine_pair": ["Aspirin", "Ibuprofen"],
      "risk_level": "high",
      "severity_score": 0.85,
      "warning": "..."
    }
  ]
}
```

## License

MIT
