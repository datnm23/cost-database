"""
BOQ Processing Service - Implement new processing flow:

Upload BOQ mới
    ↓
Extract tất cả công tác (1000 items)
    ↓
Lọc trùng tên gốc GIỐNG HỆT (tối ưu)
    ↓
Chuẩn hóa toàn bộ
    ↓
So khớp với Master
    ├─ Exact match (≥95%) → Gán mã có sẵn
    ├─ Fuzzy match (80-95%) → Review
    └─ No match (<80%) → Công tác mới
    ↓
Lọc trùng trong công tác mới
    ↓
Thêm vào Master với mã mới
"""
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.line_item import LineItem
from app.models.master_work_item import MasterWorkItem
from app.services.description_normalizer import DescriptionNormalizer
from app.services.work_code_generator import WorkCodeGenerator

logger = logging.getLogger(__name__)


# Threshold constants
EXACT_MATCH_THRESHOLD = 0.95  # ≥95% → Tự động gán mã
FUZZY_MATCH_THRESHOLD = 0.80  # 80-95% → Review
# <80% → Công tác mới


@dataclass
class MatchResult:
    """Result of matching a work item against master database"""
    original_description: str
    normalized_description: str
    match_type: str  # 'exact', 'fuzzy', 'new'
    similarity_score: float
    master_item: Optional[MasterWorkItem] = None
    master_work_code: Optional[str] = None
    needs_review: bool = False
    suggested_matches: List[Dict] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """Result of processing a BOQ file"""
    total_extracted: int
    unique_raw: int  # After raw dedup
    unique_normalized: int  # After normalization dedup
    exact_matches: int
    fuzzy_matches: int
    new_items: int
    items: List[MatchResult] = field(default_factory=list)
    new_items_deduped: int = 0  # New items after internal dedup


class BOQProcessingService:
    """
    Service xử lý BOQ theo flow mới với fuzzy matching
    """

    def __init__(self, db: Session):
        self.db = db
        self.normalizer = DescriptionNormalizer()
        self.code_generator = WorkCodeGenerator(db)

    def process_boq_items(
        self,
        file_id: int,
        items: List[Dict],
        auto_add_to_master: bool = False
    ) -> ProcessingResult:
        """
        Xử lý danh sách công tác từ BOQ file

        Args:
            file_id: ID của BOQ file
            items: List of dicts with 'description', 'unit', 'quantity', 'unit_price'
            auto_add_to_master: Tự động thêm công tác mới vào master

        Returns:
            ProcessingResult với thống kê và chi tiết
        """
        logger.info(f"Processing {len(items)} items from file {file_id}")

        # Step 1: Extract descriptions
        descriptions = [item.get('description', '') for item in items if item.get('description')]
        total_extracted = len(descriptions)
        logger.info(f"Step 1: Extracted {total_extracted} descriptions")

        # Step 2: Dedupe raw (tên gốc giống hệt)
        unique_raw = self._dedupe_raw(descriptions)
        logger.info(f"Step 2: Deduped raw: {total_extracted} → {len(unique_raw)} unique")

        # Step 3: Normalize all
        normalized_items = self._normalize_all(unique_raw)
        logger.info(f"Step 3: Normalized {len(normalized_items)} items")

        # Step 4: Match against master
        match_results = self._match_with_master(normalized_items)

        # Count results
        exact_matches = [r for r in match_results if r.match_type == 'exact']
        fuzzy_matches = [r for r in match_results if r.match_type == 'fuzzy']
        new_items = [r for r in match_results if r.match_type == 'new']

        logger.info(f"Step 4: Matching results - Exact: {len(exact_matches)}, Fuzzy: {len(fuzzy_matches)}, New: {len(new_items)}")

        # Step 5: Dedupe new items (by normalized name)
        unique_new_items = self._dedupe_new_items(new_items)
        new_items_deduped = len(unique_new_items)
        logger.info(f"Step 5: Deduped new items: {len(new_items)} → {new_items_deduped}")

        # Step 6: Add to master if requested
        if auto_add_to_master and unique_new_items:
            self._add_to_master(file_id, unique_new_items)
            logger.info(f"Step 6: Added {len(unique_new_items)} new items to master")

        return ProcessingResult(
            total_extracted=total_extracted,
            unique_raw=len(unique_raw),
            unique_normalized=len(normalized_items),
            exact_matches=len(exact_matches),
            fuzzy_matches=len(fuzzy_matches),
            new_items=len(new_items),
            new_items_deduped=new_items_deduped,
            items=match_results
        )

    def _dedupe_raw(self, descriptions: List[str]) -> List[str]:
        """
        Lọc trùng tên gốc GIỐNG HỆT
        Giữ nguyên thứ tự xuất hiện đầu tiên
        """
        seen = set()
        unique = []
        for desc in descriptions:
            desc_stripped = desc.strip()
            if desc_stripped and desc_stripped not in seen:
                seen.add(desc_stripped)
                unique.append(desc_stripped)
        return unique

    def _normalize_all(self, descriptions: List[str]) -> List[Tuple[str, str]]:
        """
        Chuẩn hóa toàn bộ descriptions

        Returns:
            List of (original, normalized) tuples
        """
        normalized = []
        seen_normalized = set()

        for desc in descriptions:
            try:
                norm = self.normalizer.normalize(desc)
                norm_lower = norm.lower().strip()

                # Dedupe by normalized form
                if norm_lower not in seen_normalized:
                    seen_normalized.add(norm_lower)
                    normalized.append((desc, norm))
            except Exception as e:
                logger.warning(f"Failed to normalize '{desc[:50]}...': {e}")
                # Keep original
                desc_lower = desc.lower().strip()
                if desc_lower not in seen_normalized:
                    seen_normalized.add(desc_lower)
                    normalized.append((desc, desc))

        return normalized

    def _match_with_master(self, items: List[Tuple[str, str]]) -> List[MatchResult]:
        """
        So khớp với Master database

        Args:
            items: List of (original, normalized) tuples

        Returns:
            List of MatchResult
        """
        results = []

        # Load all master items for matching
        master_items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()

        # Build lookup dict
        master_lookup = {
            m.description_normalized.lower(): m for m in master_items
            if m.description_normalized
        }
        master_descriptions = list(master_lookup.keys())

        for original, normalized in items:
            norm_lower = normalized.lower().strip()

            # Check exact match first
            if norm_lower in master_lookup:
                master = master_lookup[norm_lower]
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='exact',
                    similarity_score=1.0,
                    master_item=master,
                    master_work_code=master.work_code,
                    needs_review=False
                ))
                continue

            # Fuzzy match
            best_match, best_score, top_matches = self._find_best_match(
                norm_lower, master_descriptions, master_lookup
            )

            if best_score >= EXACT_MATCH_THRESHOLD:
                # High similarity - treat as exact
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='exact',
                    similarity_score=best_score,
                    master_item=best_match,
                    master_work_code=best_match.work_code if best_match else None,
                    needs_review=False
                ))
            elif best_score >= FUZZY_MATCH_THRESHOLD:
                # Fuzzy match - needs review
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='fuzzy',
                    similarity_score=best_score,
                    master_item=best_match,
                    master_work_code=best_match.work_code if best_match else None,
                    needs_review=True,
                    suggested_matches=top_matches
                ))
            else:
                # New item
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='new',
                    similarity_score=best_score,
                    needs_review=False,
                    suggested_matches=top_matches[:3] if top_matches else []
                ))

        return results

    def _find_best_match(
        self,
        description: str,
        master_descriptions: List[str],
        master_lookup: Dict[str, MasterWorkItem]
    ) -> Tuple[Optional[MasterWorkItem], float, List[Dict]]:
        """
        Tìm best match trong master database

        Returns:
            (best_master_item, best_score, top_3_matches)
        """
        if not master_descriptions:
            return None, 0.0, []

        # Calculate similarity scores
        scores = []
        for master_desc in master_descriptions:
            score = self._calculate_similarity(description, master_desc)
            if score > 0.3:  # Only consider if somewhat similar
                scores.append((master_desc, score))

        if not scores:
            return None, 0.0, []

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Get top matches
        top_matches = []
        for desc, score in scores[:5]:
            master = master_lookup.get(desc)
            if master:
                top_matches.append({
                    'work_code': master.work_code,
                    'description': master.description,
                    'similarity': round(score * 100, 1),
                    'sec_code': master.sec_code
                })

        best_desc, best_score = scores[0]
        best_master = master_lookup.get(best_desc)

        return best_master, best_score, top_matches

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings
        Uses SequenceMatcher with token-based matching
        """
        if not s1 or not s2:
            return 0.0

        # Exact match
        if s1 == s2:
            return 1.0

        # SequenceMatcher ratio
        ratio = SequenceMatcher(None, s1, s2).ratio()

        # Token-based bonus for construction terms
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())

        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_ratio = len(common) / max(len(tokens1), len(tokens2))
            # Weighted average
            ratio = 0.6 * ratio + 0.4 * token_ratio

        return ratio

    def _dedupe_new_items(self, new_items: List[MatchResult]) -> List[MatchResult]:
        """
        Lọc trùng trong công tác mới (by normalized description)
        """
        seen = set()
        unique = []

        for item in new_items:
            key = item.normalized_description.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    def _add_to_master(self, file_id: int, items: List[MatchResult]):
        """
        Thêm công tác mới vào Master database với mã mới
        """
        for item in items:
            try:
                # Generate work code
                work_code = self.code_generator.generate_work_code(
                    description=item.normalized_description,
                    sec_code=None,  # Will be classified later
                    unit=None
                )

                master_item = MasterWorkItem(
                    work_code=work_code,
                    description=item.normalized_description,
                    description_normalized=item.normalized_description.lower().strip(),
                    sec_code='UNCLASSIFIED',
                    unit_standard='',
                    occurrence_count=1,
                    source_files=json.dumps([file_id]),
                    is_verified=False
                )
                self.db.add(master_item)

            except Exception as e:
                logger.error(f"Failed to add master item '{item.normalized_description[:50]}...': {e}")

        self.db.commit()

    def process_line_items(
        self,
        file_id: int,
        auto_add_to_master: bool = False
    ) -> ProcessingResult:
        """
        Process line items from database (already parsed BOQ file)

        Args:
            file_id: BOQ file ID
            auto_add_to_master: Auto add new items to master

        Returns:
            ProcessingResult
        """
        # Get line items from DB
        line_items = self.db.query(LineItem).filter(
            LineItem.file_id == file_id,
            LineItem.description != '',
            LineItem.description.isnot(None)
        ).all()

        items = [
            {
                'description': item.description,
                'unit': item.unit,
                'quantity': item.quantity,
                'unit_price': item.unit_price
            }
            for item in line_items
        ]

        return self.process_boq_items(file_id, items, auto_add_to_master)

    def get_match_summary(self, result: ProcessingResult) -> Dict:
        """
        Get summary statistics from processing result
        """
        return {
            'total_extracted': result.total_extracted,
            'after_raw_dedup': result.unique_raw,
            'after_normalize_dedup': result.unique_normalized,
            'matches': {
                'exact': result.exact_matches,
                'fuzzy': result.fuzzy_matches,
                'new': result.new_items
            },
            'new_items_deduped': result.new_items_deduped,
            'needs_review': result.fuzzy_matches,
            'ready_to_add': result.new_items_deduped
        }


def get_boq_processing_service(db: Session) -> BOQProcessingService:
    """Factory function to get BOQ processing service"""
    return BOQProcessingService(db)
