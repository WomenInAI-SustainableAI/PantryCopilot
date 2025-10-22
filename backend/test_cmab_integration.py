"""
Integration test for CMAB recommendation system.

This test demonstrates the end-to-end flow of the CMAB system
without requiring actual Firestore or Spoonacular connections.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock firestore before importing modules that use it
sys.modules['src.db.firestore'] = MagicMock()

from src.services.cmab_service import (
    CMABRecommender, 
    map_recipe_to_category,
    extract_context_from_inventory
)
from src.db.models import InventoryItem


class TestCMABIntegration(unittest.TestCase):
    """Integration tests for CMAB system."""
    
    def setUp(self):
        """Set up test recommender."""
        self.recommender = CMABRecommender()
        
        # Create test inventory
        now = datetime.now()
        self.test_inventory = [
            InventoryItem(
                id="1",
                user_id="test_user",
                item_name="Tomatoes",
                quantity=3.0,
                unit="pieces",
                expiry_date=now + timedelta(days=1),
                added_at=now,
                updated_at=now
            ),
            InventoryItem(
                id="2",
                user_id="test_user",
                item_name="Pasta",
                quantity=500.0,
                unit="grams",
                expiry_date=now + timedelta(days=30),
                added_at=now,
                updated_at=now
            ),
            InventoryItem(
                id="3",
                user_id="test_user",
                item_name="Olive Oil",
                quantity=250.0,
                unit="ml",
                expiry_date=now + timedelta(days=90),
                added_at=now,
                updated_at=now
            )
        ]
    
    def test_full_recommendation_flow(self):
        """Test complete flow: get recommendations -> user feedback -> improved recommendations."""
        
        # Step 1: Get initial category recommendations (cold start)
        context = extract_context_from_inventory(self.test_inventory)
        initial_categories = self.recommender.select_arms(context, n_arms=3)
        
        self.assertEqual(len(initial_categories), 3)
        self.assertTrue(all(isinstance(cat, str) for cat in initial_categories))
        
        # Step 2: User provides positive feedback for Italian recipes
        italian_recipe = {
            "id": 12345,
            "title": "Spaghetti Carbonara",
            "cuisines": ["Italian"],
            "dishTypes": [],
            "readyInMinutes": 30,
            "vegetarian": False
        }
        
        italian_category = map_recipe_to_category(italian_recipe)
        
        # Simulate user cooking the recipe (strongest positive signal)
        self.recommender.update_from_feedback(italian_category, "cooked", context)
        
        # Simulate user upvoting another Italian recipe
        self.recommender.update_from_feedback(italian_category, "upvote", context)
        
        # Step 3: User provides negative feedback for Asian recipes
        asian_recipe = {
            "id": 67890,
            "title": "Pad Thai",
            "cuisines": ["Thai", "Asian"],
            "dishTypes": [],
            "readyInMinutes": 35,
            "vegetarian": False
        }
        
        asian_category = map_recipe_to_category(asian_recipe)
        self.recommender.update_from_feedback(asian_category, "downvote", context)
        
        # Step 4: Get preferences ranking
        rankings = self.recommender.get_arm_rankings()
        
        self.assertGreater(len(rankings), 0)
        
        # Italian should be ranked higher than Asian due to feedback
        italian_rank = None
        asian_rank = None
        
        for i, (cat, mean, pulls) in enumerate(rankings):
            if cat == italian_category:
                italian_rank = i
            elif cat == asian_category:
                asian_rank = i
        
        # Italian should rank higher (lower index) than Asian
        if italian_rank is not None and asian_rank is not None:
            self.assertLess(italian_rank, asian_rank,
                           "Italian should rank higher than Asian after positive feedback")
        
        # Step 5: Get new recommendations - Italian should be preferred
        new_categories = self.recommender.select_arms(context, n_arms=3)
        
        print(f"\nInitial categories: {initial_categories}")
        print(f"After feedback categories: {new_categories}")
        print(f"Rankings: {[(cat, round(mean, 3)) for cat, mean, pulls in rankings[:5]]}")
    
    def test_multiple_users_independence(self):
        """Test that different recommenders have independent states."""
        recommender1 = CMABRecommender()
        recommender2 = CMABRecommender()
        
        context = extract_context_from_inventory(self.test_inventory)
        
        # Give positive feedback to Italian for recommender1
        italian_recipe = {
            "id": 111,
            "title": "Margherita Pizza",
            "cuisines": ["Italian"],
            "dishTypes": [],
            "readyInMinutes": 45,
            "vegetarian": True
        }
        
        italian_cat = map_recipe_to_category(italian_recipe)
        for _ in range(5):
            recommender1.update_from_feedback(italian_cat, "cooked", context)
        
        # Give positive feedback to Asian for recommender2
        asian_recipe = {
            "id": 222,
            "title": "Kung Pao Chicken",
            "cuisines": ["Chinese", "Asian"],
            "dishTypes": [],
            "readyInMinutes": 30,
            "vegetarian": False
        }
        
        asian_cat = map_recipe_to_category(asian_recipe)
        for _ in range(5):
            recommender2.update_from_feedback(asian_cat, "cooked", context)
        
        # Get preferences for both recommenders
        rankings1 = recommender1.get_arm_rankings()
        rankings2 = recommender2.get_arm_rankings()
        
        # Check that preferences are different
        top1 = rankings1[0][0]
        top2 = rankings2[0][0]
        
        print(f"\nRecommender1 top category: {top1}")
        print(f"Recommender2 top category: {top2}")
        
        # Verify they learned different preferences
        self.assertNotEqual(
            recommender1.arm_stats[italian_cat].total_reward,
            recommender2.arm_stats[italian_cat].total_reward
        )
    
    def test_recipe_category_mapping_comprehensive(self):
        """Test recipe category mapping for various recipe types."""
        test_cases = [
            # (recipe, expected_category)
            (
                {
                    "title": "Quick Fried Rice",
                    "cuisines": ["Asian"],
                    "dishTypes": [],
                    "readyInMinutes": 15,
                    "vegetarian": False
                },
                "quick_meals"  # Should prioritize quick_meals over asian
            ),
            (
                {
                    "title": "Veggie Lasagna",
                    "cuisines": ["Italian"],
                    "dishTypes": [],
                    "readyInMinutes": 60,
                    "vegetarian": True
                },
                "italian"  # Should be italian despite being vegetarian
            ),
            (
                {
                    "title": "French Toast",
                    "cuisines": [],
                    "dishTypes": ["breakfast", "morning meal"],
                    "readyInMinutes": 35,  # > 30 minutes so not quick_meals
                    "vegetarian": True
                },
                "breakfast"  # Should be breakfast (dish type takes precedence)
            )
        ]
        
        for recipe, expected_category in test_cases:
            category = map_recipe_to_category(recipe)
            print(f"\nRecipe: {recipe['title']} -> {category}")
            self.assertEqual(category, expected_category)
    
    def test_learning_over_time(self):
        """Test that the recommender learns from feedback over time."""
        context = extract_context_from_inventory(self.test_inventory)
        
        # Track how often quick_meals is recommended over time
        quick_meals_recipe = {
            "id": 333,
            "title": "15-Minute Pasta",
            "cuisines": [],
            "dishTypes": [],
            "readyInMinutes": 15,
            "vegetarian": False
        }
        
        category = map_recipe_to_category(quick_meals_recipe)
        self.assertEqual(category, "quick_meals")
        
        # Provide consistent positive feedback
        for _ in range(10):
            self.recommender.update_from_feedback(category, "cooked", context)
        
        # Get statistics
        stats = self.recommender.get_arm_stats(category)
        self.assertEqual(stats.cooked_count, 10)
        self.assertEqual(stats.total_reward, 20.0)  # 10 * 2.0
        
        # After many positive samples, the mean should be high
        mean = stats.get_mean()
        print(f"\n{category} mean after 10 cooked: {mean:.3f}")
        self.assertGreater(mean, 0.8, "Mean should be high after consistent positive feedback")


if __name__ == "__main__":
    unittest.main(verbosity=2)
