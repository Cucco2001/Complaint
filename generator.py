import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def filter_relevant_articles(articles, penalty_type, race_conditions):
    # Prepara input per GPT che farà da selettore di articoli
    articles_formatted = ""
    for article in articles:
        articles_formatted += f"--- {article['title']} ---\n{article['content']}\n"

    prompt_filter = f"""
You are a Formula 1 Sporting Regulations analyst.

A driver has received the following penalty:
Penalty: {penalty_type}
Context: {race_conditions}

Below are several articles from the FIA 2025 Sporting Regulations. Select ALL the articles that could be useful in building a legal defense for the case described, even if they are not the most semantically obvious ones.

Respond in JSON format as follows:
[
  {{"article": "33", "score": 3, "reason": "Directly governs track limits"}},
  ...
]
Articles:
{articles_formatted}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt_filter}
        ],
        temperature=0.2,
        max_tokens=4000
    )

    # Estrai articoli selezionati
    import json
    import re
    json_match = re.search(r"\[.*?\]", response.choices[0].message.content, re.DOTALL)
    selected_articles = []
    if json_match:
        try:
            filtered = json.loads(json_match.group(0))
            selected_articles = [a["article"] for a in filtered if a["score"] >= 2]
        except:
            pass

    # Forza inclusione Art. 54 se assente
    if "54" not in selected_articles:
        selected_articles.append("54")

    # Riconoscimento automatico di casi speciali
    trigger_lower = (penalty_type + " " + race_conditions).lower()
    if "pit entry" in trigger_lower and "red flag" in trigger_lower:
        for extra in ["34", "37"]:
            if extra not in selected_articles:
                selected_articles.append(extra)

    # Ritorna articoli corrispondenti
    final = []
    for art in articles:
        num = art["title"].split(")")[0].strip()
        if num in selected_articles:
            final.append(art)

    return final
def generate_complaint(articles, penalty_type, race_conditions, driver=None, lap=None, turn=None):
    # STEP 1 – FILTRAGGIO INTELLIGENTE

    filtered_articles = filter_relevant_articles(articles, penalty_type, race_conditions)

    # STEP 2 – COSTRUZIONE DEL PROMPT FINALE
    regulation_section = ""
    for article in filtered_articles:
        regulation_section += f"\n--- {article['title']} ---\n{article['content']}\n"

    prompt_generate = f"""
You are a legal advisor for a Formula 1 team. Based on the penalty details and regulatory references provided, write a formal complaint to the FIA Race Director.

The letter must include:
1. A formal header with: "To", "From", "Subject", "Date"
2. Four numbered sections with headings:
   - Factual Background
   - Applicable Regulations
   - Grounds for Review
   - Conclusion and Request
3. Direct quotations of regulation articles, where appropriate.
4. You must include ALL the regulation articles that could strengthen the defense or clarify procedural aspects, not just the main ones.
5. Use a respectful and structured legal tone, as used in official correspondence by a Sporting & Legal Department.

Penalty:
{penalty_type}

Race context:
{race_conditions}

{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation references (from the FIA Sporting Regulations 2025):
{regulation_section}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a legal writer specialized in Formula 1 regulations."},
            {"role": "user", "content": prompt_generate}
        ],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()
