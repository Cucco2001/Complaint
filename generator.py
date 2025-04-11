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
You are acting as the Lead Legal Advisor for a Formula 1 team. Your task is to draft a formal complaint to the FIA Race Director, challenging a penalty imposed during a Grand Prix. You have access to all relevant regulatory references and strategic considerations.

Your output must follow this exact structure:
1. A formal header with:
   - To
   - From
   - Subject
   - Date

2. Four clearly separated numbered sections with headings:
   - Factual Background
   - Applicable Regulations
   - Grounds for Review
   - Conclusion and Request

Important instructions:

- In Section 2, **explicitly quote** the most relevant regulation articles (from the provided Regulation References). Do **not** paraphrase unless absolutely necessary.
- In Section 3, use the legal strategy considerations provided to construct a defense. Make **direct reference to the quoted articles**, and explain why their application in this context is either ambiguous, misapplied, or disproportionate.
- Always comment on:
   • whether the regulation wording is ambiguous in this case;
   • whether the penalty is proportionate to the incident;
   • whether precedent suggests inconsistent stewarding.

- If helpful to the defense, mention types of evidence that could support a review (e.g., telemetry, onboard footage, radio comms).
- Maintain a respectful, professional legal tone as expected from a team’s Sporting & Legal Department.

Your goal is to produce a letter that could realistically be submitted to the FIA in a formal dispute.

Case details:
Penalty: {penalty_type}
Race context: {race_conditions}
{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation References (from the FIA Sporting Regulations 2025):
{regulation_section}

Legal Strategy Considerations:
{', '.join(strategy_hints)}

Before writing:
Reflect on which regulation articles are most useful to the defense. Your reasoning in Section 3 must be anchored to those references.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt_generate}],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()
