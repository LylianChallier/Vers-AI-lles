from embedding import embed_query, extract_text_from_content
import json

def create_documents(file):
    documents = []
    # Lecture et parsing du fichier
    with open(file, 'r', encoding='utf-8') as f:
        try:
            # Charger tout le fichier JSON d'un coup
            data = json.load(f)

            # Vérifier si c'est un objet avec une clé "conseils"
            if isinstance(data, dict) and "conseils" in data:
                # Traiter chaque conseil comme un document séparé
                for conseil in data["conseils"]:
                    documents.append(conseil)
            # Sinon, si c'est déjà une liste de documents
            elif isinstance(data, list):
                documents = data
            # Sinon, traiter comme un seul document
            else:
                documents.append(data)

        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON du fichier complet : {e}")
            # Fallback : essayer de lire ligne par ligne (format JSONL)
            f.seek(0)  # Retourner au début du fichier
            for ligne in f:
                ligne = ligne.strip()
                if not ligne:  # Ignorer les lignes vides
                    continue
                try:
                    doc = json.loads(ligne)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    print(f"Erreur de décodage JSON ligne : {e}")
                    continue
    
    # Embedding des documents
    print(f"Embedding de {len(documents)} documents...")
    for i, document in enumerate(documents):
        # Extraire le contenu textuel selon la structure du document
        if "texte" in document:
            # Structure des conseils : {"id": "...", "texte": "..."}
            text_content = document["texte"]
            full_text = f"ID: {document.get('id', '')}\n{text_content}"
        elif "content" in document:
            # Structure originale avec content
            content = document.get("content", [])
            text_content = extract_text_from_content(content)
            full_text = f"URL: {document.get('url', '')}\nTitre: {document.get('title', '')}\n\n{text_content}"
        else:
            # Fallback : convertir tout le document en texte
            full_text = json.dumps(document, ensure_ascii=False)

        document["embedding"] = embed_query(full_text)

        if (i + 1) % 10 == 0:  # Afficher tous les 10 car l'API peut être lente
            print(f"  {i + 1}/{len(documents)} documents traités")
    
    return documents

def save_documents(documents, output_file=None):
    """
    Sauvegarde les documents avec leurs embeddings dans un fichier JSON (liste)
    """
    if output_file is None:
        output_file = f'data/documents_embedded.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(documents)} documents sauvegardés dans {output_file}")
    return output_file

# Utilisation
if __name__ == "__main__":
    documents = create_documents("data/tips.json")
    save_documents(documents, "data/tips_embedded.json")
