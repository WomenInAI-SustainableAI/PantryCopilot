"""
Recipe Scoring Service
Scores recipes based on inventory match, expiring ingredients, and user preferences
"""
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, date
from src.db.models import InventoryItem, Allergy


def calculate_inventory_match_percentage(
    recipe_ingredients: List[str],
    user_inventory: List[InventoryItem]
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate what percentage of recipe ingredients are available in inventory.
    
    Args:
        recipe_ingredients: List of ingredient names from recipe
        user_inventory: User's inventory items
        
    Returns:
        Tuple of (match_percentage, matched_ingredients, missing_ingredients)
    """
    if not recipe_ingredients:
        return 0.0, [], []
    
    inventory_names = [item.item_name.lower() for item in user_inventory]
    matched = []
    missing = []
    
    for ingredient in recipe_ingredients:
        ingredient_lower = ingredient.lower()
        is_matched = False
        
        # Check for partial matches
        for inv_name in inventory_names:
            if ingredient_lower in inv_name or inv_name in ingredient_lower:
                matched.append(ingredient)
                is_matched = True
                break
        
        if not is_matched:
            missing.append(ingredient)
    
    match_percentage = (len(matched) / len(recipe_ingredients)) * 100
    return match_percentage, matched, missing


def calculate_expiry_urgency_score(
    recipe_ingredients: List[str],
    user_inventory: List[InventoryItem]
) -> Tuple[float, List[str]]:
    """
    Calculate urgency score based on expiring ingredients used in recipe.
    
    Args:
        recipe_ingredients: List of ingredient names from recipe
        user_inventory: User's inventory items
        
    Returns:
        Tuple of (urgency_score, expiring_ingredients_list)
    """
    today = datetime.now().date()
    expiring_ingredients = []
    urgency_score = 0.0
    
    for ingredient in recipe_ingredients:
        ingredient_lower = ingredient.lower()
        
        # Find matching inventory item
        for item in user_inventory:
            if ingredient_lower in item.item_name.lower() or \
               item.item_name.lower() in ingredient_lower:
                
                # Calculate days until expiry
                days_until_expiry = (item.expiry_date - today).days
                
                if days_until_expiry <= 3:
                    expiring_ingredients.append(item.item_name)
                    # Higher urgency for items expiring sooner
                    if days_until_expiry <= 0:
                        urgency_score += 10  # Expired
                    elif days_until_expiry == 1:
                        urgency_score += 8   # Expires tomorrow
                    elif days_until_expiry == 2:
                        urgency_score += 5   # Expires in 2 days
                    else:
                        urgency_score += 3   # Expires in 3 days
                break
    
    return urgency_score, expiring_ingredients


def check_allergen_safety(
    recipe_ingredients: List[str],
    user_allergies: List[Allergy]
) -> Tuple[bool, List[str]]:
    """
    Check if recipe is safe based on user allergies.
    
    Args:
        recipe_ingredients: List of ingredient names from recipe
        user_allergies: User's allergies
        
    Returns:
        Tuple of (is_safe, allergens_found)
    """
    allergen_names = [allergy.allergen.lower() for allergy in user_allergies]
    allergens_found = []
    
    for ingredient in recipe_ingredients:
        ingredient_lower = ingredient.lower()
        
        for allergen in allergen_names:
            if allergen in ingredient_lower:
                allergens_found.append(allergen)
    
    is_safe = len(allergens_found) == 0
    return is_safe, allergens_found


def calculate_partial_usage_score(
    recipe_ingredients: Dict[str, float],
    user_inventory: List[InventoryItem]
) -> float:
    """
    Calculate score based on how well recipe uses partial quantities.
    Higher score for recipes that use up partial ingredients.
    
    Args:
        recipe_ingredients: Dictionary of ingredient names to quantities
        user_inventory: User's inventory items
        
    Returns:
        Partial usage score (0-10)
    """
    usage_score = 0.0
    matches = 0
    
    for ingredient_name, required_qty in recipe_ingredients.items():
        ingredient_lower = ingredient_name.lower()
        
        for item in user_inventory:
            if ingredient_lower in item.item_name.lower() or \
               item.item_name.lower() in ingredient_lower:
                
                matches += 1
                # Higher score if recipe uses 50-100% of available quantity
                usage_ratio = required_qty / item.quantity if item.quantity > 0 else 0
                
                if 0.5 <= usage_ratio <= 1.0:
                    usage_score += 3  # Great usage
                elif 0.3 <= usage_ratio < 0.5:
                    usage_score += 2  # Good usage
                elif usage_ratio < 0.3:
                    usage_score += 1  # Partial usage
                break
    
    # Normalize to 0-10 scale
    if matches > 0:
        usage_score = min(10, (usage_score / matches) * 3)
    
    return usage_score


def calculate_overall_recipe_score(
    match_percentage: float,
    urgency_score: float,
    is_safe: bool,
    partial_usage_score: float,
    user_feedback_score: float = 0.0
) -> float:
    """
    Calculate overall recipe recommendation score.
    
    Args:
        match_percentage: Inventory match percentage (0-100)
        urgency_score: Expiry urgency score
        is_safe: Whether recipe is allergen-safe
        partial_usage_score: Partial usage score (0-10)
        user_feedback_score: Historical feedback score (-10 to +10)
        
    Returns:
        Overall score (0-100)
    """
    # Base score from inventory match (40% weight)
    score = match_percentage * 0.4
    
    # Urgency bonus (30% weight, capped at 30 points)
    score += min(30, urgency_score * 1.5)
    
    # Partial usage bonus (15% weight)
    score += partial_usage_score * 1.5
    
    # Feedback bonus/penalty (15% weight)
    score += user_feedback_score * 1.5
    
    # Safety penalty - heavily penalize unsafe recipes
    if not is_safe:
        score = score * 0.1  # 90% penalty for allergens
    
    # Cap at 100
    return min(100, max(0, score))


def rank_recipes(
    recipes: List[Dict],
    user_inventory: List[InventoryItem],
    user_allergies: List[Allergy],
    feedback_scores: Dict[str, float] = None
) -> List[Dict]:
    """
    Rank recipes based on all scoring factors.
    
    Args:
        recipes: List of recipe dictionaries
        user_inventory: User's inventory items
        user_allergies: User's allergies
        feedback_scores: Dictionary of recipe_id to feedback score
        
    Returns:
        Sorted list of recipes with scores
    """
    if feedback_scores is None:
        feedback_scores = {}
    
    scored_recipes = []
    
    for recipe in recipes:
        recipe_ingredients = recipe.get("ingredients", [])
        recipe_id = str(recipe.get("id", ""))
        
        # Calculate all scores
        match_pct, matched, missing = calculate_inventory_match_percentage(
            recipe_ingredients,
            user_inventory
        )
        
        urgency_score, expiring = calculate_expiry_urgency_score(
            recipe_ingredients,
            user_inventory
        )
        
        is_safe, allergens = check_allergen_safety(
            recipe_ingredients,
            user_allergies
        )
        
        # For partial usage, we'd need ingredient quantities from Spoonacular
        # Using a simplified version here
        partial_score = 5.0  # Default mid-range score
        
        feedback_score = feedback_scores.get(recipe_id, 0.0)
        
        overall_score = calculate_overall_recipe_score(
            match_pct,
            urgency_score,
            is_safe,
            partial_score,
            feedback_score
        )
        
        # Add scoring metadata to recipe
        recipe["scoring"] = {
            "overall_score": overall_score,
            "match_percentage": match_pct,
            "matched_ingredients": matched,
            "missing_ingredients": missing,
            "urgency_score": urgency_score,
            "expiring_ingredients": expiring,
            "is_allergen_safe": is_safe,
            "allergens_found": allergens,
            "partial_usage_score": partial_score,
            "feedback_score": feedback_score
        }
        
        scored_recipes.append(recipe)
    
    # Sort by overall score (descending)
    scored_recipes.sort(key=lambda x: x["scoring"]["overall_score"], reverse=True)
    
    return scored_recipes
