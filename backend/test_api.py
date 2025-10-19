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


async def main():
    """Main async function to run tests."""
    print("=" * 60)
    print("PantryCopilot API Tests")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ Warning: GOOGLE_API_KEY not set in .env file")
        print("Please add your Google API key to the .env file to run the tests")
        return
    
    test1 = await test_explain_recommendation()
    test2 = await test_process_feedback()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
