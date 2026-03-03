"""
Model 4: Drug Validation Model
Uses pandas and CSV drug database for verifying whether extracted medicines are valid
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from pathlib import Path
from utils.config import VALIDATION_CONFIG

logger = logging.getLogger(__name__)


class DrugValidationModel:
    """
    Validates extracted medicines against a drug database
    """

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize drug validation model
        
        Args:
            database_path: Path to drug database CSV file
        """
        self.database_path = database_path or str(VALIDATION_CONFIG["drugs_database"])
        self.drug_database = None
        self.similarity_threshold = VALIDATION_CONFIG["similarity_threshold"]
        
        self._load_database()

    def _load_database(self) -> None:
        """Load drug database from CSV"""
        try:
            if Path(self.database_path).exists():
                logger.info(f"Loading drug database from: {self.database_path}")
                self.drug_database = pd.read_csv(self.database_path)
            else:
                logger.warning(f"Database file not found: {self.database_path}. Using default database.")
                self.drug_database = self._create_default_database()
        except Exception as e:
            logger.error(f"Error loading database: {str(e)}. Using default database.")
            self.drug_database = self._create_default_database()

    def _create_default_database(self) -> pd.DataFrame:
        """
        Create a default drug database
        
        Returns:
            DataFrame with drug information
        """
        drugs_data = [
            {
                "drug_id": 1,
                "name": "Aspirin",
                "generic_name": "Acetylsalicylic acid",
                "category": "Analgesic / Antipyretic",
                "strength": ["100mg", "325mg", "500mg", "650mg"],
                "approved": True,
                "side_effects": "Stomach upset, bruising",
            },
            {
                "drug_id": 2,
                "name": "Metformin",
                "generic_name": "Metformin Hydrochloride",
                "category": "Antidiabetic",
                "strength": ["500mg", "850mg", "1000mg"],
                "approved": True,
                "side_effects": "Lactic acidosis, GI distress",
            },
            {
                "drug_id": 3,
                "name": "Lisinopril",
                "generic_name": "Lisinopril",
                "category": "ACE Inhibitor",
                "strength": ["5mg", "10mg", "20mg", "40mg"],
                "approved": True,
                "side_effects": "Dry cough, dizziness",
            },
            {
                "drug_id": 4,
                "name": "Atorvastatin",
                "generic_name": "Atorvastatin Calcium",
                "category": "Statin",
                "strength": ["10mg", "20mg", "40mg", "80mg"],
                "approved": True,
                "side_effects": "Muscle pain, liver damage",
            },
            {
                "drug_id": 5,
                "name": "Ibuprofen",
                "generic_name": "Ibuprofen",
                "category": "NSAID",
                "strength": ["200mg", "400mg", "600mg", "800mg"],
                "approved": True,
                "side_effects": "Stomach upset, kidney problems",
            },
            {
                "drug_id": 6,
                "name": "Amoxicillin",
                "generic_name": "Amoxicillin",
                "category": "Antibiotic",
                "strength": ["250mg", "500mg", "875mg"],
                "approved": True,
                "side_effects": "Rash, allergic reaction",
            },
            {
                "drug_id": 7,
                "name": "Omeprazole",
                "generic_name": "Omeprazole",
                "category": "Proton Pump Inhibitor",
                "strength": ["10mg", "20mg", "40mg"],
                "approved": True,
                "side_effects": "Headache, diarrhea",
            },
            {
                "drug_id": 8,
                "name": "Levothyroxine",
                "generic_name": "Levothyroxine Sodium",
                "category": "Thyroid Hormone",
                "strength": ["25mcg", "50mcg", "75mcg", "100mcg", "125mcg"],
                "approved": True,
                "side_effects": "Palpitations, anxiety",
            },
        ]
        return pd.DataFrame(drugs_data)

    def validate_medicine(self, medicine_name: str) -> Dict:
        """
        Validate if a medicine exists in the database
        
        Args:
            medicine_name: Name of medicine to validate
            
        Returns:
            Dictionary with validation result
        """
        logger.info(f"Validating medicine: {medicine_name}")
        
        if not medicine_name or not isinstance(medicine_name, str):
            return {
                "medicine": medicine_name,
                "valid": False,
                "found": False,
                "confidence": 0,
                "database_match": None
            }
        
        # Case-insensitive exact match
        assert self.drug_database is not None, "Drug database not loaded"
        exact_matches = self.drug_database[
            self.drug_database["name"].str.lower() == medicine_name.lower()
        ]
        
        if not exact_matches.empty:
            match = exact_matches.iloc[0]
            return {
                "medicine": medicine_name,
                "valid": match.get("approved", True),
                "found": True,
                "confidence": 1.0,
                "database_match": {
                    "drug_id": match.get("drug_id"),
                    "name": match.get("name"),
                    "generic_name": match.get("generic_name"),
                    "category": match.get("category"),
                    "approved": match.get("approved", True),
                    "side_effects": match.get("side_effects", "N/A"),
                    "common_dosages": match.get("common_dosages", match.get("strength", ""))
                },
                "match_type": "Exact"
            }
        
        # Fuzzy match as fallback
        from rapidfuzz import fuzz, process
        
        assert self.drug_database is not None, "Drug database not loaded"
        matches = process.extract(
            medicine_name,
            self.drug_database["name"].tolist(),
            scorer=fuzz.token_set_ratio,
            limit=1
        )
        
        if matches:
            best_match_name, score, _ = matches[0]
            score_normalized = score / 100.0
            
            if score_normalized >= self.similarity_threshold:
                assert self.drug_database is not None, "Drug database not loaded"
                match_row = self.drug_database[
                    self.drug_database["name"] == best_match_name
                ].iloc[0]
                
                return {
                    "medicine": medicine_name,
                    "valid": match_row.get("approved", True),
                    "found": True,
                    "confidence": score_normalized,
                    "database_match": {
                        "drug_id": match_row.get("drug_id"),
                        "name": match_row.get("name"),
                        "generic_name": match_row.get("generic_name"),
                        "category": match_row.get("category"),
                        "approved": match_row.get("approved", True),
                        "side_effects": match_row.get("side_effects", "N/A"),
                        "common_dosages": match_row.get("common_dosages", match_row.get("strength", ""))
                    },
                    "match_type": "Fuzzy"
                }
        
        return {
            "medicine": medicine_name,
            "valid": False,
            "found": False,
            "confidence": 0,
            "database_match": None,
            "match_type": "Not found"
        }

    def validate_medicines_batch(self, medicine_names: List[str]) -> pd.DataFrame:
        """
        Validate multiple medicines
        
        Args:
            medicine_names: List of medicine names
            
        Returns:
            DataFrame with validation results
        """
        logger.info(f"Validating {len(medicine_names)} medicines...")
        
        validations = []
        for medicine_name in medicine_names:
            validation = self.validate_medicine(medicine_name)
            validations.append(validation)
        
        df_validations = pd.DataFrame(validations)
        
        valid_count = df_validations["valid"].sum()
        found_count = df_validations["found"].sum()
        
        logger.info(f"Validation complete: {valid_count} valid, {found_count} found")
        
        return df_validations

    def validate_extracted_medicines(self, medicines: List[Dict]) -> List[Dict]:
        """
        Validate extracted medicine list
        
        Args:
            medicines: List of extracted medicine dictionaries
            
        Returns:
            List of medicines with validation info
        """
        logger.info(f"Validating {len(medicines)} extracted medicines...")
        
        validated_medicines = []
        
        for medicine in medicines:
            if "name" in medicine:
                validation = self.validate_medicine(medicine["name"])
                
                validated_medicine = medicine.copy()
                validated_medicine["is_valid"] = validation["valid"]
                validated_medicine["found_in_database"] = validation["found"]
                validated_medicine["validation_confidence"] = validation["confidence"]
                validated_medicine["database_info"] = validation["database_match"]
                
                # Phase 9: Dosage validation
                if validation["found"] and medicine.get("dosage"):
                    db_match = validation["database_match"]
                    allowed = db_match.get("common_dosages", "") or db_match.get("strength", [])
                    if isinstance(allowed, str):
                        allowed = [d.strip().lower() for d in allowed.split(",")]
                    elif isinstance(allowed, list):
                        allowed = [d.lower() for d in allowed]
                    
                    if allowed and medicine["dosage"].lower() not in allowed:
                        validated_medicine["dosage_warning"] = "Unusual dosage detected"
                
                validated_medicines.append(validated_medicine)
            else:
                validated_medicines.append(medicine)
        
        return validated_medicines

    def get_validation_statistics(self, medicines: pd.DataFrame) -> Dict:
        """
        Get statistics about validations
        
        Args:
            medicines: DataFrame with validation results
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_medicines": len(medicines),
            "valid": medicines["valid"].sum(),
            "invalid": (~medicines["valid"]).sum(),
            "found": medicines["found"].sum(),
            "not_found": (~medicines["found"]).sum(),
            "average_confidence": medicines["confidence"].mean(),
            "validation_rate": medicines["found"].sum() / len(medicines) if len(medicines) > 0 else 0
        }
        
        logger.info(f"Validation Statistics: {stats}")
        
        return stats

    def get_drug_details(self, medicine_name: str) -> Dict:
        """
        Get detailed information about a drug
        
        Args:
            medicine_name: Name of medicine
            
        Returns:
            Dictionary with drug details
        """
        validation = self.validate_medicine(medicine_name)
        
        return {
            "validation": validation,
            "details": validation.get("database_match", {})
        }

    def get_drugs_by_category(self, category: str) -> pd.DataFrame:
        """
        Get all drugs in a specific category
        
        Args:
            category: Drug category
            
        Returns:
            DataFrame of drugs in category
        """
        assert self.drug_database is not None, "Drug database not loaded"
        return self.drug_database[
            self.drug_database["category"].str.lower().str.contains(category.lower(), na=False)
        ]

    def export_validations(self, medicines: pd.DataFrame, output_path: str) -> None:
        """
        Export validation results to CSV
        
        Args:
            medicines: DataFrame with validations
            output_path: Path to save CSV
        """
        try:
            medicines.to_csv(output_path, index=False)
            logger.info(f"Validations exported to: {output_path}")
        except Exception as e:
            logger.error(f"Error exporting validations: {str(e)}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    validator = DrugValidationModel()
    
    # Test single validation
    result = validator.validate_medicine("Aspirin")
    print(f"Validation result: {result}")
    
    # Test batch validation
    medicines = ["Aspirin", "Unknown Drug", "Metformin", "Fake Medicine"]
    df_validations = validator.validate_medicines_batch(medicines)
    print("\nBatch Validations:")
    print(df_validations)
    
    # Get statistics
    stats = validator.get_validation_statistics(df_validations)
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
