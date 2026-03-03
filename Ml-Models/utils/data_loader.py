"""
Data loading utilities for the prescription processing system
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def load_drug_database(database_path: str) -> pd.DataFrame:
    """
    Load drug database from CSV
    
    Args:
        database_path: Path to drug database CSV
        
    Returns:
        Pandas DataFrame with drug information
    """
    try:
        df = pd.read_csv(database_path)
        logger.info(f"Loaded {len(df)} drugs from database")
        return df
    except Exception as e:
        logger.error(f"Error loading drug database: {str(e)}")
        return pd.DataFrame()


def load_interaction_database(database_path: str) -> pd.DataFrame:
    """
    Load drug interactions database from CSV
    
    Args:
        database_path: Path to interactions database CSV
        
    Returns:
        Pandas DataFrame with interaction information
    """
    try:
        df = pd.read_csv(database_path)
        logger.info(f"Loaded {len(df)} drug interactions")
        return df
    except Exception as e:
        logger.error(f"Error loading interaction database: {str(e)}")
        return pd.DataFrame()


def get_image_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """
    Get all image files from directory
    
    Args:
        directory: Path to directory
        extensions: List of file extensions to look for
        
    Returns:
        List of image file paths
    """
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    image_files = []
    path = Path(directory)
    
    for ext in extensions:
        image_files.extend(path.glob(f'*{ext}'))
        image_files.extend(path.glob(f'*{ext.upper()}'))
    
    return sorted([str(f) for f in image_files])


def create_sample_prescription_data() -> Dict:
    """
    Create sample prescription data for testing
    
    Returns:
        Dictionary with sample prescription data
    """
    return {
        "patient_id": "P12345",
        "date": "2024-01-15",
        "doctor": "Dr. Smith",
        "medications": [
            {
                "name": "Aspirin",
                "dosage": "500mg",
                "frequency": "twice daily",
                "duration": "7 days"
            },
            {
                "name": "Metformin",
                "dosage": "1000mg",
                "frequency": "once daily",
                "duration": "30 days"
            },
            {
                "name": "Ibuprofen",
                "dosage": "400mg",
                "frequency": "three times daily",
                "duration": "as needed"
            }
        ]
    }


def save_results_to_csv(results: Dict, output_path: str) -> None:
    """
    Save processing results to CSV files
    
    Args:
        results: Dictionary with processing results
        output_path: Base path for output files
    """
    try:
        base_path = Path(output_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Save medicines
        if "medicines" in results.get("final_result", {}):
            df_medicines = pd.DataFrame(results["final_result"]["medicines"])
            df_medicines.to_csv(base_path / "medicines.csv", index=False)
            logger.info(f"Medicines saved to {base_path / 'medicines.csv'}")
        
        # Save interactions
        if "interactions" in results.get("final_result", {}):
            df_interactions = pd.DataFrame(results["final_result"]["interactions"])
            df_interactions.to_csv(base_path / "interactions.csv", index=False)
            logger.info(f"Interactions saved to {base_path / 'interactions.csv'}")
        
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
