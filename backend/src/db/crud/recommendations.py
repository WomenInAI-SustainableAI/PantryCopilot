"""
CRUD operations for Recipe Recommendations subcollection
"""
from typing import List, Optional
from datetime import datetime
import uuid

from src.db.firestore import db
from src.db.models import RecipeRecommendation, RecipeRecommendationCreate


class RecommendationCRUD:
    """CRUD operations for recipe recommendations subcollection."""
    
    USERS_COLLECTION = "users"
    RECOMMENDATIONS_SUBCOLLECTION = "recommendations"
    
    @staticmethod
    def create(user_id: str, recommendation_data: RecipeRecommendationCreate) -> RecipeRecommendation:
        """
        Create a new recipe recommendation.
        
        Args:
            user_id: User ID
            recommendation_data: Recommendation creation data
            
        Returns:
            Created recommendation
        """
        recommendation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        recommendation_dict = {
            "id": recommendation_id,
            "user_id": user_id,
            "recipe_id": recommendation_data.recipe_id,
            "inventory_match_percentage": recommendation_data.inventory_match_percentage,
            "expiring_ingredients": recommendation_data.expiring_ingredients,
            "recommendation_score": recommendation_data.recommendation_score,
            "explanation": recommendation_data.explanation,
            "recommended_at": now
        }
        
        db.collection(RecommendationCRUD.USERS_COLLECTION).document(user_id).collection(
            RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION
        ).document(recommendation_id).set(recommendation_dict)
        
        return RecipeRecommendation(**recommendation_dict)
    
    @staticmethod
    def get(user_id: str, recommendation_id: str) -> Optional[RecipeRecommendation]:
        """
        Get a specific recommendation.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            
        Returns:
            Recommendation if found, None otherwise
        """
        doc = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
            .document(recommendation_id)
            .get()
        )
        
        if doc.exists:
            return RecipeRecommendation(**doc.to_dict())
        return None
    
    @staticmethod
    def list_by_user(user_id: str, limit: int = 50) -> List[RecipeRecommendation]:
        """
        List all recommendations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommendations ordered by date (newest first)
        """
        docs = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
            .order_by("recommended_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        
        return [RecipeRecommendation(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def get_top_recommendations(user_id: str, limit: int = 10) -> List[RecipeRecommendation]:
        """
        Get top recommendations by score.
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommendations ordered by score (highest first)
        """
        docs = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
            .order_by("recommendation_score", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        
        return [RecipeRecommendation(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def update(user_id: str, recommendation_id: str, update_data: dict) -> Optional[RecipeRecommendation]:
        """
        Update a recommendation.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            update_data: Fields to update
            
        Returns:
            Updated recommendation if found, None otherwise
        """
        doc_ref = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
            .document(recommendation_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        doc_ref.update(update_data)
        
        updated_doc = doc_ref.get()
        return RecipeRecommendation(**updated_doc.to_dict())
    
    @staticmethod
    def delete(user_id: str, recommendation_id: str) -> bool:
        """
        Delete a recommendation.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
            .document(recommendation_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def delete_all(user_id: str) -> int:
        """
        Delete all recommendations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of recommendations deleted
        """
        collection_ref = (
            db.collection(RecommendationCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(RecommendationCRUD.RECOMMENDATIONS_SUBCOLLECTION)
        )
        
        docs = collection_ref.get()
        count = 0
        
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        return count
