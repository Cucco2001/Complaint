
from retriever import retrieve_articles

# Esempio di penalità e contesto
penalty_type = "10 second stop-and-go penalty"
race_conditions = "collision between two cars during the final laps of the race"

# Esecuzione della funzione
articles = retrieve_articles(penalty_type, race_conditions, k=5)

# Visualizzazione dei risultati
for i, article in enumerate(articles, 1):
    print(f"--- Article {i} ---")
    print(f"Title: {article['title']}")
    print(f"Content: {article['content']}...")
    print()
