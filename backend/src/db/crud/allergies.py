"""
CRUD operations for Allergy subcollection
"""
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from src.db.firestore import db
from src.db.models import Allergy, AllergyCreate


class AllergyCRUD:
    """CRUD operations for user allergies subcollection."""
    
    USERS_COLLECTION = "users"
    ALLERGIES_SUBCOLLECTION = "allergies"
    
    @staticmethod
    def create(user_id: str, allergy_data: AllergyCreate) -> Allergy:
        """
        Create a new allergy for a user.
        
        Args:
            user_id: User ID
            allergy_data: Allergy creation data
            
        Returns:
            Created allergy
        """
        allergy_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        allergy_dict = {
            "id": allergy_id,
            "user_id": user_id,
            "allergen": allergy_data.allergen,
            "created_at": now
        }
        
        db.collection(AllergyCRUD.USERS_COLLECTION).document(user_id).collection(
            AllergyCRUD.ALLERGIES_SUBCOLLECTION
        ).document(allergy_id).set(allergy_dict)
        
        return Allergy(**allergy_dict)
    
    @staticmethod
    def get(user_id: str, allergy_id: str) -> Optional[Allergy]:
        """
        Get a specific allergy.
        
        Args:
            user_id: User ID
            allergy_id: Allergy ID
            
        Returns:
            Allergy if found, None otherwise
        """
        doc = (
            db.collection(AllergyCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(AllergyCRUD.ALLERGIES_SUBCOLLECTION)
            .document(allergy_id)
            .get()
        )
        
        if doc.exists:
            return Allergy(**doc.to_dict())
        return None
    
    @staticmethod
    def list_by_user(user_id: str) -> List[Allergy]:
        """
        List all allergies for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of allergies
        """
        docs = (
            db.collection(AllergyCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(AllergyCRUD.ALLERGIES_SUBCOLLECTION)
            .get()
        )
        
        return [Allergy(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def delete(user_id: str, allergy_id: str) -> bool:
        """
        Delete an allergy.
        
        Args:
            user_id: User ID
            allergy_id: Allergy ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(AllergyCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(AllergyCRUD.ALLERGIES_SUBCOLLECTION)
            .document(allergy_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def delete_all(user_id: str) -> int:
        """
        Delete all allergies for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of allergies deleted
        """
        collection_ref = (
            db.collection(AllergyCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(AllergyCRUD.ALLERGIES_SUBCOLLECTION)
        )
        
        docs = collection_ref.get()
        count = 0
        
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        return count
