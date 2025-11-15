# conversational_recommender.py
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Ensure the backend package directory is on sys.path so imports work when running directly
SCRIPT_DIR = Path(__file__).resolve().parent
# backend/utils -> parent is backend
BACKEND_DIR = str(SCRIPT_DIR.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.supabase_db import create_supabase_client  # noqa: E402

class ConversationalRestaurantBot:
    def __init__(self):
        """Initialize with conversation history"""
        load_dotenv()
        self.supabase = create_supabase_client()
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are a friendly restaurant recommendation assistant.
                You have access to a restaurant database. Ask clarifying questions when needed,
                search the database based on user preferences, and provide personalized 
                recommendations. Be conversational and helpful."""
            }
        ]
    
    def search_restaurants(self, **kwargs):
        """Search restaurants in Supabase"""
        query = self.supabase.table("restaurants").select("*")
        
        # Track description-based filters for post-processing
        description_filters = []
        
        # Apply all filters
        for key, value in kwargs.items():
            if not value:
                continue
            
            if key == 'cuisine':
                query = query.ilike("cuisine_type", f"%{value}%")
            elif key == 'price_range':
                query = query.eq("price_range", value)
            elif key == 'location':
                query = query.ilike("address", f"%{value}%")
            elif key == 'vegetarian_friendly':
                description_filters.append('vegetarian')
            elif key == 'vegan_friendly':
                description_filters.append('vegan')
            elif key == 'gluten_free_options':
                description_filters.append('gluten-free')
                description_filters.append('gluten free')
            elif key == 'outdoor_seating':
                description_filters.append('outdoor')
            elif key == 'takes_reservations':
                description_filters.append('reservation')
            elif key == 'min_rating':
                query = query.gte("rating", value)
        
        # Execute query with ordering and limit
        response = query.order("rating", desc=True).limit(15).execute()  # Get more to filter
        
        restaurants = response.data if response.data else []
        
        # Post-process: filter by description keywords
        if description_filters and restaurants:
            filtered_restaurants = []
            for restaurant in restaurants:
                description = (restaurant.get('description') or '').lower()
                # Check if description contains any of the search keywords
                if any(keyword.lower() in description for keyword in description_filters):
                    filtered_restaurants.append(restaurant)
            restaurants = filtered_restaurants[:5]  # Limit to 5 after filtering
        else:
            restaurants = restaurants[:5]
        
        return restaurants
    
    def chat(self, user_message):
        """
        Send a message and get a response
        
        Args:
            user_message: User's message
            
        Returns:
            Assistant's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Define tools
        tools = [{
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Search restaurant database in Supabase",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cuisine": {"type": "string"},
                        "price_range": {"type": "string", "enum": ["$", "$$", "$$$", "$$$$"]},
                        "location": {"type": "string"},
                        "vegetarian_friendly": {"type": "boolean"},
                        "vegan_friendly": {"type": "boolean"},
                        "gluten_free_options": {"type": "boolean"},
                        "outdoor_seating": {"type": "boolean"},
                        "takes_reservations": {"type": "boolean"},
                        "min_rating": {"type": "number"}
                    }
                }
            }
        }]
        
        # Get response from OpenAI
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=self.conversation_history,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if function was called
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            
            # Search database
            restaurants = self.search_restaurants(**function_args)
            
            # Add function call and result to history
            self.conversation_history.append(message)
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(restaurants)
            })
            
            # Get final response
            final_response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=self.conversation_history
            )
            
            assistant_message = final_response.choices[0].message.content
        else:
            assistant_message = message.content
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history = self.conversation_history[:1]  # Keep system message


# Example usage
if __name__ == "__main__":
    bot = ConversationalRestaurantBot()
    
    print("🤖 Restaurant Bot: Hi! I can help you find great restaurants. What are you in the mood for?")
    print()
    
    # Simulated conversation
    messages = [
        "I'm looking for dinner tonight",
        "I love Italian food",
        "Something downtown with outdoor seating would be perfect",
        "What's the highest rated one?"
    ]
    
    for msg in messages:
        print(f"👤 You: {msg}")
        response = bot.chat(msg)
        print(f"🤖 Bot: {response}")
        print("\n" + "="*60 + "\n")