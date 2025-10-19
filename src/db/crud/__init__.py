# CRUD operations module
from src.db.crud.users import UserCRUD
from src.db.crud.allergies import AllergyCRUD
from src.db.crud.inventory import InventoryCRUD
from src.db.crud.recipes import RecipeCRUD
from src.db.crud.feedback import UserFeedbackCRUD
from src.db.crud.recommendations import RecommendationCRUD

__all__ = [
    "UserCRUD",
    "AllergyCRUD",
    "InventoryCRUD",
    "RecipeCRUD",
    "UserFeedbackCRUD",
    "RecommendationCRUD"
]
