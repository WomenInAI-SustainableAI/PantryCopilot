'use server';

/**
 * @fileOverview Explains why a recipe is recommended, including urgency, safety, and money-saving impact.
 *
 * - explainRecipeRecommendation - A function that handles explaining the recipe recommendation.
 * - ExplainRecipeRecommendationInput - The input type for the explainRecipeRecommendation function.
 * - ExplainRecipeRecommendationOutput - The return type for the explainRecipeRecommendation function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const ExplainRecipeRecommendationInputSchema = z.object({
  recipeName: z.string().describe('The name of the recipe being recommended.'),
  expiringIngredients: z
    .array(z.string())
    .describe('A list of ingredients in the user inventory that are expiring soon.'),
  allergies: z
    .array(z.string())
    .describe('A list of allergies the user has.'),
  inventoryMatchPercentage: z
    .number()
    .describe(
      'The percentage of ingredients in the recipe that match the user inventory.'
    ),
  missingIngredients: z
    .array(z.string())
    .describe('A list of ingredients required by the recipe that the user does not have enough of.'),
});
export type ExplainRecipeRecommendationInput = z.infer<
  typeof ExplainRecipeRecommendationInputSchema
>;

const ExplainRecipeRecommendationOutputSchema = z.object({
  explanation: z
    .string()
    .describe('A detailed explanation of why the recipe is recommended.'),
});
export type ExplainRecipeRecommendationOutput = z.infer<
  typeof ExplainRecipeRecommendationOutputSchema
>;

export async function explainRecipeRecommendation(
  input: ExplainRecipeRecommendationInput
): Promise<ExplainRecipeRecommendationOutput> {
  return explainRecipeRecommendationFlow(input);
}

const prompt = ai.definePrompt({
  name: 'explainRecipeRecommendationPrompt',
  input: {schema: ExplainRecipeRecommendationInputSchema},
  output: {schema: ExplainRecipeRecommendationOutputSchema},
  prompt: `You are an AI recipe recommendation expert. You are provided with the following information about a recipe recommendation:

Recipe Name: {{{recipeName}}}
Expiring Ingredients Used: {{#if expiringIngredients}}{{#each expiringIngredients}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None{{/if}}
User's Allergies: {{#if allergies}}{{#each allergies}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None{{/if}}
Inventory Match Percentage: {{{inventoryMatchPercentage}}}%
Missing or Insufficient Ingredients: {{#if missingIngredients}}{{#each missingIngredients}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None{{/if}}

Explain why this recipe is a good recommendation for the user. Your explanation should be a concise and helpful paragraph. Address the following points:

*   **Urgency:** Based on the expiring ingredients, explain why it's a good idea to cook this soon.
*   **Money Saving & Impact:** Explain how cooking this recipe helps save money by using up existing ingredients and reducing food waste.
*   **Partial Usage:** Mention that it's a good match based on the inventory. If there are missing ingredients, briefly note what they might need to pick up.
*   **Safety:** Check for allergens. If the recipe is safe, confirm it. If it contains allergens from the user's list, you MUST state this clearly.

Combine these points into a friendly, easy-to-read paragraph.
`,
});

const explainRecipeRecommendationFlow = ai.defineFlow(
  {
    name: 'explainRecipeRecommendationFlow',
    inputSchema: ExplainRecipeRecommendationInputSchema,
    outputSchema: ExplainRecipeRecommendationOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
