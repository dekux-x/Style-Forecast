from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Session
from .database import Base

from pydantic import BaseModel, field_validator, Field
import re


class UsersModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    gender = Column(String)
    weight = Column(Integer)

    clothes = relationship('ClothesModel', back_populates = 'owner')
    feedbacks = relationship('Feedbacks', back_populates='owner')
    otp = relationship('OTPModel', back_populates='owner')


class UsersRepository:
    def get_by_id(self,db: Session, user_id: int)-> UsersModel:
        return db.query(UsersModel).filter(UsersModel.id==user_id).first()
    
    def get_by_email(self,db: Session, email: str)-> UsersModel:
        return db.query(UsersModel).filter(UsersModel.email==email).first()
    
    def get_by_username(self,db: Session, username: str)-> UsersModel:
        return db.query(UsersModel).filter(UsersModel.username==username).first()
    
    def create(self, db:Session, user: None)-> UsersModel:
        db_user = UsersModel(username=user.username, password=user.password, email=user.email, 
                    gender=user.gender,weight =user.weight)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(self, db: Session, user_id: int, update_data: dict)-> UsersModel:
        user = self.get_by_id(db,user_id)
        for key, value in update_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user
    
    def update_password(self, db: Session, user: UsersModel, new_password: str)-> UsersModel:
        user.password = new_password
        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: int)-> UsersModel:
        user = self.get_by_id(db,user_id)
        db.delete(user)
        db.commit()
        return user



class UsersSchema(BaseModel):
    username: str
    email: str
    password: str
    weight: int = Field(gt=0, le=250)
    gender: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter (A-Z).")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include at least one lowercase letter (a-z).")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one numeric digit (0-9).")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValueError('Invalid email')
        return value
        
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, value):
        if value not in ['M','F','m','f',"Male","Female"]:
            raise ValueError()
        return value
        
class UserResponse(BaseModel):
    username: str
    email: str
    weight: int
    gender: str

class UserRequest(BaseModel):
    username: str
    password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter (A-Z).")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include at least one lowercase letter (a-z).")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one numeric digit (0-9).")
        return value
    
class ResetPassword(BaseModel):
    password: str
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter (A-Z).")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include at least one lowercase letter (a-z).")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one numeric digit (0-9).")
        return value
