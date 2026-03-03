# Installation & Setup Guide

Complete installation and setup instructions for the Prescription Processing ML System.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment manager (venv, conda, or similar)
- 4GB+ RAM for model inference
- GPU support optional (CUDA for accelerated inference)

## Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Download spaCy model for NER
python -m spacy download en_core_sci_md

# Alternative if above doesn't work:
python -m spacy download en_core_web_sm
```

## Step 3: Verify Installation

```bash
# Test imports
python -c "from models import *; print('All modules imported successfully')"

# Run demo to verify everything works
python demo.py
```

## Installation Troubleshooting

### EasyOCR Issues
```bash
# If EasyOCR fails to download models:
pip install --upgrade easyocr

# Pre-download models:
python -c "import easyocr; reader = easyocr.Reader(['en'])"
```

### spaCy Model Download
```bash
# If spaCy model fails:
python -m spacy download en_core_web_md
python -m spacy download en_core_web_lg
```

### GPU Support (Optional)

For CUDA acceleration with GPU:

```bash
# Install PyTorch with CUDA support (adjust CUDA version as needed)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Update EasyOCR for GPU:
pip install --upgrade easyocr
```

### Mac M1/M2 Apple Silicon

```bash
# Use conda instead of pip (recommended)
conda create -n prescription python=3.10
conda activate prescription
conda install pytorch::pytorch torchvision -c pytorch
pip install -r requirements.txt
```

## Configuration

Edit `utils/config.py` to customize:
- OCR model settings (GPU enabled/disabled)
- Similarity thresholds for correction and validation
- Drug database paths
- Interaction risk thresholds

## Project Structure

```
prescription-ml/
├── models/                  # ML model implementations
│   ├── ocr_model.py        # Text extraction from images
│   ├── ner_model.py        # Medicine extraction
│   ├── correction_model.py  # Spelling correction
│   ├── drug_validation_model.py  # Drug validation
│   └── drug_interaction_model.py  # Interaction prediction
├── data/                    # Databases and data files
│   ├── drugs_database.csv   # Drug reference database
│   ├── drug_interactions.csv # Known interactions
│   └── sample_prescriptions/  # Sample images (optional)
├── utils/                   # Utility modules
│   ├── config.py           # Configuration
│   └── data_loader.py      # Data utilities
├── pipeline.py             # Main processing pipeline
├── demo.py                 # Complete demonstration
├── requirements.txt        # Python dependencies
└── README.md              # Documentation
```

## Usage

### Quick Start

```python
from pipeline import PrescriptionProcessor

# Initialize processor
processor = PrescriptionProcessor()

# Process from OCR text
result = processor.process_from_text("""
    Take Aspirin 500mg twice daily for 7 days.
    Also take Metformin 1000mg once daily for 30 days.
""")

# Get human-readable report
print(processor.generate_report(result))
```

### Process Image (Requires Image)

```python
# Process prescription image
result = processor.process_prescription_image('prescription.jpg')

# Export results
processor.export_results(result, 'results.json')
```

### Use Individual Models

```python
from models.ner_model import MedicineExtractionModel
from models.correction_model import MedicineCorrectionModel

# Extract medicines
ner = MedicineExtractionModel()
medicines = ner.extract_medicines(text)

# Correct spelling
corrector = MedicineCorrectionModel()
corrected = corrector.correct_extracted_medicines(medicines)
```

## Running Examples

```bash
# Run comprehensive demo
python demo.py

# Run individual model demo
python -c "from demo import demo_ner_model; demo_ner_model()"

# Run correction demo
python -c "from demo import demo_correction_model; demo_correction_model()"

# Run validation demo
python -c "from demo import demo_validation_model; demo_validation_model()"

# Run interaction demo
python -c "from demo import demo_interaction_model; demo_interaction_model()"
```

## API Reference

### PrescriptionProcessor

```python
# Initialize with selective models
processor = PrescriptionProcessor(
    enable_ocr=True,
    enable_ner=True,
    enable_correction=True,
    enable_validation=True,
    enable_interaction=True
)

# Process from image
result = processor.process_prescription_image('path/to/image.jpg')

# Process from text (OCR result)
result = processor.process_from_text('OCR extracted text...')

# Process multiple images
results = processor.batch_process_images(['img1.jpg', 'img2.jpg'])

# Generate report
report = processor.generate_report(result)

# Export to JSON
processor.export_results(result, 'output.json')
```

### Individual Models

#### OCRModel
```python
from models.ocr_model import OCRModel

ocr = OCRModel(use_easy_ocr=True, use_transformer_ocr=True)
result = ocr.extract_text('prescription.jpg')
print(result['extracted_text'])
```

#### MedicineExtractionModel (NER)
```python
from models.ner_model import MedicineExtractionModel

ner = MedicineExtractionModel()
result = ner.extract_medicines('Take Aspirin 500mg twice daily')
for med in result['medicines']:
    print(f"{med['name']}: {med['dosage']} {med['frequency']}")
```

#### MedicineCorrectionModel
```python
from models.correction_model import MedicineCorrectionModel

corrector = MedicineCorrectionModel()
result = corrector.correct_medicine_name('Asprinh')
print(f"Corrected: {result['corrected']}")
```

#### DrugValidationModel
```python
from models.drug_validation_model import DrugValidationModel

validator = DrugValidationModel()
result = validator.validate_medicine('Aspirin')
print(f"Valid: {result['valid']}")
```

#### DrugInteractionModel
```python
from models.drug_interaction_model import DrugInteractionModel

interactions = DrugInteractionModel()
result = interactions.predict_interaction('Aspirin', 'Ibuprofen')
print(f"Risk Score: {result['risk_score']:.2%}")
```

## Output Format

### Complete Pipeline Result

```json
{
  "image_path": "prescription.jpg",
  "timestamp": "2024-01-15T10:30:00",
  "final_result": {
    "medicines": [
      {
        "name": "Aspirin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "duration": "7 days",
        "is_valid": true,
        "spelling_corrected": false
      }
    ],
    "interactions": [
      {
        "drug1": "Aspirin",
        "drug2": "Ibuprofen",
        "risk_score": 0.85,
        "severity": "high",
        "description": "Increased risk of gastrointestinal bleeding"
      }
    ]
  }
}
```

## Performance Optimization

### Disable Unnecessary Models
```python
# Only use NER, skip OCR
processor = PrescriptionProcessor(
    enable_ocr=False,
    enable_ner=True,
    enable_correction=True,
    enable_validation=True,
    enable_interaction=False
)
```

### Use CPU for Faster Inference
```python
# In utils/config.py
OCR_CONFIG = {
    "gpu": False,  # Disable GPU
    ...
}
```

### Batch Processing
```python
# Process multiple images efficiently
results = processor.batch_process_images(image_list)
```

## Troubleshooting

### Out of Memory Error
- Reduce batch size
- Disable GPU in config
- Process images one at a time

### Model Download Issues
- Check internet connection
- Clear pip cache: `pip cache purge`
- Manually specify model paths in config

### Accuracy Issues
- Ensure high-quality prescription images
- Try different OCR methods
- Retrain interaction model with more data

## Next Steps

1. Add your own drug database in `data/drugs_database.csv`
2. Add more interaction patterns in `data/drug_interactions.csv`
3. Fine-tune NER model on prescription-specific data
4. Train interaction model on real interaction data
5. Integrate with your healthcare application

## Support & Contributing

For issues or contributions, please refer to the main README.md

## License

MIT License - See LICENSE file for details
