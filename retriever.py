
import faiss
import numpy as np
import pickle
import json
from sentence_transformers import SentenceTransformer

# === MODELLO EMBEDDING ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === CARICAMENTO INDICE E METADATI ===
def load_faiss_index():
    index = faiss.read_index("faiss_fia2025.index")
    with open("faiss_fia2025_structured_metadata.pkl", "rb") as f:
        metadata = pickle.load(f)
    return index, metadata

# === CARICAMENTO REGOLAMENTO COMPLETO ===
def load_full_regulation():
    with open("FIA_2025_Sporting_Regulations_Structured.json", "r", encoding="utf-8") as f:
        return json.load(f)

# === AGGREGAZIONE CHUNKS ADIACENTI AL MATCH ===
def aggregate_surrounding_chunks(selected_indices, json_data, window=1):
    seen_ids = set()
    selected_chunks = []

    for idx in selected_indices:
        for offset in range(-window, window + 1):
            adj_idx = idx + offset
            if 0 <= adj_idx < len(json_data):
                chunk = json_data[adj_idx]
                if chunk["id"] not in seen_ids:
                    selected_chunks.append({
                        "title": chunk["title"],
                        "content": chunk["content"]
                    })
                    seen_ids.add(chunk["id"])
    return selected_chunks

# === FUNZIONE PRINCIPALE DI RETRIEVAL ===
def retrieve_articles(penalty_type: str, race_conditions: str, k: int = 12):
    index, metadata = load_faiss_index()
    full_regulation = load_full_regulation()

    # Costruzione query
    query = f"Penalty: {penalty_type}. Context: {race_conditions}."
    query_embedding = model.encode([query])[0].reshape(1, -1).astype("float32")

    # Retrieval top-k chunk
    D, I = index.search(query_embedding, k)
    selected_indices = [idx for idx in I[0] if 0 <= idx < len(metadata)]

    # Aggrega ±1 chunk attorno ai risultati FAISS
    full_articles = aggregate_surrounding_chunks(selected_indices, full_regulation, window=1)

    # Forza inclusione Art. 26 se necessario
    trigger_text = (penalty_type + " " + race_conditions).lower()
    if any(term in trigger_text for term in ["unsafe", "safety", "pit entry", "red flag"]):
        if not any(article["title"].startswith("26)") for article in full_articles):
            art26_chunks = [entry for entry in full_regulation if entry["title"].startswith("26)")]
            if art26_chunks:
                full_articles.extend(art26_chunks[:3])  # massimo 3 chunk

    # Forza inclusione Art. 54 sempre
    if not any(article["title"].startswith("54)") for article in full_articles):
        art54_chunks = [entry for entry in full_regulation if entry["title"].startswith("54)")]
        if art54_chunks:
            full_articles.extend(art54_chunks[:3])  # massimo 3 chunk

    # Limita il numero massimo di articoli restituiti
    if len(full_articles) > 10:
        full_articles = full_articles[:10]

    return full_articles