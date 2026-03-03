"""
Configuration settings for the prescription processing system
"""

import os
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent  # Go up from utils to root
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

# Model configurations
OCR_CONFIG = {
    "languages": ["en"],
    "gpu": False,
    "model_storage_directory": os.path.expanduser("~/.EasyOCR/model"),
}

TRANSFORMER_OCR_CONFIG = {
    "model_name": "microsoft/trocr-base-handwritten",
    "device": "cpu",
}

NER_CONFIG = {
    "model_name": "en_core_sci_md",
    "entity_types": ["MEDICINE", "DOSAGE", "DURATION"],
}

CORRECTION_CONFIG = {
    "similarity_threshold": 0.8,
    "max_distance": 2,
}

VALIDATION_CONFIG = {
    "drugs_database": str(DATA_DIR / "drugs_database.csv"),
    "similarity_threshold": 0.85,
}

INTERACTION_CONFIG = {
    "model_path": str(MODELS_DIR / "drug_interaction_model.pkl"),
    "risk_threshold": 0.5,
    "interactions_database": str(DATA_DIR / "drug_interactions.csv"),
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
