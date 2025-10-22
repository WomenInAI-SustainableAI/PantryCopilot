"""
CMAB Manager Service

This service manages user-specific CMAB recommenders, providing:
- Persistence: Load/save CMAB state to Firestore
- Integration: Connect CMAB with recommendation and feedback systems
- Cold Start: Initialize new users with reasonable defaults
"""
from typing import Dict, List, Optional
from datetime import datetime

from src.services.cmab_service import (
    CMABRecommender,
    CMABStats,
    RecipeContext,
    RECIPE_CATEGORIES,
    extract_context_from_inventory,
    map_recipe_to_category
)
from src.db.crud.cmab_stats import CMABStatsCRUD
from src.db.models import InventoryItem, UserFeedback


class CMABManager:
    """
    Manager for user-specific CMAB recommenders with persistence.
    """
    
    def __init__(self):
        # In-memory cache of active recommenders
        self._cache: Dict[str, CMABRecommender] = {}
        self._crud = CMABStatsCRUD()
    
    def get_recommender(self, user_id: str) -> CMABRecommender:
        """
        Get or create CMAB recommender for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            CMABRecommender instance
        """
        # Check cache first
        if user_id in self._cache:
            return self._cache[user_id]
        
        # Load from database
        recommender = self._load_from_db(user_id)
        
        # Cache it
        self._cache[user_id] = recommender
        
        return recommender
    
    def _load_from_db(self, user_id: str) -> CMABRecommender:
        """
        Load CMAB recommender from database.
        
        Args:
            user_id: User ID
            
        Returns:
            CMABRecommender instance (new if not found)
        """
        stats_data = self._crud.get_user_stats(user_id)
        
        # Create new recommender
        recommender = CMABRecommender()
        
        if stats_data and "arms" in stats_data:
            # Restore arm statistics from database
            arms = stats_data["arms"]
            
            for category, arm_stats in arms.items():
                if category in recommender.arm_stats:
                    stats = recommender.arm_stats[category]
                    stats.alpha = arm_stats.get("alpha", 1.0)
                    stats.beta = arm_stats.get("beta", 1.0)
                    stats.total_pulls = arm_stats.get("total_pulls", 0)
                    stats.total_reward = arm_stats.get("total_reward", 0.0)
                    stats.cooked_count = arm_stats.get("cooked_count", 0)
                    stats.upvote_count = arm_stats.get("upvote_count", 0)
                    stats.downvote_count = arm_stats.get("downvote_count", 0)
        
        return recommender
    
    def save_recommender(self, user_id: str):
        """
        Save CMAB recommender state to database.
        
        Args:
            user_id: User ID
        """
        if user_id not in self._cache:
            return
        
        recommender = self._cache[user_id]
        
        # Convert to serializable format
        arms_data = {}
        for category, stats in recommender.arm_stats.items():
            arms_data[category] = {
                "alpha": stats.alpha,
                "beta": stats.beta,
                "total_pulls": stats.total_pulls,
                "total_reward": stats.total_reward,
                "cooked_count": stats.cooked_count,
                "upvote_count": stats.upvote_count,
                "downvote_count": stats.downvote_count
            }
        
        stats_data = {
            "arms": arms_data,
            "updated_at": datetime.utcnow()
        }
        
        self._crud.save_user_stats(user_id, stats_data)
    
    def record_feedback(
        self,
        user_id: str,
        recipe: Dict,
        feedback_type: str,
        inventory: Optional[List[InventoryItem]] = None
    ):
        """
        Record user feedback and update CMAB statistics.
        
        Args:
            user_id: User ID
            recipe: Recipe dictionary
            feedback_type: Type of feedback ('upvote', 'downvote', 'cooked', 'skip', 'ignored')
            inventory: User's inventory for context (optional)
        """
        # Get recommender
        recommender = self.get_recommender(user_id)
        
        # Map recipe to category
        category = map_recipe_to_category(recipe)
        
        # Extract context if inventory provided
        context = None
        if inventory:
            context = extract_context_from_inventory(inventory)
        
        # Update recommender
        recommender.update_from_feedback(category, feedback_type, context)
        
        # Persist to database
        self.save_recommender(user_id)
    
    def get_category_recommendations(
        self,
        user_id: str,
        inventory: List[InventoryItem],
        n_categories: int = 3
    ) -> List[str]:
        """
        Get recommended recipe categories for a user.
        
        Args:
            user_id: User ID
            inventory: User's inventory
            n_categories: Number of categories to recommend
            
        Returns:
            List of recommended category names
        """
        # Get recommender
        recommender = self.get_recommender(user_id)
        
        # Extract context
        context = extract_context_from_inventory(inventory)
        
        # Select arms
        selected_categories = recommender.select_arms(context, n_arms=n_categories)
        
        return selected_categories
    
    def get_user_preferences_summary(self, user_id: str) -> Dict:
        """
        Get summary of user's learned preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with preference statistics
        """
        recommender = self.get_recommender(user_id)
        
        # Get rankings
        rankings = recommender.get_arm_rankings()
        
        # Format summary
        summary = {
            "top_categories": [
                {
                    "category": cat,
                    "preference_score": round(mean, 3),
                    "total_interactions": pulls
                }
                for cat, mean, pulls in rankings[:5]
            ],
            "total_categories": len(RECIPE_CATEGORIES),
            "explored_categories": sum(1 for _, _, pulls in rankings if pulls > 0),
            "is_cold_start": recommender._is_cold_start()
        }
        
        return summary
    
    def reset_user_stats(self, user_id: str):
        """
        Reset CMAB statistics for a user.
        
        Args:
            user_id: User ID
        """
        # Remove from cache
        if user_id in self._cache:
            del self._cache[user_id]
        
        # Delete from database
        self._crud.delete_user_stats(user_id)
    
    def clear_cache(self):
        """Clear in-memory cache of recommenders."""
        self._cache.clear()


# Global singleton instance
cmab_manager = CMABManager()
