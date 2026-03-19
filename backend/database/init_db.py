"""
init_db.py
──────────
Run this ONCE to:
1. Drop and recreate all tables (users + business_data)
2. Create a default admin account

Usage:
    cd backend
    python -m database.init_db
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_config import engine, Base
from database.models import User, BusinessData
from sqlalchemy.orm import sessionmaker
from utils.auth_utils import hash_password


def init():
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)

    print("Creating default admin account...")
    Session = sessionmaker(bind=engine)
    session = Session()

    admin = User(
        name="Admin",
        email="admin@business.com",
        password=hash_password("admin123"),
        is_admin=True,
    )
    session.add(admin)
    session.commit()
    session.close()

    print("✅ Database initialized successfully!")
    print("─────────────────────────────────────")
    print("Admin credentials:")
    print("  Email   : admin@business.com")
    print("  Password: admin123")
    print("─────────────────────────────────────")
    print("Change the admin password after first login!")


if __name__ == "__main__":
    init()