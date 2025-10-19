export enum FeedbackType {
  UPVOTE = "upvote",
  DOWNVOTE = "downvote",
  SKIP = "skip"
}

export interface ImproveRecommendationsFromFeedbackInput {
  recipeId: string;
  feedbackType: FeedbackType;
  userId: string;
}

export interface ImproveRecommendationsFromFeedbackOutput {
  success: boolean;
  message: string;
}

export async function improveRecommendationsFromFeedback(
  input: ImproveRecommendationsFromFeedbackInput
): Promise<ImproveRecommendationsFromFeedbackOutput> {
  // Mock implementation - replace with actual API call
  return {
    success: true,
    message: "Feedback processed successfully"
  };
}