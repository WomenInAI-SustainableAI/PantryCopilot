"""
Test script for CMAB (Contextual Multi-Armed Bandit) implementation
Run this to verify the CMAB system works correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.cmab_service import (
    RecipeCategory,
    ContextFeatures,
    ThompsonSamplingCMAB,
    convert_feedback_to_reward
)
from src.db.models import InventoryItem
from datetime import datetime, timedelta


def test_recipe_classification():
    """Test recipe category classification."""
    print("=" * 60)
    print("TEST 1: Recipe Category Classification")
    print("=" * 60)
    
    test_cases = [
        ("Spaghetti Carbonara", ["italian", "pasta"], ["italian"]),
        ("Thai Green Curry", ["thai", "curry"], ["asian", "indian"]),
        ("Quick 15-Minute Stir Fry", ["quick", "asian"], ["quick_meals", "asian"]),
        ("Vegan Buddha Bowl", ["vegan", "salad"], ["vegan", "salad"]),
        ("Chocolate Chip Cookies", ["dessert", "baking"], ["dessert", "baking"]),
    ]
    
    for title, tags, expected in test_cases:
        categories = RecipeCategory.classify_recipe(title, tags)
        print(f"Recipe: {title}")
        print(f"  Tags: {tags}")
        print(f"  Categories: {categories}")
        print(f"  Expected: {expected}")
        print(f"  ✓ Pass" if any(e in categories for e in expected) else "  ✗ Fail")
        print()


def test_context_extraction():
    """Test context feature extraction."""
    print("=" * 60)
    print("TEST 2: Context Feature Extraction")
    print("=" * 60)
    
    # Create mock inventory
    now = datetime.now()
    inventory = [
        InventoryItem(
            id="1", user_id="test", item_name="Chicken Breast", quantity=2.0,
            unit="lbs", expiry_date=now + timedelta(days=1),
            added_at=now, updated_at=now
        ),
        InventoryItem(
            id="2", user_id="test", item_name="Lettuce", quantity=1.0,
            unit="head", expiry_date=now + timedelta(days=2),
            added_at=now, updated_at=now
        ),
        InventoryItem(
            id="3", user_id="test", item_name="Rice", quantity=5.0,
            unit="lbs", expiry_date=now + timedelta(days=30),
            added_at=now, updated_at=now
        ),
    ]
    
    context = ContextFeatures.extract_inventory_context(inventory)
    
    print("Inventory:")
    for item in inventory:
        days_left = (item.expiry_date - now).days
        print(f"  - {item.item_name}: {item.quantity} {item.unit} (expires in {days_left} days)")
    
    print("\nExtracted Context Features:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    # Verify
    assert context["expiring_count"] == 2, "Should have 2 expiring items"
    assert context["total_items"] == 3, "Should have 3 total items"
    assert context["has_produce"] == 1, "Should have produce"
    assert context["has_protein"] == 1, "Should have protein"
    assert context["has_grains"] == 1, "Should have grains"
    print("\n✓ All assertions passed")


def test_thompson_sampling():
    """Test Thompson Sampling algorithm."""
    print("\n" + "=" * 60)
    print("TEST 3: Thompson Sampling")
    print("=" * 60)
    
    categories = ["italian", "asian", "mexican", "quick_meals"]
    cmab = ThompsonSamplingCMAB(categories)
    
    # Simulate context
    context = {
        "expiring_count": 2.0,
        "total_items": 8.0,
        "has_produce": 1.0,
        "has_protein": 1.0,
        "has_grains": 1.0,
        "inventory_diversity": 0.4,
    }
    
    print("Initial state (Cold start):")
    print(f"  Exploration rate: {cmab.get_exploration_rate()}")
    print(f"  Total pulls: {cmab.total_user_pulls}")
    print(f"  Cold start: {cmab.is_cold_start}")
    
    # Select categories 5 times
    print("\nSelecting categories (5 iterations):")
    for i in range(5):
        selected = cmab.select_categories(context, n_categories=2)
        print(f"  Iteration {i+1}: {[(cat, f'{score:.3f}') for cat, score in selected]}")
    
    # Simulate some feedback
    print("\nSimulating feedback:")
    feedback_data = [
        ("italian", 1.0),   # upvote
        ("italian", 2.0),   # cooked
        ("italian", 1.0),   # upvote
        ("asian", -1.0),    # downvote
        ("asian", 0.0),     # skip
        ("mexican", 1.0),   # upvote
        ("quick_meals", 2.0),  # cooked
    ]
    
    for category, reward in feedback_data:
        cmab.update(category, reward, context)
        print(f"  Updated {category} with reward {reward}")
    
    # Check statistics
    print("\nFinal Statistics:")
    stats = cmab.get_statistics()
    for category, data in stats.items():
        if data["pulls"] > 0:
            print(f"  {category}:")
            print(f"    Pulls: {data['pulls']}")
            print(f"    Mean reward: {data['mean_reward']:.3f}")
            print(f"    Expected value: {data['expected_value']:.3f}")
            print(f"    Beta params: α={data['alpha']:.2f}, β={data['beta']:.2f}")
    
    # Verify learning
    italian_stats = stats["italian"]
    asian_stats = stats["asian"]
    
    assert italian_stats["mean_reward"] > asian_stats["mean_reward"], \
        "Italian should have higher mean reward"
    print("\n✓ Model learned correctly: Italian preferred over Asian")


def test_feedback_conversion():
    """Test feedback to reward conversion."""
    print("\n" + "=" * 60)
    print("TEST 4: Feedback to Reward Conversion")
    print("=" * 60)
    
    test_cases = [
        ("upvote", False, 1.0),
        ("downvote", False, -1.0),
        ("skip", False, 0.0),
        ("upvote", True, 2.0),  # cooked overrides
        ("downvote", True, 2.0),  # cooked overrides
    ]
    
    for feedback_type, is_cooked, expected in test_cases:
        reward = convert_feedback_to_reward(feedback_type, is_cooked)
        status = "✓" if reward == expected else "✗"
        print(f"  {status} {feedback_type} + cooked={is_cooked} -> {reward} (expected {expected})")


def test_serialization():
    """Test model serialization and deserialization."""
    print("\n" + "=" * 60)
    print("TEST 5: Model Serialization")
    print("=" * 60)
    
    # Create model and update it
    categories = ["italian", "asian"]
    cmab = ThompsonSamplingCMAB(categories)
    
    context = {
        "expiring_count": 1.0,
        "total_items": 5.0,
        "has_produce": 1.0,
        "has_protein": 0.0,
        "has_grains": 1.0,
        "inventory_diversity": 0.3,
    }
    
    cmab.update("italian", 1.0, context)
    cmab.update("asian", -1.0, context)
    
    # Serialize
    model_dict = cmab.to_dict()
    print("Serialized model:")
    print(f"  Categories: {model_dict['categories']}")
    print(f"  Alpha: {model_dict['alpha']}")
    print(f"  Beta: {model_dict['beta']}")
    
    # Deserialize
    restored_cmab = ThompsonSamplingCMAB.from_dict(model_dict)
    print("\nRestored model:")
    print(f"  Categories: {restored_cmab.categories}")
    print(f"  Alpha: {restored_cmab.alpha}")
    print(f"  Beta: {restored_cmab.beta}")
    
    # Verify
    assert restored_cmab.alpha == cmab.alpha, "Alpha should match"
    assert restored_cmab.beta == cmab.beta, "Beta should match"
    assert restored_cmab.pulls == cmab.pulls, "Pulls should match"
    print("\n✓ Serialization successful")


def test_cold_start_behavior():
    """Test cold start strategy."""
    print("\n" + "=" * 60)
    print("TEST 6: Cold Start Behavior")
    print("=" * 60)
    
    categories = ["italian", "asian", "mexican"]
    cmab = ThompsonSamplingCMAB(categories)
    
    context = {"expiring_count": 0.0, "total_items": 5.0, "has_produce": 1.0,
               "has_protein": 1.0, "has_grains": 1.0, "inventory_diversity": 0.3}
    
    # Track category diversity in early recommendations
    category_counts = {cat: 0 for cat in categories}
    
    print("Cold start phase (first 30 selections):")
    for i in range(30):
        selected = cmab.select_categories(context, n_categories=1)
        category = selected[0][0]
        category_counts[category] += 1
        
        # Give random feedback
        import random
        reward = random.choice([1.0, 0.0, -1.0])
        cmab.update(category, reward, context)
    
    print("\nCategory distribution:")
    for category, count in category_counts.items():
        percentage = (count / 30) * 100
        print(f"  {category}: {count}/30 ({percentage:.1f}%)")
    
    # Check diversity (no category should dominate too early)
    max_count = max(category_counts.values())
    min_count = min(category_counts.values())
    diversity_ratio = min_count / max_count if max_count > 0 else 0
    
    print(f"\nDiversity ratio: {diversity_ratio:.2f}")
    assert diversity_ratio > 0.2, "Categories should be relatively balanced during cold start"
    print("✓ Cold start maintains good exploration")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CMAB SYSTEM TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_recipe_classification()
        test_context_extraction()
        test_thompson_sampling()
        test_feedback_conversion()
        test_serialization()
        test_cold_start_behavior()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
