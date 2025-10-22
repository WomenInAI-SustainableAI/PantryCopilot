"""
Recipe Recommendation Service
Main service that orchestrates recipe recommendations with all features
Including CMAB (Contextual Multi-Armed Bandit) for personalized category selection
"""
from typing import List, Dict, Optional
from src.db.crud import (
    get_user_inventory,
    get_user_allergies,
    get_user_feedback,
    create_recommendation
)
from src.db.models import RecipeRecommendationCreate
from src.services.spoonacular_service import (
    search_recipes_by_ingredients,
    get_recipe_information,
    search_recipes_complex
)
from src.services.recipe_scoring_service import rank_recipes
from src.services.inventory_service import get_expiring_soon
from src.services.cmab_manager import cmab_manager
from src.services.cmab_service import map_recipe_to_category
# from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation


async def get_personalized_recommendations(
    user_id: str,
    number_of_recipes: int = 10
) -> List[Dict]:
    """
    Get personalized recipe recommendations for a user using CMAB.
    
    This is the main recommendation function that:
    1. Gets user inventory and identifies expiring items
    2. Uses CMAB to select preferred recipe categories
    3. Gets user allergies for filtering
    4. Searches recipes via Spoonacular filtered by preferred categories
    5. Scores and ranks recipes
    6. Generates AI explanations
    7. Saves recommendations to database
    
    Args:
        user_id: User ID
        number_of_recipes: Number of recommendations to return
        
    Returns:
        List of recommended recipes with scores and explanations
    """
    # 1. Get user data
    inventory = get_user_inventory(user_id)
    allergies = get_user_allergies(user_id)
    expiring_items = get_expiring_soon(user_id, days=3)
    
    if not inventory:
        return []
    
    # 2. Get preferred categories using CMAB
    preferred_categories = cmab_manager.get_category_recommendations(
        user_id=user_id,
        inventory=inventory,
        n_categories=3  # Get top 3 preferred categories
    )
    
    # 3. Extract ingredient names
    ingredient_names = [item.item_name for item in inventory]
    expiring_names = [item.item_name for item in expiring_items]
    allergen_names = [allergy.allergen for allergy in allergies]
    
    # 4. Search recipes using Spoonacular
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
        
    # 5. Get detailed information for each recipe
    detailed_recipes = []
    for recipe in recipes[:number_of_recipes * 2]:  # Get more than needed for filtering
        try:
            recipe_info = await get_recipe_information(recipe["id"])
            
            # Extract ingredient names
            ingredients = []
            if "extendedIngredients" in recipe_info:
                ingredients = [ing.get("name", "") for ing in recipe_info["extendedIngredients"]]
            
            recipe_info["ingredients"] = ingredients
            
            # Add category information for CMAB filtering
            recipe_info["cmab_category"] = map_recipe_to_category(recipe_info)
            
            detailed_recipes.append(recipe_info)
        except Exception as e:
            print(f"Error fetching recipe {recipe['id']}: {e}")
            continue
    
    # 6. Calculate feedback scores from historical data
    feedback_history = get_user_feedback(user_id)
    feedback_scores = {}
    
    for feedback in feedback_history:
        recipe_id = feedback.recipe_id
        if recipe_id not in feedback_scores:
            feedback_scores[recipe_id] = 0.0
        
        # Update scoring to match CMAB rewards: Upvote: +2, Downvote: -3, Skip: -1, Cooked: +5
        if feedback.feedback_type.value == "upvote":
            feedback_scores[recipe_id] += 2.0
        elif feedback.feedback_type.value == "downvote":
            feedback_scores[recipe_id] -= 3.0
        elif feedback.feedback_type.value == "skip":
            feedback_scores[recipe_id] -= 1.0
        elif feedback.feedback_type.value == "cooked":
            feedback_scores[recipe_id] += 5.0
    
    # 7. Score and rank recipes
    ranked_recipes = rank_recipes(
        recipes=detailed_recipes,
        user_inventory=inventory,
        user_allergies=allergies,
        feedback_scores=feedback_scores
    )
    
    # 8. Boost recipes in preferred categories (CMAB integration)
    for recipe in ranked_recipes:
        recipe_category = recipe.get("cmab_category", "")
        if recipe_category in preferred_categories:
            # Boost score based on category preference rank
            boost_multiplier = 1.0 + (0.2 * (3 - preferred_categories.index(recipe_category)))
            recipe["scoring"]["overall_score"] *= boost_multiplier
            recipe["scoring"]["cmab_boosted"] = True
            recipe["scoring"]["preferred_category"] = recipe_category
        else:
            recipe["scoring"]["cmab_boosted"] = False
    
    # Re-sort after CMAB boost
    ranked_recipes.sort(key=lambda x: x["scoring"]["overall_score"], reverse=True)
    
    # 9. Generate AI explanations for top recipes
    final_recommendations = []
    
    for recipe in ranked_recipes[:number_of_recipes]:
        scoring = recipe["scoring"]
        
        # Only include safe recipes
        if not scoring["is_allergen_safe"]:
            continue
        
        # # Generate AI explanation
        # try:
        #     explanation = await explain_recipe_recommendation(
        #         recipe_name=recipe["title"],
        #         expiring_ingredients=scoring["expiring_ingredients"],
        #         allergies=allergen_names,
        #         inventory_match_percentage=scoring["match_percentage"]
        #     )
            
        #     recipe["ai_explanation"] = explanation.explanation
        # except Exception as e:
        #     print(f"Error generating explanation for {recipe['title']}: {e}")
        #     recipe["ai_explanation"] = "This recipe is recommended based on your inventory."
        
        # Default explanation
        explanation_parts = [f"This recipe matches {scoring['match_percentage']:.0f}% of your inventory."]
        if scoring.get("cmab_boosted"):
            explanation_parts.append(f"It's from your preferred {scoring['preferred_category'].replace('_', ' ')} category.")
        if scoring["expiring_ingredients"]:
            explanation_parts.append(f"Uses expiring ingredients: {', '.join(scoring['expiring_ingredients'][:3])}.")
        
        recipe["ai_explanation"] = " ".join(explanation_parts)
        
        # 10. Save recommendation to database
        try:
            rec_data = RecipeRecommendationCreate(
                recipe_id=str(recipe["id"]),
                inventory_match_percentage=scoring["match_percentage"],
                expiring_ingredients=scoring["expiring_ingredients"],
                recommendation_score=scoring["overall_score"],
                explanation=recipe["ai_explanation"]
            )
            create_recommendation(user_id, rec_data)
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
    inventory = get_user_inventory(user_id)
    allergies = get_user_allergies(user_id)
    
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
    feedback_history = get_user_feedback(user_id)
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
