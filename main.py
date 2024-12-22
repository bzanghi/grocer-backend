from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import logging
from ConversationManager import ConversationManager
from IngredientsParserAgent import IngredientsParserAgent, Recipe
from ListOrganizationAgent import ListOrganizationAgent, GroceryItem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://grocer-6xxixa3zg-benbenzanghicos-projects.vercel.app",
        # Add your production URL here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
conversation_manager = ConversationManager()
ingredients_parser = IngredientsParserAgent()
list_organizer = ListOrganizationAgent()

class UserInput(BaseModel):
    message: str

class AddRecipeRequest(BaseModel):
    recipe_name: str

class ItemUpdate(BaseModel):
    item_id: str
    checked: bool

class ProcessMessageResponse(BaseModel):
    response: str
    updated_list: Dict[str, List[GroceryItem]]

@app.post("/api/message", response_model=ProcessMessageResponse)
async def process_message(user_input: UserInput):
    try:
        logger.info(f"Processing message: {user_input.message}")
        logger.info(f"Current items before processing: {list_organizer.current_items}")
        
        # Process the message through conversation manager
        result = await conversation_manager.process_user_input(user_input.message)
        
        # Parse any ingredients mentioned in natural language
        ingredients = await ingredients_parser.parse_natural_language_items(user_input.message)
        logger.info(f"Parsed ingredients: {ingredients}")
        
        # Categorize ingredients into grocery items, preserving existing items
        grocery_items = await list_organizer.categorize_items(ingredients, preserve_existing=True)
        logger.info(f"Categorized items: {grocery_items}")
        
        # Add unique IDs to new items
        for item in grocery_items:
            if not hasattr(item, 'id') or not item.id:
                item.id = str(uuid.uuid4())
        
        # Organize items by aisle, preserving existing items
        organized_items = list_organizer.organize_by_aisle(grocery_items, preserve_existing=True)
        logger.info(f"Final organized items: {organized_items}")
        
        return ProcessMessageResponse(
            response=result["response"],
            updated_list=organized_items
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recipe", response_model=Dict[str, List[GroceryItem]])
async def add_recipe(request: AddRecipeRequest):
    try:
        logger.info(f"Adding recipe: {request.recipe_name}")
        logger.info(f"Current items before processing: {list_organizer.current_items}")
        
        # Get recipe and its ingredients
        recipe = await ingredients_parser.parse_meal_to_ingredients(request.recipe_name)
        
        # Categorize ingredients into grocery items, preserving existing items
        grocery_items = await list_organizer.categorize_items(recipe.ingredients, preserve_existing=True)
        logger.info(f"Categorized items: {grocery_items}")
        
        # Add unique IDs
        for item in grocery_items:
            if not hasattr(item, 'id') or not item.id:
                item.id = str(uuid.uuid4())
        
        # Organize by aisle, preserving existing items
        organized_items = list_organizer.organize_by_aisle(grocery_items, preserve_existing=True)
        logger.info(f"Final organized items: {organized_items}")
        
        return organized_items
    except Exception as e:
        logger.error(f"Error adding recipe: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/item/update", response_model=Dict[str, List[GroceryItem]])
async def update_item(update: ItemUpdate, aisle: str):
    try:
        logger.info(f"Updating item {update.item_id} in aisle {aisle} to checked={update.checked}")
        return list_organizer.update_item_status(aisle, update.item_id, update.checked)
    except Exception as e:
        logger.error(f"Error updating item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/item/remove", response_model=Dict[str, List[GroceryItem]])
async def remove_item(item_id: str, aisle: str):
    try:
        logger.info(f"Removing item {item_id} from aisle {aisle}")
        return list_organizer.remove_item(aisle, item_id)
    except Exception as e:
        logger.error(f"Error removing item: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
