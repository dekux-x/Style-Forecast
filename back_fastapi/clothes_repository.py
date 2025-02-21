from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Session
from .database import Base

from typing import ClassVar
from pydantic import BaseModel, field_validator, Field


class ClothesModel(Base):
    __tablename__ = "clothes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    subcategory = Column(String)
    color = Column(String)
    warmness = Column(String)
    image_url = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship('UsersModel', back_populates='clothes')


class ClothesRepository:
    def get_clothes(self,db: Session, user_id: int):
        return db.query(ClothesModel).filter(ClothesModel.owner_id==user_id).all()
    
    def get_clothes_by_id(self,db: Session, clothes_id: int):
        return db.query(ClothesModel).filter(ClothesModel.id==clothes_id).first()
    
    def create_clothes(self, db:Session, clothes: None):
        db_clothes = ClothesModel(name=clothes['name'], category=clothes['category'], subcategory=clothes['subcategory'],
                    color=clothes['color'],image_url=clothes['url'], warmness = clothes['warmness'], owner_id=clothes['user_id'])
        db.add(db_clothes)
        db.commit()
        db.refresh(db_clothes)
        return db_clothes
    
    def update_clothes(self, db: Session, clothes_id: int, update_data: dict):
        clothes = self.get_clothes_by_id(db, clothes_id)
        if not clothes:
            return None
        elif clothes.owner_id != update_data['user_id']:
            return False
        del update_data['user_id']
        for key, value in update_data.items():
            setattr(clothes, key, value)
        db.commit()
        db.refresh(clothes)
        return clothes

    def delete_clothes(self, db: Session, clothes_id: int, user_id: int):
        clothes = self.get_clothes_by_id(db, clothes_id)
        if not clothes:
            return None
        if clothes.owner_id != user_id:
            return False
        db.delete(clothes)
        db.commit()
        return clothes
    


class ClothingsRequest(BaseModel):
    name: str
    category: str
    subcategory: str
    warmness: str
    color: str
    url: str = None


    val_categories: ClassVar[list[str]] = ["Shirts", "Layers", "Pants", "Shoes", "Accessories"]
    val_subcategories: ClassVar[dict[str, list[str]]] = {
        "Shirts": ["T-Shirts", "Button-ups", "Polo-shirts"],
        "Layers": ["Sweaters", "Sweatshirts", "Jackets", "Cover ups", "Blazers"],
        "Pants": ["Jeans", "Sweatpants", "Shorts", "Dress trousers", "Chinos"],
        "Shoes": ["Sneakers", "Boots", "Oxfords", "Loafers", "Sandals"],
        "Accessories": ["Earrings", "Necklaces", "Rings", "Scarves", "Hats", "Bags", "Sunglasses", "Belts", "Bracelets", "Face masks", "Watches"],
    }

    @field_validator('category')
    @classmethod
    def validate_category(cls, value):
        if value not in cls.val_categories:
            raise ValueError(f"Invalid category: {value}. Must be one of {cls.val_categories}")
        return value

    @field_validator('subcategory', mode='before')
    @classmethod
    def validate_subcategory(cls, value, info):
        category = info.data.get('category')
        if not category:
            raise ValueError("Category must be provided before subcategory validation.")
        if category not in cls.val_subcategories:
            raise ValueError(f"Invalid category: {category}. No subcategories found.")
        if value not in cls.val_subcategories[category]:
            raise ValueError(f"Invalid subcategory: {value}. Must be one of {cls.val_subcategories[category]}")
        return value

    @field_validator('warmness')
    @classmethod
    def validate_warmness(cls, value):
        valid_warmness = ['Medium', 'Light', 'Extra light', 'Warm', 'Extra warm']
        if value not in valid_warmness:
            raise ValueError(f"Invalid warmness: {value}. Must be one of {valid_warmness}")
        return value
        
class ClothingsResponse(BaseModel):
    id: int
    name: str
    image_url: str | None
    category: str
    subcategory: str
    warmness: str
    color: str

    def __lt__(self, other):
        if self.category != other.category:
            return self.category < other.category  # First compare by category
        return self.id < other.id  # Then compare by id if categories are the same

    def __repr__(self):
        return f"Cloth(id={self.id}, category={self.category}, subcategory={self.subcategory}, color={self.color}, warmness={self.warmness})"
    
    class Config:
        from_attributes = True

    
        

