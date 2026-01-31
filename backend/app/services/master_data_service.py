"""
Service để xây dựng Master Database từ Line Items
"""
import re
import unicodedata
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
import logging

from app.models.line_item import LineItem
from app.models.master_work_item import MasterWorkItem
from app.utils.excel_processor import ExcelProcessor

logger = logging.getLogger(__name__)


class MasterDataService:
    """
    Service để xây dựng và quản lý Master Database
    """

    def __init__(self, db: Session):
        self.db = db
        self.excel_processor = ExcelProcessor()

    def normalize_description(self, text: str) -> str:
        """
        Chuẩn hóa description để dễ so sánh
        - Lowercase
        - Remove extra spaces
        - Unicode normalization
        """
        if not text:
            return ""

        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Lowercase
        text = text.lower()

        # Remove extra spaces
        text = ' '.join(text.split())

        return text.strip()

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
            'skipped': 0,
            'by_sec_code': defaultdict(int)
        }

        for idx, item in enumerate(items, 1):
            try:
                # Normalize description
                desc_normalized = self.normalize_description(item.description)

                # Check if similar item exists
                existing = self._find_similar_master(
                    description_normalized=desc_normalized,
                    sec_code=item.sec_code,
                    unit=item.unit
                )

                if existing:
                    # Update existing
                    self._update_master_item(existing, item)
                    stats['updated'] += 1
                else:
                    # Create new master item
                    work_code = self.extract_work_code(item.description, idx)
                    master_item = MasterWorkItem(
                        work_code=work_code,
                        description=item.description,
                        description_normalized=desc_normalized,
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
    ) -> Optional[MasterWorkItem]:
        """
        Tìm master item tương tự
        """
        # Exact match first
        exact = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.description_normalized == description_normalized,
            MasterWorkItem.sec_code == sec_code,
            MasterWorkItem.unit_standard == unit
        ).first()

        if exact:
            return exact

        # TODO: Implement fuzzy matching with similarity score
        # For now, return None if no exact match
        return None

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
