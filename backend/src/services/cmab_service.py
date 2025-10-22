"""
Contextual Multi-Armed Bandit (CMAB) Service for Recipe Recommendations

This service implements a Thompson Sampling-based CMAB algorithm to learn
user preferences for different recipe categories based on their context
(inventory state, expiring items, etc.) and feedback.

Arms: Recipe categories (Italian, Asian, Quick Meals, Healthy, Comfort Food, etc.)
Context: User inventory state, expiring items, time of day, day of week
Reward: User feedback (👍 = +1, 👎 = -1, Cooked = +2, Ignored = 0)
Goal: Learn which recipe categories each user prefers in different contexts
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import math
import random
from collections import defaultdict
from src.db.models import InventoryItem, UserFeedback, FeedbackType


# Recipe category definitions (arms in CMAB)
RECIPE_CATEGORIES = [
    "italian",
    "asian", 
    "mexican",
    "american",
    "mediterranean",
    "indian",
    "quick_meals",  # < 30 min
    "healthy",
    "comfort_food",
    "vegetarian",
    "desserts",
    "breakfast",
    "salads"
]


class RecipeContext:
    """
    Context representation for CMAB.
    Captures user's current situation for better recommendations.
    """
    
    def __init__(
        self,
        has_expiring_items: bool = False,
        expiring_item_count: int = 0,
        inventory_diversity: float = 0.0,  # 0-1 scale
        time_of_day: str = "any",  # morning, afternoon, evening, night
        day_of_week: int = 0,  # 0-6 (Monday-Sunday)
        is_weekend: bool = False
    ):
        self.has_expiring_items = has_expiring_items
        self.expiring_item_count = expiring_item_count
        self.inventory_diversity = inventory_diversity
        self.time_of_day = time_of_day
        self.day_of_week = day_of_week
        self.is_weekend = is_weekend
    
    def to_feature_vector(self) -> List[float]:
        """
        Convert context to feature vector for learning.
        
        Returns:
            Feature vector representation
        """
        return [
            1.0 if self.has_expiring_items else 0.0,
            self.expiring_item_count / 10.0,  # Normalize
            self.inventory_diversity,
            1.0 if self.time_of_day == "morning" else 0.0,
            1.0 if self.time_of_day == "evening" else 0.0,
            1.0 if self.is_weekend else 0.0
        ]


class CMABStats:
    """
    Statistics for a single arm (recipe category) in CMAB.
    Uses Beta distribution parameters for Thompson Sampling.
    """
    
    def __init__(self):
        # Beta distribution parameters (alpha, beta)
        # Start with uniform prior: Beta(1, 1)
        self.alpha = 1.0  # Successes + 1
        self.beta = 1.0   # Failures + 1
        
        # Additional statistics
        self.total_pulls = 0
        self.total_reward = 0.0
        self.cooked_count = 0  # Special tracking for "cooked" actions
        self.upvote_count = 0
        self.downvote_count = 0
    
    def sample_theta(self) -> float:
        """
        Sample from Beta distribution (Thompson Sampling).
        
        Returns:
            Sampled probability of success
        """
        return random.betavariate(self.alpha, self.beta)
    
    def get_mean(self) -> float:
        """Get mean of Beta distribution."""
        return self.alpha / (self.alpha + self.beta)
    
    def get_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for the mean.
        
        Args:
            confidence: Confidence level (default 0.95)
            
        Returns:
            (lower_bound, upper_bound)
        """
        mean = self.get_mean()
        # Use normal approximation for large sample sizes
        if self.total_pulls > 30:
            variance = (self.alpha * self.beta) / ((self.alpha + self.beta)**2 * (self.alpha + self.beta + 1))
            std_error = math.sqrt(variance)
            z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
            margin = z_score * std_error
            return (max(0, mean - margin), min(1, mean + margin))
        return (0.0, 1.0)


class CMABRecommender:
    """
    Contextual Multi-Armed Bandit Recommender using Thompson Sampling.
    
    This class manages the learning and selection of recipe categories
    based on user context and historical feedback.
    """
    
    def __init__(self, epsilon: float = 0.1, cold_start_pulls: int = 10):
        """
        Initialize CMAB recommender.
        
        Args:
            epsilon: Exploration rate for epsilon-greedy cold start (default 0.1)
            cold_start_pulls: Minimum pulls per arm before pure exploitation (default 10)
        """
        self.epsilon = epsilon
        self.cold_start_pulls = cold_start_pulls
        
        # Statistics for each arm (recipe category)
        self.arm_stats: Dict[str, CMABStats] = {
            category: CMABStats() for category in RECIPE_CATEGORIES
        }
        
        # Context-dependent statistics (advanced feature for future)
        # For now, we use global statistics per arm
        self.context_stats: Dict[str, Dict[str, CMABStats]] = {}
    
    def _is_cold_start(self) -> bool:
        """Check if we're still in cold start phase."""
        min_pulls = min(stats.total_pulls for stats in self.arm_stats.values())
        return min_pulls < self.cold_start_pulls
    
    def select_arms(
        self,
        context: RecipeContext,
        n_arms: int = 3,
        available_categories: Optional[List[str]] = None
    ) -> List[str]:
        """
        Select top N arms (recipe categories) to recommend.
        
        Uses Thompson Sampling with epsilon-greedy exploration during cold start.
        
        Args:
            context: Current context for recommendation
            n_arms: Number of arms to select (default 3)
            available_categories: Optional list of available categories to choose from
            
        Returns:
            List of selected category names
        """
        if available_categories is None:
            available_categories = RECIPE_CATEGORIES
        
        # Cold start: Use epsilon-greedy to ensure exploration
        if self._is_cold_start() and random.random() < self.epsilon:
            # Explore: Select random categories, prioritizing least-tried
            pulls = [(cat, self.arm_stats[cat].total_pulls) 
                     for cat in available_categories]
            pulls.sort(key=lambda x: x[1])  # Sort by pulls (ascending)
            return [cat for cat, _ in pulls[:n_arms]]
        
        # Thompson Sampling: Sample theta for each arm and select top N
        sampled_values = []
        for category in available_categories:
            stats = self.arm_stats[category]
            theta = stats.sample_theta()
            sampled_values.append((category, theta))
        
        # Sort by sampled value (descending) and select top N
        sampled_values.sort(key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sampled_values[:n_arms]]
    
    def update(
        self,
        category: str,
        reward: float,
        context: Optional[RecipeContext] = None
    ):
        """
        Update arm statistics based on observed reward.
        
        Args:
            category: Recipe category that was selected
            reward: Observed reward (1 for success, 0 for failure, or scaled)
            context: Context in which the arm was pulled (optional)
        """
        if category not in self.arm_stats:
            return
        
        stats = self.arm_stats[category]
        stats.total_pulls += 1
        stats.total_reward += reward
        
        # Update Beta distribution parameters
        # Reward is scaled: +2 (cooked), +1 (upvote), 0 (ignored), -1 (downvote)
        # Convert to success/failure for Beta update
        
        # Normalize reward to [0, 1] for Beta distribution
        # Reward range: -1 to +2, so we map: -1->0, 0->0.33, +1->0.67, +2->1.0
        normalized_reward = (reward + 1) / 3.0  # Maps [-1, 2] to [0, 1]
        normalized_reward = max(0.0, min(1.0, normalized_reward))
        
        # Update with normalized reward
        stats.alpha += normalized_reward
        stats.beta += (1.0 - normalized_reward)
    
    def update_from_feedback(
        self,
        category: str,
        feedback_type: str,
        context: Optional[RecipeContext] = None
    ):
        """
        Update arm statistics from user feedback.
        
        Args:
            category: Recipe category
            feedback_type: Type of feedback ('upvote', 'downvote', 'cooked', 'skip', 'ignored')
            context: Context in which feedback was given
        """
        stats = self.arm_stats[category]
        
        # Map feedback to reward
        reward_map = {
            "upvote": 1.0,
            "downvote": -1.0,
            "cooked": 2.0,
            "skip": 0.0,
            "ignored": 0.0
        }
        
        reward = reward_map.get(feedback_type.lower(), 0.0)
        
        # Track specific feedback types
        if feedback_type.lower() == "cooked":
            stats.cooked_count += 1
        elif feedback_type.lower() == "upvote":
            stats.upvote_count += 1
        elif feedback_type.lower() == "downvote":
            stats.downvote_count += 1
        
        # Update statistics
        self.update(category, reward, context)
    
    def get_arm_rankings(self) -> List[Tuple[str, float, int]]:
        """
        Get current rankings of all arms.
        
        Returns:
            List of (category, mean_reward, total_pulls) sorted by mean reward
        """
        rankings = []
        for category, stats in self.arm_stats.items():
            mean = stats.get_mean()
            rankings.append((category, mean, stats.total_pulls))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def get_arm_stats(self, category: str) -> Optional[CMABStats]:
        """Get statistics for a specific arm."""
        return self.arm_stats.get(category)
    
    def reset_arm(self, category: str):
        """Reset statistics for a specific arm."""
        if category in self.arm_stats:
            self.arm_stats[category] = CMABStats()
    
    def reset_all(self):
        """Reset all arm statistics."""
        for category in self.arm_stats:
            self.arm_stats[category] = CMABStats()


def extract_context_from_inventory(
    inventory: List[InventoryItem],
    current_time: Optional[datetime] = None
) -> RecipeContext:
    """
    Extract context features from user inventory.
    
    Args:
        inventory: User's inventory items
        current_time: Current datetime (default: now)
        
    Returns:
        RecipeContext object
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Calculate expiring items
    expiring_count = 0
    today = current_time
    
    for item in inventory:
        expiry_dt = item.expiry_date
        if hasattr(expiry_dt, 'tzinfo') and expiry_dt.tzinfo is not None:
            expiry_dt = expiry_dt.replace(tzinfo=None)
        
        days_until_expiry = (expiry_dt - today).days
        if days_until_expiry <= 3:
            expiring_count += 1
    
    has_expiring = expiring_count > 0
    
    # Calculate inventory diversity (variety of items)
    # Simple heuristic: count of unique items normalized
    diversity = min(1.0, len(inventory) / 20.0)  # Assume 20+ items is max diversity
    
    # Time of day
    hour = current_time.hour
    if 5 <= hour < 11:
        time_of_day = "morning"
    elif 11 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"
    
    # Day of week
    day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
    is_weekend = day_of_week >= 5
    
    return RecipeContext(
        has_expiring_items=has_expiring,
        expiring_item_count=expiring_count,
        inventory_diversity=diversity,
        time_of_day=time_of_day,
        day_of_week=day_of_week,
        is_weekend=is_weekend
    )


def map_recipe_to_category(recipe: Dict) -> str:
    """
    Map a recipe to a category (arm) based on its attributes.
    
    Args:
        recipe: Recipe dictionary from Spoonacular
        
    Returns:
        Category name
    """
    # Extract cuisines from recipe
    cuisines = recipe.get("cuisines", [])
    dish_types = recipe.get("dishTypes", [])
    ready_in_minutes = recipe.get("readyInMinutes", 999)
    vegetarian = recipe.get("vegetarian", False)
    
    # Priority mapping
    if ready_in_minutes <= 30:
        return "quick_meals"
    
    # Check cuisines
    for cuisine in cuisines:
        cuisine_lower = cuisine.lower()
        if "italian" in cuisine_lower:
            return "italian"
        elif "chinese" in cuisine_lower or "japanese" in cuisine_lower or "thai" in cuisine_lower:
            return "asian"
        elif "mexican" in cuisine_lower:
            return "mexican"
        elif "indian" in cuisine_lower:
            return "indian"
        elif "mediterranean" in cuisine_lower:
            return "mediterranean"
        elif "american" in cuisine_lower:
            return "american"
    
    # Check dish types
    for dish_type in dish_types:
        dish_lower = dish_type.lower()
        if "breakfast" in dish_lower:
            return "breakfast"
        elif "dessert" in dish_lower or "sweet" in dish_lower:
            return "desserts"
        elif "salad" in dish_lower:
            return "salads"
    
    # Check dietary
    if vegetarian:
        return "vegetarian"
    
    # Check for healthy indicators
    health_keywords = ["healthy", "light", "fitness", "low calorie"]
    title_lower = recipe.get("title", "").lower()
    if any(keyword in title_lower for keyword in health_keywords):
        return "healthy"
    
    # Default to comfort food
    return "comfort_food"


def initialize_user_cmab(user_id: str, feedback_history: List[UserFeedback]) -> CMABRecommender:
    """
    Initialize CMAB recommender for a user based on their feedback history.
    
    This provides warm start by learning from past feedback.
    
    Args:
        user_id: User ID
        feedback_history: List of historical feedback
        
    Returns:
        Initialized CMABRecommender
    """
    recommender = CMABRecommender()
    
    # Process historical feedback to update arm statistics
    # Note: We don't have recipe category in feedback, so we'd need to fetch it
    # For now, this is a placeholder for future enhancement
    
    return recommender
