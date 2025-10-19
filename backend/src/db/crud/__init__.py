"""
CRUD Operations Module
Simple wrapper module for all database operations
"""
from src.db.crud.users import UserCRUD
from src.db.crud.allergies import AllergyCRUD
from src.db.crud.inventory import InventoryCRUD
from src.db.crud.recipes import RecipeCRUD
from src.db.crud.feedback import UserFeedbackCRUD
from src.db.crud.recommendations import RecommendationCRUD

# Simple aliases for easier imports
users = UserCRUD
allergies = AllergyCRUD
inventory = InventoryCRUD
recipes = RecipeCRUD
feedback = UserFeedbackCRUD
recommendations = RecommendationCRUD

# Direct function aliases for common operations
get_user = UserCRUD.get
create_user = UserCRUD.create
update_user = UserCRUD.update
delete_user = UserCRUD.delete

get_user_allergies = AllergyCRUD.list_by_user
create_allergy = AllergyCRUD.create
delete_allergy = AllergyCRUD.delete

get_user_inventory = InventoryCRUD.list_by_user
get_inventory_item = InventoryCRUD.get
create_inventory_item = InventoryCRUD.create
update_inventory_item = InventoryCRUD.update
delete_inventory_item = InventoryCRUD.delete
get_expiring_items = InventoryCRUD.get_expiring_items

get_user_feedback = UserFeedbackCRUD.list_by_user
create_feedback = UserFeedbackCRUD.create
get_recipe_feedback = UserFeedbackCRUD.get_by_recipe

get_user_recommendations = RecommendationCRUD.list_by_user
create_recommendation = RecommendationCRUD.create

__all__ = [
    "UserCRUD",
    "AllergyCRUD", 
    "InventoryCRUD",
    "RecipeCRUD",
    "UserFeedbackCRUD",
    "RecommendationCRUD",
    "users",
    "allergies",
    "inventory",
    "recipes",
    "feedback",
    "recommendations",
    "get_user",
    "create_user",
    "update_user",
    "delete_user",
    "get_user_allergies",
    "create_allergy",
    "delete_allergy",
    "get_user_inventory",
    "get_inventory_item",
    "create_inventory_item",
    "update_inventory_item",
    "delete_inventory_item",
    "get_expiring_items",
    "get_user_feedback",
    "create_feedback",
    "get_recipe_feedback",
    "get_user_recommendations",
    "create_recommendation",
]
