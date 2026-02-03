"""
Service để xây dựng Master Database từ Line Items
"""
import re
import unicodedata
import json
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from difflib import SequenceMatcher
import logging

from app.models.line_item import LineItem
from app.models.master_work_item import MasterWorkItem
from app.utils.excel_processor import ExcelProcessor
from app.services.work_code_generator import WorkCodeGenerator
from app.services.description_normalizer import DescriptionNormalizer

logger = logging.getLogger(__name__)

# Matching thresholds
EXACT_MATCH_THRESHOLD = 0.95  # ≥95% → Tự động gán mã
FUZZY_MATCH_THRESHOLD = 0.80  # 80-95% → Review


class MasterDataService:
    """
    Service để xây dựng và quản lý Master Database
    """

    def __init__(self, db: Session):
        self.db = db
        self.excel_processor = ExcelProcessor()
        self.code_generator = WorkCodeGenerator(db)
        self.description_normalizer = DescriptionNormalizer()

    def normalize_description(self, text: str) -> str:
        """
        Chuẩn hóa description để dễ so sánh
        - Áp dụng Phương án 5 (Natural Syntax)
        - Lowercase
        - Remove extra spaces
        - Unicode normalization
        """
        if not text:
            return ""

        # Bước 1: Chuẩn hóa theo Natural Syntax (Phương án 5)
        try:
            text_normalized = self.description_normalizer.normalize(text)
        except Exception as e:
            logger.warning(f"Failed to apply Natural Syntax normalization: {e}")
            text_normalized = text

        # Bước 2: Chuẩn hóa cho indexing/search (lowercase)
        # Unicode normalization
        text_normalized = unicodedata.normalize('NFC', text_normalized)

        # Lowercase
        text_normalized = text_normalized.lower()

        # Remove extra spaces
        text_normalized = ' '.join(text_normalized.split())

        return text_normalized.strip()

    def extract_work_code(self, description: str, index: int) -> str:
        """
        Tạo mã công tác từ description
        VD: "Đào đất móng" -> "DAO-DAT-MONG-001"
        """
        # Remove special characters
        cleaned = re.sub(r'[^\w\s-]', '', description.lower())

        # Get first 3-4 meaningful words
        words = [w for w in cleaned.split() if len(w) >= 3][:3]

        if not words:
            return f"WORK-{index:04d}"

        # Create code
        code_parts = []
        for word in words:
            # Remove Vietnamese accents for code
            word_ascii = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('ascii')
            code_parts.append(word_ascii[:10].upper())

        code = '-'.join(code_parts)
        return f"{code}-{index:04d}"

    def build_master_from_file(
        self,
        file_id: int,
        min_confidence: float = 60.0,
        skip_unclassified: bool = True
    ) -> Dict:
        """
        Xây dựng master data từ một BOQ file

        Args:
            file_id: ID của BOQ file
            min_confidence: Chỉ lấy items có confidence >= threshold
            skip_unclassified: Bỏ qua items chưa phân loại

        Returns:
            Dict với thống kê
        """
        logger.info(f"Building master data from file {file_id}")

        # Get line items
        query = self.db.query(LineItem).filter(
            LineItem.file_id == file_id,
            LineItem.description != '',
            LineItem.description.isnot(None)
        )

        if skip_unclassified:
            query = query.filter(LineItem.sec_code.isnot(None))

        if min_confidence > 0:
            query = query.filter(LineItem.confidence_score >= min_confidence)

        items = query.all()

        stats = {
            'total_items': len(items),
            'added': 0,
            'updated': 0,
            'fuzzy_matched': 0,
            'skipped': 0,
            'by_sec_code': defaultdict(int),
            'needs_review': []
        }

        for idx, item in enumerate(items, 1):
            try:
                # Chuẩn hóa description theo Phương án 5 (Natural Syntax)
                desc_natural = self.description_normalizer.normalize(item.description)

                # Normalize cho indexing (lowercase)
                desc_normalized = self.normalize_description(item.description)

                # Check if similar item exists (now returns tuple)
                existing, similarity, match_type = self._find_similar_master(
                    description_normalized=desc_normalized,
                    sec_code=item.sec_code,
                    unit=item.unit
                )

                if match_type == 'exact':
                    # Update existing (high confidence match)
                    self._update_master_item(existing, item)
                    stats['updated'] += 1
                elif match_type == 'fuzzy':
                    # Fuzzy match - update but flag for review
                    self._update_master_item(existing, item)
                    stats['fuzzy_matched'] += 1
                    stats['needs_review'].append({
                        'line_item_id': item.line_item_id,
                        'description': item.description,
                        'matched_master': existing.work_code,
                        'similarity': round(similarity * 100, 1)
                    })
                else:
                    # Create new master item
                    work_code = self.code_generator.generate_work_code(
                        description=desc_natural,  # Sử dụng description đã chuẩn hóa
                        sec_code=item.sec_code,
                        unit=item.unit
                    )
                    master_item = MasterWorkItem(
                        work_code=work_code,
                        description=desc_natural,  # Lưu description theo Natural Syntax
                        description_normalized=desc_normalized,  # Lưu lowercase cho search
                        sec_code=item.sec_code,
                        unit_standard=item.unit,
                        ref_unit_price_min=item.unit_price if item.unit_price > 0 else None,
                        ref_unit_price_max=item.unit_price if item.unit_price > 0 else None,
                        ref_unit_price_avg=item.unit_price if item.unit_price > 0 else None,
                        occurrence_count=1,
                        source_files=json.dumps([file_id])
                    )
                    self.db.add(master_item)
                    stats['added'] += 1

                stats['by_sec_code'][item.sec_code or 'UNCLASSIFIED'] += 1

            except Exception as e:
                logger.error(f"Error processing item {item.line_item_id}: {e}")
                stats['skipped'] += 1
                continue

        # Commit all changes
        self.db.commit()

        logger.info(f"Master data build complete: {stats}")
        return stats

    def _find_similar_master(
        self,
        description_normalized: str,
        sec_code: str,
        unit: str,
        similarity_threshold: float = 0.9
    ) -> Tuple[Optional[MasterWorkItem], float, str]:
        """
        Tìm master item tương tự với fuzzy matching

        Returns:
            (master_item, similarity_score, match_type)
            match_type: 'exact', 'fuzzy', 'none'
        """
        # Exact match first (fastest)
        exact = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.description_normalized == description_normalized,
            MasterWorkItem.sec_code == sec_code,
            MasterWorkItem.unit_standard == unit
        ).first()

        if exact:
            return exact, 1.0, 'exact'

        # Fuzzy matching
        # Load candidates with same SEC code for efficiency
        candidates = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        )
        if sec_code:
            candidates = candidates.filter(MasterWorkItem.sec_code == sec_code)

        candidates = candidates.all()

        if not candidates:
            return None, 0.0, 'none'

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            if not candidate.description_normalized:
                continue

            score = self._calculate_similarity(
                description_normalized,
                candidate.description_normalized
            )

            # Bonus for matching unit
            if unit and candidate.unit_standard == unit:
                score = min(1.0, score + 0.05)

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= EXACT_MATCH_THRESHOLD:
            return best_match, best_score, 'exact'
        elif best_score >= FUZZY_MATCH_THRESHOLD:
            return best_match, best_score, 'fuzzy'
        else:
            return None, best_score, 'none'

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two normalized descriptions
        Combines SequenceMatcher with token-based matching
        """
        if not s1 or not s2:
            return 0.0

        if s1 == s2:
            return 1.0

        # SequenceMatcher ratio
        ratio = SequenceMatcher(None, s1, s2).ratio()

        # Token-based matching (important for construction terms)
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())

        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_ratio = len(common) / max(len(tokens1), len(tokens2))
            # Weighted: 60% sequence, 40% token overlap
            ratio = 0.6 * ratio + 0.4 * token_ratio

        return ratio

    def _update_master_item(self, master: MasterWorkItem, item: LineItem):
        """
        Update master item với dữ liệu từ line item mới
        """
        # Update occurrence count
        master.occurrence_count += 1

        # Update source files
        sources = json.loads(master.source_files) if master.source_files else []
        if item.file_id not in sources:
            sources.append(item.file_id)
            master.source_files = json.dumps(sources)

        # Update price statistics
        if item.unit_price > 0:
            if master.ref_unit_price_min is None or item.unit_price < master.ref_unit_price_min:
                master.ref_unit_price_min = item.unit_price

            if master.ref_unit_price_max is None or item.unit_price > master.ref_unit_price_max:
                master.ref_unit_price_max = item.unit_price

            # Recalculate average
            if master.ref_unit_price_avg:
                # Simple moving average
                count = master.occurrence_count
                master.ref_unit_price_avg = (
                    (master.ref_unit_price_avg * (count - 1) + item.unit_price) / count
                )
            else:
                master.ref_unit_price_avg = item.unit_price

    def get_statistics(self) -> Dict:
        """
        Lấy thống kê master database
        """
        total = self.db.query(MasterWorkItem).count()
        verified = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_verified == True
        ).count()

        by_sec = self.db.query(
            MasterWorkItem.sec_code,
            func.count(MasterWorkItem.master_id)
        ).group_by(MasterWorkItem.sec_code).all()

        return {
            'total_master_items': total,
            'verified_items': verified,
            'unverified_items': total - verified,
            'by_sec_code': {sec: count for sec, count in by_sec}
        }

    def export_master_csv(self, output_path: str):
        """
        Export master data to CSV
        """
        import csv

        items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).order_by(MasterWorkItem.sec_code, MasterWorkItem.work_code).all()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Work Code', 'Description', 'SEC Code', 'Unit',
                'Min Price', 'Avg Price', 'Max Price', 'Occurrences'
            ])

            for item in items:
                writer.writerow([
                    item.work_code,
                    item.description,
                    item.sec_code,
                    item.unit_standard,
                    item.ref_unit_price_min or '',
                    item.ref_unit_price_avg or '',
                    item.ref_unit_price_max or '',
                    item.occurrence_count
                ])

        logger.info(f"Exported {len(items)} master items to {output_path}")
