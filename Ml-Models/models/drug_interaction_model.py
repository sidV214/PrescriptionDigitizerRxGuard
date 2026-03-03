"""
Model 5: Drug Interaction Prediction Model
Uses XGBoost, scikit-learn, pandas, and numpy for predicting harmful interactions
between multiple medicines
"""

import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path
from utils.config import INTERACTION_CONFIG

logger = logging.getLogger(__name__)


class DrugInteractionModel:
    """
    Predicts harmful interactions between multiple medicines
    """

    def __init__(self, model_path: Optional[str] = None, load_trained: bool = False):
        """
        Initialize drug interaction model
        
        Args:
            model_path: Path to save/load trained model
            load_trained: Whether to load a previously trained model
        """
        self.model_path = model_path or str(INTERACTION_CONFIG["model_path"])
        self.model = None
        self.label_encoders = {}
        self.risk_threshold = INTERACTION_CONFIG["risk_threshold"]
        self.interaction_database = self._load_interaction_database()
        
        if load_trained and Path(self.model_path).exists():
            self.load_model()
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize XGBoost model"""
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='binary:logistic',
            random_state=42,
            eval_metric='logloss'
        )
        logger.info("Initialized new XGBoost model")

    def _load_interaction_database(self) -> pd.DataFrame:
        """
        Load drug interaction database from CSV
        
        Returns:
            DataFrame with known drug interactions
        """
        try:
            df = pd.read_csv(INTERACTION_CONFIG["interactions_database"])
            logger.info(f"Loaded {len(df)} drug interactions from database")
            return df
        except Exception as e:
            logger.error(f"Failed to load interactions from {INTERACTION_CONFIG['interactions_database']}: {e}")
            return pd.DataFrame(columns=["drug1", "drug2", "interaction_type", "severity", "risk_score", "description", "mechanism"])

    def extract_interaction_features(self, drug1: str, drug2: str) -> np.ndarray:
        """
        Extract features for interaction prediction
        
        Args:
            drug1: First drug name
            drug2: Second drug name
            
        Returns:
            Numpy array of features
        """
        features = {
            "drug1_length": len(drug1),
            "drug2_length": len(drug2),
            "combined_length": len(drug1) + len(drug2),
            "drug1_vowels": sum(1 for c in drug1.lower() if c in "aeiou"),
            "drug2_vowels": sum(1 for c in drug2.lower() if c in "aeiou"),
            "name_similarity": self._calculate_string_similarity(drug1, drug2)
        }
        
        return np.array([list(features.values())])

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0-1)
        """
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def check_known_interaction(self, drug1: str, drug2: str) -> Optional[Dict]:
        """
        Check if interaction exists in database
        
        Args:
            drug1: First drug name
            drug2: Second drug name
            
        Returns:
            Dictionary with interaction info or None
        """
        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()
        
        # Check both directions
        interactions = self.interaction_database[
            ((self.interaction_database["drug1"].str.lower() == drug1_lower) &
             (self.interaction_database["drug2"].str.lower() == drug2_lower)) |
            ((self.interaction_database["drug1"].str.lower() == drug2_lower) &
             (self.interaction_database["drug2"].str.lower() == drug1_lower))
        ]
        
        if not interactions.empty:
            interaction = interactions.iloc[0]
            return {
                "drug1": drug1,
                "drug2": drug2,
                "severity": interaction["severity"],
                "risk_score": interaction["risk_score"],
                "description": interaction["description"],
                "mechanism": interaction.get("mechanism", "Unknown mechanism"),
                "interaction_type": interaction["interaction_type"],
                "source": "Database"
            }
        
        return None

    def predict_interaction(self, drug1: str, drug2: str) -> Optional[Dict]:
        """
        Check if two drugs interact strictly using database
        
        Args:
            drug1: First drug name
            drug2: Second drug name
            
        Returns:
            Dictionary with interaction information
        """
        logger.info(f"Checking interaction between {drug1} and {drug2}")
        
        # Check database first
        known_interaction = self.check_known_interaction(drug1, drug2)
        if known_interaction:
            known_interaction["has_interaction"] = True
            return known_interaction
        
        return None

    def predict_interactions_batch(self, medicines: List[str]) -> List[Dict]:
        """
        Predict all pairwise interactions between medicines
        
        Args:
            medicines: List of medicine names
            
        Returns:
            List of interaction predictions
        """
        logger.info(f"Predicting interactions for {len(medicines)} medicines")
        
        interactions = []
        unique_interactions = {}
        
        # Check all pairs
        for i in range(len(medicines)):
            for j in range(i + 1, len(medicines)):
                drugA = medicines[i]
                drugB = medicines[j]
                
                key = tuple(sorted([drugA.lower(), drugB.lower()]))
                if key in unique_interactions:
                    continue
                    
                interaction = self.predict_interaction(drugA, drugB)
                if interaction:
                    unique_interactions[key] = interaction
                    
        interactions = list(unique_interactions.values())
        
        # Phase 11: Sort by Severity and Risk Score
        severity_map = {"high": 3, "moderate": 2, "low": 1, "unknown": 0}
        interactions.sort(
            key=lambda x: (
                severity_map.get(x.get("severity", "unknown").lower(), 0), 
                x.get("risk_score", 0.0)
            ), 
            reverse=True
        )
        
        logger.info(f"Found {len([i for i in interactions if i.get('has_interaction')])} unique interactions")
        
        return interactions

    def predict_interactions_from_medicines(self, medicines: List[Dict]) -> Dict:
        """
        Predict interactions from extracted medicine list
        
        Args:
            medicines: List of medicine dictionaries
            
        Returns:
            Dictionary with interaction predictions
        """
        medicine_names = [m["name"] for m in medicines if "name" in m]
        
        interactions = self.predict_interactions_batch(medicine_names)
        
        # Filter significant interactions
        significant_interactions = [
            i for i in interactions 
            if i.get("has_interaction") or i.get("risk_score", 0) >= 0.5
        ]
        
        return {
            "total_medicines": len(medicine_names),
            "medicine_pairs_checked": len(interactions),
            "significant_interactions": significant_interactions,
            "interaction_count": len(interactions),
            "high_risk_count": len([i for i in interactions if i.get("severity") == "high"]),
            "moderate_risk_count": len([i for i in interactions if i.get("severity") == "moderate"]),
            "low_risk_count": len([i for i in interactions if i.get("severity") == "low"]),
        }

    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_test: Optional[np.ndarray] = None, 
                   y_test: Optional[np.ndarray] = None) -> Dict:
        """
        Train the XGBoost model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Optional test features
            y_test: Optional test labels
            
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training model with {len(X_train)} samples")
        
        self._initialize_model()
        
        if X_test is not None and y_test is not None:
            assert self.model is not None, "Model not initialized"
            self.model.fit(  # type: ignore
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                verbose=False
            )
        else:
            assert self.model is not None, "Model not initialized"
            self.model.fit(X_train, y_train, verbose=False)  # type: ignore
        
        # Calculate metrics
        assert self.model is not None, "Model not initialized"
        y_pred = self.model.predict(X_train)  # type: ignore
        
        metrics = {
            "accuracy": accuracy_score(y_train, y_pred),
            "precision": precision_score(y_train, y_pred, zero_division=0),
            "recall": recall_score(y_train, y_pred, zero_division=0),
            "f1": f1_score(y_train, y_pred, zero_division=0)
        }
        
        if X_test is not None and y_test is not None:
            assert self.model is not None, "Model not initialized"
            y_test_pred = self.model.predict(X_test)  # type: ignore
            metrics["test_accuracy"] = accuracy_score(y_test, y_test_pred)
            metrics["test_f1"] = f1_score(y_test, y_test_pred, zero_division=0)
        
        logger.info(f"Model trained. Metrics: {metrics}")
        
        return metrics

    def save_model(self) -> None:
        """Save trained model to disk"""
        try:
            Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to: {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")

    def load_model(self) -> None:
        """Load trained model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Model loaded from: {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")

    def get_interaction_summary(self, interactions: List[Dict]) -> Dict:
        """
        Get summary of interactions
        
        Args:
            interactions: List of interaction predictions
            
        Returns:
            Dictionary with summary statistics
        """
        df_interactions = pd.DataFrame(interactions)
        
        summary = {
            "total_interactions": len(interactions),
            "has_interactions": df_interactions["has_interaction"].sum() if "has_interaction" in df_interactions else 0,
            "high_risk": len([i for i in interactions if i.get("severity") == "high"]),
            "moderate_risk": len([i for i in interactions if i.get("severity") == "moderate"]),
            "low_risk": len([i for i in interactions if i.get("severity") == "low"]),
            "average_risk_score": df_interactions["risk_score"].mean() if "risk_score" in df_interactions else 0,
        }
        
        return summary


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    interaction_model = DrugInteractionModel()
    
    # Test single interaction
    result = interaction_model.predict_interaction("Aspirin", "Ibuprofen")
    print(f"Interaction prediction: {result}")
    
    # Test batch interactions
    medicines = ["Aspirin", "Ibuprofen", "Metformin"]
    interactions = interaction_model.predict_interactions_batch(medicines)
    print("\nBatch interactions:")
    for interaction in interactions:
        print(f"  {interaction['drug1']} + {interaction['drug2']}: {interaction['risk_score']:.2f}")
