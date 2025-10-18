'use server';
/**
 * @fileOverview A flow that improves recipe recommendations based on user feedback.
 *
 * - improveRecommendationsFromFeedback - A function that handles the process of improving recommendations based on feedback.
 * - ImproveRecommendationsFromFeedbackInput - The input type for the improveRecommendationsFromFeedback function.
 * - ImproveRecommendationsFromFeedbackOutput - The return type for the improveRecommendationsFromFeedback function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const ImproveRecommendationsFromFeedbackInputSchema = z.object({
  recipeId: z.string().describe('The ID of the recipe the user is providing feedback for.'),
  feedbackType: z
    .enum(['upvote', 'downvote', 'skip'])
    .describe('The type of feedback the user is providing.'),
  userId: z.string().describe('The ID of the user providing feedback.'),
});
export type ImproveRecommendationsFromFeedbackInput = z.infer<
  typeof ImproveRecommendationsFromFeedbackInputSchema
>;

const ImproveRecommendationsFromFeedbackOutputSchema = z.object({
  success: z.boolean().describe('Whether the feedback was successfully processed.'),
  message: z.string().describe('A message indicating the outcome of the feedback processing.'),
});
export type ImproveRecommendationsFromFeedbackOutput = z.infer<
  typeof ImproveRecommendationsFromFeedbackOutputSchema
>;

export async function improveRecommendationsFromFeedback(
  input: ImproveRecommendationsFromFeedbackInput
): Promise<ImproveRecommendationsFromFeedbackOutput> {
  return improveRecommendationsFromFeedbackFlow(input);
}

const prompt = ai.definePrompt({
  name: 'improveRecommendationsFromFeedbackPrompt',
  input: {schema: ImproveRecommendationsFromFeedbackInputSchema},
  output: {schema: ImproveRecommendationsFromFeedbackOutputSchema},
  prompt: `You are an AI assistant that improves recipe recommendations based on user feedback.

  A user has provided the following feedback for a recipe:

  User ID: {{{userId}}}
  Recipe ID: {{{recipeId}}}
  Feedback Type: {{{feedbackType}}}

  Analyze the feedback and update your understanding of the user's preferences.
  Based on this feedback, adjust the algorithm to provide better recommendations in the future.

  Return a success boolean and message indicating the outcome of the feedback processing.
  The message should summarize how the feedback has been processed and what changes have been made to the recommendation algorithm.
  The output should be in JSON format.
  `, // Ensure output is in JSON format.
});

const improveRecommendationsFromFeedbackFlow = ai.defineFlow(
  {
    name: 'improveRecommendationsFromFeedbackFlow',
    inputSchema: ImproveRecommendationsFromFeedbackInputSchema,
    outputSchema: ImproveRecommendationsFromFeedbackOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
