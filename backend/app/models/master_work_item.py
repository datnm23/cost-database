"""
Master Work Items Table
Luu tru cong tac chuan da duoc lam sach, chuan hoa va phan loai
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, Index, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MasterWorkItem(Base):
    """
    Bang cong tac chuan (Master Data)
    Duoc tao tu viec lam sach va chuan hoa line items tu nhieu BOQ
    """
    __tablename__ = "master_work_items"

    # Primary key
    master_id = Column(Integer, primary_key=True, autoincrement=True)

    # Work item code (ma cong tac chuan)
    work_code = Column(String(50), unique=True, nullable=False, index=True)

    # Description (mo ta chuan hoa)
    description = Column(Text, nullable=False)
    description_normalized = Column(String(500))  # Chuan hoa: lowercase, trim (for indexing)

    # Classification
    sec_code = Column(String(20), nullable=False, index=True)
    category = Column(String(100))  # Danh muc chi tiet (VD: "Cong tac coc", "Tuong gach")

    # Unit standardization
    unit_standard = Column(String(20), nullable=False)  # Don vi chuan (m, m2, m3, kg, ton, pcs, etc.)
    unit_variants = Column(Text)  # JSON array cac bien the don vi ["m", "met", "meter"]

    # Reference pricing (gia tham khao)
    ref_unit_price_min = Column(Numeric(15, 2))  # Gia thap nhat tu cac BOQ
    ref_unit_price_max = Column(Numeric(15, 2))  # Gia cao nhat
    ref_unit_price_avg = Column(Numeric(15, 2))  # Gia trung binh

    # Statistics
    occurrence_count = Column(Integer, default=1)  # So lan xuat hien trong cac BOQ
    source_files = Column(Text)  # JSON array cac file_id da tao ra item nay

    # Metadata
    tags = Column(Text)  # JSON array tags cho search
    notes = Column(Text)  # Ghi chu

    # Separated Spec Fields (for fast filtering and matching key lookup)
    spec_category = Column(String(100), nullable=True, comment='Material category (Be tong, Thep, Ong)')
    spec_material = Column(String(100), nullable=True, comment='Material type (HDPE, PPR, Cu/XLPE)')
    spec_grade = Column(String(50), nullable=True, comment='Grade (M200, CB400, PN16)')
    spec_dimension = Column(String(200), nullable=True, comment='Dimensions (D110, 4x16mm2, 600x600)')

    # Fast Lookup
    matching_key = Column(String(255), nullable=True, index=True, comment='Normalized key for O(1) lookup')

    # Cached Embeddings
    embedding_vector = Column(LargeBinary, nullable=True, comment='Pre-computed SBERT embedding (768 dims)')
    embedding_version = Column(String(50), nullable=True, comment='Embedding model version')

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Da duoc verify boi user
    verified_by = Column(Integer)  # user_id
    verified_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    synonyms = relationship("MasterSynonym", back_populates="master_item", cascade="all, delete-orphan")

    # Indexes for search and filter
    __table_args__ = (
        Index('idx_master_sec_code', 'sec_code'),
        Index('idx_master_unit', 'unit_standard'),
        Index('idx_master_active', 'is_active'),
        Index('idx_master_description', 'description_normalized'),
        Index('idx_master_spec_category', 'spec_category'),
        Index('idx_master_spec_material', 'spec_material'),
        Index('idx_master_spec_grade', 'spec_grade'),
    )

    def generate_matching_key(self) -> str:
        """
        Generate matching key from separated specs.

        Format: "category|material|grade|dimension"
        Used for O(1) hash lookup of exact spec matches.
        """
        parts = [
            self.spec_category or 'X',
            self.spec_material or 'X',
            self.spec_grade or 'X',
            self.spec_dimension or 'X'
        ]
        return '|'.join(p.lower().strip() for p in parts)

    def __repr__(self):
        return f"<MasterWorkItem(code={self.work_code}, desc={self.description[:50]})>"
