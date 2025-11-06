"""
Unified recipe provider facade.

This module abstracts over live Spoonacular access and local mock data.
Use this for all recipe searches in the codebase so mocks can be removed later
by replacing this module's implementation only.
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple
import os

# Live imports
from src.services.spoonacular_service import (
    search_recipes_by_ingredients as live_search_by_ingredients,
    get_recipe_information as live_get_recipe_information,
    search_recipes_complex as live_search_complex,
)
# Mock imports
from src.services.mocks.recommendations import (
    pick_mock_recommendations_by_category,
    find_mock_recipes_by_ingredients,
)


class RecipeProvider:
    """Facade for recipe search operations."""
    def __init__(self, use_mock: Optional[bool] = None) -> None:
        if use_mock is None:
            use_mock = os.getenv("USE_MOCK_RECOMMENDATIONS", "false").lower() == "true"
        self.use_mock = bool(use_mock)

    async def search_by_category(
        self,
        category: str,
        number: int,
        exclude_ingredients: Optional[List[str]] = None,
        intolerances: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Search recipes by category/cuisine/dishType.

        For live, maps category into Spoonacular's query/cuisine/type filters.
        For mocks, picks from local dataset.
        """
        if self.use_mock:
            return pick_mock_recommendations_by_category(category or "general", number)
        # Live path
        cuisine = category if category in [
            "italian", "asian", "mexican", "american", "mediterranean", "greek", "indian"
        ] else None
        rtype = category if category in ["breakfast", "dessert", "soup", "salad"] else None
        query = category if (category and category not in (cuisine or rtype or "")) else ""
        results = await live_search_complex(
            query=query,
            cuisine=cuisine,
            type=rtype,
            exclude_ingredients=exclude_ingredients or [],
            intolerances=intolerances or [],
            number=number,
        )
        return results.get("results", [])

    async def search_with_ingredients(
        self,
        ingredients: List[str],
        number: int,
        ranking: int = 2,
    ) -> List[Dict]:
        """Search using ingredients (used for expiring inventory and fallback)."""
        if self.use_mock:
            return find_mock_recipes_by_ingredients(ingredients or [], number, ranking=ranking)
        return await live_search_by_ingredients(ingredients=ingredients or [], number=number, ranking=ranking)

    async def get_details(self, recipe_id: int) -> Optional[Dict]:
        """Fetch detailed recipe information for live path. In mock mode returns None."""
        if self.use_mock:
            return None
        return await live_get_recipe_information(int(recipe_id))


def get_recipe_provider(use_mock: Optional[bool] = None) -> RecipeProvider:
    return RecipeProvider(use_mock=use_mock)
