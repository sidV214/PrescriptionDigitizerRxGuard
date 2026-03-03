"""
Model 2: Medicine Extraction Model (NER - Named Entity Recognition)
Uses RapidFuzz and pandas for identifying and extracting medicine names, dosage, and duration from text
"""

import pandas as pd
import re
import logging
import os
from rapidfuzz import fuzz
from typing import Dict, List, Tuple, Optional
from utils.config import NER_CONFIG, VALIDATION_CONFIG

logger = logging.getLogger(__name__)


class MedicineExtractionModel:
    """
    Named Entity Recognition model for extracting medicines, dosages, and duration
    from prescription text
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize NER model
        """
        logger.info("Initializing Medicine Extraction model (SpaCy removed for performance)")
        self.debug_mode = os.environ.get("DEBUG_MODE", "False").lower() == "true"
        self._setup_custom_patterns()
        self._load_drug_database()
        
    def _load_drug_database(self):
        """Load drug names from database for fuzzy matching"""
        try:
            self.drug_names = set()
            df = pd.read_csv(VALIDATION_CONFIG["drugs_database"])
            for _, row in df.iterrows():
                if pd.notna(row.get('name')):
                    self.drug_names.add(str(row['name']).strip().lower())
                if pd.notna(row.get('generic_name')):
                    self.drug_names.add(str(row['generic_name']).strip().lower())
            logger.info(f"Loaded {len(self.drug_names)} drug names for extraction")
        except Exception as e:
            logger.error(f"Failed to load drug database: {str(e)}")
            self.drug_names = set()
    
    def _setup_custom_patterns(self):
        """Setup custom patterns for dosage and duration extraction"""
        self.dosage_pattern = r"(\d+(?:\.\d+)?)\s*(mg|g|ml|l|mcg|iu|units?|grams?|milligrams?|micrograms?)"
        self.duration_pattern = r"\b(\d+)\s*(days?|weeks?|months?|dav|da\s*y)\b"
        self.strict_duration_pattern = r"\bfor\s+(\d+)\s*(days?|dav|da\s*y)\b"
        self.frequency_pattern = r"\b(once|twice|thrice|daily|bd|tid|qid|every\s+\d+\s+hours?|morning|afternoon|evening|night|bedtime|hs|\d-\d-\d)\b"

    def _normalize_frequency(self, freq: str) -> str:
        f = freq.lower()
        if f == "1-0-1" or f == "bd" or f == "twice": return "twice daily"
        if f == "1-1-1" or f == "tid" or f == "thrice": return "thrice daily"
        if f == "0-1-0" or f == "once": return "once daily"
        if f == "0-0-1": return "once daily at night"
        return f
    
    def get_token_index(self, start: int, tokens: List[re.Match]) -> int:
        for i, t in enumerate(tokens):
            if t.start() <= start <= t.end() or start <= t.start():
                return i
        return -1

    def extract_dosages_with_tokens(self, text: str, tokens: List[re.Match]) -> List[Dict]:
        """Extract dosage information with mapped token indices"""
        dosages = []
        matches = re.finditer(self.dosage_pattern, text, re.IGNORECASE)
        for match in matches:
            amount_val = float(match.group(1))
            if amount_val.is_integer():
                amount_val = int(amount_val)
                
            token_idx = self.get_token_index(match.start(), tokens)
                
            dosages.append({
                "amount": amount_val,
                "unit": match.group(2).lower(),
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "token_index": token_idx
            })
        return dosages
    
    def extract_duration(self, text: str) -> List[Dict]:
        """Extract duration information from text"""
        durations = []
        matches = re.finditer(self.duration_pattern, text, re.IGNORECASE)
        for match in matches:
            unit = match.group(2).lower()
            if unit in ["day", "days", "dav", "da y", "da y "]:
                unit = "days"
            elif unit in ["week", "weeks"]:
                unit = "weeks"
            elif unit in ["month", "months"]:
                unit = "months"
                
            durations.append({
                "quantity": int(match.group(1)),
                "unit": unit,
                "text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        return durations

    def extract_strict_duration(self, text: str) -> List[Dict]:
        durations = []
        matches = re.finditer(self.strict_duration_pattern, text, re.IGNORECASE)
        for match in matches:
            durations.append({
                "quantity": int(match.group(1)),
                "unit": "days",
                "text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        return durations
    
    def extract_frequency(self, text: str) -> List[Dict]:
        """Extract medication frequency from text"""
        frequencies = []
        matches = re.finditer(self.frequency_pattern, text, re.IGNORECASE)
        for match in matches:
            frequencies.append({
                "text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        return frequencies
    
    def extract_medicines(self, text: str) -> Dict:
        """
        Extract complete medicine information from prescription text utilizing strict OCR line bounds
        and minimal token-index distances for robustness
        """
        logger.info("Extracting medicine information using DB matching & OCR boundaries...")
        
        if not text or not isinstance(text, str):
            logger.warning("Invalid or empty text provided")
            return {"medicines": [], "total_medicines": 0, "source": "Database matching"}
            
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        medicines = []
        
        for line_idx, line in enumerate(lines):
            tokens = list(re.finditer(r'\S+', line))
            
            # Phase 2 Rules / Line state evaluation
            has_for = bool(re.search(r'\bfor\b', line, re.IGNORECASE))
            has_duration_phrase = bool(re.search(self.duration_pattern, line, re.IGNORECASE))
            
            # Rule Phase 1.2: Ignore dosage tokens that appear on lines containing duration phrases or 'for'
            allow_dosage = not (has_for or has_duration_phrase)
                
            dosages = []
            if allow_dosage:
                dosages = self.extract_dosages_with_tokens(line, tokens)
                
            # Phase 2: strictly evaluate duration if it has 'for'
            durations = []
            if has_for:
                durations = self.extract_strict_duration(line)
            else:
                durations = self.extract_duration(line)
                
            frequencies = self.extract_frequency(line)
            
            words = list(re.finditer(r'\b[a-zA-Z]{3,}\b', line))
            candidates = []
            
            for w in words:
                candidates.append({"text": w.group(0), "start": w.start(), "end": w.end()})
            for i in range(len(words) - 1):
                if words[i+1].start() - words[i].end() <= 2:
                    text_2gram = line[words[i].start():words[i+1].end()]
                    candidates.append({"text": text_2gram, "start": words[i].start(), "end": words[i+1].end()})
                    
            candidates.sort(key=lambda c: len(c["text"]), reverse=True)
            
            line_seen = set()
            for cand in candidates:
                overlap = False
                for p in line_seen:
                    if (cand["start"] >= p[0] and cand["start"] < p[1]) or (cand["end"] > p[0] and cand["end"] <= p[1]):
                        overlap = True
                        break
                if overlap:
                    continue
                    
                token_lower = cand["text"].lower()
                best_match = None
                best_score = 0
                
                for drug in self.drug_names:
                    score = fuzz.ratio(token_lower, drug)
                    if score > best_score:
                        best_score = score
                        best_match = drug
                        
                if best_match and best_score >= 80:
                    if getattr(self, "debug_mode", False):
                        logger.info(f"Matched token '{cand['text']}' to '{best_match.capitalize()}' (Score: {best_score:.1f})")
                    line_seen.add((cand["start"], cand["end"]))
                    
                    med_token_idx = self.get_token_index(cand["start"], tokens)
                    
                    medicine = {
                        "name": best_match.capitalize(),
                        "matched_from": cand["text"],
                        "fuzzy_score": best_score,
                        "position": cand["start"],
                        "dosage": None,
                        "duration": None,
                        "frequency": None
                    }
                    
                    # Phase 1 & 3: Token Validation (nearest token window)
                    valid_dosages = []
                    for d in dosages:
                        dist = abs(d["token_index"] - med_token_idx)
                        if dist <= 3:
                            valid_dosages.append((dist, d))
                            
                    if valid_dosages:
                        valid_dosages.sort(key=lambda x: x[0])
                        closest_dosage = valid_dosages[0][1]
                        medicine["dosage"] = f"{closest_dosage['amount']}{closest_dosage['unit']}"
                        
                    if durations:
                        medicine["duration"] = f"{durations[0]['quantity']} {durations[0]['unit']}"
                        
                    if frequencies:
                        medicine["frequency"] = self._normalize_frequency(frequencies[0]["text"])
                        
                    medicines.append(medicine)

        result = {
            "medicines": medicines,
            "total_medicines": len(medicines),
            "source": "Database Fuzzy Matching"
        }
        
        if getattr(self, "debug_mode", False):
            logger.info(f"Extracted {len(medicines)} medicines")
        return result
    
    def create_medicine_dataframe(self, medicines: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(medicines)
        return df
    
    def extract_from_multiple_prescriptions(self, texts: List[str]) -> Dict:
        logger.info(f"Processing {len(texts)} prescriptions...")
        
        all_medicines = []
        all_results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.extract_medicines(text)
                result["prescription_id"] = i
                all_results.append(result)
                all_medicines.extend([(m, i) for m in result["medicines"]])
            except Exception as e:
                logger.error(f"Error processing prescription {i}: {str(e)}")
        
        if all_medicines:
            medicines_list = [{"prescription_id": pid, **medicine} 
                            for medicine, pid in all_medicines]
            df_medicines = pd.DataFrame(medicines_list)
        else:
            df_medicines = pd.DataFrame()
        
        return {
            "total_prescriptions": len(texts),
            "total_medicines": len(all_medicines),
            "results": all_results,
            "medicines_dataframe": df_medicines
        }
