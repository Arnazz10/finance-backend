from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from ..models.record import RecordType


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class RecordBase(BaseModel):
    amount: float = Field(gt=0)
    type: RecordType
    category: str = Field(min_length=1, max_length=100)
    date: datetime = Field(default_factory=utc_now)
    notes: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")

class RecordCreate(RecordBase):
    pass

class RecordUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    type: Optional[RecordType] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")

class FinancialRecord(RecordBase):
    id: int
    user_id: int
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_totals: dict[str, float]
    recent_transactions: list[FinancialRecord]

class CategoryTotal(BaseModel):
    category: str
    total: float

class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float
    balance: float
