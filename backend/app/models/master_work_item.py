"""
Master Work Items Table
Lưu trữ công tác chuẩn đã được làm sạch, chuẩn hóa và phân loại
"""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class MasterWorkItem(Base):
    """
    Bảng công tác chuẩn (Master Data)
    Được tạo từ việc làm sạch và chuẩn hóa line items từ nhiều BOQ
    """
    __tablename__ = "master_work_items"

    # Primary key
    master_id = Column(Integer, primary_key=True, autoincrement=True)

    # Work item code (mã công tác chuẩn)
    work_code = Column(String(50), unique=True, nullable=False, index=True)

    # Description (mô tả chuẩn hóa)
    description = Column(Text, nullable=False)
    description_normalized = Column(String(500))  # Chuẩn hóa: lowercase, trim (for indexing)

    # Classification
    sec_code = Column(String(20), nullable=False, index=True)
    category = Column(String(100))  # Danh mục chi tiết (VD: "Công tác cọc", "Tường gạch")

    # Unit standardization
    unit_standard = Column(String(20), nullable=False)  # Đơn vị chuẩn (m, m2, m3, kg, ton, pcs, etc.)
    unit_variants = Column(Text)  # JSON array các biến thể đơn vị ["m", "mét", "meter"]

    # Reference pricing (giá tham khảo)
    ref_unit_price_min = Column(Numeric(15, 2))  # Giá thấp nhất từ các BOQ
    ref_unit_price_max = Column(Numeric(15, 2))  # Giá cao nhất
    ref_unit_price_avg = Column(Numeric(15, 2))  # Giá trung bình

    # Statistics
    occurrence_count = Column(Integer, default=1)  # Số lần xuất hiện trong các BOQ
    source_files = Column(Text)  # JSON array các file_id đã tạo ra item này

    # Metadata
    tags = Column(Text)  # JSON array tags cho search
    notes = Column(Text)  # Ghi chú

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Đã được verify bởi user
    verified_by = Column(Integer)  # user_id
    verified_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Indexes for search and filter
    __table_args__ = (
        Index('idx_master_sec_code', 'sec_code'),
        Index('idx_master_unit', 'unit_standard'),
        Index('idx_master_active', 'is_active'),
        Index('idx_master_description', 'description_normalized'),
    )

    def __repr__(self):
        return f"<MasterWorkItem(code={self.work_code}, desc={self.description[:50]})>"
