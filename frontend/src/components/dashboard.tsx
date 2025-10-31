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
import { initialUser, RECOMMEND_LIMITS } from "@/lib/data";
import { getInventory, deleteInventoryItem, getCookedRecipes, getExpiredAck, addExpiredAck, getExpiredInventory } from "@/app/actions";
import { useAuth } from "@/lib/auth";
import RecipeDetails from "@/components/recipes/recipe-details";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import RecipeCard from "@/components/recipes/recipe-card";
import { differenceInDays } from "date-fns";
import { getExpiryInfo } from "@/lib/expiry";
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
import { getAllCategories, classifyRecipeCategory } from "@/lib/categories";
 

export default function Dashboard() {
  const { user } = useAuth();
  const [inventory, setInventory] = useState<InventoryFormItem[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [cookedRecipes, setCookedRecipes] = useState<Recipe[]>([]);
  // Preferences and settings
  const [userPreferences, setUserPreferences] = useState<UserPreferences>(initialUser);
  const [userSettings, setUserSettings] = useState<UserSettings>({ userId: "", name: "", email: "" });

  // UI state
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedLimit, setSelectedLimit] = useState<number>(3);
  const initialLoadCompleteRef = React.useRef<boolean>(false);

  // Expired items popup state
  const [removedExpired, setRemovedExpired] = useState<InventoryFormItem[]>([]);
  const [showExpiredDialog, setShowExpiredDialog] = useState<boolean>(false);

  // Cross-device acknowledgement helpers for expired popup
  const ACK_KEY = "pc_ack_expired_v1";
  const toUtcEpochMs = (input: unknown): number => {
    if (input instanceof Date) return input.getTime();
    if (typeof input === "number") return Math.trunc(input);
    const s = String(input || "");
    // If timezone info is present (Z or +/-HH:MM), Date will parse as UTC/offset correctly
    const hasTZ = /Z|[+-]\d{2}:?\d{2}$/.test(s);
    const parsed = new Date(s);
    if (hasTZ && !Number.isNaN(parsed.getTime())) return parsed.getTime();
    // Handle ISO without timezone explicitly as UTC
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$/);
    if (m) {
      const [, Y, M, D, h, mi, se, ms] = m;
      return Date.UTC(Number(Y), Number(M) - 1, Number(D), Number(h), Number(mi), Number(se), Number(ms || "0"));
    }
    // Date-only fallback (treat as end-of-day UTC to match backend expiry end-of-day semantics)
    const m2 = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (m2) {
      const [, Y, M, D] = m2;
      return Date.UTC(Number(Y), Number(M) - 1, Number(D), 23, 59, 59, 999);
    }
    // Fallback to native parsing
    return parsed.getTime();
  };
  const getAckSet = (): Set<string> => {
    try {
      const raw = typeof window !== "undefined" ? window.localStorage.getItem(ACK_KEY) : null;
      const arr = raw ? (JSON.parse(raw) as string[]) : [];
      return new Set<string>(Array.isArray(arr) ? arr : []);
    } catch {
      return new Set<string>();
    }
  };
  const setAckSet = (s: Set<string>) => {
    try {
      if (typeof window !== "undefined") window.localStorage.setItem(ACK_KEY, JSON.stringify(Array.from(s)));
    } catch {}
  };
  const makeAckKey = (it: InventoryFormItem) => `${it.id}|${toUtcEpochMs(it.expiryDate)}`;

  // Fetch recommendations from backend (backend handles any mock fallback)
  const fetchRecommendations = React.useCallback(
    async (uid: string, opts?: { category?: string; limit?: number }) => {
      setLoadingRecommendations(true);
      try {
        const category = (opts?.category || "").trim();
        const limit = Math.max(1, Number(opts?.limit || selectedLimit) || 3);
        const base = getApiBaseUrl();
        // If a category is selected, prefer server-side filtered endpoint (so backend mock/live can honor it)
        let url = `${base}/users/${uid}/recommendations?limit=${encodeURIComponent(String(limit))}`;
        if (category) {
          const lower = category.toLowerCase();
          const cuisines = new Set(["italian","asian","mexican","american","mediterranean","indian","greek","french"]);
          const dishTypes = new Set(["breakfast","dessert","soup","salad","baking","lunch","dinner","quick","snack","appetizer","main course"]);
          const params = new URLSearchParams();
          params.set("limit", String(limit));
          if (cuisines.has(lower)) params.set("cuisine", lower);
          else if (dishTypes.has(lower)) params.set("dish_type", lower);
          else params.set("dish_type", lower); // map other categories (vegan, vegetarian, healthy) to dish_type for mock classification
          url = `${base}/users/${uid}/recommendations/filtered?${params.toString()}`;
        }
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          const list = data?.recommendations || [];
          if (list.length > 0) {
            const { normalizeRecipe } = await import("@/lib/normalize-recipe");
            // When using filtered endpoint, backend already honored category; avoid double-filtering to prevent empty state
            const normalized = list.map((r: any) => normalizeRecipe(r));
            setRecipes(normalized as any);
          } else {
            setRecipes([]);
          }
        } else {
          setRecipes([]);
        }
      } catch (error) {
        console.error('Failed to load recommendations:', error);
        setRecipes([]);
      } finally {
        setLoadingRecommendations(false);
      }
    },
    [selectedLimit, selectedCategory]
  );

  // Fetch cooked recipes and de-dupe locally
  const fetchCooked = React.useCallback(async (uid: string) => {
    try {
      const cooked = await getCookedRecipes(uid, 6);
      const seen = new Set<string>();
      const unique = (cooked || []).filter((r: any) => {
        const id = String(r?.id ?? "");
        if (!id || seen.has(id)) return false;
        seen.add(id);
        return true;
      });
      setCookedRecipes(unique as any);
    } catch (e) {
      console.error('Failed to load cooked recipes:', e);
      setCookedRecipes([]);
    }
  }, []);

  const handleUpdateInventory = (newInventory: InventoryFormItem[]) => {
    setInventory(newInventory);
  };

  // Load inventory and recommendations from API (initial load only)
  React.useEffect(() => {
    const loadData = async () => {
      // Avoid reruns after initial load; subsequent changes use the debounced effect
      if (initialLoadCompleteRef.current) return;
      if (!user) {
        // Not logged in: no frontend mocks; show empty state
        setRecipes([]);
        initialLoadCompleteRef.current = true;
        return;
      }
      
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

        // Fetch authoritative expired list from the server to avoid timezone mismatches
        const serverExpired = await getExpiredInventory(user.id);
        const expiredIdSet = new Set<string>((serverExpired || []).map((e: any) => String(e?.id || "")));
        // Convert server expired items to form shape for popup display and ack keys
        const expiredForm: InventoryFormItem[] = (serverExpired || []).map((e: any) => ({
          id: String(e?.id || ""),
          name: e?.item_name,
          quantity: e?.quantity,
          unit: e?.unit,
          purchaseDate: e?.added_at,
          expiryDate: e?.expiry_date,
          shelfLife: 7,
        }));

        // Do not show expired items in current inventory UI (authoritative by server)
        const currentInventory = formInventory.filter(it => !expiredIdSet.has(String(it.id)));
        setInventory(currentInventory);

        // Show expired dialog only for items not previously acknowledged (prefer server-stored ack)
        const serverAckKeys = await getExpiredAck(user.id);
        const ack = new Set<string>(Array.isArray(serverAckKeys) ? serverAckKeys : []);
        const unseen = expiredForm.filter(it => !ack.has(makeAckKey(it)));
        if (unseen.length > 0) {
          setRemovedExpired(unseen);
          setShowExpiredDialog(true);
        }
        // Load recommendations from API with current filters
        const catParam = (selectedCategory || "").toLowerCase() === "general" ? "" : selectedCategory;
        await Promise.all([
          fetchRecommendations(user.id, { category: catParam, limit: selectedLimit }),
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
  }, [user]);

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
      Promise.all([getInventory(user.id), getExpiredInventory(user.id)])
        .then(([apiInventory, serverExpired]) => {
          const formInventory: InventoryFormItem[] = apiInventory.map(item => ({
            id: item.id,
            name: item.item_name,
            quantity: item.quantity,
            unit: item.unit,
            purchaseDate: item.added_at,
            expiryDate: item.expiry_date,
            shelfLife: 7,
          }));
          // Filter out expired from the refreshed list using server authoritative list
          const expiredIdSet = new Set<string>((serverExpired || []).map((e: any) => String(e?.id || "")));
          const currentInventory = formInventory.filter(it => !expiredIdSet.has(String(it.id)));
          setInventory(currentInventory);
        })
        .catch(() => {/* ignore background refresh errors */});
    }
  };

  const handleUpdatePreferences = (newPreferences: UserPreferences) => {
    setUserPreferences(newPreferences);
  };

  // Re-fetch recommendations when inventory or preferences change (debounced)
  React.useEffect(() => {
    if (!initialLoadCompleteRef.current) return;
    if (!user) return;
    // Immediately indicate loading to prevent empty-state flash during debounce
    setLoadingRecommendations(true);
    const handle = setTimeout(() => {
      const catParam = (selectedCategory || "").toLowerCase() === "general" ? "" : selectedCategory;
      fetchRecommendations(user.id, { category: catParam, limit: selectedLimit });
    }, 500);
    return () => clearTimeout(handle);
  }, [inventory, userPreferences, selectedCategory, selectedLimit, user, fetchRecommendations]);

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

    

    // Unit conversion helpers for better match% (e.g., 3 kg inventory vs 300 g recipe)
    const massUnits: Record<string, number> = { g: 1, gram: 1, grams: 1, kg: 1000, kilogram: 1000, kilograms: 1000, mg: 0.001, milligram: 0.001, milligrams: 0.001 };
    const volumeUnits: Record<string, number> = { ml: 1, milliliter: 1, milliliters: 1, l: 1000, liter: 1000, liters: 1000 };
    const pieceUnits = new Set(["", "piece", "pieces", "pc", "pcs", "count"]);
    const toMassG = (qty: number, unit?: string): number | null => {
      const u = String(unit || '').toLowerCase();
      if (u in massUnits) return qty * massUnits[u];
      return null;
    };
    const toVolumeML = (qty: number, unit?: string): number | null => {
      const u = String(unit || '').toLowerCase();
      if (u in volumeUnits) return qty * volumeUnits[u];
      return null;
    };
    const sameDimensionRatio = (reqQty: number, reqUnit: string | undefined, invQty: number, invUnit: string | undefined): number | null => {
      // Try mass
      const rMass = toMassG(reqQty, reqUnit);
      const iMass = toMassG(invQty, invUnit);
      if (rMass !== null && iMass !== null) return rMass > 0 ? Math.min(iMass / rMass, 1) : 1;
      // Try volume
      const rVol = toVolumeML(reqQty, reqUnit);
      const iVol = toVolumeML(invQty, invUnit);
      if (rVol !== null && iVol !== null) return rVol > 0 ? Math.min(iVol / rVol, 1) : 1;
      // Pieces: if both are piece-like, compare directly
      if (pieceUnits.has(String(reqUnit || '').toLowerCase()) && pieceUnits.has(String(invUnit || '').toLowerCase())) {
        return reqQty > 0 ? Math.min(invQty / reqQty, 1) : 1;
      }
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
          const recipeUnit = String((ingredient as any)?.unit || '');
          const invQty = Number(inventoryItem.quantity || 0);
          const invUnit = String(inventoryItem.unit || '');
          // Try to compare using unit conversions; if not comparable, fall back to presence-based match
          const ratio = sameDimensionRatio(recipeQty, recipeUnit, invQty, invUnit);
          const quantityRatio = ratio === null ? 1.0 : ratio;
          weightedMatchSum += quantityRatio * weight;
        } else if (inventoryItem) {
          // No numeric qty on ingredient; treat presence as a full match
          weightedMatchSum += 1.0 * weight;
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

    // Rely on backend to honor category filtering; avoid double-filtering here to prevent empty UI when tags differ
    const afterCategory = filteredRecipes;

    return afterCategory.sort((a, b) => b.score - a.score);
  }, [recipes, inventory, userPreferences, expiringSoonItems, selectedCategory]);

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
                    <Label htmlFor="category-select">Category</Label>
                    <Select
                      value={selectedCategory || "__any__"}
                      onValueChange={(v) => {
                        setSelectedCategory(v === "__any__" ? "" : v);
                        // Immediately show loader to avoid empty-state flash while refetching
                        setLoadingRecommendations(true);
                      }}
                    >
                      <SelectTrigger id="category-select">
                        <SelectValue placeholder="Any category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__any__">Any</SelectItem>
                        {getAllCategories().map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
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
              <div className="relative grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {loadingRecommendations && (
                  <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-background/40">
                    <svg
                      className="animate-spin h-6 w-6 text-primary mr-2"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                    </svg>
                    <p className="text-muted-foreground">Updating recommendations…</p>
                  </div>
                )}
                {selectedCategory ? (
                  recommendedRecipes.length > 0 ? (
                    recommendedRecipes.slice(0, Math.max(1, Number(selectedLimit) || 3)).map((recipe) => (
                      <RecipeCard
                        key={recipe.id}
                        recipe={recipe}
                        onSelectRecipe={setSelectedRecipe}
                      />
                    ))
                  ) : !loadingRecommendations ? (
                    <div className="col-span-full text-center py-8">
                      <p className="text-muted-foreground">
                        No recommendations match this category.
                      </p>
                    </div>
                  ) : null
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
                ) : !loadingRecommendations ? (
                  <div className="col-span-full text-center py-8">
                    <p className="text-muted-foreground">
                      No recommendations available. Try adding more items to your inventory.
                    </p>
                  </div>
                ) : null}
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
              <AlertDialogTitle>Expired items detected</AlertDialogTitle>
            </AlertDialogHeader>
            <div className="text-sm text-muted-foreground">
              <p className="mb-2">These items have expired:</p>
              <ul className="list-disc pl-5 space-y-1 text-foreground">
                {removedExpired.map((it) => (
                  <li key={it.id}>
                    {it.name} — {it.quantity} {it.unit} (expired on {new Date(it.expiryDate).toLocaleDateString()})
                  </li>
                ))}
              </ul>
            </div>
            <AlertDialogFooter>
              <AlertDialogAction onClick={async () => {
                // Mark currently shown expired items as acknowledged on the server for cross-device persistence
                const keys = removedExpired.map(it => makeAckKey(it));
                const ok = user?.id ? await addExpiredAck(user.id, keys) : false;
                // Best-effort local fallback to avoid re-show if offline
                try {
                  const local = getAckSet();
                  for (const k of keys) local.add(k);
                  setAckSet(local);
                } catch {}
                setShowExpiredDialog(false);
              }}>
                OK
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SidebarInset>
    </SidebarProvider>
  );
}

// (Mock data moved to '@/lib/mock-data')