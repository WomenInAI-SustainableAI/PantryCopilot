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
import { initialUser, CUISINES, DISH_TYPES, RECOMMEND_LIMITS } from "@/lib/data";
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
import { getApiBaseUrl } from "@/lib/config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

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
  const [selectedCuisine, setSelectedCuisine] = useState<string>("");
  const [selectedDishType, setSelectedDishType] = useState<string>("");
  const [selectedLimit, setSelectedLimit] = useState<number>(3);
  const initialLoadCompleteRef = React.useRef(false);
  const [removedExpired, setRemovedExpired] = useState<InventoryFormItem[]>([]);
  const [showExpiredDialog, setShowExpiredDialog] = useState(false);

  const fetchRecommendations = React.useCallback(async (uid: string, opts?: { cuisine?: string; dishType?: string; limit?: number }) => {
    setLoadingRecommendations(true);
    try {
      const cuisine = (opts?.cuisine || "").trim();
      const dishType = (opts?.dishType || "").trim();
      const limit = Math.max(1, Number(opts?.limit || selectedLimit) || 3);

      const base = getApiBaseUrl();
      let url = `${base}/users/${uid}/recommendations?limit=${encodeURIComponent(String(limit))}`;
      // If user selected any explicit filters, use the filtered endpoint
      if (cuisine || dishType) {
        const qs: string[] = [`limit=${encodeURIComponent(String(limit))}`];
        if (cuisine) qs.push(`cuisine=${encodeURIComponent(cuisine)}`);
        if (dishType) qs.push(`dish_type=${encodeURIComponent(dishType)}`);
        url = `${base}/users/${uid}/recommendations/filtered?${qs.join("&")}`;
      }

      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        const list = (data?.recommendations || []) as any[];
        if (list.length > 0) {
          const { normalizeRecipe } = await import("@/lib/normalize-recipe");
          const normalized = list.map((r: any) => normalizeRecipe(r));
          setRecipes(normalized as any);
        } else {
          // Fallback path when API returns 200 but no results (e.g., 402 quota with empty fallback)
          // Try personalized endpoint if we were using filters; otherwise go to mock
          if (cuisine || dishType) {
            try {
              const alt = await fetch(`${base}/users/${uid}/recommendations?limit=${encodeURIComponent(String(limit))}`);
              if (alt.ok) {
                const altData = await alt.json();
                const altList = (altData?.recommendations || []) as any[];
                if (altList.length > 0) {
                  const { normalizeRecipe } = await import("@/lib/normalize-recipe");
                  const normalized = altList.map((r: any) => normalizeRecipe(r));
                  setRecipes(normalized as any);
                } else {
                  const { normalizeRecipe } = await import("@/lib/normalize-recipe");
                  const pick = pickMockRecommendations(cuisine, dishType, limit);
                  const normalized = pick.map((r: any) => normalizeRecipe(r));
                  setRecipes(normalized as any);
                }
              } else {
                const { normalizeRecipe } = await import("@/lib/normalize-recipe");
                const pick = pickMockRecommendations(cuisine, dishType, limit);
                const normalized = pick.map((r: any) => normalizeRecipe(r));
                setRecipes(normalized as any);
              }
            } catch {
              const { normalizeRecipe } = await import("@/lib/normalize-recipe");
              const pick = pickMockRecommendations(cuisine, dishType, limit);
              const normalized = pick.map((r: any) => normalizeRecipe(r));
              setRecipes(normalized as any);
            }
          } else {
            const { normalizeRecipe } = await import("@/lib/normalize-recipe");
            const pick = pickMockRecommendations(cuisine, dishType, limit);
            const normalized = pick.map((r: any) => normalizeRecipe(r));
            setRecipes(normalized as any);
          }
        }
      } else {
        // Fallback: use provided mock recommendations when API data is unavailable
        const { normalizeRecipe } = await import("@/lib/normalize-recipe");
        const pick = pickMockRecommendations(cuisine, dishType, limit);
        const normalized = pick.map((r: any) => normalizeRecipe(r));
        setRecipes(normalized as any);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
      // Fallback: use provided mock recommendations when API is unreachable
      const { normalizeRecipe } = await import("@/lib/normalize-recipe");
      const pick = pickMockRecommendations((opts?.cuisine || selectedCuisine), (opts?.dishType || selectedDishType), Math.max(1, Number(selectedLimit) || 3));
      const normalized = pick.map((r: any) => normalizeRecipe(r));
      setRecipes(normalized as any);
    } finally {
      setLoadingRecommendations(false);
    }
  }, [selectedLimit]);

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
        // Load recommendations from API with current filters
        await Promise.all([
          fetchRecommendations(user.id, { cuisine: selectedCuisine, dishType: selectedDishType, limit: selectedLimit }),
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
  }, [user, fetchRecommendations, fetchCooked, selectedCuisine, selectedDishType, selectedLimit]);

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

    // Refresh cooked history and inventory from server after a successful cook action
    if (user?.id) {
      // Don't await to keep UI snappy; background refresh is fine
      fetchCooked(user.id);
      getInventory(user.id)
        .then((apiInventory) => {
          const formInventory: InventoryFormItem[] = apiInventory.map(item => ({
            id: item.id,
            name: item.item_name,
            quantity: item.quantity,
            unit: item.unit,
            purchaseDate: item.added_at,
            expiryDate: item.expiry_date,
            shelfLife: 7,
          }));
          setInventory(formInventory);
        })
        .catch(() => {/* ignore background refresh errors */});
    }
  };

  const handleUpdatePreferences = (newPreferences: UserPreferences) => {
    setUserPreferences(newPreferences);
  };

  // Re-fetch recommendations when inventory or preferences change (debounced)
  React.useEffect(() => {
    if (!user || !initialLoadCompleteRef.current) return;
    const handle = setTimeout(() => {
      fetchRecommendations(user.id, { cuisine: selectedCuisine, dishType: selectedDishType, limit: selectedLimit });
    }, 500);
    return () => clearTimeout(handle);
  }, [inventory, userPreferences, selectedCuisine, selectedDishType, selectedLimit, user, fetchRecommendations]);

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
        // Backend enforces allergy filtering. Frontend keeps a minimal exact check only.
        const hasAllergens = (recipe.ingredients || []).some(ingredient => {
          const n = String((ingredient as any)?.name || '').toLowerCase();
          return !!n && (userPreferences.allergies || []).includes(n);
        });
        const hasDislikes = (recipe.ingredients || []).some(ingredient => {
          const n = String((ingredient as any)?.name || '').toLowerCase();
          return !!n && (userPreferences.dislikes || []).includes(n);
        });
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
              <div className="flex flex-col gap-3">
                <h2 className="font-headline text-2xl font-semibold">
                  Recommended For You
                </h2>
                {/* Filters Row */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="flex flex-col gap-1">
                    <Label htmlFor="cuisine-select">Cuisine</Label>
                    <Select value={selectedCuisine || "__any__"} onValueChange={(v) => setSelectedCuisine(v === "__any__" ? "" : v)}>
                      <SelectTrigger id="cuisine-select">
                        <SelectValue placeholder="Any cuisine" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__any__">Any</SelectItem>
                        {CUISINES.map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <Label htmlFor="dish-type-select">Dish type</Label>
                    <Select value={selectedDishType || "__any__"} onValueChange={(v) => setSelectedDishType(v === "__any__" ? "" : v)}>
                      <SelectTrigger id="dish-type-select">
                        <SelectValue placeholder="Any type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__any__">Any</SelectItem>
                        {DISH_TYPES.map((t) => (
                          <SelectItem key={t} value={t}>{t}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <Label htmlFor="limit-select">Limit</Label>
                    <Select value={String(selectedLimit)} onValueChange={(v) => setSelectedLimit(Number(v))}>
                      <SelectTrigger id="limit-select">
                        <SelectValue placeholder="3" />
                      </SelectTrigger>
                      <SelectContent>
                        {RECOMMEND_LIMITS.map((n) => (
                          <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
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
                  recommendedRecipes.slice(0, Math.max(1, Number(selectedLimit) || 3)).map((recipe) => (
                    <RecipeCard
                      key={recipe.id}
                      recipe={recipe}
                      onSelectRecipe={setSelectedRecipe}
                    />
                  ))
                ) : recipes.length > 0 ? (
                  recipes.slice(0, Math.max(1, Number(selectedLimit) || 3)).map((recipe) => (
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
  // 30 lightweight mock recipes spanning cuisines and dish types
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

    { id: 700004, image: "https://img.spoonacular.com/recipes/700004-556x370.jpg", title: "American Pancakes", readyInMinutes: 20, servings: 4, cuisines: ["american"], dishTypes: ["breakfast","brunch"], summary: "Fluffy pancakes for a quick breakfast.", extendedIngredients: [
      { name: "flour", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "milk", amount: 250, unit: "ml", measures: { metric: { amount: 250, unitShort: "ml" }, us: { amount: 8.45, unitShort: "fl oz" } } },
      { name: "egg", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Mix batter." }, { number: 2, step: "Cook on griddle." }
    ]}], scoring: { overall_score: 19.0, match_percentage: 25.0 } },

    { id: 700005, image: "https://img.spoonacular.com/recipes/700005-556x370.jpg", title: "Japanese Miso Ramen", readyInMinutes: 35, servings: 2, cuisines: ["japanese"], dishTypes: ["main course","soup","dinner"], summary: "Comforting miso ramen with veggies.", extendedIngredients: [
      { name: "ramen noodles", amount: 2, unit: "packs", measures: { metric: { amount: 2, unitShort: "packs" }, us: { amount: 2, unitShort: "packs" } } },
      { name: "miso paste", amount: 2, unit: "Tbsp", measures: { metric: { amount: 2, unitShort: "Tbsp" }, us: { amount: 2, unitShort: "Tbsp" } } },
      { name: "spinach", amount: 60, unit: "g", measures: { metric: { amount: 60, unitShort: "g" }, us: { amount: 2.12, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Prepare broth." }, { number: 2, step: "Cook noodles and combine." }
    ]}], scoring: { overall_score: 21.0, match_percentage: 28.0 } },

    { id: 700006, image: "https://img.spoonacular.com/recipes/700006-556x370.jpg", title: "Indian Chickpea Curry", readyInMinutes: 30, servings: 4, cuisines: ["indian"], dishTypes: ["main course","dinner"], summary: "Hearty chana masala-style curry.", extendedIngredients: [
      { name: "chickpeas", amount: 400, unit: "g", measures: { metric: { amount: 400, unitShort: "g" }, us: { amount: 14.11, unitShort: "oz" } } },
      { name: "tomato puree", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "garam masala", amount: 1, unit: "Tbsp", measures: { metric: { amount: 1, unitShort: "Tbsp" }, us: { amount: 1, unitShort: "Tbsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Simmer spices and tomato." }, { number: 2, step: "Add chickpeas and cook." }
    ]}], scoring: { overall_score: 23.0, match_percentage: 32.0 } },

    { id: 700007, image: "https://img.spoonacular.com/recipes/700007-556x370.jpg", title: "Greek Salad Bowl", readyInMinutes: 15, servings: 2, cuisines: ["greek","mediterranean"], dishTypes: ["salad","side dish","lunch"], summary: "Fresh salad with feta and olives.", extendedIngredients: [
      { name: "cucumber", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } },
      { name: "tomatoes", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } },
      { name: "feta", amount: 80, unit: "g", measures: { metric: { amount: 80, unitShort: "g" }, us: { amount: 2.82, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Chop and toss ingredients." }
    ]}], scoring: { overall_score: 17.0, match_percentage: 22.0 } },

    { id: 700008, image: "https://img.spoonacular.com/recipes/700008-556x370.jpg", title: "Chinese Vegetable Stir Fry", readyInMinutes: 18, servings: 2, cuisines: ["chinese","asian"], dishTypes: ["main course","dinner"], summary: "Quick stir fry with mixed veggies.", extendedIngredients: [
      { name: "broccoli", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "soy sauce", amount: 2, unit: "Tbsp", measures: { metric: { amount: 2, unitShort: "Tbsp" }, us: { amount: 2, unitShort: "Tbsp" } } },
      { name: "carrot", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Stir fry vegetables and season." }
    ]}], scoring: { overall_score: 18.5, match_percentage: 24.0 } },

    { id: 700009, image: "https://img.spoonacular.com/recipes/700009-556x370.jpg", title: "Spanish Gazpacho", readyInMinutes: 15, servings: 3, cuisines: ["spanish","european"], dishTypes: ["soup","appetizer","starter"], summary: "Chilled tomato soup.", extendedIngredients: [
      { name: "tomatoes", amount: 4, unit: "", measures: { metric: { amount: 4, unitShort: "" }, us: { amount: 4, unitShort: "" } } },
      { name: "cucumber", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } },
      { name: "olive oil", amount: 2, unit: "Tbsp", measures: { metric: { amount: 2, unitShort: "Tbsp" }, us: { amount: 2, unitShort: "Tbsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Blend and chill." }
    ]}], scoring: { overall_score: 16.0, match_percentage: 20.0 } },

    { id: 700010, image: "https://img.spoonacular.com/recipes/700010-556x370.jpg", title: "Thai Green Curry", readyInMinutes: 30, servings: 3, cuisines: ["thai"], dishTypes: ["main course","dinner"], summary: "Aromatic green curry with coconut milk.", extendedIngredients: [
      { name: "coconut milk", amount: 400, unit: "ml", measures: { metric: { amount: 400, unitShort: "ml" }, us: { amount: 13.53, unitShort: "fl oz" } } },
      { name: "green curry paste", amount: 2, unit: "Tbsp", measures: { metric: { amount: 2, unitShort: "Tbsp" }, us: { amount: 2, unitShort: "Tbsp" } } },
      { name: "chicken thigh", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Simmer curry base." }, { number: 2, step: "Add protein and veg." }
    ]}], scoring: { overall_score: 22.5, match_percentage: 33.0 } },

    { id: 700011, image: "https://img.spoonacular.com/recipes/700011-556x370.jpg", title: "American Cheeseburger", readyInMinutes: 20, servings: 2, cuisines: ["american"], dishTypes: ["main course","lunch"], summary: "Classic cheeseburger with pickles.", extendedIngredients: [
      { name: "ground beef", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "burger buns", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } },
      { name: "cheddar", amount: 2, unit: "slices", measures: { metric: { amount: 2, unitShort: "slices" }, us: { amount: 2, unitShort: "slices" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Grill patties." }, { number: 2, step: "Assemble burger." }
    ]}], scoring: { overall_score: 18.2, match_percentage: 26.0 } },

    { id: 700012, image: "https://img.spoonacular.com/recipes/700012-556x370.jpg", title: "Mediterranean Hummus Plate", readyInMinutes: 10, servings: 2, cuisines: ["mediterranean","middle eastern"], dishTypes: ["appetizer","snack","lunch"], summary: "Creamy hummus with veggies and pita.", extendedIngredients: [
      { name: "chickpeas", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "tahini", amount: 2, unit: "Tbsp", measures: { metric: { amount: 2, unitShort: "Tbsp" }, us: { amount: 2, unitShort: "Tbsp" } } },
      { name: "pita", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Blend hummus and serve with sides." }
    ]}], scoring: { overall_score: 15.8, match_percentage: 24.0 } },

    { id: 700013, image: "https://img.spoonacular.com/recipes/700013-556x370.jpg", title: "Vietnamese Spring Rolls", readyInMinutes: 20, servings: 4, cuisines: ["vietnamese","asian"], dishTypes: ["appetizer","fingerfood","snack"], summary: "Fresh rolls with herbs and shrimp.", extendedIngredients: [
      { name: "rice paper", amount: 8, unit: "", measures: { metric: { amount: 8, unitShort: "" }, us: { amount: 8, unitShort: "" } } },
      { name: "shrimp", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "mint", amount: 10, unit: "g", measures: { metric: { amount: 10, unitShort: "g" }, us: { amount: 0.35, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Prep fillings and roll." }
    ]}], scoring: { overall_score: 17.5, match_percentage: 21.0 } },

    { id: 700014, image: "https://img.spoonacular.com/recipes/700014-556x370.jpg", title: "Irish Beef Stew", readyInMinutes: 90, servings: 4, cuisines: ["irish","british"], dishTypes: ["main course","stew","dinner"], summary: "Slow-cooked stew with root vegetables.", extendedIngredients: [
      { name: "beef chuck", amount: 500, unit: "g", measures: { metric: { amount: 500, unitShort: "g" }, us: { amount: 17.64, unitShort: "oz" } } },
      { name: "potatoes", amount: 3, unit: "", measures: { metric: { amount: 3, unitShort: "" }, us: { amount: 3, unitShort: "" } } },
      { name: "carrots", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Brown beef." }, { number: 2, step: "Simmer with veg." }
    ]}], scoring: { overall_score: 19.9, match_percentage: 27.0 } },

    { id: 700015, image: "https://img.spoonacular.com/recipes/700015-556x370.jpg", title: "Korean Bibimbap Bowl", readyInMinutes: 35, servings: 2, cuisines: ["korean"], dishTypes: ["main course","lunch"], summary: "Rice bowl with veggies and egg.", extendedIngredients: [
      { name: "rice", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "spinach", amount: 60, unit: "g", measures: { metric: { amount: 60, unitShort: "g" }, us: { amount: 2.12, unitShort: "oz" } } },
      { name: "egg", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Cook rice and toppings." }, { number: 2, step: "Assemble bowl." }
    ]}], scoring: { overall_score: 20.5, match_percentage: 29.0 } },

    { id: 700016, image: "https://img.spoonacular.com/recipes/700016-556x370.jpg", title: "Middle Eastern Shakshuka", readyInMinutes: 25, servings: 2, cuisines: ["middle eastern","mediterranean"], dishTypes: ["breakfast","brunch","main course"], summary: "Eggs poached in spiced tomato sauce.", extendedIngredients: [
      { name: "eggs", amount: 4, unit: "", measures: { metric: { amount: 4, unitShort: "" }, us: { amount: 4, unitShort: "" } } },
      { name: "tomato puree", amount: 300, unit: "g", measures: { metric: { amount: 300, unitShort: "g" }, us: { amount: 10.58, unitShort: "oz" } } },
      { name: "paprika", amount: 1, unit: "tsp", measures: { metric: { amount: 1, unitShort: "tsp" }, us: { amount: 1, unitShort: "tsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Simmer sauce." }, { number: 2, step: "Poach eggs in sauce." }
    ]}], scoring: { overall_score: 18.7, match_percentage: 23.0 } },

    { id: 700017, image: "https://img.spoonacular.com/recipes/700017-556x370.jpg", title: "British Scones", readyInMinutes: 25, servings: 6, cuisines: ["british"], dishTypes: ["bread","breakfast","snack"], summary: "Buttery scones for tea time.", extendedIngredients: [
      { name: "flour", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "butter", amount: 80, unit: "g", measures: { metric: { amount: 80, unitShort: "g" }, us: { amount: 2.82, unitShort: "oz" } } },
      { name: "milk", amount: 120, unit: "ml", measures: { metric: { amount: 120, unitShort: "ml" }, us: { amount: 4.06, unitShort: "fl oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Mix dough and bake." }
    ]}], scoring: { overall_score: 14.5, match_percentage: 19.0 } },

    { id: 700018, image: "https://img.spoonacular.com/recipes/700018-556x370.jpg", title: "Caribbean Jerk Chicken", readyInMinutes: 40, servings: 3, cuisines: ["caribbean"], dishTypes: ["main course","dinner"], summary: "Spicy jerk chicken with lime.", extendedIngredients: [
      { name: "chicken thigh", amount: 500, unit: "g", measures: { metric: { amount: 500, unitShort: "g" }, us: { amount: 17.64, unitShort: "oz" } } },
      { name: "jerk seasoning", amount: 1, unit: "Tbsp", measures: { metric: { amount: 1, unitShort: "Tbsp" }, us: { amount: 1, unitShort: "Tbsp" } } },
      { name: "lime", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Marinate and grill." }
    ]}], scoring: { overall_score: 20.2, match_percentage: 27.0 } },

    { id: 700019, image: "https://img.spoonacular.com/recipes/700019-556x370.jpg", title: "Chinese Egg Fried Rice", readyInMinutes: 15, servings: 2, cuisines: ["chinese","asian"], dishTypes: ["main course","lunch"], summary: "Leftover rice fried with egg and veg.", extendedIngredients: [
      { name: "rice", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "egg", amount: 2, unit: "", measures: { metric: { amount: 2, unitShort: "" }, us: { amount: 2, unitShort: "" } } },
      { name: "peas", amount: 60, unit: "g", measures: { metric: { amount: 60, unitShort: "g" }, us: { amount: 2.12, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Fry eggs and rice." }
    ]}], scoring: { overall_score: 17.9, match_percentage: 25.0 } },

    { id: 700020, image: "https://img.spoonacular.com/recipes/700020-556x370.jpg", title: "Italian Margherita Pizza", readyInMinutes: 30, servings: 2, cuisines: ["italian"], dishTypes: ["main course","lunch","dinner"], summary: "Classic tomato, mozzarella, basil pizza.", extendedIngredients: [
      { name: "pizza dough", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } },
      { name: "mozzarella", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "tomato sauce", amount: 120, unit: "g", measures: { metric: { amount: 120, unitShort: "g" }, us: { amount: 4.23, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Top dough and bake." }
    ]}], scoring: { overall_score: 21.8, match_percentage: 34.0 } },

    { id: 700021, image: "https://img.spoonacular.com/recipes/700021-556x370.jpg", title: "Japanese Sushi Bowl", readyInMinutes: 35, servings: 2, cuisines: ["japanese"], dishTypes: ["main course","lunch"], summary: "Deconstructed sushi with rice and fish.", extendedIngredients: [
      { name: "sushi rice", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "salmon", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "nori", amount: 1, unit: "sheet", measures: { metric: { amount: 1, unitShort: "sheet" }, us: { amount: 1, unitShort: "sheet" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Cook rice and assemble." }
    ]}], scoring: { overall_score: 19.6, match_percentage: 23.0 } },

    { id: 700022, image: "https://img.spoonacular.com/recipes/700022-556x370.jpg", title: "Greek Lemon Potatoes", readyInMinutes: 50, servings: 4, cuisines: ["greek","mediterranean"], dishTypes: ["side dish"], summary: "Roasted potatoes with lemon and herbs.", extendedIngredients: [
      { name: "potatoes", amount: 800, unit: "g", measures: { metric: { amount: 800, unitShort: "g" }, us: { amount: 28.22, unitShort: "oz" } } },
      { name: "lemon", amount: 1, unit: "", measures: { metric: { amount: 1, unitShort: "" }, us: { amount: 1, unitShort: "" } } },
      { name: "oregano", amount: 1, unit: "tsp", measures: { metric: { amount: 1, unitShort: "tsp" }, us: { amount: 1, unitShort: "tsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Roast until crisp." }
    ]}], scoring: { overall_score: 16.8, match_percentage: 18.0 } },

    { id: 700023, image: "https://img.spoonacular.com/recipes/700023-556x370.jpg", title: "Spanish Churros", readyInMinutes: 30, servings: 4, cuisines: ["spanish"], dishTypes: ["dessert","snack"], summary: "Fried dough sticks with sugar.", extendedIngredients: [
      { name: "flour", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "water", amount: 240, unit: "ml", measures: { metric: { amount: 240, unitShort: "ml" }, us: { amount: 8.12, unitShort: "fl oz" } } },
      { name: "sugar", amount: 30, unit: "g", measures: { metric: { amount: 30, unitShort: "g" }, us: { amount: 1.06, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Pipe and fry dough." }
    ]}], scoring: { overall_score: 13.9, match_percentage: 16.0 } },

    { id: 700024, image: "https://img.spoonacular.com/recipes/700024-556x370.jpg", title: "American Caesar Salad", readyInMinutes: 15, servings: 2, cuisines: ["american"], dishTypes: ["salad","lunch"], summary: "Crisp romaine with creamy dressing.", extendedIngredients: [
      { name: "romaine", amount: 1, unit: "head", measures: { metric: { amount: 1, unitShort: "head" }, us: { amount: 1, unitShort: "head" } } },
      { name: "croutons", amount: 40, unit: "g", measures: { metric: { amount: 40, unitShort: "g" }, us: { amount: 1.41, unitShort: "oz" } } },
      { name: "parmesan", amount: 30, unit: "g", measures: { metric: { amount: 30, unitShort: "g" }, us: { amount: 1.06, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Toss salad and serve." }
    ]}], scoring: { overall_score: 15.2, match_percentage: 22.0 } },

    { id: 700025, image: "https://img.spoonacular.com/recipes/700025-556x370.jpg", title: "German Pretzels", readyInMinutes: 60, servings: 6, cuisines: ["german","european"], dishTypes: ["bread","snack"], summary: "Traditional soft pretzels.", extendedIngredients: [
      { name: "flour", amount: 350, unit: "g", measures: { metric: { amount: 350, unitShort: "g" }, us: { amount: 12.35, unitShort: "oz" } } },
      { name: "yeast", amount: 7, unit: "g", measures: { metric: { amount: 7, unitShort: "g" }, us: { amount: 0.25, unitShort: "oz" } } },
      { name: "baking soda", amount: 1, unit: "Tbsp", measures: { metric: { amount: 1, unitShort: "Tbsp" }, us: { amount: 1, unitShort: "Tbsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Shape and bake pretzels." }
    ]}], scoring: { overall_score: 14.1, match_percentage: 17.0 } },

    { id: 700026, image: "https://img.spoonacular.com/recipes/700026-556x370.jpg", title: "Chinese Hot and Sour Soup", readyInMinutes: 20, servings: 3, cuisines: ["chinese","asian"], dishTypes: ["soup","starter"], summary: "Savory soup with tofu and mushrooms.", extendedIngredients: [
      { name: "tofu", amount: 150, unit: "g", measures: { metric: { amount: 150, unitShort: "g" }, us: { amount: 5.29, unitShort: "oz" } } },
      { name: "mushrooms", amount: 120, unit: "g", measures: { metric: { amount: 120, unitShort: "g" }, us: { amount: 4.23, unitShort: "oz" } } },
      { name: "vinegar", amount: 1, unit: "Tbsp", measures: { metric: { amount: 1, unitShort: "Tbsp" }, us: { amount: 1, unitShort: "Tbsp" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Simmer ingredients and season." }
    ]}], scoring: { overall_score: 16.4, match_percentage: 21.0 } },

    { id: 700027, image: "https://img.spoonacular.com/recipes/700027-556x370.jpg", title: "Italian Tiramisu", readyInMinutes: 30, servings: 6, cuisines: ["italian"], dishTypes: ["dessert"], summary: "Coffee-soaked ladyfingers with mascarpone.", extendedIngredients: [
      { name: "ladyfingers", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } },
      { name: "mascarpone", amount: 250, unit: "g", measures: { metric: { amount: 250, unitShort: "g" }, us: { amount: 8.82, unitShort: "oz" } } },
      { name: "coffee", amount: 150, unit: "ml", measures: { metric: { amount: 150, unitShort: "ml" }, us: { amount: 5.07, unitShort: "fl oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Layer and chill." }
    ]}], scoring: { overall_score: 13.7, match_percentage: 15.0 } },

    { id: 700028, image: "https://img.spoonacular.com/recipes/700028-556x370.jpg", title: "American BBQ Ribs", readyInMinutes: 120, servings: 4, cuisines: ["american"], dishTypes: ["main course","dinner"], summary: "Slow-cooked ribs with BBQ sauce.", extendedIngredients: [
      { name: "pork ribs", amount: 1000, unit: "g", measures: { metric: { amount: 1000, unitShort: "g" }, us: { amount: 35.27, unitShort: "oz" } } },
      { name: "bbq sauce", amount: 200, unit: "g", measures: { metric: { amount: 200, unitShort: "g" }, us: { amount: 7.05, unitShort: "oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Bake low and slow; finish with sauce." }
    ]}], scoring: { overall_score: 19.1, match_percentage: 20.0 } },

    { id: 700029, image: "https://img.spoonacular.com/recipes/700029-556x370.jpg", title: "Japanese Matcha Latte", readyInMinutes: 5, servings: 1, cuisines: ["japanese"], dishTypes: ["beverage","drink"], summary: "Creamy matcha green tea latte.", extendedIngredients: [
      { name: "matcha", amount: 1, unit: "tsp", measures: { metric: { amount: 1, unitShort: "tsp" }, us: { amount: 1, unitShort: "tsp" } } },
      { name: "milk", amount: 200, unit: "ml", measures: { metric: { amount: 200, unitShort: "ml" }, us: { amount: 6.76, unitShort: "fl oz" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Whisk matcha and milk." }
    ]}], scoring: { overall_score: 12.5, match_percentage: 10.0 } },

    { id: 700030, image: "https://img.spoonacular.com/recipes/700030-556x370.jpg", title: "Mexican Churro Sundae", readyInMinutes: 25, servings: 2, cuisines: ["mexican","latin american"], dishTypes: ["dessert"], summary: "Warm churros with ice cream.", extendedIngredients: [
      { name: "churros", amount: 6, unit: "", measures: { metric: { amount: 6, unitShort: "" }, us: { amount: 6, unitShort: "" } } },
      { name: "vanilla ice cream", amount: 2, unit: "scoops", measures: { metric: { amount: 2, unitShort: "scoops" }, us: { amount: 2, unitShort: "scoops" } } }
    ], analyzedInstructions: [{ steps: [
      { number: 1, step: "Assemble and serve immediately." }
    ]}], scoring: { overall_score: 14.2, match_percentage: 12.0 } },
  ];
}

// Helper: filter mock list by cuisine and dish type; fallback to full list if no matches
function pickMockRecommendations(cuisine: string, dishType: string, limit: number): any[] {
  const all = getMockRecommendationsRaw();
  let filtered = all;
  const c = (cuisine || "").toLowerCase();
  const t = (dishType || "").toLowerCase();
  if (c) {
    filtered = filtered.filter(r => Array.isArray(r.cuisines) && r.cuisines.some((x: string) => String(x || "").toLowerCase() === c));
  }
  if (t) {
    filtered = filtered.filter(r => Array.isArray(r.dishTypes) && r.dishTypes.some((x: string) => String(x || "").toLowerCase() === t));
  }
  if (filtered.length === 0) filtered = all;
  return filtered.slice(0, Math.max(1, Number(limit) || 3));
}