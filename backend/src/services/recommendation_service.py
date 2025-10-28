"""
Recipe Recommendation Service
Main service that orchestrates recipe recommendations with all features
Includes CMAB (Contextual Multi-Armed Bandit) for personalized learning
"""
from typing import List, Dict, Optional
from src.db.crud import (
    get_user_inventory,
    get_user_allergies,
    get_user_feedback,
    create_recommendation
)
from src.db.crud.cmab import CMABCRUD
from src.db.models import RecipeRecommendationCreate
from src.services.spoonacular_service import (
    search_recipes_by_ingredients,
    get_recipe_information,
    search_recipes_complex
)
from src.services.recipe_scoring_service import rank_recipes
from src.services.inventory_service import get_expiring_soon
from src.services.cmab_service import (
    RecipeCategory,
    ContextFeatures,
    convert_feedback_to_reward
)
# from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation


async def get_personalized_recommendations(
    user_id: str,
    number_of_recipes: int = 10
) -> List[Dict]:
    """
    Get personalized recipe recommendations for a user using CMAB.
    
    This is the main recommendation function that:
    1. Gets user inventory and identifies expiring items
    2. Extracts context features from inventory
    3. Uses CMAB to select recipe categories to explore
    4. Gets user allergies for filtering
    5. Searches recipes via Spoonacular in selected categories
    6. Scores and ranks recipes
    7. Generates AI explanations
    8. Saves recommendations to database
    
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
        # Return popular recipes for new users with no inventory
        try:
            popular_recipes = await search_recipes_complex(
                number=number_of_recipes
            )
            return popular_recipes.get("results", [])
        except Exception as e:
            print(f"Error fetching popular recipes: {e}")
            return []
    
    # 2. Load or create CMAB model
    cmab_model = CMABCRUD.get_or_create(user_id)
    
    # 3. Extract context features from inventory
    context = ContextFeatures.extract_inventory_context(inventory)
    
    # 4. Select top categories using CMAB (Thompson Sampling)
    selected_categories = cmab_model.select_categories(
        context=context,
        n_categories=3  # Select top 3 categories
    )
    
    print(f"CMAB selected categories for user {user_id}: {selected_categories}")
    print(f"Context: {context}")
    print(f"Cold start mode: {cmab_model.is_cold_start}")
    
    # 5. Extract ingredient names
    ingredient_names = [item.item_name for item in inventory]
    expiring_names = [item.item_name for item in expiring_items]
    allergen_names = [allergy.allergen for allergy in allergies]

    # Expand category-style allergens like "dairy" into concrete ingredient terms
    def _expand_allergy_terms(terms: List[str]) -> List[str]:
        mapping = {
            'dairy': [
                'milk','cheese','butter','yogurt','cream','whey','casein','caseinate','ghee','curd','paneer','kefir','ricotta','mozzarella','parmesan','cheddar','buttermilk','custard','lactose'
            ],
            'nuts': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'tree nut': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'treenut': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'peanut': ['peanut','peanuts','peanut butter','groundnut'],
            'shellfish': ['shrimp','prawn','crab','lobster','crayfish','krill','shellfish'],
            'fish': ['fish','salmon','tuna','cod','haddock','tilapia','trout','anchovy','sardine','mackerel','bass'],
            'gluten': ['gluten','wheat','barley','rye','malt','semolina','farina','spelt','einkorn','emmer'],
            'wheat': ['wheat','semolina','spelt','einkorn','emmer','farina'],
            'soy': ['soy','soya','soybean','soybeans','soymilk','soy sauce','edamame','tofu','miso','tempeh'],
            'sesame': ['sesame','tahini','sesame oil','sesame seeds'],
            'mustard': ['mustard','mustard seeds','mustard powder'],
            'celery': ['celery','celeriac'],
            'lupin': ['lupin','lupine','lupine flour'],
            'sulfite': ['sulfite','sulfites','sulphite','sulphites','sulfur dioxide','e220','e221','e222','e223','e224','e225','e226','e227','e228'],
            'egg': ['egg','eggs','albumen'],
        }
        out: List[str] = []
        for t in terms:
            k = (t or '').strip().lower()
            if not k:
                continue
            out.append(k)
            if k in mapping:
                out.extend(mapping[k])
        # de-duplicate while preserving order
        seen = set()
        dedup: List[str] = []
        for x in out:
            if x not in seen:
                seen.add(x)
                dedup.append(x)
        return dedup
    allergen_names_expanded = _expand_allergy_terms(allergen_names)
    
    # 6. Search recipes using Spoonacular with CMAB-selected categories
    recipes = []
    
    # Search in each selected category
    for category, score in selected_categories:
        try:
            # Use category as cuisine or tag filter
            category_recipes = await search_recipes_complex(
                query=category if category != "general" else "",
                cuisine=category if category in ["italian", "asian", "mexican", "american", "mediterranean", "indian"] else None,
                type=category if category in ["breakfast", "dessert", "soup", "salad"] else None,
                exclude_ingredients=allergen_names_expanded,
                intolerances=allergen_names_expanded,
                number=number_of_recipes
            )
            
            if "results" in category_recipes:
                recipes.extend(category_recipes["results"])
        except Exception as e:
            print(f"Error searching recipes for category {category}: {e}")
    
    # Also search with expiring ingredients to prioritize urgency
    if expiring_names:
        try:
            expiring_recipes = await search_recipes_by_ingredients(
                ingredients=expiring_names,
                number=number_of_recipes,
                ranking=2  # Minimize missing ingredients
            )
            recipes.extend(expiring_recipes)
        except Exception as e:
            print(f"Error searching recipes with expiring ingredients: {e}")
    
    # Fallback: Get recipes with all ingredients if needed
    if len(recipes) < number_of_recipes:
        try:
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
        except Exception as e:
            print(f"Error in fallback recipe search: {e}")
        
    # 7. Get detailed information for each recipe
    detailed_recipes = []
    for recipe in recipes[:number_of_recipes * 3]:  # Get more than needed for filtering
        try:
            recipe_info = await get_recipe_information(recipe["id"])
            
            # Extract ingredient names
            ingredients = []
            if "extendedIngredients" in recipe_info:
                ingredients = [ing.get("name", "") for ing in recipe_info["extendedIngredients"]]
            
            recipe_info["ingredients"] = ingredients
            
            # Classify recipe into categories for CMAB tracking
            recipe_tags = recipe_info.get("dishTypes", []) + recipe_info.get("cuisines", [])
            recipe_categories = RecipeCategory.classify_recipe(
                recipe_info.get("title", ""),
                recipe_tags
            )
            recipe_info["categories"] = recipe_categories
            
            detailed_recipes.append(recipe_info)
        except Exception as e:
            print(f"Error fetching recipe {recipe['id']}: {e}")
            continue
    
    # 8. Calculate feedback scores from historical data
    feedback_history = get_user_feedback(user_id)
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
    
    # 9. Score and rank recipes
    ranked_recipes = rank_recipes(
        recipes=detailed_recipes,
        user_inventory=inventory,
        user_allergies=allergies,
        feedback_scores=feedback_scores
    )
    
    # 10. Generate AI explanations for top recipes and save
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
        
        # Add CMAB explanation
        recipe_categories = recipe.get("categories", ["general"])
        cmab_explanation = f"Recommended based on your preference for {', '.join(recipe_categories[:2])} recipes."
        recipe["ai_explanation"] = cmab_explanation
        
        # 11. Save recommendation to database
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
    
    # 12. Save updated CMAB model
    CMABCRUD.save(user_id, cmab_model)
    
    return final_recommendations


async def update_cmab_with_feedback(
    user_id: str,
    recipe_id: str,
    recipe_categories: List[str],
    feedback_type: str,
    is_cooked: bool = False
):
    """
    Update CMAB model when user provides feedback.
    
    This function should be called whenever a user:
    - Upvotes/downvotes a recipe
    - Cooks a recipe
    - Skips a recipe
    
    Args:
        user_id: User ID
        recipe_id: Recipe ID
        recipe_categories: Categories of the recipe
        feedback_type: Type of feedback ("upvote", "downvote", "skip")
        is_cooked: Whether the recipe was cooked
    """
    # Load CMAB model
    cmab_model = CMABCRUD.get_or_create(user_id)
    
    # Get current inventory context
    inventory = get_user_inventory(user_id)
    context = ContextFeatures.extract_inventory_context(inventory)
    
    # Convert feedback to reward
    reward = convert_feedback_to_reward(feedback_type, is_cooked)
    
    # Update model for each category
    for category in recipe_categories:
        if category in cmab_model.categories:
            cmab_model.update(category, reward, context)
            print(f"Updated CMAB: category={category}, reward={reward}, context={context}")
    
    # Save updated model
    CMABCRUD.save(user_id, cmab_model)


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

    def _expand_allergy_terms(terms: List[str]) -> List[str]:
        mapping = {
            'dairy': [
                'milk','cheese','butter','yogurt','cream','whey','casein','caseinate','ghee','curd','paneer','kefir','ricotta','mozzarella','parmesan','cheddar','buttermilk','custard','lactose'
            ],
            'nuts': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'tree nut': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'treenut': [
                'almond','walnut','pecan','cashew','hazelnut','pistachio','macadamia','brazil nut','pine nut'
            ],
            'peanut': ['peanut','peanuts','peanut butter','groundnut'],
            'shellfish': ['shrimp','prawn','crab','lobster','crayfish','krill','shellfish'],
            'fish': ['fish','salmon','tuna','cod','haddock','tilapia','trout','anchovy','sardine','mackerel','bass'],
            'gluten': ['gluten','wheat','barley','rye','malt','semolina','farina','spelt','einkorn','emmer'],
            'wheat': ['wheat','semolina','spelt','einkorn','emmer','farina'],
            'soy': ['soy','soya','soybean','soybeans','soymilk','soy sauce','edamame','tofu','miso','tempeh'],
            'sesame': ['sesame','tahini','sesame oil','sesame seeds'],
            'mustard': ['mustard','mustard seeds','mustard powder'],
            'celery': ['celery','celeriac'],
            'lupin': ['lupin','lupine','lupine flour'],
            'sulfite': ['sulfite','sulfites','sulphite','sulphites','sulfur dioxide','e220','e221','e222','e223','e224','e225','e226','e227','e228'],
            'egg': ['egg','eggs','albumen'],
        }
        out: List[str] = []
        for t in terms:
            k = (t or '').strip().lower()
            if not k:
                continue
            out.append(k)
            if k in mapping:
                out.extend(mapping[k])
        seen = set()
        dedup: List[str] = []
        for x in out:
            if x not in seen:
                seen.add(x)
                dedup.append(x)
        return dedup
    allergen_names_expanded = _expand_allergy_terms(allergen_names)
    
    # Search with preferences
    search_results = await search_recipes_complex(
        cuisine=cuisine,
        diet=diet,
        exclude_ingredients=allergen_names_expanded,
        intolerances=allergen_names_expanded,
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
