from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sec_code import SECCode

logger = logging.getLogger(__name__)


class SECClassifier:
    """
    Machine Learning classifier for automatic SEC code classification
    Uses Vietnamese sentence transformers for semantic similarity
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.model = None
        self.sec_embeddings = None
        self.sec_codes = []
        self.sec_metadata = {}
        self.keywords_dict = {}
        self.model_path = Path(settings.MODEL_PATH)
        self.model_file = self.model_path / 'sec_classifier.pkl'
        
        # Create model directory if it doesn't exist
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self._load_or_initialize_model()
    
    def _load_or_initialize_model(self):
        """Load existing model or initialize a new one"""
        if self.model_file.exists():
            logger.info("Loading existing classifier model...")
            self.load_model()
        else:
            logger.info("Initializing new classifier model...")
            if self.db:
                self.initialize_model()
            else:
                logger.warning("No database session provided, classifier not fully initialized")
    
    def initialize_model(self):
        """
        Initialize the classification model with SEC codes from database
        """
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer(settings.MODEL_NAME)
        
        # Fetch SEC codes from database
        if not self.db:
            raise ValueError("Database session required for initialization")
        
        sec_codes = self.db.query(SECCode).filter(SECCode.is_active == True).all()
        
        if not sec_codes:
            logger.warning("No SEC codes found in database")
            return
        
        self.sec_codes = []
        sec_texts = []
        
        for sec in sec_codes:
            self.sec_codes.append(sec.sec_code)
            
            # Parse keywords from JSON
            keywords = []
            if sec.keywords:
                try:
                    keywords = json.loads(sec.keywords) if isinstance(sec.keywords, str) else sec.keywords
                except:
                    keywords = []
            
            # Create text representation for embedding
            text_parts = [
                sec.sec_name_vi or '',
                sec.sec_name_en or '',
                sec.description or '',
                ' '.join(keywords)
            ]
            text = ' '.join(filter(None, text_parts))
            sec_texts.append(text)
            
            # Store metadata
            self.sec_metadata[sec.sec_code] = {
                'name_vi': sec.sec_name_vi,
                'name_en': sec.sec_name_en,
                'level': sec.level,
                'parent_code': sec.parent_code
            }
            
            # Store keywords for rule-based matching
            self.keywords_dict[sec.sec_code] = set(kw.lower() for kw in keywords)
        
        logger.info(f"Generating embeddings for {len(sec_texts)} SEC codes...")
        self.sec_embeddings = self.model.encode(sec_texts, show_progress_bar=True)
        
        # Save model
        self.save_model()
        logger.info("Model initialized and saved successfully")
    
    def classify(
        self,
        description: str,
        top_k: int = 3,
        threshold: float = None
    ) -> List[Tuple[str, float]]:
        """
        Classify a description and return top-k SEC codes with confidence scores
        
        Args:
            description: Item description to classify
            top_k: Number of top results to return
            threshold: Minimum confidence threshold (0-100)
        
        Returns:
            List of tuples: [(sec_code, confidence_score), ...]
        """
        if threshold is None:
            threshold = settings.CLASSIFICATION_THRESHOLD * 100
        
        # Try rule-based matching first
        rule_result = self._rule_based_match(description)
        if rule_result:
            logger.debug(f"Rule-based match found: {rule_result}")
            return [(rule_result, 95.0)]
        
        # Fall back to ML-based classification
        if self.model is None or self.sec_embeddings is None:
            logger.warning("Model not initialized, cannot classify")
            return []
        
        # Generate embedding for description
        desc_embedding = self.model.encode([description])[0]
        
        # Calculate cosine similarity
        similarities = cosine_similarity([desc_embedding], self.sec_embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Format results
        results = []
        for idx in top_indices:
            sec_code = self.sec_codes[idx]
            confidence = float(similarities[idx] * 100)  # Convert to percentage
            
            if confidence >= threshold:
                results.append((sec_code, confidence))
        
        logger.debug(f"ML classification results: {results}")
        return results
    
    def classify_batch(
        self,
        descriptions: List[str],
        top_k: int = 1
    ) -> List[List[Tuple[str, float]]]:
        """
        Classify multiple descriptions in batch for better performance
        
        Args:
            descriptions: List of descriptions to classify
            top_k: Number of top results per description
        
        Returns:
            List of classification results for each description
        """
        results = []
        
        for desc in descriptions:
            result = self.classify(desc, top_k=top_k)
            results.append(result)
        
        return results
    
    def _rule_based_match(self, description: str) -> Optional[str]:
        """
        Perform rule-based keyword matching
        Returns SEC code if high-confidence match found, None otherwise
        """
        desc_lower = description.lower()
        
        # Check each SEC code's keywords
        for sec_code, keywords in self.keywords_dict.items():
            if not keywords:
                continue
            
            # If any keyword is found in description
            for keyword in keywords:
                if keyword and keyword in desc_lower:
                    logger.debug(f"Rule match: '{keyword}' in '{description}' -> {sec_code}")
                    return sec_code
        
        return None
    
    def get_sec_info(self, sec_code: str) -> Optional[Dict]:
        """Get metadata for a SEC code"""
        return self.sec_metadata.get(sec_code)
    
    def save_model(self):
        """Save model embeddings and metadata to disk"""
        model_data = {
            'sec_embeddings': self.sec_embeddings,
            'sec_codes': self.sec_codes,
            'sec_metadata': self.sec_metadata,
            'keywords_dict': {k: list(v) for k, v in self.keywords_dict.items()}
        }
        
        with open(self.model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {self.model_file}")
    
    def load_model(self):
        """Load model embeddings and metadata from disk"""
        if not self.model_file.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_file}")
        
        with open(self.model_file, 'rb') as f:
            model_data = pickle.load(f)
        
        self.sec_embeddings = model_data['sec_embeddings']
        self.sec_codes = model_data['sec_codes']
        self.sec_metadata = model_data['sec_metadata']
        self.keywords_dict = {k: set(v) for k, v in model_data['keywords_dict'].items()}
        
        # Load the sentence transformer model
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer(settings.MODEL_NAME)
        
        logger.info(f"Model loaded successfully: {len(self.sec_codes)} SEC codes")
    
    def retrain(self, db: Session):
        """Retrain the model with updated SEC codes"""
        self.db = db
        logger.info("Retraining classifier model...")
        self.initialize_model()
        return True
    
    def get_statistics(self) -> Dict:
        """Get classifier statistics"""
        return {
            'total_sec_codes': len(self.sec_codes),
            'model_loaded': self.model is not None,
            'embeddings_loaded': self.sec_embeddings is not None,
            'model_path': str(self.model_file),
            'model_exists': self.model_file.exists()
        }


# Global classifier instance (will be initialized in app startup)
_classifier_instance = None


def get_classifier(db: Session = None) -> SECClassifier:
    """
    Get or create global classifier instance
    """
    global _classifier_instance
    
    if _classifier_instance is None:
        _classifier_instance = SECClassifier(db=db)
    
    return _classifier_instance


def init_classifier(db: Session):
    """
    Initialize classifier at application startup
    """
    global _classifier_instance
    logger.info("Initializing SEC classifier...")
    _classifier_instance = SECClassifier(db=db)
    return _classifier_instance
