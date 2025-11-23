import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.tools import find_recipes_rag, get_recipe_details, search_mercado
from dotenv import load_dotenv
import json

load_dotenv()

class MestreCucaAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        # Fallback or error if key is missing, but for MVP we assume it's there or handled by UI
        if not api_key:
            print("Warning: GEMINI_API_KEY not found.")
            self.llm = None
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                google_api_key=api_key,
                transport="rest"
            )

    def plan_recipes(self, user_input):
        """
        Search for recipes based on user input.
        """
        recipes = find_recipes_rag(user_input)
        return recipes

    def generate_shopping_list(self, recipe_id):
        """
        Get recipe details, extract ingredients, and search in market.
        """
        recipe = get_recipe_details(recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}
            
        if not self.llm:
            return {"error": "LLM not initialized. Check API Key."}

        # Extract ingredients using LLM
        ingredients_text = recipe['details'] # This contains the full text
        
        # Direct invocation to avoid chain issues
        messages = [
            ("system", "You are a helpful cooking assistant. Extract the list of ingredients from the following recipe text. Return ONLY a JSON array of strings, where each string is a clean ingredient name (e.g., \"chicken breast\", \"salt\", \"onion\"). Remove quantities and optional instructions."),
            ("human", f"Recipe Text:\n{ingredients_text}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            response_content = response.content
        except Exception as e:
            return {"error": f"LLM generation failed: {e}"}
        
        try:
            # Clean up markdown code blocks if present
            cleaned_response = response_content.replace("```json", "").replace("```", "").strip()
            ingredients_list = json.loads(cleaned_response)
        except:
            # Fallback if JSON parsing fails
            ingredients_list = [line.strip() for line in response_content.split('\n') if line.strip()]
            
        # Search market for each ingredient
        shopping_list = []
        total_price = 0
        
        for item in ingredients_list:
            market_item = search_mercado(item)
            
            # Verify match with LLM if score is ambiguous (e.g. < 0.85)
            # "Egg (Chicken)" vs "chicken" has score ~0.76 -> needs verification
            # "Onion" vs "Onion" has score 1.0 -> auto accept
            if market_item:
                is_valid_match = True
                if market_item.get('score', 0) < 0.85:
                    try:
                        verify_prompt = f"Is the product '{market_item['product_name']}' a valid purchase for the ingredient '{item}'? Answer ONLY 'YES' or 'NO'."
                        verify_response = self.llm.invoke(verify_prompt).content.strip().upper()
                        if "NO" in verify_response:
                            is_valid_match = False
                    except:
                        pass 

                if is_valid_match:
                    shopping_list.append({
                        "ingredient": item,
                        "found": True,
                        "product": market_item['product_name'],
                        "price": market_item['price']
                    })
                    total_price += market_item['price']
                else:
                     shopping_list.append({
                        "ingredient": item,
                        "found": False,
                        "product": None,
                        "price": 0
                    })
            else:
                shopping_list.append({
                    "ingredient": item,
                    "found": False,
                    "product": None,
                    "price": 0
                })
                
        return {
            "recipe_name": recipe['name'],
            "shopping_list": shopping_list,
            "total_price": total_price
        }
