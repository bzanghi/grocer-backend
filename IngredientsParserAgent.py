from typing import List, Dict, Optional
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv()

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class Ingredient(BaseModel):
    name: str
    quantity: str
    quantity_unit: Optional[str] = None
    aisle: Optional[str] = None

class Recipe(BaseModel):
    name: str
    ingredients: List[Ingredient]
    instructions: Optional[List[str]] = None

class IngredientsParserAgent:
    def __init__(self):
        self.system_prompt = """You are a helpful cooking assistant that can:
1. Parse meal names into required ingredients
2. Suggest recipes based on available ingredients
3. Parse natural language into structured ingredient data
Output must be valid JSON matching the provided schema."""
    
    async def parse_meal_to_ingredients(self, meal_name: str) -> Recipe:
        """Convert a meal name into a list of required ingredients"""
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"List ingredients and basic instructions for {meal_name} in JSON format with this schema: {Recipe.model_json_schema()}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        recipe_data = json.loads(response.choices[0].message.content)
        return Recipe(**recipe_data)
    
    async def suggest_recipes(self, ingredients: List[str]) -> List[Recipe]:
        """Suggest possible recipes based on available ingredients"""
        ingredients_str = ", ".join(ingredients)
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Suggest 3 possible recipes using some or all of these ingredients: {ingredients_str}. Return in JSON format with this schema: {{'recipes': {Recipe.model_json_schema()}}}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        suggestions_data = json.loads(response.choices[0].message.content)
        return [Recipe(**recipe_data) for recipe_data in suggestions_data["recipes"]]
    
    async def parse_natural_language_items(self, text: str) -> List[Ingredient]:
        """Parse natural language text into structured ingredient data"""
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Parse this text into a list of ingredients: {text}. Return in JSON format with this schema: {{'ingredients': {Ingredient.model_json_schema()}}}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        ingredients_data = json.loads(response.choices[0].message.content)
        return [Ingredient(**ingredient_data) for ingredient_data in ingredients_data["ingredients"]]
