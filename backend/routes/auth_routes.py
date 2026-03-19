from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database.db_config import get_db
from database.models import User
from utils.auth_utils import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request schemas ───────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ── Register ──────────────────────────────────────────────────────
@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = User(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}


# ── Login with JSON (for frontend) ────────────────────────────────
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password — returns JWT token."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user.to_dict()}


# ── Login with OAuth2 form (for Swagger UI Authorize button) ──────
@router.post("/token")
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login for Swagger UI.
    Enter your email in the 'username' field and your password.
    Leave client_id and client_secret empty.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}


# ── Get current user profile ──────────────────────────────────────
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently logged-in user's profile."""
    return current_user.to_dict()


# ── Change password ───────────────────────────────────────────────
@router.put("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect.")
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    current_user.password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password changed successfully."}