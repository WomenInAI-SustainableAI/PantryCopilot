"""
CRUD operations for Recipe collection
"""
from typing import Optional, List
from datetime import datetime
import uuid
from google.cloud.firestore_v1 import FieldFilter

from src.db.firestore import db
from src.db.models import Recipe, RecipeCreate


class RecipeCRUD:
    """CRUD operations for recipes collection."""
    
    COLLECTION = "recipes"
    
    @staticmethod
    def create(recipe_data: RecipeCreate) -> Recipe:
        """
        Create a new recipe.
        
        Args:
            recipe_data: Recipe creation data
            
        Returns:
            Created recipe
        """
        recipe_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        recipe_dict = {
            "id": recipe_id,
            "spoonacular_id": recipe_data.spoonacular_id,
            "name": recipe_data.name,
            "image_url": recipe_data.image_url,
            "ingredients": recipe_data.ingredients,
            "instructions": recipe_data.instructions,
            "prep_time": recipe_data.prep_time,
            "servings": recipe_data.servings,
            "source_url": recipe_data.source_url,
            "created_at": now
        }
        
        db.collection(RecipeCRUD.COLLECTION).document(recipe_id).set(recipe_dict)
        
        return Recipe(**recipe_dict)
    
    @staticmethod
    def get(recipe_id: str) -> Optional[Recipe]:
        """
        Get a recipe by ID.
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            Recipe if found, None otherwise
        """
        doc = db.collection(RecipeCRUD.COLLECTION).document(recipe_id).get()
        
        if doc.exists:
            return Recipe(**doc.to_dict())
        return None
    
    @staticmethod
    def get_by_spoonacular_id(spoonacular_id: int) -> Optional[Recipe]:
        """
        Get a recipe by Spoonacular ID.
        
        Args:
            spoonacular_id: Spoonacular API ID
            
        Returns:
            Recipe if found, None otherwise
        """
        docs = (
            db.collection(RecipeCRUD.COLLECTION)
            .where(filter=FieldFilter("spoonacular_id", "==", spoonacular_id))
            .limit(1)
            .get()
        )
        
        for doc in docs:
            return Recipe(**doc.to_dict())
        return None
    
    @staticmethod
    def list_all(limit: int = 100) -> List[Recipe]:
        """
        List all recipes.
        
        Args:
            limit: Maximum number of recipes to return
            
        Returns:
            List of recipes
        """
        docs = db.collection(RecipeCRUD.COLLECTION).limit(limit).get()
        return [Recipe(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def search_by_name(name_query: str, limit: int = 20) -> List[Recipe]:
        """
        Search recipes by name (partial match).
        
        Args:
            name_query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching recipes
        """
        # Note: Firestore doesn't support full-text search natively
        # This is a simple implementation using >= and < for prefix matching
        end_query = name_query[:-1] + chr(ord(name_query[-1]) + 1)
        
        docs = (
            db.collection(RecipeCRUD.COLLECTION)
            .where(filter=FieldFilter("name", ">=", name_query))
            .where(filter=FieldFilter("name", "<", end_query))
            .limit(limit)
            .get()
        )
        
        return [Recipe(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def update(recipe_id: str, update_data: dict) -> Optional[Recipe]:
        """
        Update a recipe.
        
        Args:
            recipe_id: Recipe ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated recipe if found, None otherwise
        """
        doc_ref = db.collection(RecipeCRUD.COLLECTION).document(recipe_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        return Recipe(**updated_doc.to_dict())
    
    @staticmethod
    def delete(recipe_id: str) -> bool:
        """
        Delete a recipe.
        
        Args:
            recipe_id: Recipe ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = db.collection(RecipeCRUD.COLLECTION).document(recipe_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
