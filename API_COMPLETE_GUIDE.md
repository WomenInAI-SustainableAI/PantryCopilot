# PantryCopilot API Documentation

Complete API documentation for all features of PantryCopilot.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Add your `GOOGLE_API_KEY` (from https://aistudio.google.com/app/apikey)
   - Add your `SPOONACULAR_API_KEY` (from https://spoonacular.com/food-api)
   - Set `FIREBASE_SERVICE_ACCOUNT_PATH` to your Firebase credentials

3. **Start the server:**
   ```bash
   python main.py
   ```

4. **Access API docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 📋 Features Implemented

✅ **Inventory Input** → Name + Quantity (Expiry AUTO-CALCULATED)
✅ **Recipe Integration** → Spoonacular API
✅ **Recipe Scoring** → Match % + Expiring Ingredient Priority + Partial Usage
✅ **Preference Filtering** → Allergies + Dislikes
✅ **Mini Explanation Engine** → Urgency + Safety + Money Saving + Partial Usage
✅ **Auto Inventory Update** → "Cooked" button subtracts quantities
✅ **Feedback-based Reinforcement Learning** → Improves recommendations over time

---

## 🔗 API Endpoints

### Health Check

#### `GET /`
Health check endpoint
```json
{
  "status": "healthy",
  "service": "PantryCopilot API",
  "version": "1.0.0"
}
```

---

### 👤 User Management

#### `POST /api/users`
Create a new user
```json
Request:
{
  "email": "user@example.com",
  "name": "John Doe"
}

Response:
{
  "id": "user_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-10-18T10:00:00",
  "updated_at": "2025-10-18T10:00:00"
}
```

#### `GET /api/users/{user_id}`
Get user details

---

### 🥜 Allergy Management

#### `POST /api/users/{user_id}/allergies`
Add an allergy
```json
Request:
{
  "allergen": "peanuts"
}
```

#### `GET /api/users/{user_id}/allergies`
Get all user allergies

#### `DELETE /api/users/{user_id}/allergies/{allergy_id}`
Remove an allergy

---

### 📦 Inventory Management (AUTO-CALCULATED EXPIRY)

#### `POST /api/users/{user_id}/inventory`
**Add inventory with AUTO-CALCULATED expiry date**
```json
Request:
{
  "item_name": "milk",
  "quantity": 1,
  "unit": "liter"
}

Response:
{
  "id": "item_xyz789",
  "user_id": "user_abc123",
  "item_name": "milk",
  "quantity": 1,
  "unit": "liter",
  "expiry_date": "2025-10-25",  // ← AUTO-CALCULATED based on item type!
  "added_at": "2025-10-18T10:00:00",
  "updated_at": "2025-10-18T10:00:00"
}
```

**Expiry Calculation Logic:**
- Milk: 7 days
- Chicken: 2 days
- Tomatoes: 7 days
- Eggs: 21 days
- Rice: 365 days
- And many more predefined items!
- Unknown items: 7 days (default)

#### `GET /api/users/{user_id}/inventory`
Get all inventory items

#### `GET /api/users/{user_id}/inventory/expiring?days=3`
Get items expiring within N days (default: 3)

#### `PUT /api/users/{user_id}/inventory/{item_id}`
Update an inventory item

#### `DELETE /api/users/{user_id}/inventory/{item_id}`
Delete an inventory item

---

### 🍳 Recipe Recommendations (THE MAIN FEATURE!)

#### `GET /api/users/{user_id}/recommendations?limit=10`
**Get personalized recipe recommendations**

This endpoint does it ALL:
1. ✅ Fetches recipes from Spoonacular based on your inventory
2. ✅ Prioritizes recipes using expiring ingredients
3. ✅ Filters out allergens
4. ✅ Scores recipes based on:
   - Inventory match percentage
   - Expiring ingredient urgency
   - Partial usage optimization
   - Historical feedback (reinforcement learning)
5. ✅ Generates AI explanations for each recipe
6. ✅ Saves recommendations to database

```json
Response:
{
  "user_id": "user_abc123",
  "count": 10,
  "recommendations": [
    {
      "id": 12345,
      "title": "Creamy Tomato Basil Pasta",
      "image": "https://...",
      "ingredients": ["tomatoes", "basil", "pasta", "cream"],
      "readyInMinutes": 30,
      "servings": 4,
      "scoring": {
        "overall_score": 92.5,
        "match_percentage": 85.0,
        "matched_ingredients": ["tomatoes", "basil"],
        "missing_ingredients": ["pasta", "cream"],
        "urgency_score": 8.0,
        "expiring_ingredients": ["tomatoes"],
        "is_allergen_safe": true,
        "allergens_found": [],
        "partial_usage_score": 7.5,
        "feedback_score": 2.0
      },
      "ai_explanation": "This recipe is highly recommended because it uses tomatoes which expire tomorrow, creating urgency. It's safe for your allergies and uses 85% of your current inventory, helping you save money and reduce waste."
    }
  ]
}
```

#### `GET /api/users/{user_id}/recommendations/filtered?cuisine=italian&diet=vegetarian&limit=10`
Get filtered recommendations with additional preferences

---

### 🎯 "COOKED" Button - Auto Inventory Update

#### `POST /api/users/{user_id}/recipes/cooked`
**Mark recipe as cooked - AUTOMATICALLY SUBTRACTS INGREDIENTS**

```json
Request:
{
  "recipe_id": "12345",
  "servings_made": 2
}

Response:
{
  "recipe_id": "12345",
  "servings_made": 2,
  "inventory_updates": {
    "tomatoes": "updated (new quantity: 1.5)",
    "basil": "deleted (quantity depleted)",
    "pasta": "not found in inventory",
    "cream": "updated (new quantity: 0.5)"
  },
  "message": "Inventory updated successfully"
}
```

**How it works:**
1. Fetches exact ingredient quantities from Spoonacular
2. Scales quantities based on servings made
3. Automatically subtracts from your inventory
4. Deletes items if quantity reaches 0
5. Returns detailed status for each ingredient

---

### 👍 Feedback & Reinforcement Learning

#### `POST /api/users/{user_id}/feedback`
**Submit feedback to improve recommendations**

```json
Request:
{
  "recipe_id": "12345",
  "feedback_type": "upvote"  // "upvote" | "downvote" | "skip"
}

Response:
{
  "id": "feedback_123",
  "user_id": "user_abc123",
  "recipe_id": "12345",
  "feedback_type": "upvote",
  "created_at": "2025-10-18T10:00:00"
}
```

**Feedback Impact:**
- **Upvote** (+2 points): Recipe will rank higher in future recommendations
- **Downvote** (-3 points): Recipe will rank lower in future recommendations
- **Skip** (-1 point): Slight negative signal

The system uses this feedback in real-time to adjust future recommendation scores!

#### `GET /api/users/{user_id}/feedback`
Get feedback history

---

### 📖 Recipe Details

#### `GET /api/recipes/{recipe_id}`
Get detailed information about a specific recipe from Spoonacular

---

### 🤖 AI Explanation Endpoints

#### `POST /api/explain-recommendation`
Generate AI explanation for a recipe recommendation

```json
Request:
{
  "recipe_name": "Tomato Pasta",
  "expiring_ingredients": ["tomatoes", "basil"],
  "allergies": ["nuts"],
  "inventory_match_percentage": 85.5
}

Response:
{
  "explanation": "This Tomato Pasta is highly recommended for several reasons. Urgency: Your tomatoes and basil are expiring within the next 2 days, making this recipe urgent to prevent food waste. Safety: This recipe is safe for your nut allergy. Money Saving: With an 85.5% inventory match, you already have most ingredients, minimizing grocery costs and maximizing use of your current pantry. This recipe helps reduce waste and saves money!"
}
```

#### `POST /api/process-feedback`
Process feedback through AI for learning (usually called automatically)

---

## 🧮 Recipe Scoring Algorithm

Each recipe receives an **overall score (0-100)** based on:

### 1. Inventory Match (40% weight)
- Percentage of recipe ingredients you already have
- Higher match = Higher score

### 2. Expiring Ingredient Urgency (30% weight)
- Recipes using ingredients expiring soon get bonus points
- Expired items: +10 points
- Expires tomorrow: +8 points
- Expires in 2 days: +5 points
- Expires in 3 days: +3 points

### 3. Partial Usage Optimization (15% weight)
- Recipes that use 50-100% of available quantities score higher
- Helps avoid partial ingredient waste

### 4. Feedback History (15% weight)
- Upvotes: +2 points per upvote
- Downvotes: -3 points per downvote
- Skips: -1 point per skip

### 5. Safety Multiplier
- **Allergen detected: 90% penalty** (score × 0.1)
- Ensures unsafe recipes are heavily deprioritized

---

## 💡 Usage Flow Example

### Complete User Journey

```bash
# 1. Create user
POST /api/users
{
  "email": "jane@example.com",
  "name": "Jane Doe"
}
→ user_id: "user_123"

# 2. Add allergies
POST /api/users/user_123/allergies
{
  "allergen": "shellfish"
}

# 3. Add inventory items (expiry auto-calculated!)
POST /api/users/user_123/inventory
{
  "item_name": "chicken",
  "quantity": 2,
  "unit": "pounds"
}
→ expiry_date: "2025-10-20" (2 days - auto-calculated!)

POST /api/users/user_123/inventory
{
  "item_name": "broccoli",
  "quantity": 1,
  "unit": "head"
}
→ expiry_date: "2025-10-25" (7 days - auto-calculated!)

# 4. Get personalized recommendations
GET /api/users/user_123/recommendations?limit=5
→ Returns 5 recipes scored and ranked with AI explanations

# 5. User selects a recipe and cooks it
POST /api/users/user_123/recipes/cooked
{
  "recipe_id": "12345",
  "servings_made": 4
}
→ Inventory automatically updated! Chicken and broccoli quantities reduced.

# 6. User provides feedback
POST /api/users/user_123/feedback
{
  "recipe_id": "12345",
  "feedback_type": "upvote"
}
→ Future recommendations improved based on this feedback!

# 7. Check expiring items
GET /api/users/user_123/inventory/expiring?days=2
→ Get items expiring within 2 days for urgent cooking
```

---

## 🔧 Configuration

### Environment Variables

```env
# Required
GOOGLE_API_KEY=your_google_ai_key
SPOONACULAR_API_KEY=your_spoonacular_key
FIREBASE_SERVICE_ACCOUNT_PATH=./src/db/pantrycopilotfirebase.json

# Optional
API_HOST=0.0.0.0
API_PORT=8000
```

### Firebase Setup

1. Create a Firebase project
2. Enable Firestore Database
3. Download service account key
4. Place in `src/db/pantrycopilotfirebase.json`
5. Set path in `.env`

---

## 🧪 Testing

### Interactive Testing
Visit http://localhost:8000/docs for Swagger UI

### Example cURL Commands

```bash
# Add inventory
curl -X POST http://localhost:8000/api/users/user_123/inventory \
  -H "Content-Type: application/json" \
  -d '{"item_name": "milk", "quantity": 1, "unit": "liter"}'

# Get recommendations
curl http://localhost:8000/api/users/user_123/recommendations?limit=10

# Mark recipe as cooked
curl -X POST http://localhost:8000/api/users/user_123/recipes/cooked \
  -H "Content-Type: application/json" \
  -d '{"recipe_id": "12345", "servings_made": 2}'
```

---

## 🎯 Key Features Summary

| Feature | Endpoint | Auto-Magic |
|---------|----------|------------|
| Add inventory | `POST /api/users/{id}/inventory` | ✨ Expiry auto-calculated |
| Get recommendations | `GET /api/users/{id}/recommendations` | ✨ AI scoring + explanations |
| Cook recipe | `POST /api/users/{id}/recipes/cooked` | ✨ Inventory auto-updated |
| Submit feedback | `POST /api/users/{id}/feedback` | ✨ Reinforcement learning |
| Check expiring | `GET /api/users/{id}/inventory/expiring` | ✨ Smart alerts |

---

## 📚 Additional Resources

- **Spoonacular API Docs**: https://spoonacular.com/food-api/docs
- **Firebase Firestore**: https://firebase.google.com/docs/firestore
- **Google AI Studio**: https://aistudio.google.com/app/apikey
- **FastAPI Docs**: https://fastapi.tiangolo.com/
