import faiss
import numpy as np
import pickle

# Caricamento dell'indice FAISS e metadati
def load_faiss_index():
    index_path = "faiss_fia2025.index"
    index = faiss.read_index(index_path)
    metadata_path = "faiss_fia2025_structured_metadata.pkl"
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

# Funzione per fare query su FAISS e recuperare gli articoli
def retrieve_articles(penalty_type, lap, turn, driver, race_conditions):
    index, metadata = load_faiss_index()
    
    # Crea un "embedding" basato sulla penalità e il contesto
    query = f"{penalty_type} giro {lap}, curva {turn}, pilota {driver}, condizioni {race_conditions}"
    
    # Recupera l'embedding della query
    query_vector = model.encode([query])[0].reshape(1, -1).astype("float32")
    
    # Esegui la query su FAISS per ottenere gli articoli più simili
    D, I = index.search(query_vector, 5)  # Recupera i top 5 articoli
    relevant_articles = [metadata[i]["content"] for i in I[0]]
    
    return relevant_articles