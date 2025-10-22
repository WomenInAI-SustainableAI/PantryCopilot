"""
Unit tests for CMAB (Contextual Multi-Armed Bandit) Service

Tests the core CMAB functionality including:
- Thompson Sampling arm selection
- Reward updates
- Context extraction
- Recipe category mapping
- Cold start behavior
"""
import unittest
from datetime import datetime, timedelta
from src.services.cmab_service import (
    CMABRecommender,
    CMABStats,
    RecipeContext,
    RECIPE_CATEGORIES,
    extract_context_from_inventory,
    map_recipe_to_category
)
from src.db.models import InventoryItem


class TestCMABStats(unittest.TestCase):
    """Test CMABStats class."""
    
    def test_initial_stats(self):
        """Test initial state of CMABStats."""
        stats = CMABStats()
        self.assertEqual(stats.alpha, 1.0)
        self.assertEqual(stats.beta, 1.0)
        self.assertEqual(stats.total_pulls, 0)
        self.assertEqual(stats.total_reward, 0.0)
        self.assertEqual(stats.cooked_count, 0)
        self.assertEqual(stats.upvote_count, 0)
        self.assertEqual(stats.downvote_count, 0)
    
    def test_sample_theta(self):
        """Test theta sampling from Beta distribution."""
        stats = CMABStats()
        theta = stats.sample_theta()
        self.assertGreaterEqual(theta, 0.0)
        self.assertLessEqual(theta, 1.0)
    
    def test_get_mean(self):
        """Test mean calculation."""
        stats = CMABStats()
        # Initial mean should be 0.5 for Beta(1,1)
        self.assertEqual(stats.get_mean(), 0.5)
        
        # After some successes, mean should increase
        stats.alpha = 3.0
        stats.beta = 1.0
        self.assertEqual(stats.get_mean(), 0.75)


class TestRecipeContext(unittest.TestCase):
    """Test RecipeContext class."""
    
    def test_context_creation(self):
        """Test context object creation."""
        context = RecipeContext(
            has_expiring_items=True,
            expiring_item_count=3,
            inventory_diversity=0.7,
            time_of_day="evening",
            day_of_week=5,
            is_weekend=True
        )
        
        self.assertTrue(context.has_expiring_items)
        self.assertEqual(context.expiring_item_count, 3)
        self.assertEqual(context.inventory_diversity, 0.7)
        self.assertEqual(context.time_of_day, "evening")
        self.assertTrue(context.is_weekend)
    
    def test_feature_vector(self):
        """Test feature vector conversion."""
        context = RecipeContext(
            has_expiring_items=True,
            expiring_item_count=5,
            inventory_diversity=0.8,
            time_of_day="morning",
            is_weekend=False
        )
        
        features = context.to_feature_vector()
        self.assertEqual(len(features), 6)
        self.assertEqual(features[0], 1.0)  # has_expiring_items
        self.assertEqual(features[1], 0.5)  # expiring_count / 10
        self.assertEqual(features[2], 0.8)  # diversity
        self.assertEqual(features[3], 1.0)  # is morning
        self.assertEqual(features[5], 0.0)  # not weekend


class TestCMABRecommender(unittest.TestCase):
    """Test CMABRecommender class."""
    
    def setUp(self):
        """Set up test recommender."""
        self.recommender = CMABRecommender(epsilon=0.1, cold_start_pulls=10)
    
    def test_initialization(self):
        """Test recommender initialization."""
        self.assertEqual(len(self.recommender.arm_stats), len(RECIPE_CATEGORIES))
        for category in RECIPE_CATEGORIES:
            self.assertIn(category, self.recommender.arm_stats)
    
    def test_cold_start_detection(self):
        """Test cold start phase detection."""
        # Initially in cold start
        self.assertTrue(self.recommender._is_cold_start())
        
        # After pulling each arm 10 times, should exit cold start
        for category in RECIPE_CATEGORIES:
            for _ in range(10):
                self.recommender.update(category, 1.0)
        
        self.assertFalse(self.recommender._is_cold_start())
    
    def test_select_arms(self):
        """Test arm selection."""
        context = RecipeContext()
        
        # Select 3 arms
        selected = self.recommender.select_arms(context, n_arms=3)
        self.assertEqual(len(selected), 3)
        self.assertTrue(all(cat in RECIPE_CATEGORIES for cat in selected))
    
    def test_update_with_positive_reward(self):
        """Test updating with positive reward."""
        category = "italian"
        initial_alpha = self.recommender.arm_stats[category].alpha
        initial_beta = self.recommender.arm_stats[category].beta
        
        # Update with cooked (reward = +2)
        self.recommender.update(category, 2.0)
        
        # Alpha should increase more than beta
        stats = self.recommender.arm_stats[category]
        self.assertGreater(stats.alpha, initial_alpha)
        self.assertEqual(stats.total_pulls, 1)
        self.assertEqual(stats.total_reward, 2.0)
    
    def test_update_with_negative_reward(self):
        """Test updating with negative reward."""
        category = "asian"
        initial_alpha = self.recommender.arm_stats[category].alpha
        initial_beta = self.recommender.arm_stats[category].beta
        
        # Update with downvote (reward = -1)
        self.recommender.update(category, -1.0)
        
        # Beta should increase more than alpha
        stats = self.recommender.arm_stats[category]
        self.assertGreater(stats.beta, initial_beta)
        self.assertEqual(stats.total_pulls, 1)
        self.assertEqual(stats.total_reward, -1.0)
    
    def test_update_from_feedback(self):
        """Test updating from user feedback."""
        category = "quick_meals"
        
        # Test upvote
        self.recommender.update_from_feedback(category, "upvote")
        self.assertEqual(self.recommender.arm_stats[category].upvote_count, 1)
        self.assertEqual(self.recommender.arm_stats[category].total_reward, 1.0)
        
        # Test downvote
        self.recommender.update_from_feedback(category, "downvote")
        self.assertEqual(self.recommender.arm_stats[category].downvote_count, 1)
        self.assertEqual(self.recommender.arm_stats[category].total_reward, 0.0)
        
        # Test cooked
        self.recommender.update_from_feedback(category, "cooked")
        self.assertEqual(self.recommender.arm_stats[category].cooked_count, 1)
        self.assertEqual(self.recommender.arm_stats[category].total_reward, 2.0)
    
    def test_get_arm_rankings(self):
        """Test getting arm rankings."""
        # Add different rewards to different arms
        self.recommender.update("italian", 2.0)
        self.recommender.update("italian", 2.0)
        self.recommender.update("asian", 1.0)
        self.recommender.update("mexican", -1.0)
        
        rankings = self.recommender.get_arm_rankings()
        
        # Should have all categories
        self.assertEqual(len(rankings), len(RECIPE_CATEGORIES))
        
        # Rankings should be sorted by mean reward
        means = [mean for _, mean, _ in rankings]
        self.assertEqual(means, sorted(means, reverse=True))
        
        # Italian should rank high (2 cooked rewards)
        top_category = rankings[0][0]
        self.assertEqual(top_category, "italian")
    
    def test_reset_arm(self):
        """Test resetting a specific arm."""
        category = "healthy"
        
        # Add some data
        self.recommender.update(category, 2.0)
        self.assertGreater(self.recommender.arm_stats[category].total_pulls, 0)
        
        # Reset
        self.recommender.reset_arm(category)
        
        # Should be back to initial state
        stats = self.recommender.arm_stats[category]
        self.assertEqual(stats.alpha, 1.0)
        self.assertEqual(stats.beta, 1.0)
        self.assertEqual(stats.total_pulls, 0)
    
    def test_reset_all(self):
        """Test resetting all arms."""
        # Add data to multiple arms
        for category in ["italian", "asian", "mexican"]:
            self.recommender.update(category, 1.0)
        
        # Reset all
        self.recommender.reset_all()
        
        # All should be back to initial state
        for category in RECIPE_CATEGORIES:
            stats = self.recommender.arm_stats[category]
            self.assertEqual(stats.alpha, 1.0)
            self.assertEqual(stats.beta, 1.0)
            self.assertEqual(stats.total_pulls, 0)


class TestContextExtraction(unittest.TestCase):
    """Test context extraction from inventory."""
    
    def test_extract_context_with_expiring_items(self):
        """Test context extraction with expiring items."""
        # Create inventory with expiring items
        now = datetime.now()
        inventory = [
            InventoryItem(
                id="1",
                user_id="test_user",
                item_name="Milk",
                quantity=1.0,
                unit="liter",
                expiry_date=now + timedelta(days=1),
                added_at=now,
                updated_at=now
            ),
            InventoryItem(
                id="2",
                user_id="test_user",
                item_name="Bread",
                quantity=1.0,
                unit="loaf",
                expiry_date=now + timedelta(days=10),
                added_at=now,
                updated_at=now
            )
        ]
        
        context = extract_context_from_inventory(inventory, now)
        
        self.assertTrue(context.has_expiring_items)
        self.assertEqual(context.expiring_item_count, 1)
        self.assertGreater(context.inventory_diversity, 0)
    
    def test_extract_context_time_of_day(self):
        """Test time of day extraction."""
        # Morning (8 AM)
        morning_time = datetime.now().replace(hour=8)
        context = extract_context_from_inventory([], morning_time)
        self.assertEqual(context.time_of_day, "morning")
        
        # Evening (6 PM)
        evening_time = datetime.now().replace(hour=18)
        context = extract_context_from_inventory([], evening_time)
        self.assertEqual(context.time_of_day, "evening")
        
        # Night (11 PM)
        night_time = datetime.now().replace(hour=23)
        context = extract_context_from_inventory([], night_time)
        self.assertEqual(context.time_of_day, "night")
    
    def test_extract_context_weekend(self):
        """Test weekend detection."""
        # Create a Saturday (weekday=5)
        saturday = datetime(2024, 1, 6, 12, 0)  # Jan 6, 2024 is a Saturday
        context = extract_context_from_inventory([], saturday)
        self.assertTrue(context.is_weekend)
        
        # Create a Wednesday (weekday=2)
        wednesday = datetime(2024, 1, 3, 12, 0)
        context = extract_context_from_inventory([], wednesday)
        self.assertFalse(context.is_weekend)


class TestRecipeCategoryMapping(unittest.TestCase):
    """Test recipe to category mapping."""
    
    def test_map_italian_cuisine(self):
        """Test mapping Italian recipes."""
        recipe = {
            "title": "Spaghetti Carbonara",
            "cuisines": ["Italian"],
            "dishTypes": [],
            "readyInMinutes": 45,
            "vegetarian": False
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "italian")
    
    def test_map_quick_meal(self):
        """Test mapping quick meals."""
        recipe = {
            "title": "15-Minute Stir Fry",
            "cuisines": [],
            "dishTypes": [],
            "readyInMinutes": 15,
            "vegetarian": False
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "quick_meals")
    
    def test_map_breakfast(self):
        """Test mapping breakfast recipes."""
        recipe = {
            "title": "Pancakes",
            "cuisines": [],
            "dishTypes": ["morning meal", "breakfast"],
            "readyInMinutes": 40,
            "vegetarian": True
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "breakfast")
    
    def test_map_vegetarian(self):
        """Test mapping vegetarian recipes."""
        recipe = {
            "title": "Veggie Curry",
            "cuisines": [],
            "dishTypes": [],
            "readyInMinutes": 50,
            "vegetarian": True
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "vegetarian")
    
    def test_map_dessert(self):
        """Test mapping desserts."""
        recipe = {
            "title": "Chocolate Cake",
            "cuisines": [],
            "dishTypes": ["dessert"],
            "readyInMinutes": 60,
            "vegetarian": True
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "desserts")
    
    def test_map_asian_cuisine(self):
        """Test mapping Asian recipes."""
        recipe = {
            "title": "Pad Thai",
            "cuisines": ["Thai", "Asian"],
            "dishTypes": [],
            "readyInMinutes": 35,
            "vegetarian": False
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "asian")
    
    def test_map_default_comfort_food(self):
        """Test default mapping to comfort food."""
        recipe = {
            "title": "Burger",
            "cuisines": [],
            "dishTypes": [],
            "readyInMinutes": 40,
            "vegetarian": False
        }
        
        category = map_recipe_to_category(recipe)
        self.assertEqual(category, "comfort_food")


if __name__ == "__main__":
    unittest.main()
