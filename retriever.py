
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
def retrieve_articles(penalty_type: str, race_conditions: str, k: int = 12):
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

   # Aggregazione articoli
    full_articles = aggregate_full_articles(retrieved_chunks, full_regulation)

    # === Forza inclusione Art. 26 se si parla di unsafe, safety, pit entry, red flag ===
    trigger_text = (penalty_type + " " + race_conditions).lower()
    if any(term in trigger_text for term in ["unsafe", "safety", "pit entry", "red flag"]):
        if not any(article["title"].startswith("26)") for article in full_articles):
            art26_chunks = [entry for entry in full_regulation if entry["title"].startswith("26)")]
            if art26_chunks:
                art26_combined = " ".join(chunk["content"] for chunk in art26_chunks)
                full_articles.append({
                    "title": art26_chunks[0]["title"],
                    "content": art26_combined
                })

    return full_articles
