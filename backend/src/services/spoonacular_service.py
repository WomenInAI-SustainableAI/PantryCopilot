"""
Spoonacular API Integration Service with multi-day persistent caching and fallback.

Enhancements:
- Cache entries persisted in Firestore for several days (configurable)
- In-memory cache remains for fast hot-path reads
- On API overuse/limit (402/429) or network errors, returns a recent stale cache
"""
import os
import httpx
import hashlib
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv
from httpx import HTTPStatusError

from src.db.firestore import db

load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
SPOONACULAR_BASE_URL = "https://api.spoonacular.com"

# Simple in-memory cache: key -> (data, timestamp)
_cache: Dict[str, Tuple[dict, float]] = {}

# Configurable cache TTL and stale fallback window
# Default: 3 days fresh TTL, 7 days stale fallback window
CACHE_DURATION = int(os.getenv("SPOONACULAR_CACHE_TTL_SEC", "259200"))  # 3 days
STALE_FALLBACK_DURATION = int(os.getenv("SPOONACULAR_CACHE_STALE_SEC", "604800"))  # 7 days

# Firestore collection for persistent cache
FS_COLLECTION = "cache_spoonacular"

def _get_cache_key(url: str, params: dict) -> str:
    """Generate cache key from URL and params."""
    key_string = f"{url}_{sorted(params.items())}"
    return hashlib.md5(key_string.encode()).hexdigest()

def _get_cached_response(cache_key: str) -> Optional[dict]:
    """Get cached response from in-memory cache if still valid."""
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            return cached_data
        else:
            # drop expired entry from memory
            del _cache[cache_key]
    return None

def _cache_response(cache_key: str, data: dict) -> None:
    """Cache response with timestamp in memory and Firestore."""
    now = time.time()
    _cache[cache_key] = (data, now)

    # Persist in Firestore for multi-day reuse and fallback
    try:
        doc_ref = db.collection(FS_COLLECTION).document(cache_key)
        doc_ref.set({
            "id": cache_key,
            "data": data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ttl_seconds": CACHE_DURATION,
        })
    except Exception as e:
        # Non-fatal; continue with in-memory cache only
        print(f"Warning: failed to persist cache to Firestore: {e}")


def _get_firestore_cache(cache_key: str, allow_stale: bool = False) -> Optional[dict]:
    """Get cached response from Firestore if within TTL, or stale if allow_stale within fallback window."""
    try:
        doc = db.collection(FS_COLLECTION).document(cache_key).get()
        if not doc.exists:
            return None
        payload = doc.to_dict() or {}
        data = payload.get("data")
        created_at = payload.get("updated_at") or payload.get("created_at")
        if not data or not created_at:
            return None
        # created_at may be a datetime; compute age in seconds
        if isinstance(created_at, datetime):
            age_sec = (datetime.utcnow() - created_at).total_seconds()
        else:
            # If it's a timestamp number or string, fallback parse
            try:
                ts = float(created_at)
                age_sec = time.time() - ts
            except Exception:
                return None

        if age_sec < CACHE_DURATION:
            # also refresh in-memory cache
            _cache[cache_key] = (data, time.time())
            return data
        if allow_stale and age_sec < STALE_FALLBACK_DURATION:
            return data
        return None
    except Exception as e:
        print(f"Warning: failed to read cache from Firestore: {e}")
        return None

async def _make_cached_request(url: str, params: dict) -> dict:
    """Make HTTP request with caching (memory + Firestore) and stale fallback on API errors."""
    cache_key = _get_cache_key(url, params)

    # 1) In-memory fresh cache
    cached_result = _get_cached_response(cache_key)
    if cached_result is not None:
        return cached_result

    # 2) Firestore fresh cache
    fs_fresh = _get_firestore_cache(cache_key, allow_stale=False)
    if fs_fresh is not None:
        return fs_fresh

    # 3) Call API and cache on success; on specific errors, allow stale fallback
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            _cache_response(cache_key, result)
            return result
    except HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        # Spoonacular commonly uses 402 for quota exceeded, 429 for rate limiting
        if status in (402, 429, 403, 500, 502, 503, 504):
            fs_stale = _get_firestore_cache(cache_key, allow_stale=True)
            if fs_stale is not None:
                return fs_stale
        raise
    except Exception:
        # Network or other errors -> attempt stale fallback
        fs_stale = _get_firestore_cache(cache_key, allow_stale=True)
        if fs_stale is not None:
            return fs_stale
        raise


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
    type: Optional[str] = None,
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
    if type:
        # Spoonacular accepts 'type' such as 'dessert', 'breakfast', etc.
        params["type"] = type
    if exclude_ingredients:
        params["excludeIngredients"] = ",".join(exclude_ingredients)
    if diet:
        params["diet"] = diet
    if intolerances:
        params["intolerances"] = ",".join(intolerances)
    
    return await _make_cached_request(url, params)
