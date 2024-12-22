from typing import List, Dict, Optional
from pydantic import BaseModel
from groq import Groq
import os
import uuid
from dotenv import load_dotenv
import json
from IngredientsParserAgent import Ingredient

load_dotenv()

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class GroceryItem(BaseModel):
    id: str
    name: str
    aisle: str
    quantity: Optional[str] = None
    quantity_unit: Optional[str] = None
    checked: bool = False

class ListOrganizationAgent:
    def __init__(self):
        self.system_prompt = """You are a grocery store expert that can:
1. Categorize items into appropriate store aisles
2. Organize shopping lists efficiently
Output must be valid JSON matching the provided schema."""
        
        # Common aisle categories
        self.default_aisles = [
            "Produce",
            "Dairy",
            "Meat",
            "Frozen",
            "Pantry",
            "Canned Goods",
            "Baking",
            "Beverages",
            "Snacks",
            "Household",
            "Personal Care"
        ]

        # Keep track of current items
        self.state_file = 'state.json'
        self.current_items: Dict[str, List[GroceryItem]] = self.load_state()

    def load_state(self) -> Dict[str, List[GroceryItem]]:
        """Load state from JSON file"""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                items_dict = {}
                for aisle, items in state.get('items', {}).items():
                    items_dict[aisle] = [GroceryItem(**item) for item in items]
                return items_dict
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_state(self):
        """Save current state to JSON file"""
        state = {
            'items': {
                aisle: [item.dict() for item in items]
                for aisle, items in self.current_items.items()
            }
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def categorize_items(self, items: List[Ingredient], preserve_existing: bool = True) -> List[GroceryItem]:
        """Categorize items into appropriate aisles using Groq"""
        items_str = json.dumps([item.dict() for item in items])
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"{self.system_prompt}\nAvailable aisles: {', '.join(self.default_aisles)}"},
                {"role": "user", "content": f"Categorize these items into appropriate aisles: {items_str}. Return in JSON format with this schema: {{'items': {GroceryItem.model_json_schema()}}}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        categorized_data = json.loads(response.choices[0].message.content)
        # Generate unique IDs for new items
        new_items = []
        for item_data in categorized_data["items"]:
            if 'id' not in item_data:
                item_data['id'] = str(uuid.uuid4())
            new_items.append(GroceryItem(**item_data))

        if preserve_existing:
            # Create a set of existing item names (case-insensitive)
            existing_names = {
                item.name.lower()
                for items in self.current_items.values()
                for item in items
            }
            
            # Only add items that don't already exist
            new_items = [
                item for item in new_items
                if item.name.lower() not in existing_names
            ]

        return new_items
    
    def organize_by_aisle(self, items: List[GroceryItem], preserve_existing: bool = True) -> Dict[str, List[GroceryItem]]:
        """Organize items by aisle for efficient shopping"""
        organized: Dict[str, List[GroceryItem]] = {}
        
        # If preserving existing items, start with the current items
        if preserve_existing:
            for aisle, aisle_items in self.current_items.items():
                organized[aisle] = list(aisle_items)
        
        # Add new items to their aisles
        for item in items:
            # Check if this item already exists in any aisle
            item_exists = False
            for aisle_items in organized.values():
                if any(existing.name.lower() == item.name.lower() for existing in aisle_items):
                    item_exists = True
                    break
            
            # Only add the item if it doesn't already exist
            if not item_exists:
                if item.aisle not in organized:
                    organized[item.aisle] = []
                organized[item.aisle].append(item)
        
        # Sort aisles based on typical store layout
        sorted_aisles = sorted(
            organized.items(),
            key=lambda x: self.default_aisles.index(x[0]) if x[0] in self.default_aisles else len(self.default_aisles)
        )
        
        # Update current items and save state
        self.current_items = dict(sorted_aisles)
        self.save_state()
        
        return self.current_items
    
    def update_item_status(self, aisle: str, item_id: str, checked: bool) -> Dict[str, List[GroceryItem]]:
        """Update the checked status of an item"""
        if aisle in self.current_items:
            self.current_items[aisle] = [
                GroceryItem(**{**item.dict(), "checked": checked if item.id == item_id else item.checked})
                for item in self.current_items[aisle]
            ]
            self.save_state()
        return self.current_items
    
    def remove_item(self, aisle: str, item_id: str) -> Dict[str, List[GroceryItem]]:
        """Remove an item from the list"""
        if aisle in self.current_items:
            self.current_items[aisle] = [
                item for item in self.current_items[aisle] 
                if item.id != item_id
            ]
            # Remove aisle if empty
            if not self.current_items[aisle]:
                del self.current_items[aisle]
            self.save_state()
        return self.current_items
    
    def add_items(self, current_items: List[GroceryItem], new_items: List[GroceryItem]) -> List[GroceryItem]:
        """Add new items to the list, avoiding duplicates"""
        # Create a set of existing item names (case-insensitive)
        existing_names = {item.name.lower() for item in current_items}
        
        # Only add items that don't already exist
        unique_new_items = [
            item for item in new_items
            if item.name.lower() not in existing_names
        ]
        
        return current_items + unique_new_items
