# restaurant_recommender.py
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

class RestaurantRecommender:
    def __init__(self):
        """Initialize Supabase and OpenAI clients"""
        load_dotenv()
        self.supabase = create_supabase_client()
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def search_restaurants(self, **kwargs):
        """
        Search restaurants in Supabase based on filters
        
        Args:
            cuisine: Type of cuisine (e.g., 'Italian', 'Japanese')
            price_range: '$', '$$', '$$$', or '$$$$'
            location: Location or neighborhood (searches in address field)
            vegetarian_friendly: Boolean - searches in description and menu items
            vegan_friendly: Boolean - searches in description and menu items
            gluten_free_options: Boolean - searches in description and menu items
            outdoor_seating: Boolean - searches in description
            takes_reservations: Boolean - searches in description
            min_rating: Minimum rating (0-5)
        """
        # Start with base query
        query = self.supabase.table("restaurants").select("*")
        
        # Apply filters dynamically
        if kwargs.get('cuisine'):
            query = query.ilike("cuisine_type", f"%{kwargs['cuisine']}%")
        
        if kwargs.get('price_range'):
            query = query.eq("price_range", kwargs['price_range'])
        
        if kwargs.get('location'):
            query = query.ilike("address", f"%{kwargs['location']}%")
        
        # Search in description field for dietary preferences and amenities
        description_filters = []
        if kwargs.get('vegetarian_friendly'):
            description_filters.append(('vegetarian', 'vegetarian_friendly'))
        if kwargs.get('vegan_friendly'):
            description_filters.append(('vegan', 'vegan_friendly'))
        if kwargs.get('gluten_free_options'):
            description_filters.append(('gluten-free', 'gluten_free_options'))
            description_filters.append(('gluten free', 'gluten_free_options'))
        if kwargs.get('outdoor_seating'):
            description_filters.append(('outdoor', 'outdoor_seating'))
        if kwargs.get('takes_reservations'):
            description_filters.append(('reservation', 'takes_reservations'))
        
        # Apply description filters (OR logic - any match)
        if description_filters:
            # Use OR logic: restaurant description must contain at least one keyword
            # Note: Supabase PostgREST doesn't support complex OR directly, so we'll filter after
            pass  # Will filter in post-processing
        
        if kwargs.get('min_rating'):
            query = query.gte("rating", kwargs['min_rating'])
        
        # Execute query with ordering and limit
        response = query.order("rating", desc=True).limit(20).execute()  # Get more to filter
        
        restaurants = response.data if response.data else []
        
        # Post-process: filter by description keywords
        if description_filters and restaurants:
            filtered_restaurants = []
            search_keywords = [keyword for keyword, _ in description_filters]
            
            for restaurant in restaurants:
                description = (restaurant.get('description') or '').lower()
                # Check if description contains any of the search keywords
                if any(keyword.lower() in description for keyword in search_keywords):
                    filtered_restaurants.append(restaurant)
            
            restaurants = filtered_restaurants[:10]  # Limit to 10 after filtering
        else:
            restaurants = restaurants[:10]
        
        return restaurants
    
    def get_recommendations(self, user_query):
        """
        Get AI-powered restaurant recommendations
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            String with personalized recommendations
        """
        # Define the function schema for OpenAI
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_restaurants",
                    "description": "Search the restaurant database in Supabase for restaurants matching user criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cuisine": {
                                "type": "string",
                                "description": "Type of cuisine (e.g., Italian, Japanese, Indian, Mexican, American, Chinese, Thai, Vegetarian)"
                            },
                            "price_range": {
                                "type": "string",
                                "enum": ["$", "$$", "$$$", "$$$$"],
                                "description": "Price range: $ (cheap), $$ (moderate), $$$ (expensive), $$$$ (very expensive)"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location, neighborhood, or area to search in restaurant addresses (e.g., Downtown, Midtown, West End, Raleigh, NC)"
                            },
                            "vegetarian_friendly": {
                                "type": "boolean",
                                "description": "Search for restaurants with vegetarian options (searches in restaurant description)"
                            },
                            "vegan_friendly": {
                                "type": "boolean",
                                "description": "Search for restaurants with vegan options (searches in restaurant description)"
                            },
                            "gluten_free_options": {
                                "type": "boolean",
                                "description": "Search for restaurants with gluten-free options (searches in restaurant description)"
                            },
                            "outdoor_seating": {
                                "type": "boolean",
                                "description": "Search for restaurants with outdoor seating (searches in restaurant description)"
                            },
                            "takes_reservations": {
                                "type": "boolean",
                                "description": "Search for restaurants that accept reservations (searches in restaurant description)"
                            },
                            "min_rating": {
                                "type": "number",
                                "description": "Minimum rating (0.0 to 5.0)",
                                "minimum": 0,
                                "maximum": 5
                            }
                        }
                    }
                }
            }
        ]
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": """You are a helpful restaurant recommendation assistant. 
                You have access to a restaurant database. When a user asks for restaurant 
                recommendations, extract their preferences and search the database. 
                Then provide personalized, detailed recommendations based on the results."""
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        # First API call - OpenAI decides if it needs to search
        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if OpenAI wants to call the search function
        if message.tool_calls:
            # Extract the function arguments
            tool_call = message.tool_calls[0]
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"🔍 Searching database with filters: {function_args}")
            
            # Search Supabase using the extracted parameters
            restaurants = self.search_restaurants(**function_args)
            
            print(f"✅ Found {len(restaurants)} restaurants")
            
            # Add function call and results to conversation
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(restaurants, indent=2)
            })
            
            # Get final recommendation from OpenAI
            final_response = self.openai.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            return final_response.choices[0].message.content
        else:
            # No function call needed
            return message.content


# Example usage
if __name__ == "__main__":
    recommender = RestaurantRecommender()
    
    # Test query
    result = recommender.get_recommendations(
        "I want a romantic Italian restaurant downtown with vegetarian options"
    )
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    print(result)