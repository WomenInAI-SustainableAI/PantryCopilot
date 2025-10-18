# Genkit Flow Integration Guide

This guide explains how the PantryCopilot AI flows are structured using Genkit.

## 🎯 What is Genkit?

Genkit is Google's framework for building AI-powered applications with structured flows, type-safe schemas, and powerful tooling.

## 📚 Flow Structure

### Basic Flow Pattern

```python
from pydantic import BaseModel, Field
from src.ai.genkit import ai

class OutputSchema(BaseModel):
    """Define your output structure."""
    field: str = Field(description="Description of the field")

@ai.flow()
async def my_flow(input_param: str) -> OutputSchema:
    """
    Flow function that processes input and returns structured output.
    """
    result = await ai.generate(
        prompt=f"Process this: {input_param}",
        output_schema=OutputSchema,
    )
    return result.output
```

## 🔄 Current Flows

### 1. Explain Recipe Recommendation Flow

**File:** `src/ai/flows/explain_recipe_recommendation.py`

**Purpose:** Generates detailed explanations for recipe recommendations based on urgency, safety, and cost savings.

**Usage:**
```python
from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation

result = await explain_recipe_recommendation(
    recipe_name="Tomato Pasta",
    expiring_ingredients=["tomatoes", "basil"],
    allergies=["nuts"],
    inventory_match_percentage=85.5
)

print(result.explanation)
```

**Output Schema:**
```python
class ExplainRecipeRecommendationOutput(BaseModel):
    explanation: str  # Detailed explanation paragraph
```

### 2. Improve Recommendations from Feedback Flow

**File:** `src/ai/flows/improve_recommendations_from_feedback.py`

**Purpose:** Processes user feedback (upvote, downvote, skip) to improve future recommendations.

**Usage:**
```python
from src.ai.flows.improve_recommendations_from_feedback import improve_recommendations_from_feedback

result = await improve_recommendations_from_feedback(
    recipe_id="recipe_123",
    feedback_type="upvote",
    user_id="user_456"
)

print(f"Success: {result.success}")
print(f"Message: {result.message}")
```

**Output Schema:**
```python
class ImproveRecommendationsFromFeedbackOutput(BaseModel):
    success: bool     # Whether feedback was processed
    message: str      # Summary of what changed
```

## 🚀 Running Flows

### Option 1: Direct Execution (Standalone)

```python
import asyncio
from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation

async def main():
    result = await explain_recipe_recommendation(
        recipe_name="Chicken Soup",
        expiring_ingredients=["chicken", "carrots"],
        allergies=[],
        inventory_match_percentage=90.0
    )
    print(result.explanation)

# Run with asyncio
asyncio.run(main())

# Or with Genkit's run_main
# from src.ai.genkit import ai
# ai.run_main(main())
```

### Option 2: Via FastAPI (API Endpoint)

The flows are automatically exposed via FastAPI endpoints:

**POST /api/explain-recommendation**
```json
{
  "recipe_name": "Chicken Soup",
  "expiring_ingredients": ["chicken", "carrots"],
  "allergies": [],
  "inventory_match_percentage": 90.0
}
```

**POST /api/process-feedback**
```json
{
  "recipe_id": "recipe_123",
  "feedback_type": "upvote",
  "user_id": "user_456"
}
```

### Option 3: Example Script

Run the provided example script:
```bash
python example_flows.py
```

## 🔧 Configuration

The Genkit AI instance is configured in `src/ai/genkit.py`:

```python
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI
import os

ai = Genkit(
    plugins=[GoogleAI()],
    model='googleai/gemini-2.5-flash',
    api_key=os.getenv("GOOGLE_API_KEY")
)
```

## 🎨 Creating New Flows

To create a new AI flow:

1. **Create a new file** in `src/ai/flows/`

2. **Define your output schema:**
```python
from pydantic import BaseModel, Field

class MyFlowOutput(BaseModel):
    result: str = Field(description="The result")
```

3. **Create the flow function:**
```python
from src.ai.genkit import ai

@ai.flow()
async def my_new_flow(input_data: str) -> MyFlowOutput:
    """Description of what the flow does."""
    result = await ai.generate(
        prompt=f"Your prompt: {input_data}",
        output_schema=MyFlowOutput,
    )
    return result.output
```

4. **Add to FastAPI** in `main.py`:
```python
from src.ai.flows.my_new_flow import my_new_flow, MyFlowOutput

@app.post("/api/my-endpoint", response_model=MyFlowOutput)
async def api_my_endpoint(input_data: str):
    return await my_new_flow(input_data)
```

## 🧪 Testing Flows

### Unit Tests
```python
import asyncio
from src.ai.flows.explain_recipe_recommendation import explain_recipe_recommendation

async def test_flow():
    result = await explain_recipe_recommendation(
        recipe_name="Test Recipe",
        expiring_ingredients=["ingredient1"],
        allergies=["allergy1"],
        inventory_match_percentage=75.0
    )
    assert result.explanation is not None
    assert len(result.explanation) > 0

asyncio.run(test_flow())
```

### API Tests
Visit the interactive API docs at `http://localhost:8000/docs` to test endpoints directly.

## 📦 Key Benefits of Genkit

1. **Type Safety**: Pydantic models ensure structured outputs
2. **Flow Decorator**: `@ai.flow()` provides tracing and observability
3. **Async Support**: Native async/await for better performance
4. **Structured Generation**: `output_schema` guarantees valid responses
5. **Plugin System**: Easy integration with different AI providers

## 🔍 Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check flow execution in the Genkit developer UI (if available):
```bash
genkit start
```

## 📚 Additional Resources

- [Genkit Documentation](https://firebase.google.com/docs/genkit)
- [Google AI Studio](https://aistudio.google.com/app/apikey) - Get your API key
- [Pydantic Documentation](https://docs.pydantic.dev/) - Schema validation
