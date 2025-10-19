import { ExplainRecipeRecommendationInput, ExplainRecipeRecommendationOutput } from '@/ai/flows/explain-recipe-recommendation'
import { ImproveRecommendationsFromFeedbackInput, ImproveRecommendationsFromFeedbackOutput } from '@/ai/flows/improve-recommendations-from-feedback'

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
