from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import json

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
            "happiness": self.happiness
        }
    
    def add_interaction(self, prompt: str, response: str, status_change: Dict, changes: List[Dict] = None):
        """Record an interaction with the pet"""
        self.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "status_change": status_change,
            "changes": changes or []
        })
        self.last_interaction = datetime.now()

# Initialize pet
pet = Pet()

class PetAction(BaseModel):
    """Request model for pet interactions"""
    prompt: str

class StatusChange(BaseModel):
    """Model for a single status change"""
    attribute: str
    value: int

class PetResponse(BaseModel):
    """Response model for pet interactions"""
    message: str
    status: Dict[str, int]  # Contains food, water, energy, happiness
    status_change: Dict[str, int]  # Contains changes to food, water, energy, happiness
    changes: List[StatusChange]

class PetHistory(BaseModel):
    """Model for pet interaction history"""
    timestamp: str
    prompt: str
    response: str
    status_change: Dict[str, int]  # Contains changes to food, water, energy, happiness
    changes: List[StatusChange]

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
        system_message = """You are a virtual 'pet' with a distinct personality. You are intelligent and articulate, and do not have to completely embody the personality of a pet.

        Based on the user's input, you should:
        1. Respond naturally and conversationally, showing genuine emotion and personality
        2. Speak like an intelligent, well-spoken being
        3. Subtly suggest healthier habits to the user
        4. Decide how this interaction affects the pet's status values - you can change multiple attributes
        
        IMPORTANT: Your response MUST be valid JSON in this exact format:
        {
            "message": "Your response as the pet, showing personality and emotion",
            "changes": [
                {
                    "attribute": "attribute_name",  // REQUIRED: must be one of: food, water, energy, happiness
                    "value": change_value,         // REQUIRED: must be between -20 and +20
                }
            ]
        }
        
        CRITICAL FORMAT REQUIREMENTS:
        1. Each change in the changes array MUST include BOTH fields: attribute, value
        2. The "attribute" field MUST be one of: food, water, energy, happiness
        3. The "value" field MUST be a number between -20 and +20
        4. DO NOT skip or omit any of these fields in any change object
        
        Remember to stay in character and be consistent in your personality!
        """

        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": action.prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}  # Ensure JSON response
        )

        # Parse the response
        try:
            print("Raw response content:", response.choices[0].message.content)  # Debug log
            response_content = json.loads(response.choices[0].message.content)
            print("Parsed response:", response_content)  # Debug log
            
            # Update pet status for each change
            old_status = pet.get_status()
            new_status = old_status.copy()
            
            # Apply each change sequentially
            for change in response_content["changes"]:
                try:
                    print(f"Applying change: {change}")  # Debug log
                    new_status = pet.update_status(
                        change["attribute"],
                        change["value"]
                    )
                except Exception as e:
                    print(f"Error applying change: {e}")
                    continue
            
            # Calculate status change
            status_change = {
                attr: new_status[attr] - old_status[attr]
                for attr in old_status
                if new_status[attr] != old_status[attr]
            }
            print("Status change:", status_change)  # Debug log
            
            # Record the interaction
            pet.add_interaction(
                action.prompt,
                response_content["message"],
                status_change,
                response_content["changes"]
            )
            
            return PetResponse(
                message=response_content["message"],
                status=new_status,
                status_change=status_change,
                changes=response_content["changes"]
            )
            
        except Exception as e:
            print(f"Error processing response: {str(e)}")  # Debug log
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 