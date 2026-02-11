"""
Master Work Items Table
Luu tru cong tac chuan da duoc lam sach, chuan hoa va phan loai
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, Index, LargeBinary, Float, Enum, ForeignKey
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

    # Spec Lifecycle
    spec_status = Column(
        Enum('draft', 'detailed', 'final', name='spec_status_enum'),
        default='draft',
        nullable=False,
        comment='Spec lifecycle stage',
    )
    spec_source = Column(
        Enum('default', 'boq', 'drawing', 'as_built', name='spec_source_enum'),
        default='default',
        nullable=False,
        comment='Where the spec data came from',
    )
    spec_confidence = Column(Float, default=0.0, nullable=False, comment='Confidence 0.0-1.0 based on source')
    spec_completeness = Column(Float, default=0.0, nullable=False, comment='Weighted completeness 0.0-1.0')

    # v4.0 Code (reference code — non-unique, FK to sec_codes_v4)
    sec_code_v4 = Column(String(15), ForeignKey('sec_codes_v4.code'), nullable=True, index=True, comment='v4.0 ref code e.g. A.CONC.STR')
    # Instance code (unique identifier per master item)
    instance_code = Column(String(20), unique=True, nullable=True, index=True, comment='Unique instance e.g. A.CONC.STR-001')
    item_table_type = Column(
        Enum('A', 'M', 'L', 'E', name='item_table_type_enum'),
        default='A',
        nullable=False,
        comment='Which v4.0 table: Activity/Material/Labour/Equipment',
    )

    # v4.0 Attributes (stored separately, not in the code)
    discipline = Column(String(5), nullable=True, comment='Discipline: CV, AR, EL, PL, ME, FP')
    location = Column(String(5), nullable=True, comment='Location (Activity): COL, BEM, SLB, FND, WAL')
    material_type = Column(String(10), nullable=True, comment='Material type (Material): RDMX, HDPE, XLPE')
    worker_grade = Column(String(10), nullable=True, comment='Worker grade (Labour): THO3, THO4, OPER')
    equip_type = Column(String(10), nullable=True, comment='Equipment type (Equipment): PUMP, EXCV, CRAN')

    # Legacy preservation
    work_code_legacy = Column(String(50), nullable=True, comment='Original S-prefix work code before v4.0 migration')

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
    ref_code_rel = relationship("SECCodeV4", back_populates="master_items", foreign_keys=[sec_code_v4])

    # Indexes for search and filter
    __table_args__ = (
        Index('idx_master_sec_code', 'sec_code'),
        Index('idx_master_unit', 'unit_standard'),
        Index('idx_master_active', 'is_active'),
        Index('idx_master_description', 'description_normalized'),
        Index('idx_master_spec_category', 'spec_category'),
        Index('idx_master_spec_material', 'spec_material'),
        Index('idx_master_spec_grade', 'spec_grade'),
        Index('idx_master_spec_status', 'spec_status'),
        Index('idx_master_table_type', 'item_table_type'),
        Index('idx_master_discipline', 'discipline'),
    )

    def compute_spec_completeness(self) -> float:
        """
        Compute weighted spec completeness score (0.0 - 1.0).

        Weights:
          - spec_category:  25%
          - spec_material:  25%
          - spec_grade:     30%
          - spec_dimension: 20%
        """
        score = 0.0
        if self.spec_category:
            score += 0.25
        if self.spec_material:
            score += 0.25
        if self.spec_grade:
            score += 0.30
        if self.spec_dimension:
            score += 0.20
        return round(score, 2)

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
