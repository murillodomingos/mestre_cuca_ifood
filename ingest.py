import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os
import ast

def ingest_recipes():
    print("Loading dataset...")
    try:
        df = pd.read_csv('data/RAW_recipes.csv')
    except FileNotFoundError:
        print("Error: data/RAW_recipes.csv not found.")
        return

    # Sample for MVP - 1000 recipes
    df = df.head(1000).fillna('')
    
    print("Initializing ChromaDB...")
    # Ensure db_files directory exists
    os.makedirs("db_files", exist_ok=True)
    
    client = chromadb.PersistentClient(path="db_files")
        
    collection = client.get_or_create_collection(name="recipes")
    
    print("Initializing Embedding Model...")
    # Using a small, fast model
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    
    print("Generating embeddings and adding to ChromaDB...")
    
    ids = [str(x) for x in df['id'].tolist()]
    
    # Create a rich document representation for search
    documents = []
    for _, row in df.iterrows():
        # Parse ingredients list if it's a string
        ingredients = row['ingredients']
        if isinstance(ingredients, str):
            try:
                ingredients_list = ast.literal_eval(ingredients)
                ingredients_str = ", ".join(ingredients_list)
            except:
                ingredients_str = ingredients
        else:
            ingredients_str = str(ingredients)
            
        doc = f"Recipe: {row['name']}\nDescription: {row['description']}\nIngredients: {ingredients_str}"
        documents.append(doc)
    
    metadatas = []
    for _, row in df.iterrows():
        meta = {
            'name': str(row['name']),
            'minutes': int(row['minutes']) if str(row['minutes']).isdigit() else 0,
            'n_ingredients': int(row['n_ingredients']) if str(row['n_ingredients']).isdigit() else 0
        }
        metadatas.append(meta)
    
    # Batch processing to avoid memory issues
    batch_size = 100
    total_batches = len(ids) // batch_size + (1 if len(ids) % batch_size != 0 else 0)
    
    for i in range(0, len(ids), batch_size):
        print(f"Processing batch {i//batch_size + 1}/{total_batches}...")
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        
        batch_embeddings = model.encode(batch_docs).tolist()
        
        collection.add(
            documents=batch_docs,
            embeddings=batch_embeddings,
            metadatas=batch_metas,
            ids=batch_ids
        )
    
    print(f"Successfully ingested {len(ids)} recipes.")

if __name__ == "__main__":
    ingest_recipes()
