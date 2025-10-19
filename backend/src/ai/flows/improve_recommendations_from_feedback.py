"""
Improve Recommendations from Feedback Flow
A flow that improves recipe recommendations based on user feedback.
"""
from pydantic import BaseModel, Field
from enum import Enum
from src.ai.genkit import ai


class FeedbackType(str, Enum):
    """Enum for feedback types."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    SKIP = "skip"


class ImproveRecommendationsFromFeedbackOutput(BaseModel):
    """Output schema for feedback processing results."""
    success: bool = Field(description="Whether the feedback was successfully processed")
    message: str = Field(description="A message indicating the outcome of the feedback processing")


@ai.flow()
async def improve_recommendations_from_feedback(
    recipe_id: str,
    feedback_type: str,
    user_id: str
) -> ImproveRecommendationsFromFeedbackOutput:
    """
    Processes user feedback to improve future recipe recommendations.
    
    Args:
        recipe_id: The ID of the recipe the user is providing feedback for
        feedback_type: The type of feedback (upvote, downvote, or skip)
        user_id: The ID of the user providing feedback
        
    Returns:
        ImproveRecommendationsFromFeedbackOutput with success status and message
    """
    # Construct the prompt
    prompt = f"""You are an AI assistant that improves recipe recommendations based on user feedback.

A user has provided the following feedback for a recipe:

User ID: {user_id}
Recipe ID: {recipe_id}
Feedback Type: {feedback_type}

Analyze the feedback and update your understanding of the user's preferences.
Based on this feedback, adjust the algorithm to provide better recommendations in the future.

Provide a summary of:
- Whether the feedback was successfully processed (success: true/false)
- A message summarizing how the feedback has been processed and what changes have been made"""

    # Generate the response using ai.generate
    result = await ai.generate(
        prompt=prompt,
        output_schema=ImproveRecommendationsFromFeedbackOutput,
    )
    
    return result.output
