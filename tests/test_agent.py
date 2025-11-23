import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.engine import MestreCucaAgent
from dotenv import load_dotenv

# Force CPU for testing to avoid CUDA errors
os.environ["CUDA_VISIBLE_DEVICES"] = ""

def test_agent():
    print("Loading environment...")
    load_dotenv()
    
    print("Initializing Agent...")
    try:
        agent = MestreCucaAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    print("\n--- Test 1: Plan Recipes (RAG) ---")
    query = "chicken and corn"
    print(f"Query: {query}")
    recipes = agent.plan_recipes(query)
    
    if recipes:
        print(f"Found {len(recipes)} recipes.")
        for r in recipes:
            print(f"- {r['name']} (Score: {r['score']:.4f})")
            first_recipe_id = recipes[0]['id']
    else:
        print("No recipes found.")
        return

    print("\n--- Test 2: Generate Shopping List (LLM + Tools) ---")
    if 'first_recipe_id' in locals():
        print(f"Generating list for recipe ID: {first_recipe_id}")
        result = agent.generate_shopping_list(first_recipe_id)
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Recipe: {result['recipe_name']}")
            print(f"Total Price: ${result['total_price']:.2f}")
            print("Shopping List Items:")
            for item in result['shopping_list']:
                status = "✅ Found" if item['found'] else "❌ Not Found"
                print(f"  {status}: {item['ingredient']} -> {item['product']} (${item['price']})")

if __name__ == "__main__":
    test_agent()
