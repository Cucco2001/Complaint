
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

# === AGGREGAZIONE ARTICOLI COMPLETI (FILTRATI) ===
def aggregate_full_articles(retrieved_chunks, json_data):
    seen_titles = set()
    full_articles = []

    for res in retrieved_chunks:
        title = res['title'].strip()

        # Filtra titoli malformati o sospetti
        if title and len(title) > 4 and title[0].isdigit() and ")" in title:
            if title not in seen_titles:
                combined = " ".join(
                    entry["content"] for entry in json_data if entry["title"] == title
                )
                full_articles.append({
                    "title": title,
                    "content": combined
                })
                seen_titles.add(title)

    return full_articles

# === FUNZIONE PRINCIPALE DI RETRIEVAL ===
def retrieve_articles(penalty_type: str, race_conditions: str, k: int = 7):
    index, metadata = load_faiss_index()
    full_regulation = load_full_regulation()

    # Costruzione query in inglese
    query = f"Penalty: {penalty_type}. Context: {race_conditions}."
    query_embedding = model.encode([query])[0].reshape(1, -1).astype("float32")

    # Retrieval top-k chunk
    D, I = index.search(query_embedding, k)
    retrieved_chunks = []
    for idx in I[0]:
        if 0 <= idx < len(metadata):
            retrieved_chunks.append({
                "title": metadata[idx]["title"],
                "content": metadata[idx]["content"]
            })

    # Aggregazione degli articoli completi filtrando titoli inconsistenti
    full_articles = aggregate_full_articles(retrieved_chunks, full_regulation)
    return full_articles