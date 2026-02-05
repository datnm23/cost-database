"""
Embedding Service for SBERT-based semantic embeddings.

Generates and manages embeddings for master work items using
the Vietnamese SBERT model (keepitreal/vietnamese-sbert).
"""

import logging
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any
import numpy as np

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.ai_config import load_model_cpu_optimized

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating and managing SBERT embeddings.

    Reuses the model loading pattern from classifier_service.py
    to share the SBERT model across services.
    """

    def __init__(self, model_name: str = None, cache_dir: str = None):
        """
        Initialize EmbeddingService.

        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory for caching model and embeddings
        """
        self.model_name = model_name or settings.MODEL_NAME
        self.cache_dir = Path(cache_dir or settings.MODEL_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.embeddings_file = self.cache_dir / 'master_embeddings.pkl'

        self.model: Optional[SentenceTransformer] = None
        self.embeddings: Optional[np.ndarray] = None
        self.id_to_index: Dict[int, int] = {}  # master_id -> embedding index
        self.index_to_id: Dict[int, int] = {}  # embedding index -> master_id
        self.description_to_index: Dict[str, int] = {}  # normalized_desc -> index

        self._model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load the SBERT model."""
        if not self._model_loaded:
            logger.info(f"Loading SBERT model: {self.model_name}")
            self.model = load_model_cpu_optimized(
                self.model_name,
                cache_folder=str(self.cache_dir)
            )
            self._model_loaded = True
            logger.info("SBERT model loaded successfully")

    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode
            show_progress: Whether to show progress bar

        Returns:
            Numpy array of embeddings (N x embedding_dim)
        """
        self._ensure_model_loaded()
        return self.model.encode(
            texts,
            show_progress_bar=show_progress,
            normalize_embeddings=True  # For cosine similarity with dot product
        )

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text to embedding.

        Args:
            text: Text to encode

        Returns:
            Embedding vector (embedding_dim,)
        """
        self._ensure_model_loaded()
        return self.model.encode(
            [text],
            normalize_embeddings=True
        )[0]

    def build_master_embeddings(
        self,
        master_items: List[Any],
        description_field: str = 'description_normalized'
    ) -> np.ndarray:
        """
        Build embeddings for all master items.

        Args:
            master_items: List of MasterWorkItem objects
            description_field: Field name for the description to embed

        Returns:
            Numpy array of embeddings
        """
        logger.info(f"Building embeddings for {len(master_items)} master items")

        descriptions = []
        self.id_to_index = {}
        self.index_to_id = {}
        self.description_to_index = {}

        for idx, item in enumerate(master_items):
            desc = getattr(item, description_field, None)
            if desc:
                desc_lower = desc.lower().strip()
                descriptions.append(desc_lower)
                self.id_to_index[item.master_id] = idx
                self.index_to_id[idx] = item.master_id
                self.description_to_index[desc_lower] = idx

        if not descriptions:
            logger.warning("No descriptions to embed")
            return np.array([])

        self.embeddings = self.encode(descriptions, show_progress=True)
        logger.info(f"Generated {len(self.embeddings)} embeddings of dimension {self.embeddings.shape[1]}")

        return self.embeddings

    def save_embeddings(self):
        """Save embeddings and mappings to disk."""
        if self.embeddings is None:
            logger.warning("No embeddings to save")
            return

        data = {
            'embeddings': self.embeddings,
            'id_to_index': self.id_to_index,
            'index_to_id': self.index_to_id,
            'description_to_index': self.description_to_index,
        }

        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Embeddings saved to {self.embeddings_file}")

    def load_embeddings(self) -> bool:
        """
        Load embeddings from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.embeddings_file.exists():
            logger.info("No saved embeddings found")
            return False

        try:
            with open(self.embeddings_file, 'rb') as f:
                data = pickle.load(f)

            self.embeddings = data['embeddings']
            self.id_to_index = data['id_to_index']
            self.index_to_id = data['index_to_id']
            self.description_to_index = data['description_to_index']

            logger.info(f"Loaded {len(self.embeddings)} embeddings from disk")
            return True

        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            return False

    def has_embeddings(self) -> bool:
        """Check if embeddings are available."""
        return self.embeddings is not None and len(self.embeddings) > 0

    def get_embedding_by_id(self, master_id: int) -> Optional[np.ndarray]:
        """Get embedding by master_id."""
        idx = self.id_to_index.get(master_id)
        if idx is not None and self.embeddings is not None:
            return self.embeddings[idx]
        return None

    def get_embedding_by_description(self, description: str) -> Optional[np.ndarray]:
        """Get embedding by normalized description."""
        desc_lower = description.lower().strip()
        idx = self.description_to_index.get(desc_lower)
        if idx is not None and self.embeddings is not None:
            return self.embeddings[idx]
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        return {
            'model_name': self.model_name,
            'model_loaded': self._model_loaded,
            'embeddings_count': len(self.embeddings) if self.embeddings is not None else 0,
            'embedding_dim': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'embeddings_file': str(self.embeddings_file),
            'embeddings_file_exists': self.embeddings_file.exists(),
        }


# Module-level singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
