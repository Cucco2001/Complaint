
import json
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# === CONFIGURAZIONE ===
JSON_PATH = "FIA_2025_Sporting_Regulations_Structured.json"
FAISS_INDEX_PATH = "faiss_fia2025.index"
METADATA_PATH = "faiss_fia2025_structured_metadata.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"  # o percorso locale se scaricato manualmente

# === CARICAMENTO ARTICOLI ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

texts = []
ids = []
titles = []

for entry in data:
    content = entry.get("content", "").strip()
    article_id = entry.get("id", "").strip()
    title = entry.get("title", "").strip()

    if content:
        texts.append(content)
        ids.append(article_id)
        titles.append(title)

# === EMBEDDING ===
print(f"Generating embeddings for {len(texts)} articles...")
model = SentenceTransformer(MODEL_NAME)
embeddings = model.encode(texts, show_progress_bar=True)
embedding_matrix = np.array(embeddings).astype("float32")

# === FAISS INDEX ===
print("Building FAISS index...")
index = faiss.IndexFlatL2(embedding_matrix.shape[1])
index.add(embedding_matrix)
faiss.write_index(index, FAISS_INDEX_PATH)

# === METADATA ===
metadata = [
    {
        "id": ids[i],
        "title": titles[i],
        "content": texts[i]
    }
    for i in range(len(texts))
]
with open(METADATA_PATH, "wb") as f:
    pickle.dump(metadata, f)

print("✅ FAISS index and metadata saved.")
