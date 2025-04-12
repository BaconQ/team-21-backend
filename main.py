from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import openai
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Virtual Pet API",
             description="Backend API for a virtual pet simulator with LLM-powered interactions")

class Pet:
    def __init__(self, name: str = "Pet"):
        self.name = name
        self.food = 100
        self.water = 100
        self.energy = 100
        self.happiness = 100
        self.health = 100
        self.last_interaction = datetime.now()
        self.interaction_history: List[Dict] = []

    def update_status(self, attribute: str, value: int) -> Dict[str, int]:
        """Update a pet's attribute and return the new status"""
        if hasattr(self, attribute):
            current_value = getattr(self, attribute)
            new_value = max(0, min(100, current_value + value))
            setattr(self, attribute, new_value)
            return self.get_status()
        raise ValueError(f"Invalid attribute: {attribute}")

    def get_status(self) -> Dict[str, int]:
        """Get the current status of all pet attributes"""
        return {
            "food": self.food,
            "water": self.water,
            "energy": self.energy,
            "happiness": self.happiness,
            "health": self.health
        }
    
    def add_interaction(self, prompt: str, response: str, status_change: Dict):
        """Record an interaction with the pet"""
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "status_change": status_change
        })
        self.last_interaction = datetime.now()

# Initialize pet
pet = Pet()

class PetAction(BaseModel):
    """Request model for pet interactions"""
    prompt: str

class PetResponse(BaseModel):
    """Response model for pet interactions"""
    message: str
    status: Dict[str, int]
    status_change: Dict[str, int]

class PetHistory(BaseModel):
    """Model for pet interaction history"""
    timestamp: str
    prompt: str
    response: str
    status_change: Dict

@app.get("/")
async def read_root():
    """API root endpoint with basic pet information"""
    return {
        "name": pet.name,
        "status": pet.get_status(),
        "last_interaction": pet.last_interaction.isoformat()
    }

@app.get("/status")
async def get_pet_status():
    """Get current pet status"""
    return pet.get_status()

@app.get("/history")
async def get_interaction_history():
    """Get pet interaction history"""
    return pet.interaction_history

@app.post("/interact")
async def interact_with_pet(action: PetAction) -> PetResponse:
    """
    Interact with the pet using natural language.
    The LLM will interpret the action and respond appropriately.
    """
    try:
        # Create a system message that defines the pet's behavior and available actions
        system_message = """You are a virtual pet with a distinct personality. Based on the user's input, you should:
        1. Respond as the pet would (be playful, caring, and maintain character)
        2. Decide how this interaction affects one of the pet's status values
        
        Return your response in this format:
        {
            "message": "Your response as the pet, showing personality and emotion",
            "attribute": "attribute_to_change",
            "value": change_value (-20 to +20),
            "explanation": "brief explanation of the status change"
        }
        
        Available attributes: food, water, energy, happiness, health
        Remember to stay in character and be consistent in your personality!
        """

        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": action.prompt}
            ],
            temperature=0.7
        )

        # Parse the response
        try:
            response_content = eval(response.choices[0].message.content)
            
            # Update pet status
            old_status = pet.get_status()
            new_status = pet.update_status(
                response_content["attribute"], 
                response_content["value"]
            )
            
            # Calculate status change
            status_change = {
                attr: new_status[attr] - old_status[attr]
                for attr in old_status
                if new_status[attr] != old_status[attr]
            }
            
            # Record the interaction
            pet.add_interaction(
                action.prompt,
                response_content["message"],
                status_change
            )
            
            return PetResponse(
                message=response_content["message"],
                status=new_status,
                status_change=status_change
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to process pet's response: " + str(e)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 