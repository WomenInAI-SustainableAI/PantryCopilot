"""
FastAPI Application for PantryCopilot
Provides AI-powered recipe recommendation APIs
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
import uvicorn
import os
from dotenv import load_dotenv

from src.ai.flows.explain_recipe_recommendation import (
    explain_recipe_recommendation,
    ExplainRecipeRecommendationOutput
)
from src.ai.flows.improve_recommendations_from_feedback import (
    improve_recommendations_from_feedback,
    ImproveRecommendationsFromFeedbackOutput,
    FeedbackType
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PantryCopilot API",
    description="AI-powered recipe recommendations based on your pantry inventory",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models for API endpoints
class ExplainRecipeRecommendationRequest(BaseModel):
    """Request schema for explaining recipe recommendations."""
    recipe_name: str = Field(description="The name of the recipe being recommended")
    expiring_ingredients: List[str] = Field(
        default=[],
        description="A list of ingredients in the user inventory that are expiring soon"
    )
    allergies: List[str] = Field(
        default=[],
        description="A list of allergies the user has"
    )
    inventory_match_percentage: float = Field(
        description="The percentage of ingredients in the recipe that match the user inventory"
    )


class ImproveRecommendationsFromFeedbackRequest(BaseModel):
    """Request schema for processing user feedback."""
    recipe_id: str = Field(description="The ID of the recipe the user is providing feedback for")
    feedback_type: FeedbackType = Field(description="The type of feedback the user is providing")
    user_id: str = Field(description="The ID of the user providing feedback")


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "PantryCopilot API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Recipe Recommendation Explanation Endpoint
@app.post(
    "/api/explain-recommendation",
    response_model=ExplainRecipeRecommendationOutput,
    summary="Explain Recipe Recommendation",
    description="Get a detailed explanation of why a recipe is recommended based on inventory, allergies, and expiring ingredients"
)
async def api_explain_recommendation(
    input_data: ExplainRecipeRecommendationRequest
) -> ExplainRecipeRecommendationOutput:
    """
    Explain why a specific recipe is recommended.
    
    Args:
        input_data: Recipe details including name, expiring ingredients, allergies, and match percentage
        
    Returns:
        Detailed explanation of the recommendation
    """
    try:
        result = await explain_recipe_recommendation(
            recipe_name=input_data.recipe_name,
            expiring_ingredients=input_data.expiring_ingredients,
            allergies=input_data.allergies,
            inventory_match_percentage=input_data.inventory_match_percentage
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")


# Feedback Processing Endpoint
@app.post(
    "/api/process-feedback",
    response_model=ImproveRecommendationsFromFeedbackOutput,
    summary="Process User Feedback",
    description="Process user feedback (upvote, downvote, skip) to improve future recommendations"
)
async def api_process_feedback(
    input_data: ImproveRecommendationsFromFeedbackRequest
) -> ImproveRecommendationsFromFeedbackOutput:
    """
    Process user feedback for a recipe recommendation.
    
    Args:
        input_data: Feedback details including recipe ID, feedback type, and user ID
        
    Returns:
        Success status and message about the feedback processing
    """
    try:
        result = await improve_recommendations_from_feedback(
            recipe_id=input_data.recipe_id,
            feedback_type=input_data.feedback_type.value,
            user_id=input_data.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")


# Run the application
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
