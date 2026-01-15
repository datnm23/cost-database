from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, JSON, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class SECCode(Base):
    __tablename__ = "sec_codes"
    
    sec_code = Column(String(20), primary_key=True, index=True)
    sec_name_vi = Column(String(255), nullable=False)
    sec_name_en = Column(String(255))
    parent_code = Column(String(20), ForeignKey("sec_codes.sec_code"))
    level = Column(Integer, default=1)
    keywords = Column(JSON)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    children = relationship("SECCode", backref="parent", remote_side=[sec_code])
    
    def __repr__(self):
        return f"<SECCode {self.sec_code}: {self.sec_name_vi}>"
