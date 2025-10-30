import { ExplainRecipeRecommendationInput, ExplainRecipeRecommendationOutput } from '@/ai/flows/explain-recipe-recommendation'
import { ImproveRecommendationsFromFeedbackInput, ImproveRecommendationsFromFeedbackOutput } from '@/ai/flows/improve-recommendations-from-feedback'
import { InventoryItem, AddInventoryRequest, UserPreferences, UserSettings } from '@/lib/types'
import { getBaseUrl } from '@/lib/config'

// Use the same API base URL helper as auth to avoid env mismatch issues
const API_BASE = getBaseUrl();

export async function getRecipeExplanation(input: ExplainRecipeRecommendationInput): Promise<ExplainRecipeRecommendationOutput> {
    try {
        const response = await fetch(`${API_BASE}/ai/explain-recipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(input)
        })
        return await response.json()
    } catch (error) {
        console.error("Error getting recipe explanation:", error);
        return { explanation: "I'm sorry, but I couldn't generate an explanation for this recipe at the moment. Please try again later." };
    }
}

export async function submitFeedback(input: ImproveRecommendationsFromFeedbackInput): Promise<ImproveRecommendationsFromFeedbackOutput> {
    try {
        const url = `${API_BASE}/api/users/${input.userId}/feedback`;
        const payload = {
            recipe_id: input.recipeId,
            recipe_title: input.recipeTitle || "",
            recipe_categories: input.recipeCategories && input.recipeCategories.length > 0 ? input.recipeCategories : ["general"],
            feedback_type: input.feedbackType,
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            // Try to parse error message, fallback to status text
            let message = response.statusText || 'Failed to submit feedback.';
            try {
                const data = await response.json();
                message = (data && (data.message || data.detail)) || message;
            } catch {}
            return { success: false, message };
        }

        // Backend returns a UserFeedback object; map to our simple success shape
        await response.json();
        return { success: true, message: 'Thanks! Your feedback helps improve recommendations.' };
    } catch (error) {
        console.error('Error submitting feedback:', error);
        return { success: false, message: 'Failed to submit feedback due to an internal error.' };
    }
}

// Fetch the user's latest feedback for a specific recipe (if any)
export async function getUserFeedbackForRecipe(
    userId: string,
    recipeId: string
): Promise<"upvote" | "downvote" | "skip" | null> {
    try {
        const res = await fetch(`${API_BASE}/api/users/${userId}/feedback`);
        if (!res.ok) return null;
        const items = await res.json();
        // items are ordered desc by created_at on the backend; pick the first matching recipe
        const match = (items || []).find((f: any) => f?.recipe_id === recipeId);
        const t = match?.feedback_type;
        return t === "upvote" || t === "downvote" || t === "skip" ? t : null;
    } catch (e) {
        console.error("Error fetching user feedback:", e);
        return null;
    }
}

// Get a list of cooked recipe IDs (most recent first, de-duplicated by recipe_id)
export async function getCookedRecipeIds(userId: string, limit: number = 6): Promise<string[]> {
    try {
        const res = await fetch(`${API_BASE}/api/users/${userId}/cooked?limit=${limit}`);
        if (!res.ok) return [];
        const items = await res.json();
        // items already most recent first; dedupe by recipe_id
        const seen = new Set<string>();
        const ids: string[] = [];
        for (const it of (items || [])) {
            const rid = String(it?.recipe_id || '');
            if (rid && !seen.has(rid)) {
                seen.add(rid);
                ids.push(rid);
                if (ids.length >= limit) break;
            }
        }
        return ids;
    } catch (e) {
        console.error('Error fetching cooked recipes:', e);
        return [];
    }
}

// Get cooked recipes with optional embedded snapshot. If snapshot is present,
// return it normalized; otherwise, fetch details by ID as a fallback.
export async function getCookedRecipes(userId: string, limit: number = 6): Promise<any[]> {
    try {
        const res = await fetch(`${API_BASE}/api/users/${userId}/cooked?limit=${limit}`);
        if (!res.ok) return [];
        const items = await res.json();
        const { normalizeRecipe } = await import("@/lib/normalize-recipe");

        // Collect normalized recipes from embedded snapshots first
        const normalizedFromSnapshots: any[] = [];
        const missingIds: string[] = [];
        for (const it of (items || [])) {
            const snap = it?.recipe;
            if (snap && snap.id) {
                try {
                    normalizedFromSnapshots.push(normalizeRecipe(snap));
                } catch {
                    // If normalization fails, fallback to fetch
                    if (it?.recipe_id) missingIds.push(String(it.recipe_id));
                }
            } else if (it?.recipe_id) {
                missingIds.push(String(it.recipe_id));
            }
            if (normalizedFromSnapshots.length >= limit) break;
        }

        // Fetch details for any missing IDs (deduped)
        const seen = new Set(normalizedFromSnapshots.map(r => String(r.id)));
        const toFetch = missingIds.filter(id => !seen.has(id)).slice(0, Math.max(0, limit - normalizedFromSnapshots.length));
        if (toFetch.length > 0) {
            const details = await Promise.all(toFetch.map(id => getRecipeDetails(id)));
            for (const d of (details || [])) {
                if (d) {
                    try {
                        normalizedFromSnapshots.push(normalizeRecipe(d));
                    } catch {}
                }
                if (normalizedFromSnapshots.length >= limit) break;
            }
        }
        return normalizedFromSnapshots.slice(0, limit);
    } catch (e) {
        console.error('Error fetching cooked recipes:', e);
        return [];
    }
}

// Fetch recipe details by ID (proxied through our backend)
export async function getRecipeDetails(recipeId: string | number): Promise<any | null> {
    try {
        const id = Number(recipeId);
        if (!id || Number.isNaN(id)) return null;
        const res = await fetch(`${API_BASE}/api/recipes/${id}`);
        if (!res.ok) return null;
        return await res.json();
    } catch (e) {
        console.error('Error fetching recipe details:', e);
        return null;
    }
}

// Inventory API functions
export async function addInventoryItem(userId: string, item: AddInventoryRequest): Promise<InventoryItem> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/inventory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item)
    })
    if (!response.ok) throw new Error('Failed to add inventory item')
    return response.json()
}

export async function getInventory(userId: string): Promise<InventoryItem[]> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/inventory`)
    if (!response.ok) throw new Error('Failed to fetch inventory')
    return response.json()
}

export async function updateInventoryItem(userId: string, itemId: string, updates: Partial<InventoryItem>): Promise<InventoryItem> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/inventory/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    })
    if (!response.ok) throw new Error('Failed to update inventory item')
    return response.json()
}

export async function deleteInventoryItem(userId: string, itemId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/inventory/${itemId}`, {
        method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete inventory item')
}

// User preferences API functions
export async function getUserPreferences(userId: string): Promise<UserPreferences> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/preferences`)
    if (!response.ok) throw new Error('Failed to fetch user preferences')
    return response.json()
}

export async function updateUserPreferences(userId: string, preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
    })
    if (!response.ok) throw new Error('Failed to update user preferences')
    return response.json()
}

export async function getUserSettings(userId: string): Promise<UserSettings> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/settings`)
    if (!response.ok) throw new Error('Failed to fetch user settings')
    return response.json()
}

export async function updateUserSettings(userId: string, settings: Partial<UserSettings>): Promise<UserSettings> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
    })
    if (!response.ok) throw new Error('Failed to update user settings')
    return response.json()
}

// Cooked Recipe API function
export interface CookedRecipeResponse {
    recipe_id: string
    servings_made: number
    recipe_servings: number
    inventory_updates: Record<string, string>
    cmab_updated: boolean
    message: string
}

// SNAPSHOT-COOK SUPPORT (temporary):
// cookRecipe accepts an optional 'snapshot' so the backend can bypass Spoonacular (402 quota/mocks).
// To REMOVE snapshot support later:
//   - Delete the 'snapshot' parameter and its usage in the body below.
//   - The backend can then require Spoonacular for cooking as before.
export async function cookRecipe(
    userId: string,
    recipeId: string,
    servingsMade: number = 1,
    snapshot?: {
        title?: string
        servings?: number
        dishTypes?: string[]
        cuisines?: string[]
        ingredients?: Array<{ name: string; quantity: number; unit?: string }>
        extendedIngredients?: Array<{ name: string; measures?: { metric?: { amount?: number; unitShort?: string } } }>
    }
): Promise<{ success: boolean; data?: CookedRecipeResponse; message?: string }>{
    try {
                const res = await fetch(`${API_BASE}/api/users/${userId}/recipes/cooked`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                            recipe_id: recipeId,
                            servings_made: servingsMade,
                            recipe_title: snapshot?.title,
                            servings: snapshot?.servings,
                            dish_types: snapshot?.dishTypes,
                            cuisines: snapshot?.cuisines,
                            ingredients: snapshot?.ingredients,
                            extended_ingredients: snapshot?.extendedIngredients,
                        })
        });
        if (!res.ok) {
            let message = res.statusText || 'Failed to mark recipe as cooked.';
            try {
                const err = await res.json();
                message = (err && (err.detail || err.message)) || message;
            } catch {}
            return { success: false, message };
        }
        const data = await res.json() as CookedRecipeResponse;
        return { success: true, data };
    } catch (e) {
        console.error('Error calling cooked endpoint:', e);
        return { success: false, message: 'Network error calling cooked endpoint.' };
    }
}
