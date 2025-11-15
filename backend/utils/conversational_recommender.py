# conversational_recommender.py
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq  

# Ensure backend package directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = str(SCRIPT_DIR.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.supabase_db import create_supabase_client


class ConversationalRestaurantBot:
    def __init__(self):
        """Initialize Groq and conversation history"""
        load_dotenv()
        self.supabase = create_supabase_client()

        # Initialize Groq client (FREE)
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Must be a function-calling model
        self.model = "llama-3.1-8b-instant"

        # Conversation history
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are a friendly restaurant recommendation assistant.
                Ask clarifying questions when needed. You can query a restaurant database
                using the search_restaurants function. Be conversational and helpful."""
            }
        ]

    def search_restaurants(self, **kwargs):
        """Search restaurants in Supabase"""
        query = self.supabase.table("restaurants").select("*")
        description_filters = []

        for key, value in kwargs.items():
            if not value:
                continue

            if key == "cuisine":
                query = query.ilike("cuisine_type", f"%{value}%")
            elif key == "price_range":
                query = query.eq("price_range", value)
            elif key == "location":
                query = query.ilike("address", f"%{value}%")
            elif key == "vegetarian_friendly":
                description_filters.append("vegetarian")
            elif key == "vegan_friendly":
                description_filters.append("vegan")
            elif key == "gluten_free_options":
                description_filters.extend(["gluten-free", "gluten free"])
            elif key == "outdoor_seating":
                description_filters.append("outdoor")
            elif key == "takes_reservations":
                description_filters.append("reservation")
            elif key == "min_rating":
                query = query.gte("rating", value)

        response = query.order("rating", desc=True).limit(20).execute()
        restaurants = response.data or []

        # Post-filter by description keywords
        if description_filters:
            filtered = []
            for r in restaurants:
                desc = (r.get("description") or "").lower()
                if any(keyword in desc for keyword in description_filters):
                    filtered.append(r)
            restaurants = filtered[:5]
        else:
            restaurants = restaurants[:5]

        return restaurants

    def chat(self, user_message):
        """Main chat method"""
        self.conversation_history.append({"role": "user", "content": user_message})

        tools = [{
            "type": "function",
            "function": {
                "name": "search_restaurants",
                "description": "Search restaurant database",
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

        # --- First Groq call ---
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # --- If Groq triggers function calling ---
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)

            restaurants = self.search_restaurants(**args)

            # Add tool result back into conversation
            self.conversation_history.append(message)
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(restaurants)
            })

            # --- Second Groq call: final answer ---
            final = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history
            )

            assistant_message = final.choices[0].message.content

        else:
            # No tool call — return direct answer
            assistant_message = message.content

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        """Reset conversation history"""
        self.conversation_history = self.conversation_history[:1]


# Example usage
if __name__ == "__main__":
    bot = ConversationalRestaurantBot()

    print("🤖 Bot ready! What kind of food are you craving?\n")

    demo_msgs = [
        "I'm looking for dinner",
        "I want Italian food",
        "Downtown preferably",
        "Something with outdoor seating",
        "What's the highest rated option?"
    ]

    for msg in demo_msgs:
        print("👤:", msg)
        print("🤖:", bot.chat(msg))
        print()
