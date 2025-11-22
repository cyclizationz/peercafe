# backend/utils/restaurant_recommender.py
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Support both OpenAI and Groq
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Ensure the backend package directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = str(SCRIPT_DIR.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.supabase_db import create_supabase_client  # noqa: E402


class RestaurantRecommender:
    def __init__(self, use_groq=None):
        """
        Initialize Supabase and LLM clients

        Args:
            use_groq: Boolean to force Groq (True) or OpenAI (False).
                     If None, auto-detects based on available API keys.
                     Defaults to Groq if both are available (it's free!)
        """
        load_dotenv()
        self.supabase = create_supabase_client()

        # Determine which LLM provider to use
        if use_groq is None:
            # Auto-detect: prefer Groq if available (it's free!)
            use_groq = bool(os.getenv("GROQ_API_KEY"))

        if use_groq:
            if not GROQ_AVAILABLE:
                raise ImportError("Groq library not installed. Run: pip install groq")
            if not os.getenv("GROQ_API_KEY"):
                raise ValueError(
                    "GROQ_API_KEY not set in environment. "
                    "Get your free key at https://console.groq.com/"
                )

            self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.model = (
                "llama-3.1-8b-instant"  # Reliable, fast, supports function calling
            )
            self.provider = "groq"
            print("🚀 Using Groq API (FREE)")
        else:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "OpenAI library not installed. Run: pip install openai"
                )
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY not set in environment")

            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o-mini"  # Cheaper OpenAI model
            self.provider = "openai"
            print("💰 Using OpenAI API (paid)")

    def search_restaurants(self, **kwargs):
        """
        Search restaurants in Supabase based on filters

        Args:
            cuisine: Type of cuisine (e.g., 'Italian', 'Japanese')
            price_range: '$', '$$', '$$$', or '$$$$'
            location: Location or neighborhood (searches in address field)
            vegetarian_friendly: Boolean - searches in description
            vegan_friendly: Boolean - searches in description
            gluten_free_options: Boolean - searches in description
            outdoor_seating: Boolean - searches in description
            takes_reservations: Boolean - searches in description
            min_rating: Minimum rating (0-5)

        Returns:
            List of restaurant dictionaries matching the criteria
        """
        # Start with base query
        query = self.supabase.table("restaurants").select("*")

        # Apply filters dynamically
        if kwargs.get("cuisine"):
            query = query.ilike("cuisine_type", f"%{kwargs['cuisine']}%")

        if kwargs.get("price_range"):
            query = query.eq("price_range", kwargs["price_range"])

        if kwargs.get("location"):
            query = query.ilike("address", f"%{kwargs['location']}%")

        # Search in description field for dietary preferences and amenities
        description_filters = []
        if kwargs.get("vegetarian_friendly"):
            description_filters.append("vegetarian")
        if kwargs.get("vegan_friendly"):
            description_filters.append("vegan")
        if kwargs.get("gluten_free_options"):
            description_filters.extend(["gluten-free", "gluten free"])
        if kwargs.get("outdoor_seating"):
            description_filters.append("outdoor")
        if kwargs.get("takes_reservations"):
            description_filters.append("reservation")

        if kwargs.get("min_rating"):
            query = query.gte("rating", kwargs["min_rating"])

        # Execute query with ordering and limit
        response = query.order("rating", desc=True).limit(20).execute()

        restaurants = response.data if response.data else []

        # Post-process: filter by description keywords
        if description_filters and restaurants:
            filtered_restaurants = []

            for restaurant in restaurants:
                description = (restaurant.get("description") or "").lower()
                # Check if description contains any of the search keywords
                if any(
                    keyword.lower() in description for keyword in description_filters
                ):
                    filtered_restaurants.append(restaurant)

            restaurants = filtered_restaurants[:10]  # Limit to 10 after filtering
        else:
            restaurants = restaurants[:10]

        return restaurants

    def get_recommendations(self, user_query):
        """
        Get AI-powered restaurant recommendations with robust error handling

        Args:
            user_query: Natural language query from user

        Returns:
            String with personalized recommendations
        """
        # Define the function schema for function calling
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
                                "description": "Type of cuisine (e.g., Italian, Japanese, Indian, Mexican, American, Chinese, Thai, Vegetarian)",
                            },
                            "price_range": {
                                "type": "string",
                                "enum": ["$", "$$", "$$$", "$$$$"],
                                "description": "Price range: $ (cheap), $$ (moderate), $$$ (expensive), $$$$ (very expensive)",
                            },
                            "location": {
                                "type": "string",
                                "description": "Location, neighborhood, or area to search in restaurant addresses (e.g., Downtown, Midtown, West End)",
                            },
                            "vegetarian_friendly": {
                                "type": "boolean",
                                "description": "Search for restaurants with vegetarian options (searches in restaurant description)",
                            },
                            "vegan_friendly": {
                                "type": "boolean",
                                "description": "Search for restaurants with vegan options (searches in restaurant description)",
                            },
                            "gluten_free_options": {
                                "type": "boolean",
                                "description": "Search for restaurants with gluten-free options (searches in restaurant description)",
                            },
                            "outdoor_seating": {
                                "type": "boolean",
                                "description": "Search for restaurants with outdoor seating (searches in restaurant description)",
                            },
                            "takes_reservations": {
                                "type": "boolean",
                                "description": "Search for restaurants that accept reservations (searches in restaurant description)",
                            },
                            "min_rating": {
                                "type": "number",
                                "description": "Minimum rating (0.0 to 5.0)",
                                "minimum": 0,
                                "maximum": 5,
                            },
                        },
                    },
                },
            }
        ]

        # Create messages for the LLM with EXTREMELY strict instructions
        messages = [
            {
                "role": "system",
                "content": """You are a restaurant database query assistant. Your ONLY job is to report what exists in the database.

🚨 ABSOLUTE RULES - BREAKING THESE IS STRICTLY FORBIDDEN:

1. You MUST ONLY mention restaurants that appear in the search_restaurants results
2. You are FORBIDDEN from inventing, creating, or mentioning ANY restaurant names not in the results
3. You MUST use the EXACT name, address, rating, and price from the database - DO NOT modify or embellish
4. If a detail (like outdoor seating) is not in the database result, DO NOT mention it
5. You are NOT creative - you are a data reporter
6. NEVER say things like "try their famous dish" unless that specific dish is in the database
7. If search returns 0 results, say ONLY: "No restaurants found matching those criteria"

Your response format:
- List each restaurant with its exact name from the database
- Include only details that are explicitly in the database results
- Do not add recommendations, suggestions, or fictional details

Remember: You are a database interface, not a creative writer. Accuracy over helpfulness.""",
            },
            {"role": "user", "content": user_query},
        ]

        try:
            # First API call - LLM decides if it needs to search
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice="auto"
            )

            message = response.choices[0].message

            # Check if LLM wants to call the search function
            if message.tool_calls:
                # Extract the function arguments
                tool_call = message.tool_calls[0]

                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    print(
                        f"⚠️  Invalid JSON in function call: {tool_call.function.arguments}"
                    )
                    print(f"⚠️  Error: {e}")
                    # Fallback to direct response without tools
                    return self._fallback_response(messages)

                print(f"🔍 Searching database with filters: {function_args}")

                # Search Supabase using the extracted parameters
                restaurants = self.search_restaurants(**function_args)

                print(f"✅ Found {len(restaurants)} restaurants")
                if restaurants:
                    print(
                        f"📊 Restaurant names: {[r.get('name') for r in restaurants]}"
                    )
                else:
                    print("⚠️  No restaurants found in database!")

                # ✅ VALIDATION: Handle empty results - DON'T send to LLM
                if not restaurants or len(restaurants) == 0:
                    return "No restaurants found matching those criteria. Try adjusting your filters (different cuisine, location, or price range)."

                # Create a strict instruction with the results
                restaurant_names = [r.get("name", "Unknown") for r in restaurants]

                # Add function call and results to conversation with VERY explicit instructions
                messages.append(message)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"""DATABASE SEARCH RESULTS (YOU MUST ONLY USE THESE):

{json.dumps(restaurants, indent=2)}

🚨 CRITICAL REMINDER:
- ONLY mention these {len(restaurants)} restaurants: {', '.join(restaurant_names)}
- Use their EXACT names and details as shown above
- DO NOT invent ANY other restaurants
- DO NOT add details not in the data above
- If you mention a restaurant not in this list, you have failed""",
                    }
                )

                # Get final recommendation from LLM
                final_response = self.client.chat.completions.create(
                    model=self.model, messages=messages
                )

                llm_response = final_response.choices[0].message.content

                # 🛡️ SAFETY CHECK: Verify LLM only mentioned real restaurants
                mentioned_fake = self._check_for_hallucinations(
                    llm_response, restaurant_names
                )
                if mentioned_fake:
                    print(f"⚠️  LLM hallucinated restaurants: {mentioned_fake}")
                    # Return a safe, factual response instead
                    return self._create_safe_response(restaurants)

                return llm_response
            else:
                # No function call needed - direct response
                return message.content

        except Exception as e:
            # Handle any API errors gracefully
            error_msg = str(e)

            if (
                "tool_use_failed" in error_msg
                or "tool call validation failed" in error_msg
            ):
                print(f"⚠️  Function calling failed: {error_msg}")
                # Retry without tools as fallback
                return self._fallback_response(messages)
            else:
                print(f"❌ Unexpected error: {error_msg}")
                raise

    def _check_for_hallucinations(self, response_text, valid_names):
        """
        Check if LLM mentioned restaurants not in the database

        Returns list of fake restaurant names found, or empty list if clean
        """
        # Common fake restaurant name patterns
        fake_indicators = [
            "Golden Lake",
            "Szechuan House",
            "Din Tai Fung",
            "Bella Italia",
            "Mama Mia",
            "The Golden Dragon",
            "Spice Palace",
            "Tokyo Sushi",
            "Le Bistro",
        ]

        found_fakes = []
        response_lower = response_text.lower()

        for fake in fake_indicators:
            if fake.lower() in response_lower and fake not in valid_names:
                found_fakes.append(fake)

        return found_fakes

    def _create_safe_response(self, restaurants):
        """
        Create a factual response directly from database data
        """
        if not restaurants:
            return "No restaurants found matching those criteria."

        response = "Here are the restaurants from our database:\n\n"

        for i, r in enumerate(restaurants, 1):
            name = r.get("name", "Unknown")
            cuisine = r.get("cuisine_type", "N/A")
            price = r.get("price_range", "N/A")
            rating = r.get("rating", "N/A")
            address = r.get("address", "N/A")

            response += f"{i}. **{name}**\n"
            response += f"   - Cuisine: {cuisine}\n"
            response += f"   - Price: {price}\n"
            response += f"   - Rating: {rating}/5\n"
            response += f"   - Location: {address}\n\n"

        return response

    def _fallback_response(self, messages):
        """
        Fallback to direct response without function calling

        Args:
            messages: Conversation messages

        Returns:
            String response from LLM without tool use
        """
        try:
            print("🔄 Retrying without function calling...")
            response = self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Fallback also failed: {e}")
            return "I'm having trouble processing your request right now. Please try rephrasing your query or try again later."


# Example usage
if __name__ == "__main__":
    recommender = RestaurantRecommender()

    # Test query
    result = recommender.get_recommendations(
        "I want a romantic Italian restaurant downtown with vegetarian options"
    )

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print(result)
