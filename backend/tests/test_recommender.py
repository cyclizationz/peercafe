from utils.restaurant_recommender import RestaurantRecommender

def main():
    # Create recommender
    recommender = RestaurantRecommender()

# Test different queries
    queries = [
        "Find me a cheap Mexican place",
        "I want fancy Italian food for a date night",
        "Looking for vegan-friendly restaurants downtown",
        "Show me highly rated Japanese restaurants",
        "I need a place with outdoor seating and good vegetarian options"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print('=' * 60)

        result = recommender.get_recommendations(query)
        print(result)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()