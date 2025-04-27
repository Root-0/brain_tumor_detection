# brain_tumor_detection/api/database.py

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from datetime import datetime
from typing import Dict, Any, Optional

from .settings import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    scans = relationship("ScanRecord", back_populates="user")

class ScanRecord(Base):
    __tablename__ = "scan_records"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    status = Column(String)  # 'processing', 'completed', 'failed'
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="scans")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables if they don't exist
def init_db():
    Base.metadata.create_all(bind=engine)

# Create admin user if it doesn't exist
def create_admin_user(db):
    from .security import get_password_hash
    
    # Check if admin user exists
    admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if not admin:
        admin_user = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully")
    else:
        print("Admin user already exists")

# Initialize the database
if settings.INITIALIZE_DB:
    init_db()
    db = next(get_db())
    create_admin_user(db)