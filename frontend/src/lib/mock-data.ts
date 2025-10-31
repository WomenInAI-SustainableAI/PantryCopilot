import { classifyRecipeCategory } from "@/lib/categories";

// Raw mock recommendations (Spoonacular-like shape)
export function getMockRecommendationsRaw(): any[] {
  // 30+ lightweight mock recipes spanning cuisines and dish types, plus added CMAB coverage
  return [
    { id: 700001, image: "https://img.spoonacular.com/recipes/700001-556x370.jpg", title: "Italian Tomato Basil Pasta", readyInMinutes: 25, servings: 2, cuisines: ["italian"], dishTypes: ["main course","dinner"], summary: "A quick pasta with tomatoes and basil.", extendedIngredients: [
      { name: "spaghetti", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "tomatoes", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } },
      { name: "basil", amount: 10, unit: "g", measures: { metric: { amount: 10, unitShort: "g" }, us: { amount: 0.35, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Cook pasta." }, { number: 2, step: "Sauté tomatoes and basil." }, { number: 3, step: "Combine and serve." }
    ]}], scoring: { overall_score: 20.1, match_percentage: 40.0 } },

    { id: 700002, image: "https://img.spoonacular.com/recipes/700002-556x370.jpg", title: "Mexican Chicken Tacos", readyInMinutes: 30, servings: 3, cuisines: ["mexican"], dishTypes: ["main course","lunch","dinner"], summary: "Simple tacos with spiced chicken.", extendedIngredients: [
      { name: "tortillas", amount: 6, unit: "", measures: { metric: { amount: 6, unitShort: "" }, us: { amount: 6, unitShort: "" } } },
      { name: "chicken breast", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "lettuce", amount: 50, unit: "g", measures: { metric: { amount: 50, unitShort: "g" }, us: { amount: 1.76, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Cook spiced chicken." }, { number: 2, step: "Warm tortillas." }, { number: 3, step: "Assemble tacos." }
    ]}], scoring: { overall_score: 22.0, match_percentage: 35.0 } },

    { id: 700003, image: "https://img.spoonacular.com/recipes/700003-556x370.jpg", title: "French Onion Soup", readyInMinutes: 45, servings: 4, cuisines: ["french"], dishTypes: ["soup","starter","appetizer"], summary: "Classic onion soup with toasted bread.", extendedIngredients: [
      { name: "onions", amount: 4, unit: "", measures: { metric: { amount: 4, unitShort: "" }, us: { amount: 4, unitShort: "" } } },
      { name: "beef broth", amount: 750, unit: "ml", measures: { metric: { amount: 750, unitShort: "ml" }, us: { amount: 25.36, unitShort: "fl oz" } } },
      { name: "baguette", amount: 6, unit: "slices", measures: { metric: { amount: 6, unitShort: "slices" }, us: { amount: 6, unitShort: "slices" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Caramelize onions." }, { number: 2, step: "Add broth and simmer." }, { number: 3, step: "Serve with toasted bread." }
    ]}], scoring: { overall_score: 18.0, match_percentage: 30.0 } },

    // ... (content copied from dashboard mock list) ...

    { id: 700030, image: "https://img.spoonacular.com/recipes/700030-556x370.jpg", title: "Mexican Churro Sundae", readyInMinutes: 25, servings: 2, cuisines: ["mexican","latin american"], dishTypes: ["dessert"], summary: "Warm churros with ice cream.", extendedIngredients: [
      { name: "churros", amount: 6, unit: "", measures: { metric: { amount: 6, unitShort: "" }, us: { amount: 6, unitShort: "" } } },
      { name: "vanilla ice cream", amount: 2, unit: "scoops", measures: { metric: { amount: 2, unitShort: "scoops" }, us: { amount: 2, unitShort: "scoops" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Assemble and serve immediately." }
    ]}], scoring: { overall_score: 14.2, match_percentage: 12.0 } },

    // Added category coverage
    { id: 700031, image: "https://img.spoonacular.com/recipes/700031-556x370.jpg", title: "Easy 15 Minute Garlic Shrimp", readyInMinutes: 15, servings: 2, cuisines: ["american"], dishTypes: ["main course","dinner","quick"], summary: "Quick and easy garlic shrimp.", extendedIngredients: [
      { name: "shrimp", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "garlic", amount: 3, unit: "cloves", measures: { metric: { amount: 3, unitShort: "cloves" }, us: { amount: 3, unitShort: "cloves" } } },
      { name: "butter", amount: 30, unit: "g", measures: { metric: { amount: 30, unitShort: "g" }, us: { amount: 1.06, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Sauté garlic and shrimp for 2-3 minutes." },
      { number: 2, step: "Finish with butter and serve." }
    ]}], scoring: { overall_score: 18.0, match_percentage: 22.0 } },

    { id: 700032, image: "https://img.spoonacular.com/recipes/700032-556x370.jpg", title: "Banana Bread Loaf", readyInMinutes: 60, servings: 8, cuisines: ["american"], dishTypes: ["bread","snack","baking"], summary: "Classic moist banana bread.", extendedIngredients: [
      { name: "bananas", amount: 3, unit: "", measures: { metric: { amount: 3, unitShort: "" }, us: { amount: 3, unitShort: "" } } },
      { name: "flour", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "sugar", amount: 120, unit: "g", measures: { metric: { amount: 120, unitShort: "g" }, us: { amount: 4.23, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Mix and bake until done." }
    ]}], scoring: { overall_score: 15.0, match_percentage: 18.0 } },

    { id: 700033, image: "https://img.spoonacular.com/recipes/700033-556x370.jpg", title: "Chocolate Lava Cake Dessert", readyInMinutes: 25, servings: 2, cuisines: ["french"], dishTypes: ["dessert"], summary: "Rich chocolate lava cakes.", extendedIngredients: [
      { name: "chocolate", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "butter", amount: 80, unit: "g", measures: { metric: { amount: 80, unitShort: "g" }, us: { amount: 2.82, unitShort: "oz" } } },
      { name: "eggs", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Bake until edges set and center molten." }
    ]}], scoring: { overall_score: 16.5, match_percentage: 20.0 } },

    { id: 700034, image: "https://img.spoonacular.com/recipes/700034-556x370.jpg", title: "Vegetarian Lentil Bolognese", readyInMinutes: 40, servings: 4, cuisines: ["italian","vegetarian"], dishTypes: ["main course","dinner"], summary: "Hearty veggie bolognese with lentils.", extendedIngredients: [
      { name: "lentils", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "tomato puree", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "spaghetti", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Simmer sauce and cook pasta." }
    ]}], scoring: { overall_score: 19.0, match_percentage: 28.0 } },

    { id: 700035, image: "https://img.spoonacular.com/recipes/700035-556x370.jpg", title: "Vegan Buddha Bowl", readyInMinutes: 20, servings: 2, cuisines: ["asian","vegan"], dishTypes: ["salad","lunch"], summary: "Colorful bowl with grains and veg.", extendedIngredients: [
      { name: "quinoa", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "broccoli", amount: 120, unit: "g", measures: { metric: { amount: 120, unitShort: "g" }, us: { amount: 4.23, unitShort: "oz" } } },
      { name: "avocado", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Assemble cooked grains and toppings." }
    ]}], scoring: { overall_score: 17.2, match_percentage: 23.0 } },

    { id: 700036, image: "https://img.spoonacular.com/recipes/700036-556x370.jpg", title: "Healthy Quinoa Salad", readyInMinutes: 15, servings: 2, cuisines: ["mediterranean"], dishTypes: ["salad","lunch"], summary: "Light and healthy quinoa salad.", extendedIngredients: [
      { name: "quinoa", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "tomatoes", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } },
      { name: "cucumber", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Combine all ingredients and toss." }
    ]}], scoring: { overall_score: 16.8, match_percentage: 22.0 } },

    { id: 700037, image: "https://img.spoonacular.com/recipes/700037-556x370.jpg", title: "30 Minute Waffle Breakfast", readyInMinutes: 30, servings: 2, cuisines: ["american"], dishTypes: ["breakfast","brunch"], summary: "Crisp waffles in 30 minutes.", extendedIngredients: [
      { name: "flour", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "milk", amount: 250, unit: "ml", measures: { metric: { amount: 250, unitShort: "ml" }, us: { amount: 8.45, unitShort: "fl oz" } } },
      { name: "egg", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Mix batter and cook in waffle iron." }
    ]}], scoring: { overall_score: 15.9, match_percentage: 19.0 } },

    { id: 700038, image: "https://img.spoonacular.com/recipes/700038-556x370.jpg", title: "Muffin Pastry Sampler", readyInMinutes: 35, servings: 6, cuisines: ["american"], dishTypes: ["breakfast","snack","bread"], summary: "Assorted muffins and pastries.", extendedIngredients: [
      { name: "flour", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "sugar", amount: 120, unit: "g", measures: { metric: { amount: 120, unitShort: "g" }, us: { amount: 4.23, unitShort: "oz" } } },
      { name: "butter", amount: 100, unit: "g", measures: { metric: { amount: 100, unitShort: "g" }, us: { amount: 3.53, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Prepare batter and bake in tins." }
    ]}], scoring: { overall_score: 14.8, match_percentage: 17.0 } },
  ];
}

// Filter mock list by CMAB category; fallback to full list if no matches
export function pickMockRecommendationsByCategory(category: string, limit: number): any[] {
  const all = getMockRecommendationsRaw();
  const c = (category || "").toLowerCase();
  if (!c || c === "general") return all.slice(0, Math.max(1, Number(limit) || 3));
  let filtered = all.filter((r) => {
    const tags: string[] = [
      ...(((r as any)?.dishTypes || []) as string[]),
      ...(((r as any)?.cuisines || []) as string[]),
    ].filter(Boolean);
    const cats = classifyRecipeCategory(String(r?.title || ""), tags);
    return cats.map(String).includes(c);
  });
  if (filtered.length === 0) filtered = all;
  return filtered.slice(0, Math.max(1, Number(limit) || 3));
}
