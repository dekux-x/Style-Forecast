from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Session
from .database import Base

from pydantic import BaseModel, field_validator, Field
from datetime import datetime, timezone

class Feedbacks(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    created_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship('UsersModel', back_populates='feedbacks')


class FeedbackRequest(BaseModel):
    content: str = Field(..., min_length=5, max_length=1000)

class FeedbackResponse(BaseModel):
    content: str
    created_date: datetime
    user_id: int


class FeedbackRepository:
    def create_feedback(self, db: Session, feedback_data: dict):
        feedback = Feedbacks(**feedback_data)
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    def get_feedbacks(self, db: Session):
        return db.query(Feedbacks).all()
    
    def delete_feedback(self, db: Session, feedback_id: int):
        feedback = db.query(Feedbacks).filter(Feedbacks.id == feedback_id).first()
        if feedback:
            db.delete(feedback)
            db.commit()
        return feedback