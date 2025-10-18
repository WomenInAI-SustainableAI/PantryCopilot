"""
Explain Recipe Recommendation Flow
Explains why a recipe is recommended based on urgency, safety, and money-saving impact.
"""
from pydantic import BaseModel, Field
from typing import List
from src.ai.genkit import ai


class ExplainRecipeRecommendationInput(BaseModel):
    """Input schema for explaining recipe recommendations."""
    recipe_name: str = Field(description="The name of the recipe being recommended")
    expiring_ingredients: List[str] = Field(
        default=[],
        description="A list of ingredients in the user inventory that are expiring soon"
    )
    allergies: List[str] = Field(
        default=[],
        description="A list of allergies the user has"
    )
    inventory_match_percentage: float = Field(
        description="The percentage of ingredients in the recipe that match the user inventory"
    )


class ExplainRecipeRecommendationOutput(BaseModel):
    """Output schema for recipe recommendation explanations."""
    explanation: str = Field(
        description="A detailed explanation of why the recipe is recommended"
    )


@ai.flow()
async def explain_recipe_recommendation(
    recipe_name: str,
    expiring_ingredients: List[str] = None,
    allergies: List[str] = None,
    inventory_match_percentage: float = 0.0
) -> ExplainRecipeRecommendationOutput:
    """
    Explains why a recipe is recommended to the user.
    
    Args:
        recipe_name: The name of the recipe being recommended
        expiring_ingredients: List of ingredients in the user inventory that are expiring soon
        allergies: List of allergies the user has
        inventory_match_percentage: The percentage of ingredients in the recipe that match the user inventory
        
    Returns:
        ExplainRecipeRecommendationOutput with detailed explanation
    """
    # Handle None defaults
    if expiring_ingredients is None:
        expiring_ingredients = []
    if allergies is None:
        allergies = []
    
    # Format expiring ingredients
    expiring_text = ', '.join(expiring_ingredients) if expiring_ingredients else 'None'
    
    # Format allergies
    allergies_text = ', '.join(allergies) if allergies else 'None'
    
    # Construct the prompt
    prompt = f"""You are an AI recipe recommendation expert. You are provided with the following information about a recipe recommendation:

Recipe Name: {recipe_name}
Expiring Ingredients: {expiring_text}
Allergies: {allergies_text}
Inventory Match Percentage: {inventory_match_percentage}%

Explain why this recipe is a good recommendation for the user. Your explanation should include:

*   Urgency: Based on the expiring ingredients, explain how urgent it is to cook this recipe.
*   Safety: Based on the user's allergies, explain if this recipe is safe for them to consume. Highlight any potential allergens present in the recipe.
*   Money Saving/Impact: Explain how cooking this recipe will help the user save money by using the ingredients they already have and reducing food waste.
*   Overall, what makes this recipe a good recommendation?

Format your response in a paragraph."""

    # Generate the explanation using ai.generate
    result = await ai.generate(
        prompt=prompt,
        output_schema=ExplainRecipeRecommendationOutput,
    )
    
    return result.output
