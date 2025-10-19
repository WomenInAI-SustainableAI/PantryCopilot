'use server'

import { explainRecipeRecommendation, ExplainRecipeRecommendationInput, ExplainRecipeRecommendationOutput } from '@/ai/flows/explain-recipe-recommendation'
import { improveRecommendationsFromFeedback, ImproveRecommendationsFromFeedbackInput, ImproveRecommendationsFromFeedbackOutput } from '@/ai/flows/improve-recommendations-from-feedback'

export async function getRecipeExplanation(input: ExplainRecipeRecommendationInput): Promise<ExplainRecipeRecommendationOutput> {
    try {
        const result = await explainRecipeRecommendation(input);
        return result;
    } catch (error) {
        console.error("Error getting recipe explanation:", error);
        return { explanation: "I'm sorry, but I couldn't generate an explanation for this recipe at the moment. Please try again later." };
    }
}

export async function submitFeedback(input: ImproveRecommendationsFromFeedbackInput): Promise<ImproveRecommendationsFromFeedbackOutput> {
     try {
        const result = await improveRecommendationsFromFeedback(input);
        return result;
    } catch (error) {
        console.error("Error submitting feedback:", error);
        return { success: false, message: "Failed to submit feedback due to an internal error." };
    }
}
