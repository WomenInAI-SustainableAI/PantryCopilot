import { ExplainRecipeRecommendationInput, ExplainRecipeRecommendationOutput } from '@/ai/flows/explain-recipe-recommendation'
import { ImproveRecommendationsFromFeedbackInput, ImproveRecommendationsFromFeedbackOutput } from '@/ai/flows/improve-recommendations-from-feedback'
import { InventoryItem, AddInventoryRequest } from '@/lib/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(input)
        })
        return await response.json()
    } catch (error) {
        console.error("Error submitting feedback:", error);
        return { success: false, message: "Failed to submit feedback due to an internal error." };
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

export async function deleteInventoryItem(userId: string, itemId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/users/${userId}/inventory/${itemId}`, {
        method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete inventory item')
}
