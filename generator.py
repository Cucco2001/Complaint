import streamlit as st
import json
import re
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

Below are several articles from the FIA 2025 Sporting Regulations. Select ONLY the articles that could be genuinely useful in supporting a legal defense of the driver. Avoid listing articles that are only loosely connected or which do not add argumentative value.

Respond in JSON format as follows:
[
  {{"article": "33", "score": 3, "reason": "Directly governs track limits"}},
  {{"article": "17", "score": 2, "reason": "Governs right of review"}},
  ...
]
Articles:
{articles_formatted}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_filter}],
        temperature=0.2,
        max_tokens=4000
    )

    selected_articles = []
    strategy_hints = []
    json_match = re.search(r"\[.*?\]", response.choices[0].message.content, re.DOTALL)
    if json_match:
        try:
            filtered = json.loads(json_match.group(0))
            for a in filtered:
                if a["score"] >= 2:
                    selected_articles.append(a["article"])
                    strategy_hints.append(a["reason"])
        except Exception:
            pass

    # Forza inclusione Art. 54 se penalità è comportamentale
    if "54" not in selected_articles and any(x in penalty_type.lower() for x in ["collision", "incident", "unsafe"]):
        selected_articles.append("54")
        strategy_hints.append("Standard article for incident and fault assessment (collision/unsafe behavior)")

    # Estrai articoli completi
    final_articles = []
    for art in articles:
        num = art["title"].split(")")[0].strip()
        if num in selected_articles:
            final_articles.append(art)

    return {
        "articles": final_articles,
        "strategy_hints": list(set(strategy_hints))  # Elimina duplicati
    }

def generate_complaint(articles, penalty_type, race_conditions, driver=None, lap=None, turn=None):
    # STEP 1 – FILTRAGGIO INTELLIGENTE
    filtered_result = filter_relevant_articles(articles, penalty_type, race_conditions)
    filtered_articles = filtered_result["articles"]
    strategy_hints = filtered_result["strategy_hints"]

    # STEP 2 – COSTRUZIONE DEL PROMPT
    regulation_section = ""
    for article in filtered_articles:
        regulation_section += f"\n--- {article['title']} ---\n{article['content']}\n"

    prompt_generate = f"""
You are a legal advisor for a Formula 1 team. Based on the penalty details, regulatory references, and strategy considerations provided, write a formal complaint to the FIA Race Director.

The letter must include:
1. A formal header with: "To", "From", "Subject", "Date"
2. Four numbered sections with headings:
   - Factual Background
   - Applicable Regulations
   - Grounds for Review
   - Conclusion and Request

Guidance:
- Quote regulation articles verbatim when useful.
- Use any ambiguity in article wording to support the defense in Section 3.
- Evaluate whether the penalty was proportionate to the actual impact or intent.
- If similar past incidents were treated differently, mention them to support a consistency argument.
- Propose relevant evidence types (telemetry, radio, footage) that could assist in the review.
- Maintain a professional, respectful, and legal tone, as expected from a team’s Sporting & Legal Department.

Penalty:
{penalty_type}

Race context:
{race_conditions}

{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation references (from the FIA Sporting Regulations 2025):
{regulation_section}

Legal strategy considerations (from article analysis):
{', '.join(strategy_hints)}

Before writing, briefly reflect on what elements of this case might be challenged or reinterpreted to the team’s advantage.
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
