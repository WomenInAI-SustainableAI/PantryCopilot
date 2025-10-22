# CMAB Recipe Recommendation System

## Overview

The PantryCopilot recommendation system uses a **Contextual Multi-Armed Bandit (CMAB)** approach to learn user preferences and provide personalized recipe recommendations. This implementation uses **Thompson Sampling** for balancing exploration and exploitation.

## What is CMAB?

A Contextual Multi-Armed Bandit is a reinforcement learning framework that:
- **Arms**: Different options to choose from (recipe categories in our case)
- **Context**: Current situation or state (user's inventory, time of day, etc.)
- **Reward**: Feedback signal indicating how good the choice was
- **Goal**: Learn which arms to pull (categories to recommend) in different contexts to maximize cumulative reward

## Architecture

### Components

#### 1. Recipe Categories (Arms)

We have 13 recipe categories that serve as "arms" in the bandit:

- `italian` - Italian cuisine
- `asian` - Asian cuisine (Chinese, Japanese, Thai, etc.)
- `mexican` - Mexican cuisine
- `american` - American cuisine
- `mediterranean` - Mediterranean cuisine
- `indian` - Indian cuisine
- `quick_meals` - Recipes under 30 minutes
- `healthy` - Health-focused recipes
- `comfort_food` - Comfort food recipes
- `vegetarian` - Vegetarian recipes
- `desserts` - Desserts and sweets
- `breakfast` - Breakfast recipes
- `salads` - Salad recipes

#### 2. Context Features

The system extracts contextual features from the user's current state:

- **Expiring Items**: Whether user has items expiring soon (0-3 days)
- **Expiring Count**: Number of items expiring soon
- **Inventory Diversity**: Variety of items in inventory (0-1 scale)
- **Time of Day**: Morning, afternoon, evening, or night
- **Day of Week**: 0-6 (Monday-Sunday)
- **Is Weekend**: Boolean flag for Saturday/Sunday

#### 3. Reward System

User feedback is mapped to rewards:

| Feedback Type | Reward | Description |
|--------------|--------|-------------|
| **Cooked** | +2 | User actually made the recipe (strongest positive signal) |
| **Upvote** (👍) | +1 | User liked the recipe |
| **Downvote** (👎) | -1 | User disliked the recipe |
| **Skip** | 0 | User skipped the recipe |
| **Ignored** | 0 | User ignored the recommendation |

### Algorithm: Thompson Sampling

Thompson Sampling is a Bayesian approach that:

1. **Maintains Beta Distributions**: For each arm (category), we maintain a Beta(α, β) distribution representing our belief about its success probability
2. **Samples**: When selecting arms, we sample from each Beta distribution
3. **Selects**: Choose the arms with the highest sampled values
4. **Updates**: After receiving feedback, update the Beta distribution parameters

**Initial State**: All arms start with Beta(1, 1), which is a uniform distribution (no prior knowledge).

**Update Rule**:
- Reward is normalized to [0, 1] range: `normalized_reward = (reward + 1) / 3`
- Update: `α += normalized_reward`, `β += (1 - normalized_reward)`

### Cold Start Solution

To handle new users without historical data, we implement:

1. **Epsilon-Greedy Exploration**: During cold start phase, with probability ε (default 0.1), we explore by selecting random categories, prioritizing least-tried ones
2. **Cold Start Threshold**: Continue exploration until each arm has been tried at least N times (default 10)
3. **Uniform Prior**: Start with Beta(1, 1) for all arms, giving equal initial probability
4. **Popularity Fallback**: In extreme cold start (no data at all), all categories have equal chance

## Implementation

### File Structure

```
backend/src/
├── services/
│   ├── cmab_service.py          # Core CMAB algorithm
│   ├── cmab_manager.py          # User-specific CMAB management
│   └── recommendation_service.py # Integration with recommendations
├── db/
│   ├── crud/
│   │   └── cmab_stats.py        # Firestore persistence
│   └── models.py                 # Data models (FeedbackType enum)
└── tests/
    └── test_cmab.py              # Unit tests
```

### Usage Examples

#### 1. Getting Recommendations

```python
from src.services.recommendation_service import get_personalized_recommendations

# Get personalized recommendations (CMAB automatically applied)
recommendations = await get_personalized_recommendations(
    user_id="user123",
    number_of_recipes=10
)

# Recommendations are automatically boosted based on learned preferences
```

#### 2. Recording Feedback

```python
from src.services.cmab_manager import cmab_manager

# Record that user cooked a recipe
cmab_manager.record_feedback(
    user_id="user123",
    recipe=recipe_dict,
    feedback_type="cooked",
    inventory=user_inventory
)
```

#### 3. Getting User Preferences

```python
from src.services.cmab_manager import cmab_manager

# Get summary of learned preferences
preferences = cmab_manager.get_user_preferences_summary("user123")

# Returns:
# {
#   "top_categories": [
#     {"category": "italian", "preference_score": 0.812, "total_interactions": 25},
#     {"category": "quick_meals", "preference_score": 0.701, "total_interactions": 18},
#     ...
#   ],
#   "is_cold_start": False
# }
```

## API Endpoints

### Submit Feedback

**POST** `/api/users/{user_id}/feedback`

Submit feedback for a recipe. CMAB is automatically updated.

```json
{
  "recipe_id": "12345",
  "feedback_type": "cooked"
}
```

**Feedback Types**: `upvote`, `downvote`, `skip`, `cooked`, `ignored`

### Get User Preferences

**GET** `/api/users/{user_id}/preferences`

Get learned preferences for a user.

**Response**:
```json
{
  "top_categories": [
    {
      "category": "italian",
      "preference_score": 0.812,
      "total_interactions": 25
    }
  ],
  "total_categories": 13,
  "explored_categories": 8,
  "is_cold_start": false
}
```

### Get Recommendations

**GET** `/api/users/{user_id}/recommendations?limit=10`

Get personalized recommendations (CMAB automatically boosts preferred categories).

## How It Works: Step by Step

### 1. User Gets Recommendations

1. System extracts context from user's inventory (expiring items, diversity, time)
2. CMAB selects top 3 preferred categories using Thompson Sampling
3. Recipes are fetched from Spoonacular
4. Each recipe is categorized
5. Recipes in preferred categories get a score boost (up to 20%)
6. Final recommendations are returned sorted by boosted scores

### 2. User Provides Feedback

1. User interacts with a recipe (upvote, downvote, cook, skip)
2. Feedback is saved to database
3. Recipe is categorized
4. CMAB updates Beta distribution for that category
5. User's preference model is persisted to Firestore

### 3. Learning Over Time

As users provide more feedback:
- Beta distributions become more confident (α and β grow)
- Preferred categories consistently get higher sampled values
- Recommendations increasingly match user preferences
- Exploration still occurs occasionally to discover new preferences

## Testing

Run the comprehensive test suite:

```bash
cd backend
python -m unittest test_cmab -v
```

**Test Coverage**:
- 24 unit tests covering all CMAB components
- Tests for Thompson Sampling, context extraction, category mapping
- Tests for feedback updates and arm selection
- Tests for cold start behavior

## Persistence

CMAB statistics are persisted to Firestore:

```
users/{user_id}/cmab_stats/stats
{
  "arms": {
    "italian": {
      "alpha": 3.5,
      "beta": 1.2,
      "total_pulls": 25,
      "total_reward": 18.0,
      "cooked_count": 5,
      "upvote_count": 8,
      "downvote_count": 2
    },
    ...
  },
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Performance Characteristics

### Exploration vs Exploitation

- **Cold Start**: High exploration (ε = 0.1, minimum 10 pulls per arm)
- **After Cold Start**: Balanced by Thompson Sampling's natural exploration
- **Long Term**: Exploitation of best arms with occasional exploration

### Computational Complexity

- **Arm Selection**: O(n × k) where n = number of arms, k = arms to select
- **Update**: O(1) per feedback
- **Storage**: O(n) per user where n = number of arms

### Sample Efficiency

Thompson Sampling is known for excellent sample efficiency:
- Converges to optimal policy quickly
- Better than ε-greedy and UCB in many scenarios
- Naturally balances exploration and exploitation

## Future Enhancements

Potential improvements for the CMAB system:

1. **Contextual Features**: Use context features in arm selection (currently global per user)
2. **Hierarchical Learning**: Learn across users with similar preferences
3. **Time-Based Decay**: Give more weight to recent feedback
4. **Dynamic Arms**: Add/remove categories based on availability
5. **Multi-Objective**: Balance multiple objectives (taste, health, cost)

## References

- Thompson, W. R. (1933). "On the likelihood that one unknown probability exceeds another in view of the evidence of two samples"
- Agrawal, S., & Goyal, N. (2012). "Analysis of Thompson Sampling for the Multi-armed Bandit Problem"
- Li, L., et al. (2010). "A Contextual-Bandit Approach to Personalized News Article Recommendation"

## Support

For questions or issues related to the CMAB system:
1. Check the unit tests for usage examples
2. Review the inline documentation in `cmab_service.py`
3. Open an issue on GitHub with `[CMAB]` prefix
