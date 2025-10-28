"use client";

import * as React from "react";
import { useMemo, useState } from "react";
import {
  SidebarProvider,
  Sidebar,
  SidebarInset,
} from "@/components/ui/sidebar";
import SidebarContent from "@/components/layout/sidebar-content";
import Header from "@/components/layout/header";
import type { InventoryFormItem, Recipe, NormalizedRecipe, UserPreferences, UserSettings, Ingredient } from "@/lib/types";
import { initialUser } from "@/lib/data";
import { getInventory, deleteInventoryItem, getCookedRecipes } from "@/app/actions";
import { useAuth } from "@/lib/auth";
import RecipeDetails from "@/components/recipes/recipe-details";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import RecipeCard from "@/components/recipes/recipe-card";
import { differenceInDays } from "date-fns";
import { getExpiryInfo } from "@/lib/expiry";
import { Console } from "console";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export default function Dashboard() {
  const { user } = useAuth();
  const [inventory, setInventory] = useState<InventoryFormItem[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [cookedRecipes, setCookedRecipes] = useState<Recipe[]>([]);
  const [userPreferences, setUserPreferences] =
    useState<UserPreferences>(initialUser);
  const [userSettings, setUserSettings] = useState<UserSettings>({
    userId: '',
    name: '',
    email: ''
  });
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const initialLoadCompleteRef = React.useRef(false);
  const [removedExpired, setRemovedExpired] = useState<InventoryFormItem[]>([]);
  const [showExpiredDialog, setShowExpiredDialog] = useState(false);

  const fetchRecommendations = React.useCallback(async (uid: string) => {
    setLoadingRecommendations(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_URL}/api/users/${uid}/recommendations?limit=3`);
      if (response.ok) {
        const data = await response.json();
        // Normalize recipes so ingredients are consistently objects with name/quantity/unit
        const { normalizeRecipe } = await import("@/lib/normalize-recipe");
        const normalized = (data.recommendations || []).map((r: any) => normalizeRecipe(r));
        setRecipes(normalized as any);
      } else {
        // Fallback: use provided mock recommendations when API data is unavailable
        const { normalizeRecipe } = await import("@/lib/normalize-recipe");
        const normalized = getMockRecommendationsRaw().map((r: any) => normalizeRecipe(r));
        setRecipes(normalized as any);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      // Fallback: use provided mock recommendations when API is unreachable
      const { normalizeRecipe } = await import("@/lib/normalize-recipe");
      const normalized = getMockRecommendationsRaw().map((r: any) => normalizeRecipe(r));
      setRecipes(normalized as any);
    } finally {
      setLoadingRecommendations(false);
    }
  }, []);

  const fetchCooked = React.useCallback(async (uid: string) => {
    try {
      const cooked = await getCookedRecipes(uid, 6);
      setCookedRecipes((cooked || []) as any);
    } catch (e) {
      console.error('Failed to load cooked recipes:', e);
      setCookedRecipes([]);
    }
  }, []);

  const handleUpdateInventory = (newInventory: InventoryFormItem[]) => {
    setInventory(newInventory);
  };

  // Load inventory and recommendations from API
  React.useEffect(() => {
    const loadData = async () => {
      if (!user) return;
      
      try {
        // Load inventory
        const apiInventory = await getInventory(user.id);
        const formInventory: InventoryFormItem[] = apiInventory.map(item => ({
          id: item.id,
          name: item.item_name,
          quantity: item.quantity,
          unit: item.unit,
          purchaseDate: item.added_at,
          expiryDate: item.expiry_date,
          shelfLife: 7
        }));

        // On login/initial load: remove expired items and notify the user
        const now = new Date();
        const expiredItems = formInventory.filter(it => {
          const d = new Date(it.expiryDate);
          if (isNaN(d.getTime())) return false;
          return differenceInDays(d, now) < 0; // already expired
        });

        if (expiredItems.length > 0) {
          const keep: InventoryFormItem[] = [];
          const actuallyRemoved: InventoryFormItem[] = [];
          const expiredSet = new Set(expiredItems.map(i => i.id));
          // Start with non-expired items
          for (const it of formInventory) {
            if (!expiredSet.has(it.id)) keep.push(it);
          }
          // Try to delete expired on the server; if deletion fails, keep the item
          for (const it of expiredItems) {
            try {
              await deleteInventoryItem(user.id, it.id);
              actuallyRemoved.push(it);
            } catch (e) {
              // Keep it if deletion failed
              keep.push(it);
              console.error("Failed to delete expired item:", it.name, e);
            }
          }
          setInventory(keep);
          if (actuallyRemoved.length > 0) {
            setRemovedExpired(actuallyRemoved);
            setShowExpiredDialog(true);
          }
        } else {
          setInventory(formInventory);
        }
        // Load recommendations from API (limit to 3)
        await Promise.all([
          fetchRecommendations(user.id),
          fetchCooked(user.id),
        ]);
      } catch (error) {
        console.error('Failed to load data:', error);
        setInventory([]);
        setRecipes([]);
      } finally {
        setLoadingRecommendations(false);
        initialLoadCompleteRef.current = true;
      }
    };
    loadData();
  }, [user, fetchRecommendations, fetchCooked]);

  const handleCookRecipe = (recipe: NormalizedRecipe, servingsCooked?: number) => {
    // Normalize names helper (align with recommendation matching and summary logic)
    const norm = (s: string) => String(s || "").toLowerCase().replace(/["']/g, "").trim()
      .replace(/\(.*?\)|\[.*?\]|\{.*?\}/g, " ") // drop bracketed descriptors
      .replace(/[^a-z0-9\s]/g, " ") // punctuation
      .replace(/\b(the|a|an)\b/g, " ") // common stopwords
      .replace(/\s+/g, " ")
      .trim()
      .replace(/s\b/g, ""); // naive singularization

    const tokens = (s: string) => new Set(norm(s).split(" ").filter(Boolean));

    // Compute scaling factor from original servings to cooked servings
    const baseServings = Math.max(1, Number((recipe as any)?.servings) || 1);
    const cookedServings = Math.max(1, Number(servingsCooked) || 1);
    const factor = cookedServings / baseServings;

    // Build a mutable map of inventory by id for cumulative updates
    const invById = new Map<string, InventoryFormItem>(inventory.map(item => [item.id, { ...item }]));

    // Helper to find matching inventory item using strict rules:
    // 1) exact normalized match
    // 2) if ingredient has 2+ tokens, require its tokens be a subset of inventory tokens
    const findInventoryFor = (ingredientName: string): InventoryFormItem | undefined => {
      const nameKey = norm(ingredientName);
      // exact match first
      for (const item of invById.values()) {
        if (norm(item.name) === nameKey) return item;
      }
      // multi-word subset from ingredient -> inventory only
      const ingTokensArr = Array.from(tokens(ingredientName));
      if (ingTokensArr.length >= 2) {
        const ingSet = new Set(ingTokensArr);
        for (const item of invById.values()) {
          const invSet = tokens(item.name);
          let subset = true;
          for (const t of ingSet) { if (!invSet.has(t)) { subset = false; break; } }
          if (subset) return item;
        }
      }
      return undefined;
    };

    // Apply reductions per recipe ingredient
    for (const ing of (recipe.ingredients || [])) {
      const invItem = findInventoryFor(ing.name);
      if (!invItem) continue;
      const used = Math.max(0, (ing.quantity || 0) * factor);
      // clamp at zero, only reduce what's available
      const newQty = Math.max(0, invItem.quantity - used);
      invById.set(invItem.id, { ...invItem, quantity: newQty });
    }

    const updatedInventory = Array.from(invById.values()).filter(item => item.quantity > 0);
    setInventory(updatedInventory);
    setSelectedRecipe(null);
  };

  const handleUpdatePreferences = (newPreferences: UserPreferences) => {
    setUserPreferences(newPreferences);
  };

  // Re-fetch recommendations when inventory or preferences change (debounced)
  React.useEffect(() => {
    if (!user || !initialLoadCompleteRef.current) return;
    const handle = setTimeout(() => {
      fetchRecommendations(user.id);
    }, 500);
    return () => clearTimeout(handle);
  }, [inventory, userPreferences, user, fetchRecommendations]);

  // Load preferences and settings from API on mount
  React.useEffect(() => {
    const loadData = async () => {
      if (!user) return;
      
      try {
        const { getUserPreferences, getUserSettings } = await import('@/app/actions');
        const [savedPreferences, savedSettings] = await Promise.all([
          getUserPreferences(user.id),
          getUserSettings(user.id)
        ]);
        setUserPreferences(savedPreferences);
        setUserSettings(savedSettings);
      } catch (error) {
        console.error('Failed to load user data:', error);
      }
    };
    loadData();
  }, [user]);

  const expiringSoonItems = useMemo(() => {
    return inventory
      .filter((item) => {
        const daysUntilExpiry = differenceInDays(new Date(item.expiryDate), new Date());
        return daysUntilExpiry >= 0 && daysUntilExpiry <= 7;
      })
      .sort(
        (a, b) =>
          new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime()
      );
  }, [inventory]);

  const recommendedRecipes = useMemo(() => {
    // Normalize names to improve matching between inventory and recipe ingredients.
    const normalizeName = (s: string) =>
      String(s)
        .toLowerCase()
        // remove bracketed descriptors like "(whole)", "[chopped]", "{organic}"
        .replace(/\(.*?\)|\[.*?\]|\{.*?\}/g, " ")
        // remove punctuation
        .replace(/[^a-z0-9\s]/g, " ")
        // drop common stopwords
        .replace(/\b(the|a|an)\b/g, " ")
        // collapse whitespace
        .replace(/\s+/g, " ")
        .trim()
        // naive singularization (eggs -> egg, tomatoes -> tomate -> not perfect but helps)
        .replace(/s\b/g, "");

    const inventoryMap = new Map(
      inventory.map(item => [normalizeName(item.name), item])
    );
    const expiringSoonNames = new Set(
      expiringSoonItems.map(i => normalizeName(i.name))
    );

    // Build a small index for fuzzy matching using tokens
    const tokenize = (s: string) => new Set(s.split(" ").filter(Boolean));
    type InvIdx = { key: string; item: InventoryFormItem; tokens: Set<string> };
    const inventoryIndex: InvIdx[] = Array.from(inventoryMap.entries()).map(([key, item]) => ({
      key,
      item,
      tokens: tokenize(key),
    }));

    const jaccard = (a: Set<string>, b: Set<string>) => {
      if (a.size === 0 && b.size === 0) return 1;
      let inter = 0;
      for (const t of a) if (b.has(t)) inter++;
      const union = a.size + b.size - inter;
      return union === 0 ? 0 : inter / union;
    };

    const findClosestInventory = (nameKey: string) => {
      const exact = inventoryMap.get(nameKey);
      if (exact) return { item: exact, key: nameKey, score: 1 } as const;
      const tokens = tokenize(nameKey);
      let best: { item: InventoryFormItem; key: string; score: number } | null = null;
      for (const idx of inventoryIndex) {
        // Overlap score based on tokens
        let overlap = 0;
        for (const t of idx.tokens) if (tokens.has(t)) overlap++;
        const overlapScore = Math.max(
          overlap / Math.max(1, idx.tokens.size),
          overlap / Math.max(1, tokens.size)
        );
        // Jaccard similarity across tokens
        const jac = jaccard(idx.tokens, tokens);
        // Simple substring boost (handles phrases like "milanese chicken")
        const substringBoost = nameKey.includes(idx.key) || idx.key.includes(nameKey) ? 0.2 : 0;
        const score = Math.max(overlapScore, jac) + substringBoost;
        if (!best || score > best.score) best = { item: idx.item, key: idx.key, score };
      }
      // Threshold tuned to be permissive but avoid unrelated matches
      if (best && best.score >= 0.6) return best;
      return null;
    };

    

    const updatedRecipes = recipes.map(recipe => {
      let weightedMatchSum = 0;
      let expiringMatches = 0;
      let totalPossibleWeight = 0;
      console.log("Expiring:", Array.from(expiringSoonNames));
      (recipe.ingredients || []).forEach(ingredient => {
        // Support both string ingredient names (e.g. ["milk", "sugar"]) and
        // object ingredients (e.g. [{ name: "milk", quantity: 1 }]).
        const rawName = typeof ingredient === "string" ? ingredient : ingredient?.name;
        console.log("ingredient:", rawName);
        if (!rawName) return;
  const nameKey = normalizeName(String(rawName));
  const closest = findClosestInventory(nameKey);
  const inventoryItem = closest?.item;
        const weight = 1;
        totalPossibleWeight += weight;

        // Match score: only compute ratio when recipe specifies a numeric quantity and we have inventory
        const hasNumericQty = typeof ingredient === "object" && ingredient !== null && (ingredient as any).quantity !== undefined;
        if (inventoryItem && hasNumericQty) {
          const recipeQty = Number((ingredient as any).quantity || 0);
          // avoid division by zero
          const quantityRatio = recipeQty > 0 ? Math.min(inventoryItem.quantity / recipeQty, 1.0) : 1.0;
          weightedMatchSum += quantityRatio * weight;
        }

        // Expiring match: count any ingredient that exists in inventory and is expiring soon,
        // regardless of the recipe-specified quantity. This helps show expiring badges even when
        // ingredient quantities are 0/undefined in the recipe payload.
        if (inventoryItem && closest && expiringSoonNames.has(closest.key)) {
          expiringMatches++;
        }
      });
      
      const matchPercentage = totalPossibleWeight > 0 ? (weightedMatchSum / totalPossibleWeight) * 100 : 0;
      const expiringIngredientBonus = expiringMatches * 10;
      const score = matchPercentage + expiringIngredientBonus;

      

      return {
        ...recipe,
        matchPercentage: Math.round(matchPercentage),
        expiringIngredientsCount: expiringMatches,
        score,
      };
    });

    const filteredRecipes = updatedRecipes.filter((recipe) => {
        const hasAllergens = (recipe.ingredients || []).some(ingredient => ingredient?.name && userPreferences.allergies.includes(ingredient.name.toLowerCase()));
        const hasDislikes = (recipe.ingredients || []).some(ingredient => ingredient?.name && userPreferences.dislikes.includes(ingredient.name.toLowerCase()));
        return !hasAllergens && !hasDislikes;
    });

    return filteredRecipes.sort((a, b) => b.score - a.score);
  }, [recipes, inventory, userPreferences, expiringSoonItems]);

  return (
    <SidebarProvider defaultOpen>
      <Sidebar>
        <SidebarContent
          inventory={inventory}
          onUpdateInventory={handleUpdateInventory}
          preferences={userPreferences}
          onUpdatePreferences={handleUpdatePreferences}
        />
      </Sidebar>
      <SidebarInset>
        <Header 
          settings={userSettings}
          onUpdateSettings={(newSettings) => setUserSettings(newSettings)}
        />
        <main className="p-4 sm:p-6 lg:p-8 space-y-8">
          <div>
            <h1 className="font-headline text-3xl font-bold text-foreground">
              Welcome Back!
            </h1>
            <p className="text-muted-foreground">
              Here&apos;s what&apos;s cooking in your pantry.
            </p>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-6">
              <h2 className="font-headline text-2xl font-semibold">
                Recommended For You
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {loadingRecommendations ? (
                  <div className="col-span-full flex flex-col items-center justify-center py-8">
                    <svg
                      className="animate-spin h-6 w-6 text-primary mb-2"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                    </svg>
                    <p className="text-muted-foreground">Loading recommendations...</p>
                  </div>
                ) : recommendedRecipes.length > 0 ? (
                  // Only display up to 3 recommendations in the UI as an extra safety
                  recommendedRecipes.map((recipe) => (
                    <RecipeCard
                      key={recipe.id}
                      recipe={recipe}
                      onSelectRecipe={setSelectedRecipe}
                    />
                  ))
                ) : (
                  <div className="col-span-full text-center py-8">
                    <p className="text-muted-foreground">
                      No recommendations available. Try adding more items to your inventory.
                    </p>
                  </div>
                )}
              </div>

              <h2 className="font-headline text-2xl font-semibold mt-4">
                Cooked Before
              </h2>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {cookedRecipes.length > 0 ? (
                  cookedRecipes.map((recipe) => (
                    <RecipeCard
                      key={`cooked-${recipe.id}`}
                      recipe={recipe}
                      onSelectRecipe={setSelectedRecipe}
                    />
                  ))
                ) : (
                  <div className="col-span-full text-center py-6">
                    <p className="text-muted-foreground text-sm">No cooked recipes yet.</p>
                  </div>
                )}
              </div>
            </div>
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="font-headline">Expiring Soon</CardTitle>
                </CardHeader>
                <CardContent>
                  {expiringSoonItems.length > 0 ? (
                    <ul className="space-y-4">
                      {expiringSoonItems.map((item) => (
                        <li key={item.id} className="flex justify-between items-center">
                          <div>
                            <p className="font-medium">{item.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {item.quantity} {item.unit}
                            </p>
                          </div>
                          {(() => {
                            const { text, severity } = getExpiryInfo(item.expiryDate);
                            const content = text;
                            if (severity === "expired") return <Badge variant="destructive">{content}</Badge>;
                            if (severity === "urgent") return <Badge variant="destructive">{content}</Badge>;
                            if (severity === "soon") return <Badge variant="secondary" className="bg-accent text-accent-foreground">{content}</Badge>;
                            return <Badge variant="outline">{content}</Badge>;
                          })()}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      Nothing is expiring soon. Cook freely!
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
        {selectedRecipe && (
          <RecipeDetails
            recipe={selectedRecipe}
            userPreferences={userPreferences}
            inventory={inventory}
            open={!!selectedRecipe}
            onOpenChange={(isOpen) => !isOpen && setSelectedRecipe(null)}
            onCookRecipe={handleCookRecipe}
          />
        )}

        {/* Expired items removed dialog */}
        <AlertDialog open={showExpiredDialog} onOpenChange={setShowExpiredDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Expired items removed</AlertDialogTitle>
            </AlertDialogHeader>
            <div className="text-sm text-muted-foreground">
              <p className="mb-2">We noticed some items had expired and removed them from your inventory:</p>
              <ul className="list-disc pl-5 space-y-1 text-foreground">
                {removedExpired.map((it) => (
                  <li key={it.id}>
                    {it.name} — {it.quantity} {it.unit} (expired on {new Date(it.expiryDate).toLocaleDateString()})
                  </li>
                ))}
              </ul>
            </div>
            <AlertDialogFooter>
              <AlertDialogAction onClick={() => setShowExpiredDialog(false)}>
                OK
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SidebarInset>
    </SidebarProvider>
  );
}

// Local mock data used when API data is not available
function getMockRecommendationsRaw(): any[] {
  return [
    {
      id: 665734,
      image: "https://img.spoonacular.com/recipes/665734-556x370.jpg",
      title: "Zucchini Chicken Omelette",
      readyInMinutes: 45,
      servings: 2,
      summary: "Zucchini Chicken Omelette is a main course that serves 2. For <b>72 cents per serving</b>...",
      dishTypes: ["lunch","main course","morning meal","brunch","main dish","breakfast","dinner"],
      extendedIngredients: [
        { name: "eggs", amount: 3.0, unit: "", measures: { metric: { amount: 3.0, unitShort: "" }, us: { amount: 3.0, unitShort: "" } } },
        { name: "water", amount: 1.0, unit: "tablespoon", measures: { metric: { amount: 1.0, unitShort: "Tbsp" }, us: { amount: 1.0, unitShort: "Tbsp" } } },
        { name: "zucchini", amount: 150.0, unit: "grams", measures: { metric: { amount: 150.0, unitShort: "g" }, us: { amount: 5.291, unitShort: "oz" } } },
        { name: "salt and pepper", amount: 2.0, unit: "servings", measures: { metric: { amount: 2.0, unitShort: "servings" }, us: { amount: 2.0, unitShort: "servings" } } },
        { name: "oil", amount: 1.0, unit: "tablespoon", measures: { metric: { amount: 1.0, unitShort: "Tbsp" }, us: { amount: 1.0, unitShort: "Tbsp" } } },
        { name: "milanese chicken left over", amount: 80.0, unit: "grams", measures: { metric: { amount: 80.0, unitShort: "g" }, us: { amount: 1.355, unitShort: "oz" } } }
      ],
      analyzedInstructions: [{ steps: [
        { number: 1, step: "Beat eggs and water in a bowl." },
        { number: 2, step: "Mix in grated zucchini and season with salt and pepper." },
        { number: 3, step: "Heat oil, add half the egg mixture and diced chicken." },
        { number: 4, step: "Cook until set and fold; repeat." },
        { number: 5, step: "Serve with salad." }
      ]}],
      scoring: { overall_score: 21.6667, match_percentage: 16.6667 }
    },
    {
      id: 649495,
      image: "https://img.spoonacular.com/recipes/649495-556x370.jpg",
      title: "Lemon and Garlic Slow Roasted Chicken",
      readyInMinutes: 45,
      servings: 6,
      summary: "Lemon and Garlic Slow Roasted Chicken might be a good recipe to expand your main course recipe box...",
      dishTypes: ["lunch","main course","main dish","dinner"],
      extendedIngredients: [
        { name: "chicken weighing 2.3kg", amount: 1.0, unit: "large", measures: { metric: { amount: 0.48, unitShort: "large" }, us: { amount: 0.48, unitShort: "large" } } },
        { name: "bulbs garlic", amount: 2.0, unit: "", measures: { metric: { amount: 2.0, unitShort: "" }, us: { amount: 2.0, unitShort: "" } } },
        { name: "lemons", amount: 2.0, unit: "large", measures: { metric: { amount: 2.0, unitShort: "large" }, us: { amount: 2.0, unitShort: "large" } } },
        { name: "olive oil", amount: 1.0, unit: "tablespoon", measures: { metric: { amount: 1.0, unitShort: "Tbsp" }, us: { amount: 1.0, unitShort: "Tbsp" } } },
        { name: "salt and pepper", amount: 1.0, unit: "", measures: { metric: { amount: 1.0, unitShort: "" }, us: { amount: 1.0, unitShort: "" } } },
        { name: "sunflower oil", amount: 2.0, unit: "tablespoons", measures: { metric: { amount: 2.0, unitShort: "Tbsps" }, us: { amount: 2.0, unitShort: "Tbsps" } } }
      ],
      analyzedInstructions: [{ steps: [
        { number: 1, step: "Trim chicken, season, prepare garlic." },
        { number: 2, step: "Roast and then slow-cook until tender." },
        { number: 3, step: "Stir-fry vegetables and serve with chicken." }
      ]}],
      scoring: { overall_score: 21.6667, match_percentage: 16.6667 }
    },
    {
      id: 632075,
      image: "https://img.spoonacular.com/recipes/632075-556x370.jpg",
      title: "All Day Simple Slow-Cooker FALL OFF the BONE Ribs",
      readyInMinutes: 45,
      servings: 4,
      summary: "All Day Simple Slow-Cooker FALL OFF the BONE Ribs takes around <b>45 minutes</b>...",
      dishTypes: ["antipasti","starter","snack","appetizer","antipasto","hor d'oeuvre"],
      extendedIngredients: [
        { name: "slabs of pork ribs", amount: 2.0, unit: "", measures: { metric: { amount: 2.0, unitShort: "" }, us: { amount: 2.0, unitShort: "" } } },
        { name: "broth", amount: 0.25, unit: "Cup", measures: { metric: { amount: 0.12, unitShort: "cups" }, us: { amount: 0.25, unitShort: "cups" } } },
        { name: "bbq sauce", amount: 40.0, unit: "oz", measures: { metric: { amount: 1.134, unitShort: "kgs" }, us: { amount: 40.0, unitShort: "oz" } } },
        { name: "salt", amount: 4.0, unit: "servings", measures: { metric: { amount: 4.0, unitShort: "servings" }, us: { amount: 4.0, unitShort: "servings" } } }
      ],
      analyzedInstructions: [{ steps: [
        { number: 1, step: "Season and layer ribs in slow cooker with BBQ sauce and broth." },
        { number: 2, step: "Cook low 8-10 hrs; broil with more sauce to finish." }
      ]}],
      scoring: { overall_score: 7.5, match_percentage: 0.0 }
    }
  ];
}