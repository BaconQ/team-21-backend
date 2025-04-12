# Virtual Pet API

A backend API for a Tamagotchi-like virtual pet simulator with AI-powered interactions using FastAPI and OpenAI.

## Features

- RESTful API endpoints for pet interaction and status management
- OpenAI GPT-3.5 integration for natural language pet responses
- Pet status tracking (food, water, energy, happiness, health)
- Interaction history tracking

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.template` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.template .env
   # Edit .env and add your OpenAI API key
   ```

## Running the API Server

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### GET /
Get basic pet information
```json
{
    "name": "Pet",
    "status": {
        "food": 100,
        "water": 100,
        "energy": 100,
        "happiness": 100,
        "health": 100
    },
    "last_interaction": "2024-03-14T12:00:00.000Z"
}
```

### GET /status
Get current pet status
```json
{
    "food": 100,
    "water": 100,
    "energy": 100,
    "happiness": 100,
    "health": 100
}
```

### GET /history
Get pet interaction history
```json
[
    {
        "timestamp": "2024-03-14T12:00:00.000Z",
        "prompt": "Let's play!",
        "response": "Yay! I love playing with you!",
        "status_change": {
            "energy": -10,
            "happiness": 15
        }
    }
]
```

### POST /interact
Interact with the pet using natural language

Request:
```json
{
    "prompt": "Let's play fetch!"
}
```

Response:
```json
{
    "message": "Woof! I love playing fetch! *wags tail excitedly*",
    "status": {
        "food": 100,
        "water": 100,
        "energy": 90,
        "happiness": 100,
        "health": 100
    },
    "status_change": {
        "energy": -10
    }
}
```

## Status Values

All status values range from 0 to 100:
- food: Pet's hunger level
- water: Pet's thirst level
- energy: Pet's energy level
- happiness: Pet's mood
- health: Pet's overall health

The LLM will automatically adjust these values based on interactions, with changes ranging from -20 to +20 per interaction.

## For Frontend Developers

- All endpoints return JSON responses
- The `/interact` endpoint accepts POST requests with a JSON body containing a `prompt` field
- Status changes are automatically calculated and returned with each interaction
- Error responses include appropriate HTTP status codes and error messages
- CORS is enabled by default for frontend integration 