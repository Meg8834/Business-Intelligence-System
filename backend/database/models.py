from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.db_config import Base


class User(Base):
    """
    Users table — stores registered accounts.
    Each user has their own isolated business data.
    """
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False, index=True)
    password   = Column(String(255), nullable=False)   # bcrypt hashed
    is_admin   = Column(Boolean, default=False)         # admin can see all data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship — one user has many business data rows
    business_data = relationship("BusinessData", back_populates="owner",
                                  cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": str(self.created_at),
        }


class BusinessData(Base):
    """
    Business data table — each row belongs to a specific user.
    """
    __tablename__ = "business_data"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    month           = Column(String(50), nullable=False)
    revenue         = Column(Float, nullable=False, default=0.0)
    expenses        = Column(Float, nullable=False, default=0.0)
    marketing_spend = Column(Float, nullable=False, default=0.0)
    customer_growth = Column(Float, nullable=False, default=0.0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship — each row belongs to one user
    owner = relationship("User", back_populates="business_data")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "revenue": self.revenue,
            "expenses": self.expenses,
            "marketing_spend": self.marketing_spend,
            "customer_growth": self.customer_growth,
            "created_at": str(self.created_at),
        }