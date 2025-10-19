"""
Recipe Recommendation Service
Main service that orchestrates recipe recommendations with all features
"""
from typing import List, Dict, Optional
from src.db.crud.inventory import InventoryCRUD
from src.db.crud.allergies import AllergyCRUD
from src.db.crud.feedback import UserFeedbackCRUD
from src.db.crud.recommendations import RecommendationCRUD
from src.db.models import RecipeRecommendationCreate
from src.services.spoonacular_service import (
    search_recipes_by_ingredients,
    get_recipe_information,
    search_recipes_complex
)
from src.services.recipe_scoring_service import rank_recipes
from src.services.inventory_service import get_expiring_soon
from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation


async def get_personalized_recommendations(
    user_id: str,
    number_of_recipes: int = 10
) -> List[Dict]:
    """
    Get personalized recipe recommendations for a user.
    
    This is the main recommendation function that:
    1. Gets user inventory and identifies expiring items
    2. Gets user allergies for filtering
    3. Searches recipes via Spoonacular
    4. Scores and ranks recipes
    5. Generates AI explanations
    6. Saves recommendations to database
    
    Args:
        user_id: User ID
        number_of_recipes: Number of recommendations to return
        
    Returns:
        List of recommended recipes with scores and explanations
    """
    # 1. Get user data
    inventory = InventoryCRUD.list_by_user(user_id)
    allergies = AllergyCRUD.list_by_user(user_id)
    expiring_items = await get_expiring_soon(user_id, days=3)
    
    if not inventory:
        return []
    
    # 2. Extract ingredient names
    ingredient_names = [item.item_name for item in inventory]
    expiring_names = [item.item_name for item in expiring_items]
    allergen_names = [allergy.allergen for allergy in allergies]
    
    # 3. Search recipes using Spoonacular
    # First try with expiring ingredients to prioritize urgency
    recipes = []
    
    if expiring_names:
        expiring_recipes = await search_recipes_by_ingredients(
            ingredients=expiring_names,
            number=number_of_recipes,
            ranking=2  # Minimize missing ingredients
        )
        recipes.extend(expiring_recipes)
    
    # Get more recipes with all ingredients if needed
    if len(recipes) < number_of_recipes:
        all_recipes = await search_recipes_by_ingredients(
            ingredients=ingredient_names,
            number=number_of_recipes * 2,
            ranking=2
        )
        
        # Add recipes that aren't already in the list
        existing_ids = {r.get("id") for r in recipes}
        for recipe in all_recipes:
            if recipe.get("id") not in existing_ids:
                recipes.append(recipe)
        
    # 4. Get detailed information for each recipe
    detailed_recipes = []
    for recipe in recipes[:number_of_recipes * 2]:  # Get more than needed for filtering
        try:
            recipe_info = await get_recipe_information(recipe["id"])
            
            # Extract ingredient names
            ingredients = []
            if "extendedIngredients" in recipe_info:
                ingredients = [ing.get("name", "") for ing in recipe_info["extendedIngredients"]]
            
            recipe_info["ingredients"] = ingredients
            detailed_recipes.append(recipe_info)
        except Exception as e:
            print(f"Error fetching recipe {recipe['id']}: {e}")
            continue
    
    # 5. Calculate feedback scores from historical data
    feedback_history = UserFeedbackCRUD.list_by_user(user_id)
    feedback_scores = {}
    
    for feedback in feedback_history:
        recipe_id = feedback.recipe_id
        if recipe_id not in feedback_scores:
            feedback_scores[recipe_id] = 0.0
        
        # Upvote: +2, Downvote: -3, Skip: -1
        if feedback.feedback_type.value == "upvote":
            feedback_scores[recipe_id] += 2.0
        elif feedback.feedback_type.value == "downvote":
            feedback_scores[recipe_id] -= 3.0
        elif feedback.feedback_type.value == "skip":
            feedback_scores[recipe_id] -= 1.0
    
    # 6. Score and rank recipes
    ranked_recipes = rank_recipes(
        recipes=detailed_recipes,
        user_inventory=inventory,
        user_allergies=allergies,
        feedback_scores=feedback_scores
    )
    
    # 7. Generate AI explanations for top recipes
    final_recommendations = []
    
    for recipe in ranked_recipes[:number_of_recipes]:
        scoring = recipe["scoring"]
        
        # Only include safe recipes
        if not scoring["is_allergen_safe"]:
            continue
        
        # Generate AI explanation
        try:
            explanation = await explain_recipe_recommendation(
                recipe_name=recipe["title"],
                expiring_ingredients=scoring["expiring_ingredients"],
                allergies=allergen_names,
                inventory_match_percentage=scoring["match_percentage"]
            )
            
            recipe["ai_explanation"] = explanation.explanation
        except Exception as e:
            print(f"Error generating explanation for {recipe['title']}: {e}")
            recipe["ai_explanation"] = "This recipe is recommended based on your inventory."
        
        # 8. Save recommendation to database
        try:
            rec_data = RecipeRecommendationCreate(
                recipe_id=str(recipe["id"]),
                inventory_match_percentage=scoring["match_percentage"],
                expiring_ingredients=scoring["expiring_ingredients"],
                recommendation_score=scoring["overall_score"],
                explanation=recipe["ai_explanation"]
            )
            RecommendationCRUD.create(user_id, rec_data)
        except Exception as e:
            print(f"Error saving recommendation: {e}")
        
        final_recommendations.append(recipe)
    
    return final_recommendations


async def get_recommendations_by_preferences(
    user_id: str,
    cuisine: Optional[str] = None,
    diet: Optional[str] = None,
    number_of_recipes: int = 10
) -> List[Dict]:
    """
    Get recipe recommendations filtered by additional preferences.
    
    Args:
        user_id: User ID
        cuisine: Cuisine type filter
        diet: Diet type filter
        number_of_recipes: Number of recommendations
        
    Returns:
        List of filtered and ranked recipes
    """
    # Get user data
    inventory = InventoryCRUD.list_by_user(user_id)
    allergies = AllergyCRUD.list_by_user(user_id)
    
    if not inventory:
        return []
    
    # Get allergen names for exclusion
    allergen_names = [allergy.allergen for allergy in allergies]
    
    # Search with preferences
    search_results = await search_recipes_complex(
        cuisine=cuisine,
        diet=diet,
        exclude_ingredients=allergen_names,
        intolerances=allergen_names,
        number=number_of_recipes * 2
    )
    
    recipes = search_results.get("results", [])
    
    # Extract ingredients
    for recipe in recipes:
        ingredients = []
        if "extendedIngredients" in recipe:
            ingredients = [ing.get("name", "") for ing in recipe["extendedIngredients"]]
        recipe["ingredients"] = ingredients
    
    # Get feedback scores
    feedback_history = UserFeedbackCRUD.list_by_user(user_id)
    feedback_scores = {}
    
    for feedback in feedback_history:
        recipe_id = feedback.recipe_id
        if recipe_id not in feedback_scores:
            feedback_scores[recipe_id] = 0.0
        
        if feedback.feedback_type.value == "upvote":
            feedback_scores[recipe_id] += 2.0
        elif feedback.feedback_type.value == "downvote":
            feedback_scores[recipe_id] -= 3.0
        elif feedback.feedback_type.value == "skip":
            feedback_scores[recipe_id] -= 1.0
    
    # Rank recipes
    ranked_recipes = rank_recipes(
        recipes=recipes,
        user_inventory=inventory,
        user_allergies=allergies,
        feedback_scores=feedback_scores
    )
    
    return ranked_recipes[:number_of_recipes]
