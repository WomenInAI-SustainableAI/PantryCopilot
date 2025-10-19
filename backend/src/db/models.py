"""
Pydantic models for Firestore database collections
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class FeedbackType(str, Enum):
    """Enum for user feedback types."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    SKIP = "skip"


# User Models
class UserBase(BaseModel):
    """Base user model."""
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User's full name")


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., description="User password")


class UserLogin(BaseModel):
    """Model for user login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(UserBase):
    """User response model without password."""
    id: str = Field(..., description="User ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(UserBase):
    """User model with ID and timestamps."""
    id: str = Field(..., description="User ID")
    password_hash: str = Field(..., description="Hashed password")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Allergy Models
class AllergyBase(BaseModel):
    """Base allergy model."""
    allergen: str = Field(..., description="Name of the allergen")


class AllergyCreate(AllergyBase):
    """Model for creating a new allergy."""
    pass


class Allergy(AllergyBase):
    """Allergy model with ID and timestamps."""
    id: str = Field(..., description="Allergy ID")
    user_id: str = Field(..., description="User ID this allergy belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Inventory Models
class InventoryItemBase(BaseModel):
    """Base inventory item model."""
    item_name: str = Field(..., description="Name of the inventory item")
    quantity: float = Field(..., gt=0, description="Quantity of the item")
    unit: Optional[str] = Field("piece", description="Unit of measurement")
    expiry_date: date = Field(..., description="Expiry date of the item")


class InventoryItemCreate(InventoryItemBase):
    """Model for creating a new inventory item."""
    pass


class InventoryItemUpdate(BaseModel):
    """Model for updating an inventory item."""
    item_name: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    expiry_date: Optional[date] = None


class InventoryItem(InventoryItemBase):
    """Inventory item model with ID and timestamps."""
    id: str = Field(..., description="Inventory item ID")
    user_id: str = Field(..., description="User ID this item belongs to")
    added_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Recipe Models
class RecipeBase(BaseModel):
    """Base recipe model."""
    name: str = Field(..., description="Recipe name")
    image_url: Optional[str] = Field(None, description="URL to recipe image")
    ingredients: List[str] = Field(default=[], description="List of ingredients")
    instructions: Optional[str] = Field(None, description="Cooking instructions")
    prep_time: Optional[int] = Field(None, description="Preparation time in minutes")
    servings: Optional[int] = Field(None, description="Number of servings")
    source_url: Optional[str] = Field(None, description="Source URL")


class RecipeCreate(RecipeBase):
    """Model for creating a new recipe."""
    spoonacular_id: Optional[int] = Field(None, description="Spoonacular API ID")


class Recipe(RecipeBase):
    """Recipe model with ID and timestamps."""
    id: str = Field(..., description="Recipe ID")
    spoonacular_id: Optional[int] = Field(None, description="Spoonacular API ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# User Feedback Models
class UserFeedbackBase(BaseModel):
    """Base user feedback model."""
    recipe_id: str = Field(..., description="Recipe ID")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")


class UserFeedbackCreate(UserFeedbackBase):
    """Model for creating new user feedback."""
    pass


class UserFeedback(UserFeedbackBase):
    """User feedback model with ID and timestamps."""
    id: str = Field(..., description="Feedback ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# Recipe Recommendation Models
class RecipeRecommendationBase(BaseModel):
    """Base recipe recommendation model."""
    recipe_id: str = Field(..., description="Recipe ID")
    inventory_match_percentage: float = Field(..., ge=0, le=100, description="Match percentage")
    expiring_ingredients: List[str] = Field(default=[], description="List of expiring ingredients")
    recommendation_score: Optional[float] = Field(None, description="Overall recommendation score")
    explanation: Optional[str] = Field(None, description="AI-generated explanation")


class RecipeRecommendationCreate(RecipeRecommendationBase):
    """Model for creating a new recipe recommendation."""
    pass


class RecipeRecommendation(RecipeRecommendationBase):
    """Recipe recommendation model with ID and timestamps."""
    id: str = Field(..., description="Recommendation ID")
    user_id: str = Field(..., description="User ID")
    recommended_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
