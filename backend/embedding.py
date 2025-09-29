from dotenv import load_dotenv
import os
import numpy as np
# from sentence_transformers import SentenceTransformer
from mistralai import Mistral

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = None

def get_mistral_client():
    global client
    if client is None:
        api_key = os.getenv('MISTRAL_API_KEY')
        
        # Vérifier que la clé existe
        if not api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas définie dans les variables d'environnement")
        
        print(f"Clé API chargée : {api_key[:10]}...")
        
        client = Mistral(api_key=api_key)
    return client

def extract_text_from_content(content):
    """
    Extrait tout le texte d'une structure content complexe
    """
    texts = []
    
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        for item in content:
            texts.append(extract_text_from_content(item))
    
    elif isinstance(content, dict):
        # Extraire le texte des clés pertinentes
        if 'text' in content:
            texts.append(content['text'])
        
        if 'heading' in content and isinstance(content['heading'], dict):
            if 'text' in content['heading']:
                texts.append(content['heading']['text'])
        
        if 'content' in content:
            texts.append(extract_text_from_content(content['content']))
        
        if 'items' in content:
            texts.append(extract_text_from_content(content['items']))
    
    # Joindre tous les textes en filtrant les vides
    result = ' '.join(filter(None, texts))
    return result.strip()

def embed_query(query):
    client = get_mistral_client()
    
    # Extraire le texte si c'est une structure complexe
    if isinstance(query, (dict, list)):
        query = extract_text_from_content(query)
    
    # S'assurer qu'on a du texte
    if not query or not isinstance(query, str):
        return []
    
    max_chars = 20000
    
    # Si le texte est court, traitement normal
    if len(query) <= max_chars:
        response = client.embeddings.create(
            model="mistral-embed",
            inputs=[query]
        )
        return response.data[0].embedding
    
    # Sinon, découper en chunks
    chunks = []
    for i in range(0, len(query), max_chars):
        chunks.append(query[i:i + max_chars])
    
    print(f"📄 Document découpé en {len(chunks)} chunks")
    
    # Obtenir les embeddings de chaque chunk
    all_embeddings = []
    for chunk in chunks:
        response = client.embeddings.create(
            model="mistral-embed",
            inputs=[chunk]
        )
        all_embeddings.append(response.data[0].embedding)
    
    # Moyenner les embeddings
    import numpy as np
    avg_embedding = np.mean(all_embeddings, axis=0).tolist()
    
    return avg_embedding

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    return dot_product / (norm_vec1 * norm_vec2)

def manathan(vec1, vec2):
    return np.sum(np.abs(np.array(vec1) - np.array(vec2)))

def euclidian(vec1, vec2):
    return np.sqrt(np.sum((np.array(vec1) - np.array(vec2))**2))


def select_top_n_similar_documents(query, documents, n=3,metric='cosine'):
    #metric can be 'cosine', 'manathan', 'euclidian'
    query_embedding = embed_query(query)
    if metric == 'cosine':
        similarities = [cosine_similarity(query_embedding, doc["embedding"]) for doc in documents]
        top_n_indices = np.argsort(similarities)[-n:]
    elif metric == 'manathan':
        distances = [manathan(query_embedding, doc["embedding"]) for doc in documents]
        top_n_indices = np.argsort(distances)[:n]
    elif metric == 'euclidian':
        distances = [euclidian(query_embedding, doc["embedding"]) for doc in documents]
        top_n_indices = np.argsort(distances)[:n]
    else:
        raise ValueError("Unsupported metric. Choose from 'cosine', 'manathan', or 'euclidian'.")
    top_n_documents = [documents[i] for i in top_n_indices]
    return top_n_documents
