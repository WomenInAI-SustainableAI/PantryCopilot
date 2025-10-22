# CMAB System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interaction                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Endpoints                                │
│                                                                       │
│  GET  /api/users/{user_id}/recommendations                          │
│  POST /api/users/{user_id}/feedback                                 │
│  GET  /api/users/{user_id}/preferences                              │
└───────────────────┬─────────────────┬─────────────────┬─────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────┐   ┌────────────────┐   ┌─────────────┐
        │ Recommendation│   │    Feedback    │   │ Preferences │
        │    Service    │   │    Handler     │   │   Service   │
        └───────┬───────┘   └────────┬───────┘   └──────┬──────┘
                │                    │                   │
                │                    │                   │
                ▼                    ▼                   ▼
        ┌───────────────────────────────────────────────────────┐
        │              CMAB Manager                              │
        │                                                         │
        │  • Load/Save user-specific recommenders                │
        │  • Manage in-memory cache                              │
        │  • Coordinate feedback updates                         │
        └───────────────────┬────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────────────┐
        │            CMAB Recommender (per user)                 │
        │                                                         │
        │  ┌─────────────────────────────────────────────────┐  │
        │  │  Recipe Categories (Arms)                       │  │
        │  │                                                 │  │
        │  │  • italian      Beta(α₁, β₁)                  │  │
        │  │  • asian        Beta(α₂, β₂)                  │  │
        │  │  • mexican      Beta(α₃, β₃)                  │  │
        │  │  • quick_meals  Beta(α₄, β₄)                  │  │
        │  │  • healthy      Beta(α₅, β₅)                  │  │
        │  │  • ... (13 total categories)                   │  │
        │  └─────────────────────────────────────────────────┘  │
        │                                                         │
        │  Thompson Sampling Algorithm:                          │
        │  1. Sample θᵢ ~ Beta(αᵢ, βᵢ) for each arm            │
        │  2. Select top-k arms with highest θᵢ                 │
        │  3. Update Beta parameters based on feedback           │
        └───────────────────┬────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────────────────┐
        │              Context Extraction                        │
        │                                                         │
        │  • Expiring items (count, urgency)                    │
        │  • Inventory diversity (0-1)                          │
        │  • Time of day (morning/afternoon/evening/night)      │
        │  • Day of week (weekday/weekend)                      │
        │  • Feature vector: [has_expiring, count, diversity,  │
        │                     is_morning, is_evening, is_weekend]│
        └────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                    Recommendation Flow                               │
└─────────────────────────────────────────────────────────────────────┘

    User Requests       Extract Context      Select Categories
    Recommendations  ──────────────────▶   (Thompson Sampling)
          │                                       │
          │                                       ▼
          │                              ┌─────────────────┐
          │                              │ Top 3 Categories│
          │                              │  1. italian     │
          │                              │  2. quick_meals │
          │                              │  3. healthy     │
          │                              └────────┬────────┘
          │                                       │
          ▼                                       ▼
    ┌─────────────┐                    ┌─────────────────┐
    │  Spoonacular│◀───────────────────│ Fetch & Filter  │
    │     API     │                    │    Recipes      │
    └──────┬──────┘                    └────────┬────────┘
           │                                    │
           │                                    ▼
           │                          ┌──────────────────┐
           └─────────────────────────▶│  Score & Rank   │
                                      │   with CMAB     │
                                      │     Boost       │
                                      └────────┬─────────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │ Return Top N     │
                                      │ Recommendations  │
                                      └──────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                       Learning Flow                                  │
└─────────────────────────────────────────────────────────────────────┘

    User Provides       Map to            Update Beta
    Feedback        ────────────▶      Distribution
    (cooked: +2)      Category           Parameters
         │           (italian)                │
         │                                    │
         ▼                                    ▼
    ┌─────────────┐                  ┌──────────────┐
    │ Save to DB  │                  │ Alpha ← α+r' │
    │  (Firestore)│                  │ Beta  ← β+(1-r')│
    └─────────────┘                  └──────┬───────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Persist to      │
                                   │ Firestore       │
                                   └─────────────────┘

    Where r' = (reward + 1) / 3  (normalized to [0,1])


┌─────────────────────────────────────────────────────────────────────┐
│                     Cold Start Solution                              │
└─────────────────────────────────────────────────────────────────────┘

    New User           Initialize All      Epsilon-Greedy
    (no history)       Arms: Beta(1,1)     Exploration
         │                    │                   │
         │                    │                   │
         ▼                    ▼                   ▼
    ┌─────────────────────────────────────────────────────┐
    │  First 10 pulls per arm: Explore                    │
    │  • With probability ε=0.1: random selection         │
    │  • Otherwise: Thompson Sampling                      │
    │  • Prioritize least-tried categories                │
    └───────────────────────┬─────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────┐
    │  After cold start: Pure Thompson Sampling           │
    │  • Natural exploration from sampling                │
    │  • Exploitation of learned preferences              │
    └─────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                    Data Storage Schema                               │
└─────────────────────────────────────────────────────────────────────┘

Firestore Structure:

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
    "asian": { ... },
    "mexican": { ... },
    ...
  },
  "updated_at": "2024-01-15T10:30:00Z"
}


┌─────────────────────────────────────────────────────────────────────┐
│                   Performance Metrics                                │
└─────────────────────────────────────────────────────────────────────┘

Computational Complexity:
  • Arm Selection:     O(n × k) where n=13, k=3  → ~39 operations
  • Feedback Update:   O(1)                       → constant time
  • Storage per User:  O(n)                       → 13 arms

Sample Efficiency:
  • Thompson Sampling converges quickly (< 100 samples typically)
  • Better than ε-greedy and UCB in empirical studies
  • Natural balance between exploration and exploitation

Memory Usage:
  • Per-user state:    ~2KB (13 arms × ~150 bytes)
  • In-memory cache:   Configurable, LRU eviction possible
  • Firestore docs:    One document per user
```

## Key Algorithms

### Thompson Sampling (Arm Selection)

```python
def select_arms(context, n_arms=3):
    sampled_values = []
    for category in RECIPE_CATEGORIES:
        # Sample from Beta distribution
        theta = random.betavariate(arm_stats[category].alpha, 
                                   arm_stats[category].beta)
        sampled_values.append((category, theta))
    
    # Select top N by sampled value
    sampled_values.sort(key=lambda x: x[1], reverse=True)
    return [cat for cat, _ in sampled_values[:n_arms]]
```

### Beta Distribution Update

```python
def update(category, reward):
    # Normalize reward from [-1, 2] to [0, 1]
    normalized_reward = (reward + 1) / 3.0
    
    # Update Beta parameters
    arm_stats[category].alpha += normalized_reward
    arm_stats[category].beta += (1.0 - normalized_reward)
    arm_stats[category].total_pulls += 1
```

### Cold Start (Epsilon-Greedy)

```python
def select_with_cold_start(context, n_arms=3):
    min_pulls = min(stats.total_pulls for stats in arm_stats.values())
    
    if min_pulls < COLD_START_THRESHOLD:
        if random.random() < EPSILON:
            # Explore: prioritize least-tried
            pulls = [(cat, stats.total_pulls) for cat, stats in arm_stats.items()]
            pulls.sort(key=lambda x: x[1])
            return [cat for cat, _ in pulls[:n_arms]]
    
    # Exploit with Thompson Sampling
    return thompson_sampling_select(context, n_arms)
```
