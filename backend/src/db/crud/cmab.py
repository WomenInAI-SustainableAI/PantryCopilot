"""
CRUD operations for CMAB (Contextual Multi-Armed Bandit) models
Stores user-specific bandit models in Firestore
"""
from typing import Optional
from datetime import datetime

from src.db.firestore import db
from src.services.cmab_service import ThompsonSamplingCMAB, RecipeCategory


class CMABCRUD:
    """CRUD operations for CMAB models."""
    
    USERS_COLLECTION = "users"
    CMAB_DOCUMENT = "cmab_model"
    
    @staticmethod
    def get_or_create(user_id: str) -> ThompsonSamplingCMAB:
        """
        Get existing CMAB model for user or create new one.
        
        Args:
            user_id: User ID
            
        Returns:
            CMAB model
        """
        doc_ref = (
            db.collection(CMABCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection("models")
            .document(CMABCRUD.CMAB_DOCUMENT)
        )
        
        doc = doc_ref.get()
        
        if doc.exists:
            # Load existing model
            data = doc.to_dict()
            return ThompsonSamplingCMAB.from_dict(data)
        else:
            # Create new model
            categories = RecipeCategory.get_all_categories()
            model = ThompsonSamplingCMAB(categories)
            
            # Save to Firestore
            CMABCRUD.save(user_id, model)
            return model
    
    @staticmethod
    def save(user_id: str, model: ThompsonSamplingCMAB):
        """
        Save CMAB model to Firestore.
        
        Args:
            user_id: User ID
            model: CMAB model to save
        """
        doc_ref = (
            db.collection(CMABCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection("models")
            .document(CMABCRUD.CMAB_DOCUMENT)
        )
        
        model_dict = model.to_dict()
        model_dict["updated_at"] = datetime.utcnow()
        
        doc_ref.set(model_dict)
    
    @staticmethod
    def delete(user_id: str) -> bool:
        """
        Delete CMAB model for user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(CMABCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection("models")
            .document(CMABCRUD.CMAB_DOCUMENT)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def get_statistics(user_id: str) -> Optional[dict]:
        """
        Get CMAB statistics for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary or None
        """
        model = CMABCRUD.get_or_create(user_id)
        return model.get_statistics()
