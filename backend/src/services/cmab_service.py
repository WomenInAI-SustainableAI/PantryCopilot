"""
Contextual Multi-Armed Bandit (CMAB) Service for Recipe Recommendations

This service implements a contextual bandit approach where:
- Arms: Recipe categories (Italian, Asian, Quick Meals, etc.)
- Context: User's inventory state (expiring items, available categories)
- Reward: User feedback (👍 = +1, 👎 = -1, Cooked = +2, Ignored/Skip = 0)
- Algorithm: Thompson Sampling with contextual features

Cold Start Strategy:
1. Epsilon-greedy exploration (ε=0.3 for new users, decays to 0.1)
2. Content-based bootstrapping using inventory match
3. Popularity baseline from all users
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, date, timezone

from src.db.models import InventoryItem, FeedbackType


class RecipeCategory:
    """Recipe category definitions (Arms in the bandit)."""
    
    CATEGORIES = {
        "italian": ["pasta", "pizza", "risotto", "italian"],
        "asian": ["asian", "chinese", "japanese", "thai", "korean", "vietnamese"],
        "mexican": ["mexican", "taco", "burrito", "quesadilla"],
        "american": ["burger", "bbq", "american", "sandwich"],
        "mediterranean": ["mediterranean", "greek", "middle eastern"],
        "indian": ["indian", "curry"],
        "quick_meals": ["quick", "easy", "30 minute", "15 minute"],
        "baking": ["cake", "bread", "cookie", "muffin", "pastry"],
        "dessert": ["dessert", "sweet", "chocolate"],
        "breakfast": ["breakfast", "brunch", "pancake", "waffle"],
        "salad": ["salad", "bowl"],
        "soup": ["soup", "stew", "chili"],
        "vegetarian": ["vegetarian", "veggie"],
        "vegan": ["vegan"],
        "healthy": ["healthy", "low calorie", "diet"],
    }
    
    @staticmethod
    def classify_recipe(recipe_title: str, recipe_tags: List[str] = None) -> List[str]:
        """
        Classify a recipe into one or more categories.
        
        Args:
            recipe_title: Recipe title
            recipe_tags: Optional tags from Spoonacular
            
        Returns:
            List of category names
        """
        title_lower = recipe_title.lower()
        tags_lower = [tag.lower() for tag in (recipe_tags or [])]
        
        categories = []
        for category, keywords in RecipeCategory.CATEGORIES.items():
            for keyword in keywords:
                if keyword in title_lower or any(keyword in tag for tag in tags_lower):
                    categories.append(category)
                    break
        
        return categories if categories else ["general"]
    
    @staticmethod
    def get_all_categories() -> List[str]:
        """Get all category names."""
        return list(RecipeCategory.CATEGORIES.keys()) + ["general"]


class ContextFeatures:
    """Extract context features from user's current state."""
    
    @staticmethod
    def extract_inventory_context(inventory: List[InventoryItem]) -> Dict[str, float]:
        """
        Extract features from inventory state.
        
        Features:
        - expiring_count: Number of items expiring soon
        - total_items: Total inventory count
        - has_produce: Whether user has fresh produce
        - has_protein: Whether user has proteins
        - has_grains: Whether user has grains
        - inventory_diversity: Shannon entropy of item categories
        
        Args:
            inventory: User's inventory items
            
        Returns:
            Dictionary of context features
        """
        if not inventory:
            return {
                "expiring_count": 0.0,
                "total_items": 0.0,
                "has_produce": 0.0,
                "has_protein": 0.0,
                "has_grains": 0.0,
                "inventory_diversity": 0.0,
            }
        
        # Always use UTC on the server
        now = datetime.now(timezone.utc)
        expiring_count = 0
        
        # Category indicators
        produce_keywords = ["lettuce", "tomato", "onion", "pepper", "carrot", "vegetable", "fruit"]
        protein_keywords = ["chicken", "beef", "pork", "fish", "tofu", "egg", "meat"]
        grain_keywords = ["rice", "pasta", "bread", "flour", "wheat", "oat"]
        
        has_produce = 0
        has_protein = 0
        has_grains = 0
        
        for item in inventory:
            # Check expiring
            expiry_dt = item.expiry_date
            # Normalize to UTC-aware datetime
            if isinstance(expiry_dt, date) and not isinstance(expiry_dt, datetime):
                expiry_dt = datetime.combine(expiry_dt, datetime.min.time(), tzinfo=timezone.utc)
            if isinstance(expiry_dt, datetime):
                if getattr(expiry_dt, "tzinfo", None) is None:
                    expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                else:
                    expiry_dt = expiry_dt.astimezone(timezone.utc)
                days_until = (expiry_dt - now).days
                if days_until <= 3:
                    expiring_count += 1
            
            # Check categories
            item_name_lower = item.item_name.lower()
            if any(kw in item_name_lower for kw in produce_keywords):
                has_produce = 1
            if any(kw in item_name_lower for kw in protein_keywords):
                has_protein = 1
            if any(kw in item_name_lower for kw in grain_keywords):
                has_grains = 1
        
        # Calculate diversity (simplified)
        total_items = len(inventory)
        diversity = min(1.0, total_items / 20.0)  # Normalized to [0, 1]
        
        return {
            "expiring_count": float(expiring_count),
            "total_items": float(total_items),
            "has_produce": float(has_produce),
            "has_protein": float(has_protein),
            "has_grains": float(has_grains),
            "inventory_diversity": diversity,
        }


class ThompsonSamplingCMAB:
    """
    Thompson Sampling Contextual Multi-Armed Bandit.
    
    Uses Beta distribution for each arm (category) to model reward probability.
    Incorporates context through contextual features.
    """
    
    def __init__(self, categories: List[str]):
        """
        Initialize the CMAB model.
        
        Args:
            categories: List of category names (arms)
        """
        self.categories = categories
        
        # Beta distribution parameters for each arm: (successes, failures)
        # Start with (1, 1) for uniform prior
        self.alpha = {cat: 1.0 for cat in categories}  # Successes
        self.beta = {cat: 1.0 for cat in categories}   # Failures
        
        # Track pulls and rewards for each arm
        self.pulls = {cat: 0 for cat in categories}
        self.total_reward = {cat: 0.0 for cat in categories}
        
        # Context-specific parameters (simplified linear model)
        # Weight for each context feature per category
        self.context_weights = {
            cat: {
                "expiring_count": 0.5,
                "total_items": 0.2,
                "has_produce": 0.0,
                "has_protein": 0.0,
                "has_grains": 0.0,
                "inventory_diversity": 0.1,
            }
            for cat in categories
        }
        
        # Cold start parameters
        self.total_user_pulls = 0
        self.is_cold_start = True
    
    def get_exploration_rate(self) -> float:
        """
        Get epsilon for epsilon-greedy exploration.
        Decays from 0.3 to 0.1 as user gets more experience.
        """
        if self.total_user_pulls < 10:
            return 0.3  # High exploration for new users
        elif self.total_user_pulls < 50:
            return 0.2
        else:
            return 0.1  # Low exploration for experienced users
    
    def calculate_context_bonus(self, category: str, context: Dict[str, float]) -> float:
        """
        Calculate contextual bonus for a category given context.
        
        Args:
            category: Category name
            context: Context features
            
        Returns:
            Contextual bonus value
        """
        weights = self.context_weights.get(category, {})
        bonus = 0.0
        
        for feature, value in context.items():
            bonus += weights.get(feature, 0.0) * value
        
        return bonus
    
    def select_categories(
        self,
        context: Dict[str, float],
        n_categories: int = 3,
        available_categories: List[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Select top N categories using Thompson Sampling with epsilon-greedy.
        
        Args:
            context: Current context features
            n_categories: Number of categories to select
            available_categories: Optional list to filter categories
            
        Returns:
            List of (category, score) tuples
        """
        if available_categories is None:
            available_categories = self.categories
        
        epsilon = self.get_exploration_rate()
        
        # Epsilon-greedy: random exploration
        if np.random.random() < epsilon:
            # Pure exploration: random selection
            selected = np.random.choice(
                available_categories,
                size=min(n_categories, len(available_categories)),
                replace=False
            )
            return [(cat, 1.0) for cat in selected]
        
        # Thompson Sampling: sample from posterior
        category_scores = []
        
        for category in available_categories:
            # Sample from Beta distribution
            theta = np.random.beta(
                self.alpha[category],
                self.beta[category]
            )
            
            # Add contextual bonus
            context_bonus = self.calculate_context_bonus(category, context)
            
            # Final score
            score = theta + context_bonus
            category_scores.append((category, score))
        
        # Sort by score and select top N
        category_scores.sort(key=lambda x: x[1], reverse=True)
        return category_scores[:n_categories]
    
    def update(
        self,
        category: str,
        reward: float,
        context: Dict[str, float]
    ):
        """
        Update bandit model with observed reward.
        
        Args:
            category: Category that was selected
            reward: Observed reward (normalized to [0, 1] or [-1, 1])
            context: Context features when category was selected
        """
        # Normalize reward to [0, 1] for Beta distribution
        # Mapping: -1 -> 0, 0 -> 0.5, +1 -> 1, +2 -> 1
        normalized_reward = max(0, min(1, (reward + 1) / 3))
        
        # Update Beta distribution
        self.alpha[category] += normalized_reward
        self.beta[category] += (1 - normalized_reward)
        
        # Track statistics
        self.pulls[category] += 1
        self.total_reward[category] += reward
        self.total_user_pulls += 1
        
        # Update cold start flag
        if self.total_user_pulls >= 10:
            self.is_cold_start = False
        
        # Simple context weight update (gradient-like)
        learning_rate = 0.01
        for feature, value in context.items():
            if feature in self.context_weights[category]:
                # Update weight based on prediction error
                predicted = self.alpha[category] / (self.alpha[category] + self.beta[category])
                error = normalized_reward - predicted
                self.context_weights[category][feature] += learning_rate * error * value
    
    def get_statistics(self) -> Dict[str, Dict]:
        """Get current statistics for each category."""
        stats = {}
        
        for category in self.categories:
            mean_reward = (
                self.total_reward[category] / self.pulls[category]
                if self.pulls[category] > 0
                else 0.0
            )
            
            # Expected value from Beta distribution
            expected_value = self.alpha[category] / (self.alpha[category] + self.beta[category])
            
            stats[category] = {
                "pulls": self.pulls[category],
                "total_reward": self.total_reward[category],
                "mean_reward": mean_reward,
                "expected_value": expected_value,
                "alpha": self.alpha[category],
                "beta": self.beta[category],
            }
        
        return stats
    
    def to_dict(self) -> Dict:
        """Serialize model to dictionary for storage."""
        return {
            "categories": self.categories,
            "alpha": self.alpha,
            "beta": self.beta,
            "pulls": self.pulls,
            "total_reward": self.total_reward,
            "context_weights": self.context_weights,
            "total_user_pulls": self.total_user_pulls,
            "is_cold_start": self.is_cold_start,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "ThompsonSamplingCMAB":
        """Deserialize model from dictionary."""
        model = ThompsonSamplingCMAB(data["categories"])
        model.alpha = data["alpha"]
        model.beta = data["beta"]
        model.pulls = data["pulls"]
        model.total_reward = data["total_reward"]
        model.context_weights = data["context_weights"]
        model.total_user_pulls = data["total_user_pulls"]
        model.is_cold_start = data["is_cold_start"]
        return model


def convert_feedback_to_reward(feedback_type: str, is_cooked: bool = False) -> float:
    """
    Convert user feedback to numerical reward.
    
    Reward Scheme:
    - Upvote (👍): +1
    - Downvote (👎): -1
    - Cooked: +2
    - Skip/Ignored: 0
    
    Args:
        feedback_type: Type of feedback ("upvote", "downvote", "skip")
        is_cooked: Whether the recipe was cooked
        
    Returns:
        Numerical reward
    """
    if is_cooked:
        return 2.0
    
    if feedback_type == "upvote" or feedback_type == FeedbackType.UPVOTE.value:
        return 1.0
    elif feedback_type == "downvote" or feedback_type == FeedbackType.DOWNVOTE.value:
        return -1.0
    else:  # skip
        return 0.0
