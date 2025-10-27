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
import { getInventory } from "@/app/actions";
import { useAuth } from "@/lib/auth";
import RecipeDetails from "@/components/recipes/recipe-details";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import RecipeCard from "@/components/recipes/recipe-card";
import { differenceInDays, formatDistanceToNow } from "date-fns";
import { Console } from "console";

export default function Dashboard() {
  const { user } = useAuth();
  const [inventory, setInventory] = useState<InventoryFormItem[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
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
        setRecipes([]);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      setRecipes([]);
    } finally {
      setLoadingRecommendations(false);
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
        setInventory(formInventory);
        // Load recommendations from API (limit to 3)
        await fetchRecommendations(user.id);
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
  }, [user, fetchRecommendations]);

  const handleCookRecipe = (recipe: NormalizedRecipe) => {
    const updatedInventory = inventory.map(invItem => {
      const recipeIngredient = recipe.ingredients.find(
        ing => ing.name.toLowerCase() === invItem.name.toLowerCase()
      );
      if (recipeIngredient) {
        return {
          ...invItem,
          quantity: Math.max(0, invItem.quantity - recipeIngredient.quantity),
        };
      }
      return invItem;
    }).filter(item => item.quantity > 0);
  
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
                          <Badge variant="destructive">
                            Expires in {formatDistanceToNow(new Date(item.expiryDate))}
                          </Badge>
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
      </SidebarInset>
    </SidebarProvider>
  );
}