from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..models.record import FinancialRecord, RecordType
from ..schemas.record import CategoryTotal, DashboardSummary, MonthlyTrend
from ..middleware.rbac import RoleChecker

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Dashboard endpoints are accessible to Viewer+ (Viewer, Analyst, Admin)
viewer_plus = RoleChecker([UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN])
# Trends might be restricted to Analyst+ if needed, but per prompt Analyst+
analyst_plus = RoleChecker([UserRole.ANALYST, UserRole.ADMIN])


def _active_records_query(db: Session):
    return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(viewer_plus)):
    records_query = _active_records_query(db)
    total_income = (
        records_query.filter(FinancialRecord.type == RecordType.INCOME)
        .with_entities(func.coalesce(func.sum(FinancialRecord.amount), 0.0))
        .scalar()
    )
    total_expenses = (
        records_query.filter(FinancialRecord.type == RecordType.EXPENSE)
        .with_entities(func.coalesce(func.sum(FinancialRecord.amount), 0.0))
        .scalar()
    )

    category_rows = (
        records_query.with_entities(
            FinancialRecord.category,
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                        else_=-FinancialRecord.amount,
                    )
                ),
                0.0,
            ),
        )
        .group_by(FinancialRecord.category)
        .order_by(FinancialRecord.category.asc())
        .all()
    )

    recent_transactions = (
        records_query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .limit(5)
        .all()
    )

    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "net_balance": float(total_income - total_expenses),
        "category_totals": {
            category: float(total) for category, total in category_rows
        },
        "recent_transactions": recent_transactions,
    }


@router.get("/category-totals", response_model=List[CategoryTotal])
def get_category_totals(
    db: Session = Depends(get_db),
    current_user: User = Depends(viewer_plus),
):
    rows = (
        _active_records_query(db)
        .with_entities(
            FinancialRecord.category,
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                        else_=-FinancialRecord.amount,
                    )
                ),
                0.0,
            ).label("total"),
        )
        .group_by(FinancialRecord.category)
        .order_by(FinancialRecord.category.asc())
        .all()
    )
    return [{"category": category, "total": float(total)} for category, total in rows]


@router.get("/monthly-trends", response_model=List[MonthlyTrend])
@router.get("/trends", response_model=List[MonthlyTrend], include_in_schema=False)
def get_trends(db: Session = Depends(get_db), current_user: User = Depends(analyst_plus)):
    six_months_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=180)
    records = (
        _active_records_query(db)
        .filter(FinancialRecord.date >= six_months_ago)
        .order_by(FinancialRecord.date.asc(), FinancialRecord.id.asc())
        .all()
    )

    trends: dict[str, dict[str, float]] = {}
    for record in records:
        month_key = record.date.strftime("%Y-%m")
        bucket = trends.setdefault(month_key, {"income": 0.0, "expenses": 0.0})
        if record.type == RecordType.INCOME:
            bucket["income"] += float(record.amount)
        else:
            bucket["expenses"] += float(record.amount)

    return [
        {
            "month": month,
            "income": values["income"],
            "expenses": values["expenses"],
            "balance": values["income"] - values["expenses"],
        }
        for month, values in sorted(trends.items())
    ]
