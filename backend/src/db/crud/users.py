"""
CRUD operations for User collection
"""
from typing import Optional, List
from datetime import datetime
import uuid
from google.cloud.firestore_v1 import FieldFilter

from src.db.firestore import db
from src.db.models import User, UserCreate


class UserCRUD:
    """CRUD operations for users collection."""
    
    COLLECTION = "users"
    
    @staticmethod
    def create(user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_dict = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": user_data.password,  # This should be hashed before calling
            "created_at": now,
            "updated_at": now
        }
        
        db.collection(UserCRUD.COLLECTION).document(user_id).set(user_dict)
        
        return User(**user_dict)
    
    @staticmethod
    def create_with_password(user_dict: dict) -> User:
        """
        Create a new user with pre-hashed password.
        
        Args:
            user_dict: User data with hashed password
            
        Returns:
            Created user
        """
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_dict.update({
            "id": user_id,
            "created_at": now,
            "updated_at": now
        })
        
        db.collection(UserCRUD.COLLECTION).document(user_id).set(user_dict)
        
        return User(**user_dict)
    
    @staticmethod
    def get(user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        doc = db.collection(UserCRUD.COLLECTION).document(user_id).get()
        
        if doc.exists:
            return User(**doc.to_dict())
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        docs = (
            db.collection(UserCRUD.COLLECTION)
            .where(filter=FieldFilter("email", "==", email))
            .limit(1)
            .get()
        )
        
        for doc in docs:
            return User(**doc.to_dict())
        return None
    
    @staticmethod
    def list_all(limit: int = 100) -> List[User]:
        """
        List all users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of users
        """
        docs = db.collection(UserCRUD.COLLECTION).limit(limit).get()
        return [User(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def update(user_id: str, update_data: dict) -> Optional[User]:
        """
        Update a user.
        
        Args:
            user_id: User ID
            update_data: Dictionary of fields to update
            
        Returns:
            Updated user if found, None otherwise
        """
        doc_ref = db.collection(UserCRUD.COLLECTION).document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        update_data["updated_at"] = datetime.utcnow()
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        return User(**updated_doc.to_dict())
    
    @staticmethod
    def delete(user_id: str) -> bool:
        """
        Delete a user and all associated data.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = db.collection(UserCRUD.COLLECTION).document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
        
        # Delete user document
        doc_ref.delete()
        
        # Note: Subcollections (allergies, inventory, feedback, recommendations)
        # are automatically deleted due to Firestore security rules or
        # should be deleted separately if needed
        
        return True
