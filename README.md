# 🤖 MestreCuca iFood Agent

**Portfolio project developed as a candidate solution for the iFood GenAI Internship Program.**

---

## 📍 Demo & Video

* **Test the Agent live:** `https://mestre-cuca-ifood.streamlit.app/`
* **Watch a sample video:** 
![Demo](assets/demo-mestre-cuca.gif)

---

## 1. The Problem: From "What to eat?" to "Ready Cart"

Choosing a recipe, listing the ingredients, and finding products at the market is a manual and fragmented process. This project proposes a unified solution: a **conversational AI agent** that guides the user from initial inspiration to a simulated shopping list at iFood Mercado.

This project was designed to directly address the challenges proposed by the iFood GenAI position, focusing on:

* **Creating Intelligent Agents:** The core of the project is an agent that plans and executes tasks.
* **Applying LLMs to Products:** Uses LLMs to understand intent, extract entities, and generate responses.
* **LLMOps (RAG):** Implements a *Retrieval-Augmented Generation* (RAG) pipeline to search recipes in a knowledge base, instead of relying on fragile scraping.

## 2. The Flow: How Does It Work?

The agent operates in a multi-step conversational flow, managing conversation state:

1.  **User (Input):** "I'm craving something with chicken and corn."
2.  **Agent (Planning - RAG):** The agent uses **RAG** to perform a semantic search in a database of 10,000+ recipes and finds the 3 most relevant options.
3.  **Agent (Response):** "Great idea! I found 3 options:
    1.  Chicken Fricassee
    2.  Chicken and Corn Pie
    3.  Corn Soup with Shredded Chicken

    Which one do you prefer?"
4.  **User (Choice):** The user clicks on the desired option.
5.  **Agent (Execution - Tools):**
    * **Tool 1 `get_recipe_details`:** Fetches the exact ingredients and quantities of the chosen recipe.
    * **Tool 2 `extract_shopping_list` (LLM):** An LLM "cleans" the ingredient list (e.g., "salt to taste" is removed; "500g of chicken breast" becomes "chicken breast").
    * **Tool 3 `search_mercado`:** For each "cleaned" item, searches for the price in a simulated iFood Mercado datastore.
6.  **Agent (Final Output):** "Perfect. For the Chicken Fricassee, I simulated your basket at 'iFood Mercado':"
    * Chicken Breast (500g): R$ 18.90 (Market X)
    * Green Corn (can): R$ 4.50 (Market Y)
    * ...etc.

## 3. Solution Architecture

```mermaid
graph TD
    subgraph "Interface (Streamlit)"
        %% CORREÇÃO AQUI: Aspas externas duplas, internas simples
        A["User: 'I want lasagna'"] --> B{MestreCuca Agent}
    end

    subgraph "Agent Logic (Python/LangChain)"
        B --> C["1. find_recipes_rag(query)"]
        C --> D[("ChromaDB (10k Recipes)")]
        D --> B
        B --> E["User chooses: 'Bolognese Lasagna'"]
        E --> F["2. get_recipe_details(name)"]
        F --> G[("Dataset (CSV)")]
        G --> H["3. extract_shopping_list(ingredients)"]
        H --> I[LLM (Gemini/OpenAI)]
        I --> J["4. search_mercado(item)"]
        J --> K[("Grocery Dataset (CSV)")]
        K --> L[Final Shopping List]
    end

    %% Conexão final
    L --> A
    
    %% Estilização (Opcional: Para destacar o Knowledge Base sem quebrar o fluxo)
    classDef database fill:#f9f,stroke:#333,stroke-width:2px;
    class D,G,K database;
```

## 4. Technology Stack

* **Interface (UI):** Streamlit
* **Agent Orchestration:** LangChain (or pure Python logic)
* **AI Model:** Google Gemini (or OpenAI GPT)
* **Vector Database (RAG):** ChromaDB
* **Embeddings Model (RAG):** all-MiniLM-L6-v2 (Sentence Transformers)
* **Data Engineering:** Pandas
* **Deployment:** Streamlit Community Cloud

## 5. How to Run Locally

### Prerequisites:

* Python 3.9+
* Kaggle account (to download the dataset)
* An LLM API Key (Gemini or OpenAI), saved in a `.env` file as `GOOGLE_API_KEY` or `OPENAI_API_KEY`.

### Steps:

1. **Clone the repository:**

```bash
git clone https://github.com/[YOUR_USERNAME]/agente-mestrecuca-ifood.git
cd agente-mestrecuca-ifood
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Download the Datasets:**

   * **Recipes:** Download `RAW_recipes.csv` from [Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli98/food-com-recipes-and-user-interactions) and save it to `data/RAW_recipes.csv`.
   * **Market:** The file `data/Grocery_Inventory_and_Sales_Dataset.csv` is included in the repo.

4. **Build the Vector Database (RAG):**

   *Note: The repository comes with a pre-built database in `db_files/`. You can skip this step unless you want to rebuild it from scratch.*

   If you need to rebuild:
   ```bash
   python ingest.py
   ```

5. **Run the Application:**

```bash
streamlit run app.py
```

## 6. Next Steps (Roadmap)

- [ ] **Real Connection:** Replace the simulated `mercado.json` with a real connection (if/when available) to the iFood Mercado catalog.
- [ ] **Additional Filters:** Allow the user to filter recipes by criteria (e.g., "vegetarian", "gluten-free", "under 30 min").
- [ ] **Long-Term Memory:** Save user conversation history (in Firestore, for example) to learn their preferences over time.