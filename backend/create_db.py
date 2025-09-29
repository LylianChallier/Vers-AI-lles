from backend.embedding import embed_query, extract_text_from_content
import json
import os


def create_documents():
    file = 'data/versailles_semantic_complete_20250813_204248.jsonl'
    documents = []
    i = 0
    # Lecture et parsing du fichier
    with open(file, 'r', encoding='utf-8') as f:
        for ligne in f:
            i += 1
            if i > 50:
                break
            ligne = ligne.strip()
            if not ligne:  # Ignorer les lignes vides
                continue
            try:
                # objet est déjà un dict après json.loads(ligne)
                # Pas besoin de parser deux fois
                doc = json.loads(ligne)
                documents.append(doc)
            except json.JSONDecodeError as e:
                print(f"Erreur de décodage JSON : {e}")
                continue
    
    # Embedding des documents
    print(f"Embedding de {len(documents)} documents...")
    for i, document in enumerate(documents):
        # Extraire le contenu textuel
        content = document.get("content", [])
        
        # Extraire tout le texte
        text_content = extract_text_from_content(content)
        
        # Ajouter aussi le titre et l'URL pour plus de contexte
        full_text = f"URL: {document.get('url', '')}\nTitre: {document.get('title', '')}\n\n{text_content}"
        
        document["embedding"] = embed_query(full_text)
        
        if (i + 1) % 10 == 0:  # Afficher tous les 10 car l'API peut être lente
            print(f"  {i + 1}/{len(documents)} documents traités")
    
    return documents

documents = []
if os.getenv("BUILD_RAG_ON_START", "0") == "1":
    documents = create_documents()

