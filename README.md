# Grocer Backend

FastAPI backend for the Grocer app, providing natural language processing for grocery lists using the Groq API.

## Features

- Natural language processing for grocery items
- Recipe suggestions and ingredient parsing
- Automatic aisle categorization
- State persistence
- CORS support

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
GROQ_API_KEY=your_key_here
```

3. Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /api/message`: Process natural language input
- `POST /api/recipe`: Add recipe ingredients
- `POST /api/item/update`: Update item status
- `POST /api/item/remove`: Remove item from list

## Deployment

This backend is configured for deployment to Railway:

1. Create a new Railway project
2. Add environment variables:
   - `GROQ_API_KEY`: Your Groq API key
3. Deploy using the Railway CLI or GitHub integration

## Development

The backend uses a multi-agent system:
- ConversationManager: Handles user input processing
- IngredientsParser: Extracts ingredients from text
- ListOrganizer: Categorizes items by aisle

State is persisted in a JSON file and CORS is configured to allow requests from the frontend.
