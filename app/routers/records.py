from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..models.record import FinancialRecord, RecordType
from ..schemas.record import FinancialRecord as RecordSchema, RecordCreate, RecordUpdate
from ..middleware.rbac import RoleChecker

router = APIRouter(prefix="/records", tags=["records"])

# Access control dependencies
analyst_plus = RoleChecker([UserRole.ANALYST, UserRole.ADMIN])
admin_only = RoleChecker([UserRole.ADMIN])

@router.get("/", response_model=list[RecordSchema])
def list_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(analyst_plus),
    category: Optional[str] = None,
    type: Optional[RecordType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be earlier than or equal to date_to",
        )

    query = db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    
    if category:
        query = query.filter(FinancialRecord.category == category)
    if type:
        query = query.filter(FinancialRecord.type == type)
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)
        
    return query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc()).all()


@router.get("/{record_id}", response_model=RecordSchema)
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(analyst_plus),
):
    db_record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )
    return db_record

@router.post("/", response_model=RecordSchema, status_code=status.HTTP_201_CREATED)
def create_record(
    record: RecordCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(analyst_plus)
):
    db_record = FinancialRecord(
        **record.model_dump(),
        user_id=current_user.id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.put("/{record_id}", response_model=RecordSchema)
def update_record(
    record_id: int,
    update_data: RecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(analyst_plus)
):
    db_record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id, 
        FinancialRecord.is_deleted == False
    ).first()
    
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(db_record, key, value)
        
    db.commit()
    db.refresh(db_record)
    return db_record

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(admin_only)
):
    db_record = db.query(FinancialRecord).filter(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,
    ).first()
    
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    
    # Soft delete
    db_record.is_deleted = True
    db.commit()
    return None
