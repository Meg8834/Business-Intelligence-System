from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.db_config import get_db
from database.models import User, BusinessData
from utils.auth_utils import get_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only — returns all registered users."""
    users = db.query(User).all()
    return {
        "total_users": len(users),
        "users": [u.to_dict() for u in users]
    }


@router.get("/users/{user_id}/data")
def get_user_data(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only — returns all business data for a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    data = db.query(BusinessData).filter(
        BusinessData.user_id == user_id
    ).order_by(BusinessData.id.asc()).all()

    return {
        "user": user.to_dict(),
        "total_records": len(data),
        "data": [d.to_dict() for d in data]
    }


@router.get("/overview")
def get_system_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only — system-wide overview of all users and data."""
    total_users = db.query(User).count()
    total_records = db.query(BusinessData).count()
    users = db.query(User).all()

    user_summary = []
    for user in users:
        count = db.query(BusinessData).filter(
            BusinessData.user_id == user.id
        ).count()
        user_summary.append({
            **user.to_dict(),
            "data_records": count
        })

    return {
        "total_users": total_users,
        "total_records": total_records,
        "users": user_summary,
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only — delete a user and all their data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin account.")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} and all their data deleted successfully."}


@router.put("/users/{user_id}/make-admin")
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin only — promote a user to admin."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_admin = True
    db.commit()
    return {"message": f"{user.email} has been promoted to admin."}