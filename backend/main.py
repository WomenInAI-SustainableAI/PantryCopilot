"""
FastAPI Application for PantryCopilot
Provides AI-powered recipe recommendation APIs with full CRUD operations
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    UserFeedbackCreate, UserFeedback, FeedbackType
)
from src.auth import hash_password, verify_password

# CRUD Operations
from src.db.crud import users, allergies, feedback
from src.db.crud.inventory import InventoryCRUD
from src.db.crud.users import UserCRUD

# Add wrapper functions (remove async since CRUD methods are sync)
def create_user_with_password(user_dict: dict):
    return UserCRUD.create_with_password(user_dict)

def get_user_by_email(email: str):
    return UserCRUD.get_by_email(email)

# Services
from src.services.inventory_service import add_inventory_item, subtract_inventory_items, get_expiring_soon
from src.db.crud.inventory import get_expired_items as crud_get_expired_items
from src.services.foodkeeper_service import estimate_shelf_life_days, choose_storage
from src.services.recommendation_service import (
    get_personalized_recommendations,
    get_recommendations_by_preferences,
    update_cmab_with_feedback
)
from src.db.crud.cmab import CMABCRUD
from src.services.cmab_service import RecipeCategory
from src.services.spoonacular_service import get_recipe_information
from src.db.firestore import db

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
    # Allow local frontend dev servers (ports used in this project include 3000, 3001 and the Next dev port 9002)
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:9002", "http://127.0.0.1:9002"],
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
    purchase_date: Optional[str] = Field(None, description="Purchase date (YYYY-MM-DD)")
    shelf_life_days: Optional[int] = Field(None, description="Manual shelf life in days")


def get_shelf_life_days(item_name: str) -> int:
    """Get estimated shelf life in days using FSIS USDA FoodKeeper data.

    We infer the storage location heuristically to avoid changing the API.
    """
    try:
        storage = choose_storage(item_name)
        return int(estimate_shelf_life_days(item_name, storage))
    except Exception as e:
        # Fallback to conservative default if anything goes wrong
        print(f"FoodKeeper shelf life lookup failed for '{item_name}': {e}")
        return 14

@app.post("/api/users/{user_id}/inventory", response_model=InventoryItem, status_code=201)
async def add_inventory(user_id: str, item_data: AddInventoryRequest):
    """
    Add inventory item with calculated expiry date.
    Uses manual shelf life if provided, otherwise auto-calculates based on item type.
    """
    from datetime import datetime, timedelta
    from src.db.models import InventoryItemCreate
    
    # Determine purchase date (convert to UTC)
    if item_data.purchase_date:
        # Parse as local date and convert to UTC
        local_date = datetime.fromisoformat(item_data.purchase_date)
        purchase_date = local_date.replace(tzinfo=None)  # Treat as UTC
    else:
        purchase_date = datetime.utcnow()
    
    # Determine shelf life
    if item_data.shelf_life_days:
        shelf_life_days = item_data.shelf_life_days
    else:
        shelf_life_days = get_shelf_life_days(item_data.item_name)
    
    # Calculate expiry date (store as end of day UTC)
    expiry_date = purchase_date + timedelta(days=shelf_life_days)
    # Set to end of day (23:59:59) so it expires at end of the day, not exact time
    expiry_date = expiry_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Create inventory item
    inventory_create = InventoryItemCreate(
        item_name=item_data.item_name,
        quantity=item_data.quantity,
        unit=item_data.unit or "piece",
        expiry_date=expiry_date
    )
    
    return InventoryCRUD.create(user_id, inventory_create)


@app.get("/api/users/{user_id}/inventory", response_model=List[InventoryItem])
async def list_inventory(user_id: str):
    """Get all inventory items for a user."""
    return InventoryCRUD.list_by_user(user_id)


@app.get("/api/users/{user_id}/inventory/expiring", response_model=List[InventoryItem])
async def list_expiring_inventory(
    user_id: str,
    days: int = Query(3, description="Number of days to look ahead")
):
    """Get inventory items expiring within specified days."""
    return get_expiring_soon(user_id, days)


@app.get("/api/users/{user_id}/inventory/expired", response_model=List[InventoryItem])
async def list_expired_inventory(user_id: str):
    """Get inventory items that have already expired (expiry_date < now)."""
    try:
        items = await crud_get_expired_items(user_id)
        return items
    except Exception as e:
        print(f"Error fetching expired inventory: {e}")
        return []


# Acknowledgement of expired items (so we don't re-show across devices)
class ExpiredAckPayload(BaseModel):
    keys: List[str] = []  # keys like "<item_id>|<expiry_ts_ms>"


@app.get("/api/users/{user_id}/inventory/expired/ack")
async def get_expired_ack(user_id: str):
    """Return previously acknowledged expired-item keys for this user."""
    try:
        doc = (
            db.collection("users").document(user_id)
            .collection("meta").document("expired_ack")
            .get()
        )
        if doc.exists:
            data = doc.to_dict() or {}
            keys = list(data.get("keys", []))
            return {"keys": keys}
        return {"keys": []}
    except Exception as e:
        print(f"Error getting expired acks: {e}")
        return {"keys": []}


@app.post("/api/users/{user_id}/inventory/expired/ack")
async def add_expired_ack(user_id: str, payload: ExpiredAckPayload):
    """Merge the provided keys into the user's acknowledged set."""
    try:
        ref = (
            db.collection("users").document(user_id)
            .collection("meta").document("expired_ack")
        )
        existing = {}
        snap = ref.get()
        if snap.exists:
            existing = snap.to_dict() or {}
        now = __import__("datetime").datetime.utcnow()
        merged = set(existing.get("keys", []))
        for k in (payload.keys or []):
            if isinstance(k, str) and k:
                merged.add(k)
        ref.set({"keys": list(merged), "updated_at": now})
        return {"ok": True, "count": len(merged)}
    except Exception as e:
        print(f"Error updating expired acks: {e}")
        return {"ok": False}


# Bulk consume inventory (user cooked outside the app)
class BulkConsumeItem(BaseModel):
    name: str = Field(..., description="Ingredient name as listed in inventory")
    quantity: float = Field(..., gt=0, description="Amount to subtract from inventory")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., g, kg, ml, l, piece)")


class BulkConsumeRequest(BaseModel):
    items: List[BulkConsumeItem] = Field(default_factory=list)


@app.post("/api/users/{user_id}/inventory/bulk-consume")
async def bulk_consume_inventory(user_id: str, payload: BulkConsumeRequest):
    """
    Subtract multiple ingredients from inventory in one request.

    Accepts a list of { name, quantity, unit } and performs unit-aware, oldest-first
    subtraction using the same logic as the cooked endpoint.
    """
    try:
        if not payload.items:
            return {"ok": True, "inventory_updates": {}, "message": "No items provided"}

        ingredient_quantities: Dict[str, float] = {}
        ingredient_units: Dict[str, str] = {}
        for it in payload.items:
            n = (it.name or "").strip()
            q = float(it.quantity or 0)
            if not n or q <= 0:
                continue
            ingredient_quantities[n] = (ingredient_quantities.get(n, 0.0) + q)
            if it.unit:
                ingredient_units[n] = it.unit

        if not ingredient_quantities:
            return {"ok": True, "inventory_updates": {}, "message": "No valid items to consume"}

        results = subtract_inventory_items(user_id, ingredient_quantities, ingredient_units)
        return {
            "ok": True,
            "inventory_updates": results,
            "message": "Bulk consumption applied",
        }
    except Exception as e:
        print(f"Error in bulk consumption: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply bulk consumption")


@app.put("/api/users/{user_id}/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory(
    user_id: str,
    item_id: str,
    update_data: InventoryItemUpdate
):
    """Update an inventory item."""
    return InventoryCRUD.update(user_id, item_id, update_data)


@app.delete("/api/users/{user_id}/inventory/{item_id}", status_code=204)
async def delete_inventory(user_id: str, item_id: str):
    """Delete an inventory item."""
    InventoryCRUD.delete(user_id, item_id)
    return None


# ========== USER PREFERENCES ENDPOINTS ==========

class UserPreferencesRequest(BaseModel):
    """Request model for user preferences."""
    allergies: List[str] = Field(default=[])
    dislikes: List[str] = Field(default=[])
    dietary_restrictions: List[str] = Field(default=[])
    cooking_skill_level: Optional[str] = Field("beginner")
    preferred_cuisines: List[str] = Field(default=[])

@app.get("/api/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user preferences."""
    from src.db.firestore import db
    
    doc = db.collection("users").document(user_id).collection("preferences").document("settings").get()
    if doc.exists:
        return doc.to_dict()
    
    # Return default preferences
    return {
        "userId": user_id,
        "allergies": [],
        "dislikes": [],
        "dietary_restrictions": [],
        "cooking_skill_level": "beginner",
        "preferred_cuisines": []
    }

@app.put("/api/users/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: UserPreferencesRequest):
    """Update user preferences."""
    from src.db.firestore import db
    from datetime import datetime
    
    prefs_data = {
        "userId": user_id,
        "allergies": preferences.allergies,
        "dislikes": preferences.dislikes,
        "dietary_restrictions": preferences.dietary_restrictions,
        "cooking_skill_level": preferences.cooking_skill_level,
        "preferred_cuisines": preferences.preferred_cuisines,
        "updated_at": datetime.utcnow()
    }
    
    db.collection("users").document(user_id).collection("preferences").document("settings").set(prefs_data)
    return prefs_data

class UserSettingsRequest(BaseModel):
    """Request model for user settings."""
    name: Optional[str] = None
    email: Optional[str] = None

@app.get("/api/users/{user_id}/settings")
async def get_user_settings(user_id: str):
    """Get user settings."""
    from src.db.firestore import db
    
    doc = db.collection("users").document(user_id).collection("settings").document("profile").get()
    if doc.exists:
        return doc.to_dict()
    
    return {
        "userId": user_id,
        "name": "",
        "email": "",
    }

@app.put("/api/users/{user_id}/settings")
async def update_user_settings(user_id: str, settings: UserSettingsRequest):
    """Update user settings."""
    from src.db.firestore import db
    from datetime import datetime
    
    settings_data = {
        "userId": user_id,
        "name": settings.name or "",
        "email": settings.email or "",
        "updated_at": datetime.utcnow()
    }
    
    db.collection("users").document(user_id).collection("settings").document("profile").set(settings_data)
    return settings_data

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
    dish_type: Optional[str] = Query(None, description="Dish type (e.g., appetizer, main course, dessert)"),
    limit: int = Query(10, description="Number of recommendations")
):
    """Get recipe recommendations with additional filters."""
    recommendations = await get_recommendations_by_preferences(
        user_id=user_id,
        cuisine=cuisine,
        diet=diet,
        dish_type=dish_type,
        number_of_recipes=limit
    )
    return {
        "user_id": user_id,
        "filters": {"cuisine": cuisine, "diet": diet, "dish_type": dish_type},
        "count": len(recommendations),
        "recommendations": recommendations
    }


# ========== RECIPE COOKING / "COOKED" BUTTON ==========

class CookedRecipeRequest(BaseModel):
        """Request model for marking a recipe as cooked.

        SNAPSHOT-COOK SUPPORT (temporary):
        This block enables a snapshot-based cook path to bypass Spoonacular (e.g., 402 quota).
        To REMOVE snapshot support later:
            1) Delete the optional fields below (recipe_title, servings, dish_types, cuisines,
                 extended_ingredients, ingredients).
            2) In mark_recipe_cooked, delete the 'use_snapshot' branch and fallback usage.
            3) In the cooked snapshot creation, remove the simple-ingredients translation.

        Supports two modes:
        - Spoonacular mode: provide recipe_id only; backend fetches details.
        - Snapshot mode: provide a lightweight snapshot with ingredients to avoid external API calls
            (used for mock data or when quota is exceeded).
        """
        recipe_id: str = Field(..., description="Recipe ID (Spoonacular or mock)")
        # Allow fractional servings (e.g., 1.5, 2.25)
        servings_made: float = Field(1.0, gt=0, description="Number of servings made (can be fractional)")
        # Optional snapshot fields to bypass Spoonacular
        recipe_title: Optional[str] = Field(None, description="Recipe title")
        servings: Optional[int] = Field(None, description="Default servings of the recipe")
        dish_types: Optional[List[str]] = Field(None, description="Dish types for CMAB categorization")
        cuisines: Optional[List[str]] = Field(None, description="Cuisines for CMAB categorization")
        # Either extended_ingredients (Spoonacular-like) or simple ingredients
        extended_ingredients: Optional[List[Dict]] = Field(None, description="Spoonacular-like extendedIngredients payload")
        ingredients: Optional[List[Dict]] = Field(
                None,
                description="Simple ingredients with name, quantity, unit (from normalized recipe)")


@app.post("/api/users/{user_id}/recipes/cooked")
async def mark_recipe_cooked(user_id: str, request: CookedRecipeRequest):
    """
    Mark recipe as cooked - AUTOMATICALLY SUBTRACTS INGREDIENTS FROM INVENTORY.
    Also updates CMAB model with positive reward.
    
    This endpoint:
    1. Fetches recipe information from Spoonacular (single API call)
    2. Extracts ingredient quantities and categories from response
    3. Adjusts quantities based on servings made
    4. Subtracts ingredients from user inventory
    5. Updates CMAB with "cooked" reward (+2)
    6. Returns status of each ingredient update
    """
    
    # SNAPSHOT-COOK: If snapshot is provided, use it and SKIP Spoonacular entirely
    use_snapshot = bool(request.extended_ingredients or request.ingredients)
    recipe_info: Dict = {}
    if use_snapshot:
        recipe_info = {
            "id": request.recipe_id,
            "title": request.recipe_title or "",
            "servings": request.servings or 1,
            "dishTypes": request.dish_types or [],
            "cuisines": request.cuisines or [],
            "extendedIngredients": request.extended_ingredients or [],
        }
    else:
        # Validate recipe id and fetch info (single API call contains all needed data)
        try:
            rid = int(request.recipe_id)
        except Exception:
            raise HTTPException(status_code=400, detail="recipe_id must be an integer when no snapshot is provided")
        try:
            recipe_info = await get_recipe_information(rid)
        except Exception as e:
            # SNAPSHOT-COOK: If Spoonacular fails, but client provided snapshot fields, try to proceed
            if request.recipe_title or request.ingredients or request.extended_ingredients:
                recipe_info = {
                    "id": request.recipe_id,
                    "title": request.recipe_title or "",
                    "servings": request.servings or 1,
                    "dishTypes": request.dish_types or [],
                    "cuisines": request.cuisines or [],
                    "extendedIngredients": request.extended_ingredients or [],
                }
            else:
                raise HTTPException(status_code=502, detail=f"Failed to fetch recipe information: {e}")
    
    # Extract ingredient quantities
    ingredient_quantities: Dict[str, float] = {}
    ingredient_units: Dict[str, str] = {}
    if request.ingredients:
        # SNAPSHOT-COOK: Simple ingredient objects: { name, quantity, unit }
        recipe_servings = int(request.servings or recipe_info.get("servings", 1) or 1)
        for ing in (request.ingredients or []):
            name = (ing or {}).get("name") or ""
            amount = float((ing or {}).get("quantity") or 0)
            unit = (ing or {}).get("unit") or ""
            adjusted_amount = (amount / max(1, recipe_servings)) * float(request.servings_made)
            if name and adjusted_amount > 0:
                ingredient_quantities[name] = adjusted_amount
                if unit:
                    ingredient_units[name] = unit
    else:
        # Spoonacular-like extended ingredients
        for ingredient in recipe_info.get("extendedIngredients", []):
            name = ingredient.get("name", "")
            amount = ingredient.get("measures", {}).get("metric", {}).get("amount", 0)
            unit = ingredient.get("measures", {}).get("metric", {}).get("unitShort", "")
            # Adjust for servings
            recipe_servings = recipe_info.get("servings", 1) or 1
            adjusted_amount = (float(amount) / max(1, recipe_servings)) * float(request.servings_made)
            if name and adjusted_amount > 0:
                ingredient_quantities[name] = adjusted_amount
                if unit:
                    ingredient_units[name] = unit
    
    # Classify recipe for CMAB
    recipe_tags = (recipe_info.get("dishTypes", []) or []) + (recipe_info.get("cuisines", []) or [])
    recipe_categories = RecipeCategory.classify_recipe(
        recipe_info.get("title", ""),
        recipe_tags
    )
    
    # Subtract from inventory
    results = subtract_inventory_items(user_id, ingredient_quantities, ingredient_units)
    
    # Record a 'cooked' history entry in a dedicated subcollection, including a light recipe snapshot
    try:
        from datetime import datetime
        import uuid
        cooked_id = str(uuid.uuid4())
        now = datetime.utcnow()
        # Keep a compact snapshot to avoid refetching from Spoonacular later
        recipe_snapshot = {
            "id": str(recipe_info.get("id")),
            "title": recipe_info.get("title"),
            "image": recipe_info.get("image"),
            "summary": recipe_info.get("summary"),
            "servings": recipe_info.get("servings"),
            # store just what's needed for quick cards/normalization on the frontend
            "extendedIngredients": [
                {
                    "name": ing.get("name"),
                    "measures": ing.get("measures"),
                    "amount": ing.get("measures", {}).get("metric", {}).get("amount"),
                    "unit": ing.get("measures", {}).get("metric", {}).get("unitShort"),
                }
                for ing in (recipe_info.get("extendedIngredients") or [])
            ],
            "dishTypes": recipe_info.get("dishTypes", []),
            "cuisines": recipe_info.get("cuisines", []),
            "readyInMinutes": recipe_info.get("readyInMinutes"),
        }
        # SNAPSHOT-COOK: If we were provided simple ingredients, embed a translated extendedIngredients for consistency
        if (not recipe_snapshot["extendedIngredients"]) and request.ingredients:
            ei = []
            for ing in (request.ingredients or []):
                name = (ing or {}).get("name")
                qty = float((ing or {}).get("quantity") or 0)
                unit = (ing or {}).get("unit") or ""
                ei.append({
                    "name": name,
                    "measures": {"metric": {"amount": qty, "unitShort": unit}},
                    "amount": qty,
                    "unit": unit,
                })
            recipe_snapshot["extendedIngredients"] = ei
        cooked_doc = {
            "id": cooked_id,
            "user_id": user_id,
            "recipe_id": str(request.recipe_id),
            "servings_made": float(request.servings_made),
            "cooked_at": now,
            "recipe": recipe_snapshot,
        }
        db.collection("users").document(user_id).collection("cooked").document(cooked_id).set(cooked_doc)
    except Exception as e:
        print(f"Warning: failed to record cooked history: {e}")

    # Update CMAB with positive reward for cooking
    await update_cmab_with_feedback(
        user_id=user_id,
        recipe_id=request.recipe_id,
        recipe_categories=recipe_categories,
        feedback_type="upvote",
        is_cooked=True  # +2 reward
    )
    
    return {
        "recipe_id": request.recipe_id,
        "servings_made": request.servings_made,
        "recipe_servings": recipe_info.get("servings", 1),
        "inventory_updates": results,
        "cmab_updated": True,
        "message": "Inventory updated and preferences learned successfully"
    }


@app.get("/api/users/{user_id}/cooked")
async def list_cooked_history(user_id: str, limit: int = Query(12, description="Max number of cooked records")):
    """Return recent cooked recipe history for a user (most recent first)."""
    try:
        docs = (
            db.collection("users")
            .document(user_id)
            .collection("cooked")
            .order_by("cooked_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [d.to_dict() for d in docs]
    except Exception as e:
        print(f"Error listing cooked history: {e}")
        # Fallback without ordering if index is missing
        try:
            docs = (
                db.collection("users")
                .document(user_id)
                .collection("cooked")
                .limit(limit)
                .get()
            )
            # sort client-side by cooked_at desc if present
            items = [d.to_dict() for d in docs]
            items.sort(key=lambda x: x.get("cooked_at", 0), reverse=True)
            return items[:limit]
        except Exception as e2:
            print(f"Error fallback listing cooked history: {e2}")
            return []


# ========== FEEDBACK ENDPOINTS ==========

class FeedbackRequest(BaseModel):
    """Request model for submitting recipe feedback."""
    recipe_id: str = Field(..., description="Recipe ID")
    recipe_title: str = Field(..., description="Recipe title")
    recipe_categories: List[str] = Field(default=["general"], description="Recipe categories")
    feedback_type: str = Field(..., description="Feedback type: upvote, downvote, skip")


@app.post("/api/users/{user_id}/feedback", response_model=UserFeedback, status_code=201)
async def submit_feedback(user_id: str, feedback_data: FeedbackRequest):
    """
    Submit feedback for a recipe (upvote, downvote, skip).
    This feedback is used by CMAB to learn user preferences.
    
    Reward scheme:
    - Upvote (👍): +1
    - Downvote (👎): -1
    - Skip/Ignored: 0
    - Cooked: +2 (handled in /cooked endpoint)
    """
    # Save or update feedback to database (toggle-safe upsert)
    feedback_create = UserFeedbackCreate(
        recipe_id=feedback_data.recipe_id,
        feedback_type=FeedbackType(feedback_data.feedback_type)
    )
    # Get previous latest feedback (if any) to detect changes
    try:
        prev = feedback.get_by_recipe(user_id, feedback_data.recipe_id)
    except AttributeError:
        prev = None

    # Use upsert to avoid creating duplicate records for the same recipe
    try:
        feedback_record = feedback.upsert_by_recipe(user_id, feedback_create)
    except AttributeError:
        # Fallback for environments without the upsert method
        feedback_record = feedback.create(user_id, feedback_create)
    
    # Update CMAB model with feedback
    try:
        # Only update CMAB if this action changes the latest feedback type
        changed = True
        if prev and prev.feedback_type.value == feedback_data.feedback_type:
            changed = False
        if changed:
            await update_cmab_with_feedback(
                user_id=user_id,
                recipe_id=feedback_data.recipe_id,
                recipe_categories=feedback_data.recipe_categories,
                feedback_type=feedback_data.feedback_type,
                is_cooked=False
            )
    except Exception as e:
        print(f"Error updating CMAB with feedback: {e}")
    
    return feedback_record


@app.get("/api/users/{user_id}/feedback", response_model=List[UserFeedback])
async def get_feedback_history(user_id: str):
    """Get all feedback submitted by a user."""
    return feedback.list_by_user(user_id)


@app.get("/api/users/{user_id}/cmab/statistics")
async def get_cmab_statistics(user_id: str):
    """
    Get CMAB statistics for a user.
    
    Shows learning progress for each recipe category:
    - Number of times recommended
    - Total reward received
    - Mean reward
    - Expected value (Beta distribution)
    """
    stats = CMABCRUD.get_statistics(user_id)
    
    # Sort by pulls (most recommended categories first)
    sorted_stats = dict(sorted(
        stats.items(),
        key=lambda x: x[1]["pulls"],
        reverse=True
    ))
    
    return {
        "user_id": user_id,
        "categories": sorted_stats
    }


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
