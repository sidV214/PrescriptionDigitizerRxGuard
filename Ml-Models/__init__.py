"""
Package initialization for prescription processing models
"""

from models.ocr_model import OCRModel
from models.ner_model import MedicineExtractionModel
from models.correction_model import MedicineCorrectionModel
from models.drug_validation_model import DrugValidationModel
from models.drug_interaction_model import DrugInteractionModel
from pipeline import PrescriptionProcessor

__version__ = "1.0.0"
__author__ = "Prescription Processing Team"

__all__ = [
    'OCRModel',
    'MedicineExtractionModel',
    'MedicineCorrectionModel',
    'DrugValidationModel',
    'DrugInteractionModel',
    'PrescriptionProcessor'
]
