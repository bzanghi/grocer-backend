from typing import List, Dict
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class Message(BaseModel):
    role: str
    content: str

class ConversationManager:
    def __init__(self):
        self.conversation_history: List[Message] = []
        
    async def process_user_input(self, user_input: str) -> Dict:
        """Process user input and coordinate with other agents"""
        # Add user message to history
        self.conversation_history.append(Message(role="user", content=user_input))
        
        # Call Groq API to understand user intent
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful grocery list assistant. Parse user input to determine if they want to add items, remove items, or get recipe suggestions."},
                *[{"role": m.role, "content": m.content} for m in self.conversation_history]
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract the assistant's response
        assistant_response = response.choices[0].message.content
        self.conversation_history.append(Message(role="assistant", content=assistant_response))
        
        # TODO: Parse response and coordinate with other agents
        # This will be expanded to handle different intents and coordinate with other agents
        
        return {
            "response": assistant_response,
            "intent": "pending_implementation",  # Will be replaced with actual intent parsing
            "updated_list": []  # Will be replaced with actual list updates
        }

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
