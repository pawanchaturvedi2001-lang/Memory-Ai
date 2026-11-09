import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User, UserRole, AuditLog
from app.schemas.schemas import (
    UserCreate, UserLogin, UserResponse, Token, UserRoleUpdate
)
from app.security.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, require_roles
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # First user registered automatically gets Admin role, others get requested role or default
    user_count = db.query(User).count()
    assigned_role = UserRole.ADMIN if user_count == 0 else user_in.role

    # Validate role string
    valid_roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER, UserRole.INCOMING_MEMBER]
    if assigned_role not in valid_roles:
        assigned_role = UserRole.INCOMING_MEMBER

    hashed_pw = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        role=assigned_role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log registration in audit log
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="user",
        entity_id=user.id,
        details=f"User {user.email} registered with role {user.role}"
    )
    db.add(audit)
    db.commit()

    # Generate token
    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
):
    valid_roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.OUTGOING_MEMBER, UserRole.INCOMING_MEMBER]
    if role_update.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = target_user.role
    target_user.role = role_update.role
    db.commit()
    db.refresh(target_user)

    audit = AuditLog(
        user_id=current_user.id,
        action="USER_ROLE_UPDATED",
        entity_type="user",
        entity_id=target_user.id,
        details=f"Role changed from {old_role} to {target_user.role} by {current_user.email}"
    )
    db.add(audit)
    db.commit()

    return target_user
