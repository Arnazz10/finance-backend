from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import User as UserSchema, UserCreate, UserUpdate
from ..middleware.rbac import RoleChecker
from ..utils.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

# Only Admins can list and update user roles
admin_check = RoleChecker([UserRole.ADMIN])

@router.get("/", response_model=list[UserSchema])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(admin_check)):
    return db.query(User).all()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_check),
):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.patch("/{user_id}/role", response_model=UserSchema)
def update_user_role(
    user_id: int, 
    update_data: UserUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(admin_check)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if update_data.role:
        db_user.role = update_data.role
    if update_data.is_active is not None:
        db_user.is_active = update_data.is_active
    if update_data.name is not None:
        db_user.name = update_data.name
    if update_data.email is not None:
        conflicting_user = db.query(User).filter(
            User.email == update_data.email,
            User.id != user_id,
        ).first()
        if conflicting_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        db_user.email = update_data.email
    
    db.commit()
    db.refresh(db_user)
    return db_user
