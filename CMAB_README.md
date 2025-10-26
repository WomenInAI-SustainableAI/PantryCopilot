# Contextual Multi-Armed Bandit (CMAB) for Recipe Recommendations

## Overview

The PantryCopilot recommendation system now uses a **Contextual Multi-Armed Bandit (CMAB)** approach to learn and adapt to user preferences over time. This provides personalized recipe recommendations that improve with each interaction.

## How It Works

### The Bandit Framework

- **Arms**: Different recipe categories (Italian, Asian, Quick Meals, Baking, etc.)
- **Context**: User's current inventory state (expiring items, available ingredients, diversity)
- **Reward**: User feedback signals
  - 👍 Upvote: **+1**
  - 👎 Downvote: **-1**
  - 🍳 Cooked: **+2** (strongest positive signal)
  - ⏭️ Skip/Ignored: **0**
- **Goal**: Learn which recipe categories each user prefers based on their current context

### Algorithm: Thompson Sampling

We use **Thompson Sampling** with Beta distributions for each category:
- Each category maintains two parameters: `α` (successes) and `β` (failures)
- When recommending, we sample from each category's Beta distribution
- Categories with higher expected rewards are selected more often
- Still maintains exploration to discover new preferences

### Contextual Features

The system extracts features from the user's current inventory:

1. **expiring_count**: Number of items expiring within 3 days
2. **total_items**: Total inventory size
3. **has_produce**: Whether user has fresh vegetables/fruits
4. **has_protein**: Whether user has proteins (meat, fish, tofu, eggs)
5. **has_grains**: Whether user has grains/pasta/rice
6. **inventory_diversity**: Normalized diversity score

These features help the system understand **when** to recommend certain categories. For example:
- High expiring_count → prioritize quick meals
- Has produce + protein → good time for salads or Asian dishes

## Cold Start Solution

For new users with limited interaction history, we employ a multi-pronged strategy:

### 1. Epsilon-Greedy Exploration
- **New users (< 10 interactions)**: ε = 0.3 (30% random exploration)
- **Learning users (10-50 interactions)**: ε = 0.2
- **Experienced users (> 50 interactions)**: ε = 0.1

This ensures new users see diverse categories before the system settles on preferences.

### 2. Content-Based Bootstrapping
- Initial recommendations still use inventory matching
- Recipes that use expiring ingredients get urgency bonuses
- Allergen filtering is always applied

### 3. Uniform Prior
- All categories start with Beta(1, 1) - uniform distribution
- No category is initially favored or penalized
- Early feedback quickly shapes the distribution

### 4. Fallback Mechanisms
- If CMAB-selected categories yield few results, fallback to ingredient-based search
- Expiring ingredients always get priority regardless of category preferences

## API Integration

### New Endpoints

#### 1. Submit Feedback (with CMAB update)
```http
POST /api/users/{user_id}/feedback
Content-Type: application/json

{
  "recipe_id": "123456",
  "recipe_title": "Chicken Tikka Masala",
  "recipe_categories": ["indian", "asian"],
  "feedback_type": "upvote"
}
```

**Response:**
```json
{
  "id": "feedback-uuid",
  "user_id": "user-123",
  "recipe_id": "123456",
  "feedback_type": "upvote",
  "created_at": "2025-10-22T10:30:00Z"
}
```

#### 2. Get CMAB Statistics
```http
GET /api/users/{user_id}/cmab/statistics
```

**Response:**
```json
{
  "user_id": "user-123",
  "categories": {
    "italian": {
      "pulls": 15,
      "total_reward": 12.0,
      "mean_reward": 0.8,
      "expected_value": 0.82,
      "alpha": 13.0,
      "beta": 3.0
    },
    "asian": {
      "pulls": 10,
      "total_reward": 5.0,
      "mean_reward": 0.5,
      "expected_value": 0.55,
      "alpha": 6.0,
      "beta": 5.0
    },
    ...
  }
}
```

#### 3. Mark Recipe as Cooked (Enhanced)
```http
POST /api/users/{user_id}/recipes/cooked
Content-Type: application/json

{
  "recipe_id": "123456",
  "servings_made": 4
}
```

Now also updates CMAB with **+2 reward** automatically.

### Updated Recommendations Endpoint

The existing `/api/users/{user_id}/recommendations` endpoint now uses CMAB internally:

```http
GET /api/users/{user_id}/recommendations?limit=10
```

**What's different:**
- Recipes are now selected based on learned category preferences
- Each recipe includes `categories` field showing classification
- `ai_explanation` mentions which categories were preferred
- System adapts over time based on user feedback

## Recipe Categories

The system classifies recipes into these categories:

| Category | Keywords |
|----------|----------|
| **italian** | pasta, pizza, risotto, italian |
| **asian** | asian, chinese, japanese, thai, korean, vietnamese |
| **mexican** | mexican, taco, burrito, quesadilla |
| **american** | burger, bbq, american, sandwich |
| **mediterranean** | mediterranean, greek, middle eastern |
| **indian** | indian, curry |
| **quick_meals** | quick, easy, 30 minute, 15 minute |
| **baking** | cake, bread, cookie, muffin, pastry |
| **dessert** | dessert, sweet, chocolate |
| **breakfast** | breakfast, brunch, pancake, waffle |
| **salad** | salad, bowl |
| **soup** | soup, stew, chili |
| **vegetarian** | vegetarian, veggie |
| **vegan** | vegan |
| **healthy** | healthy, low calorie, diet |
| **general** | (fallback for unclassified recipes) |

A recipe can belong to multiple categories (e.g., "Vegan Thai Curry" → asian, vegan, healthy).

## Implementation Details

### Files Added

1. **`backend/src/services/cmab_service.py`**
   - Core CMAB implementation
   - Thompson Sampling algorithm
   - Context feature extraction
   - Recipe category classification

2. **`backend/src/db/crud/cmab.py`**
   - Firestore CRUD operations for CMAB models
   - Model persistence per user

### Files Modified

1. **`backend/src/services/recommendation_service.py`**
   - Integrated CMAB into recommendation flow
   - Added `update_cmab_with_feedback()` function

2. **`backend/main.py`**
   - New feedback endpoint with CMAB update
   - New CMAB statistics endpoint
   - Enhanced cooked endpoint

3. **`backend/src/db/models.py`**
   - Added `COOKED` to `FeedbackType` enum

## Database Schema

### CMAB Model Storage

Each user has a CMAB model stored in Firestore:

```
users/{user_id}/models/cmab_model
```

**Document structure:**
```json
{
  "categories": ["italian", "asian", "mexican", ...],
  "alpha": {"italian": 5.2, "asian": 3.1, ...},
  "beta": {"italian": 2.1, "asian": 4.3, ...},
  "pulls": {"italian": 7, "asian": 7, ...},
  "total_reward": {"italian": 4.0, "asian": -1.0, ...},
  "context_weights": {
    "italian": {
      "expiring_count": 0.5,
      "has_produce": 0.2,
      ...
    }
  },
  "total_user_pulls": 14,
  "is_cold_start": false,
  "updated_at": "2025-10-22T10:30:00Z"
}
```

## Example User Journey

### Day 1: New User (Cold Start)
1. User adds inventory: chicken, rice, tomatoes
2. Requests recommendations
3. CMAB uses ε=0.3 → explores diverse categories
4. Shows: Italian pasta, Asian stir-fry, Mexican burrito (diverse)
5. User upvotes Italian pasta → italian +1 reward

### Day 3: Learning Phase
1. User has given 8 feedbacks (3 italian upvotes, 2 asian downvotes)
2. CMAB learns: italian (α=4, β=1), asian (α=1, β=3)
3. Thompson Sampling favors italian category
4. Recommendations lean toward Italian while still exploring
5. User cooks "Chicken Alfredo" → italian +2 reward

### Day 30: Personalized Experience
1. User has 50+ interactions
2. CMAB knows preferences: italian (0.85), quick_meals (0.78), salad (0.65)
3. ε=0.1 → mostly exploitation with minimal exploration
4. Recommendations are highly personalized
5. System still adapts if preferences change

## Monitoring & Debugging

### Check User's CMAB State

```bash
curl http://localhost:8000/api/users/{user_id}/cmab/statistics
```

Look for:
- **High α, low β**: Preferred category
- **Low α, high β**: Disliked category
- **Both low**: Under-explored category
- **High pulls**: Frequently recommended

### Console Logs

When recommendations are generated, you'll see:
```
CMAB selected categories for user user-123: [('italian', 0.85), ('asian', 0.62), ('quick_meals', 0.58)]
Context: {'expiring_count': 2.0, 'total_items': 8.0, 'has_produce': 1.0, ...}
Cold start mode: False
```

When feedback is received:
```
Updated CMAB: category=italian, reward=1.0, context={...}
```

## Performance Considerations

- **Model size**: ~2-5 KB per user (lightweight)
- **Computation**: O(k) where k = number of categories (~15)
- **Latency**: < 10ms for category selection
- **Storage**: Firestore document per user
- **Updates**: Real-time on every feedback

## Future Enhancements

1. **Collaborative Filtering**: Bootstrap new users with similar users' preferences
2. **Temporal Patterns**: Learn time-of-day preferences (breakfast vs dinner)
3. **Advanced Context**: Weather, season, holidays
4. **Multi-Objective**: Balance novelty, diversity, and exploitation
5. **Neural Contextual Bandits**: Deep learning for complex context-reward relationships

## References

- Thompson Sampling: [Agrawal & Goyal, 2013]
- Contextual Bandits: [Li et al., 2010 - LinUCB]
- Beta-Bernoulli Bandit: [Chapelle & Li, 2011]

---

**Questions?** Check the implementation in `backend/src/services/cmab_service.py` or API docs at `API_COMPLETE_GUIDE.md`
