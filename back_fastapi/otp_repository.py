from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, desc
from sqlalchemy.orm import relationship, Session
from datetime import datetime, timedelta
from .database import Base
from pydantic import BaseModel, field_validator, Field
import re


class OTPModel(Base):
    __tablename__ = "otp"

    id = Column(Integer, primary_key=True, index=True)
    otp_code = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    email = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship('UsersModel', back_populates='otp')

    def is_valid(self):
        return datetime.now() < self.expires_at
    
class OTPRequest(BaseModel):
    email: str
    content: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError('Invalid email')
        return value

class OTPRepository:
    def create_otp(self, db: Session, otp_data: dict):
        expires_at = datetime.now() + timedelta(minutes=10)  # OTP действителен 10 минут
        otp = OTPModel(otp_code = otp_data['otp_code'], created_at = datetime.now(),
                       expires_at = expires_at, user_id = otp_data['user_id'],email = otp_data['email'])
        db.add(otp)
        db.commit()
        db.refresh(otp)
        return otp

    def get_otp_by_user(self, db: Session, user_id: int):
        return db.query(OTPModel).filter(OTPModel.user_id == user_id).order_by(OTPModel.created_at.desc()).first()
    
    def get_otp_by_email(self, db: Session, email: str):
        return db.query(OTPModel).filter(OTPModel.email == email).order_by(OTPModel.created_at.desc()).first()

    def delete_otp(self, db: Session, otp_id: int):
        otp = db.query(OTPModel).filter(OTPModel.id == otp_id).first()
        if otp:
            db.delete(otp)
            db.commit()
        return otp