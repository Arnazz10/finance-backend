from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone
from ..database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class RecordType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(Enum(RecordType))
    category = Column(String)
    date = Column(DateTime, default=utc_now)
    notes = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False)

    owner = relationship("User", backref="records")
