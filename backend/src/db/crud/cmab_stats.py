"""
CRUD operations for CMAB (Contextual Multi-Armed Bandit) statistics.

Stores and retrieves per-user CMAB statistics for recipe category recommendations.
"""
from typing import Dict, Optional
from datetime import datetime
import uuid

from src.db.firestore import db


class CMABStatsCRUD:
    """CRUD operations for CMAB statistics subcollection."""
    
    USERS_COLLECTION = "users"
    CMAB_SUBCOLLECTION = "cmab_stats"
    
    @staticmethod
    def get_user_stats(user_id: str) -> Optional[Dict]:
        """
        Get CMAB statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of arm statistics or None if not found
        """
        doc = (
            db.collection(CMABStatsCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(CMABStatsCRUD.CMAB_SUBCOLLECTION)
            .document("stats")
            .get()
        )
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    @staticmethod
    def save_user_stats(user_id: str, stats_data: Dict) -> Dict:
        """
        Save CMAB statistics for a user.
        
        Args:
            user_id: User ID
            stats_data: Dictionary containing arm statistics
            
        Returns:
            Saved statistics
        """
        stats_data["updated_at"] = datetime.utcnow()
        
        db.collection(CMABStatsCRUD.USERS_COLLECTION).document(user_id).collection(
            CMABStatsCRUD.CMAB_SUBCOLLECTION
        ).document("stats").set(stats_data, merge=True)
        
        return stats_data
    
    @staticmethod
    def update_arm_stats(
        user_id: str,
        category: str,
        alpha: float,
        beta: float,
        total_pulls: int,
        total_reward: float,
        cooked_count: int = 0,
        upvote_count: int = 0,
        downvote_count: int = 0
    ) -> Dict:
        """
        Update statistics for a specific arm (recipe category).
        
        Args:
            user_id: User ID
            category: Recipe category name
            alpha: Beta distribution alpha parameter
            beta: Beta distribution beta parameter
            total_pulls: Total number of times this arm was selected
            total_reward: Cumulative reward
            cooked_count: Number of times recipes were cooked
            upvote_count: Number of upvotes
            downvote_count: Number of downvotes
            
        Returns:
            Updated statistics
        """
        arm_data = {
            f"arms.{category}.alpha": alpha,
            f"arms.{category}.beta": beta,
            f"arms.{category}.total_pulls": total_pulls,
            f"arms.{category}.total_reward": total_reward,
            f"arms.{category}.cooked_count": cooked_count,
            f"arms.{category}.upvote_count": upvote_count,
            f"arms.{category}.downvote_count": downvote_count,
            "updated_at": datetime.utcnow()
        }
        
        db.collection(CMABStatsCRUD.USERS_COLLECTION).document(user_id).collection(
            CMABStatsCRUD.CMAB_SUBCOLLECTION
        ).document("stats").set(arm_data, merge=True)
        
        return arm_data
    
    @staticmethod
    def delete_user_stats(user_id: str) -> bool:
        """
        Delete CMAB statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(CMABStatsCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(CMABStatsCRUD.CMAB_SUBCOLLECTION)
            .document("stats")
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def reset_arm_stats(user_id: str, category: str) -> bool:
        """
        Reset statistics for a specific arm.
        
        Args:
            user_id: User ID
            category: Recipe category name
            
        Returns:
            True if reset, False if user stats not found
        """
        # Reset to initial values (Beta(1, 1) prior)
        arm_data = {
            f"arms.{category}.alpha": 1.0,
            f"arms.{category}.beta": 1.0,
            f"arms.{category}.total_pulls": 0,
            f"arms.{category}.total_reward": 0.0,
            f"arms.{category}.cooked_count": 0,
            f"arms.{category}.upvote_count": 0,
            f"arms.{category}.downvote_count": 0,
            "updated_at": datetime.utcnow()
        }
        
        doc_ref = (
            db.collection(CMABStatsCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(CMABStatsCRUD.CMAB_SUBCOLLECTION)
            .document("stats")
        )
        
        if not doc_ref.get().exists:
            return False
        
        doc_ref.set(arm_data, merge=True)
        return True


# Singleton instance
cmab_stats_crud = CMABStatsCRUD()
