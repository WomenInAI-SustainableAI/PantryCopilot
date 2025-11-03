// CMAB categories mirrored from backend src/services/cmab_service.py RecipeCategory.CATEGORIES
// Keep this in sync with backend; used for client-side classification and UI filters.

export const CATEGORIES: Record<string, string[]> = {
  italian: ["pasta", "pizza", "risotto", "italian"],
  asian: ["asian", "chinese", "japanese", "thai", "korean", "vietnamese"],
  mexican: ["mexican", "taco", "burrito", "quesadilla"],
  american: ["burger", "bbq", "american", "sandwich"],
  mediterranean: ["mediterranean", "greek", "middle eastern"],
  indian: ["indian", "curry"],
  quick_meals: ["quick", "easy", "30 minute", "15 minute"],
  baking: ["cake", "bread", "cookie", "muffin", "pastry"],
  dessert: ["dessert", "sweet", "chocolate"],
  breakfast: ["breakfast", "brunch", "pancake", "waffle"],
  salad: ["salad", "bowl"],
  soup: ["soup", "stew", "chili"],
  vegetarian: ["vegetarian", "veggie"],
  vegan: ["vegan"],
  healthy: ["healthy", "low calorie", "diet"],
};

export type RecipeCategory = keyof typeof CATEGORIES | "general";

export function getAllCategories(): RecipeCategory[] {
  return [...Object.keys(CATEGORIES), "general"] as RecipeCategory[];
}

// Classify a recipe title + optional tags (e.g., spoonacular dishTypes/cuisines) into CMAB categories.
export function classifyRecipeCategory(recipeTitle: string, recipeTags?: string[] | null): RecipeCategory[] {
  const titleLower = String(recipeTitle || "").toLowerCase();
  const tagsLower = (Array.isArray(recipeTags) ? recipeTags : []).map((t) => String(t || "").toLowerCase());
  const out: string[] = [];
  for (const [cat, keywords] of Object.entries(CATEGORIES)) {
    for (const kw of keywords) {
      if (titleLower.includes(kw) || tagsLower.some((t) => t.includes(kw))) {
        out.push(cat);
        break;
      }
    }
  }
  return (out.length ? out : ["general"]) as RecipeCategory[];
}
