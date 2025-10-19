export interface ExplainRecipeRecommendationInput {
  recipeName: string;
  expiringIngredients: string[];
  allergies: string[];
  inventoryMatchPercentage: number;
  missingIngredients?: string[];
}

export interface ExplainRecipeRecommendationOutput {
  explanation: string;
}

export async function explainRecipeRecommendation(
  input: ExplainRecipeRecommendationInput
): Promise<ExplainRecipeRecommendationOutput> {
  // Mock implementation - replace with actual API call
  return {
    explanation: `This recipe is recommended because it uses ${input.inventoryMatchPercentage}% of your available ingredients and helps use up expiring items.`
  };
}