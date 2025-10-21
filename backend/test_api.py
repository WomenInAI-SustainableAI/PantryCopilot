"""
Test script to verify the FastAPI setup
"""
import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation
from src.ai.flows.improve_recommendations_from_feedback import improve_recommendations_from_feedback


async def test_explain_recommendation():
    """Test the explain recommendation flow."""
    print("Testing Explain Recipe Recommendation...")
    
    try:
        result = await explain_recipe_recommendation(
            recipe_name="Tomato Basil Pasta",
            expiring_ingredients=["tomatoes", "basil"],
            allergies=["nuts"],
            inventory_match_percentage=85.5
        )
        print(f"✓ Success! Explanation: {result.explanation[:100]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_process_feedback():
    """Test the process feedback flow."""
    print("\nTesting Process Feedback...")
    
    try:
        result = await improve_recommendations_from_feedback(
            recipe_id="recipe_123",
            feedback_type="upvote",
            user_id="user_456"
        )
        print(f"✓ Success! {result.message}")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_inventory_crud():
    """Test inventory CRUD operations."""
    print("\nTesting Inventory CRUD...")
    
    try:
        from src.db.crud.inventory import create_inventory_item, get_user_inventory, delete_inventory_item
        from src.db.models import InventoryItemCreate
        from datetime import datetime, timedelta
        
        user_id = "test_user"
        
        # Create test item
        item_data = InventoryItemCreate(
            item_name="Test Tomatoes",
            quantity=5.0,
            unit="pieces",
            expiry_date=datetime.utcnow() + timedelta(days=7)
        )
        
        created_item = await create_inventory_item(user_id, item_data)
        print(f"✓ Created item: {created_item.item_name}")
        
        # List items
        items = await get_user_inventory(user_id)
        print(f"✓ Found {len(items)} items in inventory")
        
        # Clean up
        await delete_inventory_item(user_id, created_item.id)
        print("✓ Cleaned up test item")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main async function to run tests."""
    print("=" * 60)
    print("PantryCopilot API Tests")
    print("=" * 60)
    
    # Test inventory first (doesn't need API key)
    test3 = await test_inventory_crud()
    
    # Check if API key is set for AI tests
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ Warning: GOOGLE_API_KEY not set in .env file")
        print("Skipping AI tests - add your Google API key to run them")
        test1 = test2 = True  # Skip AI tests
    else:
        test1 = await test_explain_recommendation()
        test2 = await test_process_feedback()
    
    print("\n" + "=" * 60)
    if test1 and test2 and test3:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
