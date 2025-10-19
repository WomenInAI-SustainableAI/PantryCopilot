"""
FastAPI Application for PantryCopilot
Provides AI-powered recipe recommendation APIs with full CRUD operations
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uvicorn
import os
from dotenv import load_dotenv

# Database Models
from src.db.models import (
    UserCreate, User, UserLogin, UserResponse,
    AllergyCreate, Allergy,
    InventoryItem, InventoryItemUpdate,
    UserFeedbackCreate, UserFeedback
)
from src.auth import hash_password, verify_password

# CRUD Operations
from src.db.crud import users, allergies, inventory, feedback

# Add wrapper functions (remove async since CRUD methods are sync)
def create_user_with_password(user_dict: dict):
    return users.UserCRUD.create_with_password(user_dict)

def get_user_by_email(email: str):
    return users.UserCRUD.get_by_email(email)

# Services
from src.services.inventory_service import add_inventory_item, subtract_inventory_items, get_expiring_soon
from src.services.recommendation_service import (
    get_personalized_recommendations,
    get_recommendations_by_preferences
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

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PantryCopilot API",
        "version": "1.0.0"
    }



# ========== AUTH ENDPOINTS ==========

@app.post("/api/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hashed_password
    }
    
    user = create_user_with_password(user_dict)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@app.post("/api/login", response_model=UserResponse)
async def login_user(login_data: UserLogin):
    """Login user."""
    user = get_user_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# ========== AUTH ENDPOINTS ==========

@app.post("/api/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hashed_password
    }
    
    user = create_user_with_password(user_dict)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@app.post("/api/login", response_model=UserResponse)
async def login_user(login_data: UserLogin):
    """Login user."""
    user = get_user_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# ========== USER ENDPOINTS ==========

@app.post("/api/users", response_model=User, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user."""
    return users.create(user_data)


@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID."""
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


# ========== ALLERGY ENDPOINTS ==========

@app.post("/api/users/{user_id}/allergies", response_model=Allergy, status_code=201)
async def add_allergy(user_id: str, allergy_data: AllergyCreate):
    """Add an allergy for a user."""
    return allergies.create(user_id, allergy_data)


@app.get("/api/users/{user_id}/allergies", response_model=List[Allergy])
async def list_allergies(user_id: str):
    """Get all allergies for a user."""
    return allergies.list_by_user(user_id)


@app.delete("/api/users/{user_id}/allergies/{allergy_id}", status_code=204)
async def remove_allergy(user_id: str, allergy_id: str):
    """Delete an allergy."""
    allergies.delete(user_id, allergy_id)
    return None


# ========== INVENTORY ENDPOINTS ==========

class AddInventoryRequest(BaseModel):
    """Request model for adding inventory with auto-calculated expiry."""
    item_name: str = Field(..., description="Name of the item")
    quantity: float = Field(..., gt=0, description="Quantity")
    unit: Optional[str] = Field("piece", description="Unit of measurement")


@app.post("/api/users/{user_id}/inventory", response_model=InventoryItem, status_code=201)
async def add_inventory(user_id: str, item_data: AddInventoryRequest):
    """
    Add inventory item with AUTO-CALCULATED expiry date.
    Expiry is calculated based on item type and quantity.
    """
    return add_inventory_item(
        user_id=user_id,
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        unit=item_data.unit
    )


@app.get("/api/users/{user_id}/inventory", response_model=List[InventoryItem])
async def list_inventory(user_id: str):
    """Get all inventory items for a user."""
    return inventory.list_by_user(user_id)


@app.get("/api/users/{user_id}/inventory/expiring", response_model=List[InventoryItem])
async def list_expiring_inventory(
    user_id: str,
    days: int = Query(3, description="Number of days to look ahead")
):
    """Get inventory items expiring within specified days."""
    return get_expiring_soon(user_id, days)


@app.put("/api/users/{user_id}/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory(
    user_id: str,
    item_id: str,
    update_data: InventoryItemUpdate
):
    """Update an inventory item."""
    return inventory.update(user_id, item_id, update_data)


@app.delete("/api/users/{user_id}/inventory/{item_id}", status_code=204)
async def delete_inventory(user_id: str, item_id: str):
    """Delete an inventory item."""
    inventory.delete(user_id, item_id)
    return None


# ========== RECIPE RECOMMENDATION ENDPOINTS ==========

@app.get("/api/users/{user_id}/recommendations")
async def get_recommendations(
    user_id: str,
    limit: int = Query(10, description="Number of recommendations")
):
    """
    Get personalized recipe recommendations.
    
    Features:
    - Auto inventory matching
    - Expiring ingredient prioritization
    - Allergen filtering
    - AI-generated explanations
    - Feedback-based learning
    """
    recommendations = await get_personalized_recommendations(user_id, limit)
    return {
        "user_id": user_id,
        "count": len(recommendations),
        "recommendations": recommendations
    }


@app.get("/api/users/{user_id}/recommendations/filtered")
async def get_filtered_recommendations(
    user_id: str,
    cuisine: Optional[str] = Query(None, description="Cuisine type filter"),
    diet: Optional[str] = Query(None, description="Diet type filter"),
    limit: int = Query(10, description="Number of recommendations")
):
    """Get recipe recommendations with additional filters."""
    recommendations = await get_recommendations_by_preferences(
        user_id=user_id,
        cuisine=cuisine,
        diet=diet,
        number_of_recipes=limit
    )
    return {
        "user_id": user_id,
        "filters": {"cuisine": cuisine, "diet": diet},
        "count": len(recommendations),
        "recommendations": recommendations
    }


# ========== RECIPE COOKING / "COOKED" BUTTON ==========

class CookedRecipeRequest(BaseModel):
    """Request model for marking a recipe as cooked."""
    recipe_id: str = Field(..., description="Spoonacular recipe ID")
    servings_made: int = Field(1, description="Number of servings made")


@app.post("/api/users/{user_id}/recipes/cooked")
async def mark_recipe_cooked(user_id: str, request: CookedRecipeRequest):
    """
    Mark recipe as cooked - AUTOMATICALLY SUBTRACTS INGREDIENTS FROM INVENTORY.
    
    This endpoint:
    1. Fetches recipe ingredient quantities from Spoonacular
    2. Adjusts quantities based on servings made
    3. Subtracts ingredients from user inventory
    4. Returns status of each ingredient update
    """
    from src.services.spoonacular_service import get_recipe_ingredients_by_id
    
    # Get recipe ingredients with quantities
    recipe_ingredients_data = await get_recipe_ingredients_by_id(int(request.recipe_id))
    
    # Extract ingredient quantities
    ingredient_quantities = {}
    for ingredient in recipe_ingredients_data.get("ingredients", []):
        name = ingredient.get("name", "")
        amount = ingredient.get("amount", {}).get("metric", {}).get("value", 0)
        
        # Adjust for servings
        # Assuming recipe is for default servings, scale proportionally
        adjusted_amount = amount * request.servings_made
        
        if name and adjusted_amount > 0:
            ingredient_quantities[name] = adjusted_amount
    
    # Subtract from inventory
    results = subtract_inventory_items(user_id, ingredient_quantities)
    
    return {
        "recipe_id": request.recipe_id,
        "servings_made": request.servings_made,
        "inventory_updates": results,
        "message": "Inventory updated successfully"
    }


# ========== FEEDBACK ENDPOINTS ==========

# @app.post("/api/users/{user_id}/feedback", response_model=UserFeedback, status_code=201)
# async def submit_feedback(user_id: str, feedback_data: UserFeedbackCreate):
#     """
#     Submit feedback for a recipe (upvote, downvote, skip).
#     This feedback is used for reinforcement learning to improve recommendations.
#     """
#     # Save feedback to database
#     feedback_record = feedback.create(user_id, feedback_data)
    
#     # Process feedback through AI flow for learning
#     try:
#         await improve_recommendations_from_feedback(
#             recipe_id=feedback_data.recipe_id,
#             feedback_type=feedback_data.feedback_type.value,
#             user_id=user_id
#         )
#     except Exception as e:
#         print(f"Error processing feedback through AI: {e}")
    
#     return feedback_record


# @app.get("/api/users/{user_id}/feedback", response_model=List[UserFeedback])
# async def get_feedback_history(user_id: str):
#     """Get all feedback submitted by a user."""
#     return feedback.list_by_user(user_id)


# ========== RECIPE DETAILS ENDPOINT ==========

@app.get("/api/recipes/{recipe_id}")
async def get_recipe_details(recipe_id: int):
    """
    Get detailed information about a specific recipe from Spoonacular.
    """
    from src.services.spoonacular_service import get_recipe_information
    
    recipe_info = await get_recipe_information(recipe_id)
    return recipe_info

# Serve static files (must be last to not override API routes)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

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
