import streamlit as st
from src.engine import MestreCucaAgent

st.set_page_config(page_title="MestreCuca iFood", page_icon="🍳")

st.title("🍳 MestreCuca iFood Agent")

if "agent" not in st.session_state:
    st.session_state.agent = MestreCucaAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "state" not in st.session_state:
    st.session_state.state = "SEARCH" # SEARCH or SELECT

if "current_recipes" not in st.session_state:
    st.session_state.current_recipes = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Check if we are expecting a selection
        if st.session_state.state == "SELECT" and (prompt.isdigit() or any(r['name'].lower() in prompt.lower() for r in st.session_state.current_recipes)):
            # Handle selection
            selected_recipe = None
            if prompt.isdigit():
                idx = int(prompt) - 1
                if 0 <= idx < len(st.session_state.current_recipes):
                    selected_recipe = st.session_state.current_recipes[idx]
            else:
                # Fuzzy match name
                for r in st.session_state.current_recipes:
                    if r['name'].lower() in prompt.lower():
                        selected_recipe = r
                        break
            
            if selected_recipe:
                st.markdown(f"Great choice! Preparing shopping list for **{selected_recipe['name']}**...")
                result = st.session_state.agent.generate_shopping_list(selected_recipe['id'])
                
                if "error" in result:
                    response = f"Error: {result['error']}"
                    st.markdown(response)
                else:
                    response = f"### Shopping List for {result['recipe_name']}\n\n"
                    for item in result['shopping_list']:
                        if item['found']:
                            response += f"- ✅ **{item['ingredient']}** -> {item['product']} (${item['price']:.2f})\n"
                        else:
                            response += f"- ❌ **{item['ingredient']}** (Not found in market)\n"
                    
                    response += f"\n**Total Estimated Price: ${result['total_price']:.2f}**"
                    st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.state = "SEARCH" # Reset to search
                st.session_state.current_recipes = []
            else:
                response = "I didn't understand which recipe you wanted. Please type the number or name, or ask for something else."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        else:
            # Default: Search for recipes
            st.markdown("Thinking... searching for recipes...")
            recipes = st.session_state.agent.plan_recipes(prompt)
            
            if not recipes:
                response = "I couldn't find any recipes matching your request. Try something else!"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                response = "I found these recipes for you:\n\n"
                for i, recipe in enumerate(recipes):
                    response += f"{i+1}. **{recipe['name']}**\n"
                
                response += "\nWhich one would you like to cook? (Type the number)"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.session_state.current_recipes = recipes
                st.session_state.state = "SELECT"
