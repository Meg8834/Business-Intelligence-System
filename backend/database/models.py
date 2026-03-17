from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database.db_config import Base


class BusinessData(Base):
    """
    ORM representation of the business_data table.

    Columns:
        id               : Auto-increment primary key
        month            : Month label e.g. "Jan 2024"
        revenue          : Total revenue for the month
        expenses         : Total expenses for the month
        marketing_spend  : Marketing budget spent
        customer_growth  : Customer growth (as a number, e.g. 5.0 = 5%)
        created_at       : Timestamp of when the row was inserted
    """
    __tablename__ = "business_data"

    id               = Column(Integer, primary_key=True, index=True, autoincrement=True)
    month            = Column(String(50), nullable=False)
    revenue          = Column(Float, nullable=False, default=0.0)
    expenses         = Column(Float, nullable=False, default=0.0)
    marketing_spend  = Column(Float, nullable=False, default=0.0)
    customer_growth  = Column(Float, nullable=False, default=0.0)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        """Returns the row as a plain dictionary."""
        return {
            "id": self.id,
            "month": self.month,
            "revenue": self.revenue,
            "expenses": self.expenses,
            "marketing_spend": self.marketing_spend,
            "customer_growth": self.customer_growth,
            "created_at": str(self.created_at),
        }