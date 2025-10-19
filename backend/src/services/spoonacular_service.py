"""
Spoonacular API Integration Service
"""
import os
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE_URL = "https://api.spoonacular.com"


async def search_recipes_by_ingredients(
    ingredients: List[str],
    number: int = 10,
    ranking: int = 2,
    ignore_pantry: bool = True
) -> List[Dict]:
    """
    Search for recipes based on available ingredients.
    
    Args:
        ingredients: List of ingredient names
        number: Number of recipes to return
        ranking: 1 = maximize used ingredients, 2 = minimize missing ingredients
        ignore_pantry: Whether to ignore pantry staples
        
    Returns:
        List of recipe results
    """
    if not SPOONACULAR_API_KEY:
        raise ValueError("SPOONACULAR_API_KEY not set in environment variables")
    
    url = f"{SPOONACULAR_BASE_URL}/recipes/findByIngredients"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ",".join(ingredients),
        "number": number,
        "ranking": ranking,
        "ignorePantry": ignore_pantry
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def get_recipe_information(recipe_id: int) -> Dict:
    """
    Get detailed information about a recipe.
    
    Args:
        recipe_id: Spoonacular recipe ID
        
    Returns:
        Recipe information dictionary
    """
    if not SPOONACULAR_API_KEY:
        raise ValueError("SPOONACULAR_API_KEY not set in environment variables")
    
    url = f"{SPOONACULAR_BASE_URL}/recipes/{recipe_id}/information"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def get_recipe_ingredients_by_id(recipe_id: int) -> Dict:
    """
    Get ingredient quantities for a recipe.
    
    Args:
        recipe_id: Spoonacular recipe ID
        
    Returns:
        Recipe ingredients with quantities
    """
    if not SPOONACULAR_API_KEY:
        raise ValueError("SPOONACULAR_API_KEY not set in environment variables")
    
    url = f"{SPOONACULAR_BASE_URL}/recipes/{recipe_id}/ingredientWidget.json"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def search_recipes_complex(
    query: Optional[str] = None,
    cuisine: Optional[str] = None,
    exclude_ingredients: Optional[List[str]] = None,
    diet: Optional[str] = None,
    intolerances: Optional[List[str]] = None,
    number: int = 10
) -> Dict:
    """
    Complex recipe search with filters.
    
    Args:
        query: Search query
        cuisine: Cuisine type
        exclude_ingredients: Ingredients to exclude
        diet: Diet type (vegetarian, vegan, etc.)
        intolerances: List of intolerances
        number: Number of recipes to return
        
    Returns:
        Search results
    """
    if not SPOONACULAR_API_KEY:
        raise ValueError("SPOONACULAR_API_KEY not set in environment variables")
    
    url = f"{SPOONACULAR_BASE_URL}/recipes/complexSearch"
    
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": number,
        "addRecipeInformation": True
    }
    
    if query:
        params["query"] = query
    if cuisine:
        params["cuisine"] = cuisine
    if exclude_ingredients:
        params["excludeIngredients"] = ",".join(exclude_ingredients)
    if diet:
        params["diet"] = diet
    if intolerances:
        params["intolerances"] = ",".join(intolerances)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
