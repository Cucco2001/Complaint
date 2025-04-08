import openai

# Funzione per generare un complaint tramite GPT
def generate_complaint(retrieved_articles, penalty_type, lap, turn, driver, race_conditions):
    # Costruisci il prompt
    prompt = f"""
    Pilota: {driver}
    Penalità: {penalty_type} al giro {lap}, curva {turn}
    Condizioni gara: {race_conditions}
    
    Articoli del regolamento pertinenti:
    {retrieved_articles}

    Scrivi un complaint formale alla Direzione Gara, argomentando la non validità della penalità in base agli articoli del regolamento FIA 2025.
    """
    
    # Usa OpenAI GPT per generare il testo
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    
    return response.choices[0].text.strip()