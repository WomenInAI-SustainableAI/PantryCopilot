"""
Spoonacular API Integration Service
"""
import os
import httpx
import hashlib
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE_URL = "https://api.spoonacular.com"

# Simple in-memory cache
_cache = {}
CACHE_DURATION = 3600  # 1 hour in seconds

def _get_cache_key(url: str, params: dict) -> str:
    """Generate cache key from URL and params."""
    key_string = f"{url}_{sorted(params.items())}"
    return hashlib.md5(key_string.encode()).hexdigest()

def _get_cached_response(cache_key: str) -> Optional[dict]:
    """Get cached response if still valid."""
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return cached_data
        else:
            del _cache[cache_key]
    return None

def _cache_response(cache_key: str, data: dict) -> None:
    """Cache response with timestamp."""
    _cache[cache_key] = (data, time.time())

async def _make_cached_request(url: str, params: dict) -> dict:
    """Make HTTP request with caching."""
    cache_key = _get_cache_key(url, params)
    cached_result = _get_cached_response(cache_key)
    if cached_result is not None:
        return cached_result
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        _cache_response(cache_key, result)
        return result


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
    
    return await _make_cached_request(url, params)


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
    
    return await _make_cached_request(url, params)


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
    
    return await _make_cached_request(url, params)


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
    
    return await _make_cached_request(url, params)
