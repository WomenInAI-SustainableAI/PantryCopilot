"""
CRUD operations for User Feedback subcollection
"""
from typing import List, Optional
from datetime import datetime
import uuid
from google.cloud.firestore_v1 import FieldFilter

from src.db.firestore import db
from src.db.models import UserFeedback, UserFeedbackCreate, FeedbackType


class UserFeedbackCRUD:
    """CRUD operations for user feedback subcollection."""
    
    USERS_COLLECTION = "users"
    FEEDBACK_SUBCOLLECTION = "feedback"
    
    @staticmethod
    def create(user_id: str, feedback_data: UserFeedbackCreate) -> UserFeedback:
        """
        Create new user feedback.
        
        Args:
            user_id: User ID
            feedback_data: Feedback creation data
            
        Returns:
            Created feedback
        """
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        feedback_dict = {
            "id": feedback_id,
            "user_id": user_id,
            "recipe_id": feedback_data.recipe_id,
            "feedback_type": feedback_data.feedback_type.value,
            "created_at": now
        }
        
        db.collection(UserFeedbackCRUD.USERS_COLLECTION).document(user_id).collection(
            UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION
        ).document(feedback_id).set(feedback_dict)
        
        return UserFeedback(**feedback_dict)
    
    @staticmethod
    def get(user_id: str, feedback_id: str) -> Optional[UserFeedback]:
        """
        Get specific feedback.
        
        Args:
            user_id: User ID
            feedback_id: Feedback ID
            
        Returns:
            Feedback if found, None otherwise
        """
        doc = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
            .document(feedback_id)
            .get()
        )
        
        if doc.exists:
            return UserFeedback(**doc.to_dict())
        return None
    
    @staticmethod
    def list_by_user(user_id: str, limit: int = 100) -> List[UserFeedback]:
        """
        List all feedback for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of feedback items to return
            
        Returns:
            List of feedback
        """
        docs = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        
        return [UserFeedback(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def get_by_recipe(user_id: str, recipe_id: str) -> Optional[UserFeedback]:
        """
        Get user feedback for a specific recipe.
        
        Args:
            user_id: User ID
            recipe_id: Recipe ID
            
        Returns:
            Feedback if found, None otherwise
        """
        docs = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
            .where(filter=FieldFilter("recipe_id", "==", recipe_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(1)
            .get()
        )
        
        for doc in docs:
            return UserFeedback(**doc.to_dict())
        return None
    
    @staticmethod
    def get_by_feedback_type(user_id: str, feedback_type: FeedbackType, limit: int = 50) -> List[UserFeedback]:
        """
        Get feedback by type (upvote, downvote, skip).
        
        Args:
            user_id: User ID
            feedback_type: Type of feedback
            limit: Maximum number of feedback items to return
            
        Returns:
            List of feedback
        """
        docs = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
            .where(filter=FieldFilter("feedback_type", "==", feedback_type.value))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        
        return [UserFeedback(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def delete(user_id: str, feedback_id: str) -> bool:
        """
        Delete feedback.
        
        Args:
            user_id: User ID
            feedback_id: Feedback ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
            .document(feedback_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def delete_all(user_id: str) -> int:
        """
        Delete all feedback for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of feedback items deleted
        """
        collection_ref = (
            db.collection(UserFeedbackCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(UserFeedbackCRUD.FEEDBACK_SUBCOLLECTION)
        )
        
        docs = collection_ref.get()
        count = 0
        
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        return count
