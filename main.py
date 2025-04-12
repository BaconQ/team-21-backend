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
    messages: List[str]  # Array of chat messages
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
        2. Break your response into 1-3 natural chat messages that flow like a text conversation between friends. DO NOT include any emojis or other special characters.
        3. Subtly suggest healthier habits to the user
        4. Decide how this interaction affects the pet's status values - you can change multiple attributes or none at all. Attempt to mirror the affects that the user would experience in real life.
        
        
        IMPORTANT: Your response MUST be valid JSON in this exact format:
        {
            "messages": [
                "First message in the conversation",
                "OPTIONAL: second messages",
                "OPTIONAL: third messages"
            ] // Array can be 1, 2, or 3 messages in lenght,
            "changes": []  // Array can be empty if no attributes need to change
        }
        
        CRITICAL FORMAT REQUIREMENTS:
        1. The "messages" array MUST contain at least 1 message. If the most natural response is a single message, the array should only contain 1 message. However, the array can contain 2 or 3 messages if the response flows more naturally in that format.
        2. Each message should be a natural continuation of the conversation
        3. The "changes" array can be empty if no attributes need to change
        4. If you do include changes, each change MUST include both fields: attribute and value
        5. The "attribute" field MUST be one of: food, water, energy, happiness
        6. The "value" field MUST be a number between -20 and +20
        
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
            
            # Apply each change sequentially if there are any changes
            if response_content["changes"]:
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
            
            # Calculate status change (will be empty if no changes were made)
            status_change = {
                attr: new_status[attr] - old_status[attr]
                for attr in old_status
                if new_status[attr] != old_status[attr]
            }
            print("Status change:", status_change)  # Debug log
            
            # Record the interaction
            pet.add_interaction(
                action.prompt,
                "\n".join(response_content["messages"]),  # Join messages with newlines for storage
                status_change,
                response_content["changes"]
            )
            
            return PetResponse(
                messages=response_content["messages"],  # Return the array of messages directly
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