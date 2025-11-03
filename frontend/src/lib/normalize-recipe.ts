import type { NormalizedRecipe } from "@/lib/types";
import { classifyRecipeCategory } from "@/lib/categories";

// Convert Spoonacular/backend recipe payloads to a consistent NormalizedRecipe shape
function stripHtmlToSteps(html?: string): string[] {
  if (!html) return [];
  const withSep = html.replace(/<li[^>]*>/gi, "||").replace(/<\/li>/gi, "");
  const text = withSep.replace(/<[^>]+>/g, "");
  return text.split("||").map((s) => s.trim()).filter(Boolean);
}

export function normalizeRecipe(raw: any): NormalizedRecipe {
  if (!raw) {
    return {
      id: "",
      title: "",
      description: "",
      ingredients: [],
      instructions: [],
      imageId: "",
      matchPercentage: 0,
    } as NormalizedRecipe;
  }

  // Idempotency: if it already looks normalized (ingredients are objects with name/quantity),
  // return a normalized shape without re-parsing Spoonacular fields.
  const looksNormalized = Array.isArray(raw?.ingredients) && raw.ingredients.every((i: any) => i && typeof i === 'object' && 'name' in i && 'quantity' in i);
  if (looksNormalized) {
    const tags: string[] = [
      ...(((raw as any)?.dishTypes || []) as string[]),
      ...(((raw as any)?.cuisines || []) as string[]),
    ].filter(Boolean);
    const categories = classifyRecipeCategory(String(raw?.title || ''), tags);
    return {
      id: raw?.id ? String(raw.id) : (raw?.recipeId ? String(raw.recipeId) : ''),
      title: raw?.title || '',
      description: raw?.summary || raw?.description || '',
      ingredients: raw.ingredients,
      instructions: Array.isArray(raw?.instructions)
        ? raw.instructions
        : (typeof raw?.instructions === 'string' ? stripHtmlToSteps(raw.instructions) : []),
      imageId: raw?.imageId || '',
      image: raw?.image || raw?.imageUrl,
      matchPercentage: raw?.matchPercentage ?? raw?.scoring?.match_percentage ?? 0,
      categories,
    } as NormalizedRecipe;
  }

  // Instructions: prefer analyzedInstructions -> steps, otherwise parse `instructions` HTML or coerce string -> array
  let instructions: string[] = [];
  if (Array.isArray(raw?.analyzedInstructions) && raw.analyzedInstructions.length) {
    const steps = raw.analyzedInstructions[0]?.steps || [];
    instructions = steps.map((s: any) => s?.step).filter(Boolean);
  } else if (Array.isArray(raw?.instructions)) {
    instructions = raw.instructions.filter(Boolean);
  } else if (typeof raw?.instructions === "string") {
    const parsed = stripHtmlToSteps(raw.instructions);
    instructions = parsed.length ? parsed : raw.instructions.split("\n").map((s: string) => s.trim()).filter(Boolean);
  }

  // Ingredients: prefer extendedIngredients -> map to {name, quantity, unit}
  let ingredients: Array<{ name: string; quantity: number; unit: string }> = [];
  if (Array.isArray(raw?.extendedIngredients) && raw.extendedIngredients.length) {
    ingredients = raw.extendedIngredients.map((ing: any) => {
      const metricAmt = typeof ing?.measures?.metric?.amount === 'number' ? ing.measures.metric.amount : (typeof ing?.amount === 'number' ? ing.amount : 0);
      const metricUnit = ing?.measures?.metric?.unitShort || ing?.unit || ing?.measures?.us?.unitShort || '';
      return {
        name: ing?.name || ing?.original || "",
        quantity: metricAmt,
        unit: metricUnit,
      };
    });
  } else if (Array.isArray(raw?.ingredients) && raw.ingredients.length) {
    ingredients = raw.ingredients.map((i: any) =>
      typeof i === "string" ? { name: i, quantity: 0, unit: "" } : { name: i?.name || "", quantity: i?.quantity ?? 0, unit: i?.unit || "" }
    );
  }

  const matchPercentage = raw?.scoring?.match_percentage ?? raw?.matchPercentage ?? raw?.scoring?.matchPercentage ?? 0;
  const tags: string[] = [
    ...(((raw as any)?.dishTypes || []) as string[]),
    ...(((raw as any)?.cuisines || []) as string[]),
  ].filter(Boolean);
  const categories = classifyRecipeCategory(String(raw?.title || ''), tags);

  return {
    id: raw?.id ? String(raw.id) : (raw?.recipeId ? String(raw.recipeId) : ''),
    title: raw?.title || '',
    description: raw?.summary || raw?.description || '',
    ingredients: ingredients as any,
    instructions,
    imageId: raw?.imageId || '',
    image: raw?.image || raw?.imageUrl,
    servings: typeof raw?.servings === 'number' ? raw.servings : undefined,
    matchPercentage: matchPercentage,
    categories,
  } as NormalizedRecipe;
}
