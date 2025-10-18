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
Expiring Ingredients: {{#if expiringIngredients}}{{#each expiringIngredients}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None{{/if}}
Allergies: {{#if allergies}}{{#each allergies}}{{{this}}}{{#unless @last}}, {{/unless}}{{/each}}{{else}}None{{/if}}
Inventory Match Percentage: {{{inventoryMatchPercentage}}}%

Explain why this recipe is a good recommendation for the user. Your explanation should include:

*   Urgency: Based on the expiring ingredients, explain how urgent it is to cook this recipe.
*   Safety: Based on the user's allergies, explain if this recipe is safe for them to consume. Highlight any potential allergens present in the recipe.
*   Money Saving/Impact: Explain how cooking this recipe will help the user save money by using the ingredients they already have and reducing food waste.
*   Overall, what makes this recipe a good recommendation?

Format your response in a paragraph.
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
