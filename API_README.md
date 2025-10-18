# PantryCopilot FastAPI Backend

This directory contains the Python FastAPI backend for PantryCopilot.

## Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows CMD:
     ```cmd
     .\venv\Scripts\activate.bat
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Add your Google API key to the `.env` file:
     ```
     GOOGLE_API_KEY=your_actual_api_key_here
     ```

## Running the API

### Development Mode (with auto-reload)
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API docs (Swagger): http://localhost:8000/docs
- Alternative API docs (ReDoc): http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Recipe Recommendations
- `POST /api/explain-recommendation` - Get explanation for a recipe recommendation
  ```json
  {
    "recipe_name": "Tomato Pasta",
    "expiring_ingredients": ["tomatoes", "basil"],
    "allergies": ["nuts"],
    "inventory_match_percentage": 85.5
  }
  ```

### User Feedback
- `POST /api/process-feedback` - Process user feedback for recommendations
  ```json
  {
    "recipe_id": "recipe_123",
    "feedback_type": "upvote",
    "user_id": "user_456"
  }
  ```

## Project Structure

```
PantryCopilot/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create from .env.example)
├── .env.example                    # Example environment variables
└── src/
    └── ai/
        ├── __init__.py
        ├── genkit.py               # AI configuration (Google Gemini)
        └── flows/
            ├── __init__.py
            ├── explain_recipe_recommendation.py
            └── improve_recommendations_from_feedback.py
```

## Integration with Next.js Frontend

To call these APIs from your Next.js frontend (TypeScript):

```typescript
// Example: Explain recommendation
async function explainRecommendation(recipeData: {
  recipe_name: string;
  expiring_ingredients: string[];
  allergies: string[];
  inventory_match_percentage: number;
}) {
  const response = await fetch('http://localhost:8000/api/explain-recommendation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(recipeData),
  });
  
  return await response.json();
}

// Example: Process feedback
async function processFeedback(feedbackData: {
  recipe_id: string;
  feedback_type: 'upvote' | 'downvote' | 'skip';
  user_id: string;
}) {
  const response = await fetch('http://localhost:8000/api/process-feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedbackData),
  });
  
  return await response.json();
}
```

## Testing

Visit http://localhost:8000/docs to test the API using the interactive Swagger UI.
