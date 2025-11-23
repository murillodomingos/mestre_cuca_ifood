import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Global variables to cache resources
_chroma_client = None
_embedding_model = None
_market_df = None
_market_embeddings = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="db_files")
    return _chroma_client

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    return _embedding_model

def get_market_df():
    global _market_df
    if _market_df is None:
        try:
            _market_df = pd.read_csv('data/Grocery_Inventory_and_Sales_Dataset.csv')
            # Clean up price column (remove $ and whitespace)
            if 'Unit_Price' in _market_df.columns:
                _market_df['Unit_Price'] = _market_df['Unit_Price'].astype(str).str.replace('$', '', regex=False).str.strip()
                _market_df['Unit_Price'] = pd.to_numeric(_market_df['Unit_Price'], errors='coerce')
        except Exception as e:
            print(f"Error loading market data: {e}")
            _market_df = pd.DataFrame()
    return _market_df

def get_market_embeddings():
    global _market_embeddings
    df = get_market_df()
    if _market_embeddings is None and not df.empty:
        model = get_embedding_model()
        if _market_embeddings is None:
            # print("Computing market embeddings (this happens once)...")
            _market_embeddings = model.encode(df['Product_Name'].tolist())
    return _market_embeddings

def find_recipes_rag(query: str, n_results: int = 3):
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="recipes")
    except:
        return []

    model = get_embedding_model()
    
    query_embedding = model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # Format results
    formatted_results = []
    if results['ids']:
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'name': results['metadatas'][0][i]['name'],
                'description': results['documents'][0][i], # This contains the full text including ingredients
                'score': results['distances'][0][i] if 'distances' in results else 0
            })
            
    return formatted_results

def get_recipe_details(recipe_id: str):
    # In this MVP, the details are already in the RAG document.
    # But if we needed to fetch more specific structured data, we would do it here.
    # For now, we can just retrieve the document from Chroma by ID.
    client = get_chroma_client()
    try:
        collection = client.get_collection(name="recipes")
    except:
        return None
    
    result = collection.get(ids=[recipe_id])
    
    if result['documents']:
        return {
            'id': recipe_id,
            'name': result['metadatas'][0]['name'],
            'details': result['documents'][0]
        }
    return None

def search_mercado(item_name: str):
    df = get_market_df()
    embeddings = get_market_embeddings()
    
    if df.empty or embeddings is None:
        return None
        
    model = get_embedding_model()
    query_embedding = model.encode([item_name])
    
    # Calculate similarities
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Find best match
    best_idx = np.argmax(similarities)
    best_score = similarities[best_idx]
    
    # Threshold for match
    # Lowered to 0.65 to allow "Ground Beef" (0.79) vs "beef"
    # We will use LLM verification in the engine for ambiguous cases
    if best_score > 0.65:
        best_match = df.iloc[best_idx]
        return {
            'product_name': best_match['Product_Name'],
            'price': best_match['Unit_Price'],
            'stock': best_match['Stock_Quantity'],
            'score': float(best_score)
        }
    
    return None
