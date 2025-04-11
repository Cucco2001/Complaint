import streamlit as st
import json
import re
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def filter_relevant_articles(articles, penalty_type, race_context):
    """
    First-layer GPT call to select only the most legally relevant articles and strategy notes.
    """
    regulations_text = "\n".join(
        f"--- {article['title']} ---\n{article['content']}" for article in articles
    )

    prompt = f"""
You are a Formula 1 Sporting Regulations analyst.

A driver has received the following penalty:
Penalty: {penalty_type}
Context: {race_context}

Below are articles from the FIA 2025 Sporting Regulations. Your task is to:
- Select ONLY those articles that are genuinely useful in supporting a legal defense.
- Avoid articles only loosely connected or offering no argumentative value.

Respond strictly in JSON format like this:
[
  {{"article": "33", "score": 3, "reason": "Directly governs track limits"}},
  {{"article": "17", "score": 2, "reason": "Outlines petition for review"}}
]

Articles:
{regulations_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4096
    )

    # Extract JSON safely
    selected_articles, strategy_hints = [], []
    json_match = re.search(r"\[.*?\]", response.choices[0].message.content, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            for entry in parsed:
                if int(entry.get("score", 0)) >= 2:
                    selected_articles.append(entry["article"])
                    strategy_hints.append(entry["reason"])
        except Exception:
            pass

    # Always include Article 54 if behavioral penalty
    if "54" not in selected_articles and any(x in penalty_type.lower() for x in ["collision", "incident", "unsafe"]):
        selected_articles.append("54")
        strategy_hints.append("Standard article for assessing driver blame and incident responsibility")

    filtered = [a for a in articles if a["title"].split(")")[0].strip() in selected_articles]

    return {"articles": filtered, "strategy_hints": list(set(strategy_hints))}

def generate_complaint(articles, penalty_type, race_context, driver=None, lap=None, turn=None):
    """
    Second-layer GPT call: builds the formal legal complaint using ONLY selected articles.
    """
    # Step 1: Select legal articles
    result = filter_relevant_articles(articles, penalty_type, race_context)
    selected_articles = result["articles"]
    strategy = result["strategy_hints"]

    # Step 2: Format regulation section
    regulation_block = "\n\n".join(
        f"--- {a['title']} ---\n{a['content']}" for a in selected_articles
    )

    # Step 3: Construct final-generation prompt
    prompt = f"""
You are a legal advisor for a Formula 1 team. Write a formal complaint letter challenging a penalty.
STRICT RULES:
- Use ONLY the regulation articles below. DO NOT add external knowledge.
- Organize the letter in 4 titled sections:
  1. Factual Background
  2. Applicable Regulations
  3. Grounds for Review
  4. Conclusion and Request
- Quote AT LEAST one article VERBATIM in section 2.
- DO NOT invent any regulation or wording.
- Do NOT reference articles not listed below.
- Maintain a respectful, legal tone like a real FIA Sporting & Legal Department letter.

Context:
Penalty: {penalty_type}
Race: {race_context}
{f"Driver: {driver}" if driver else ""} {f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Articles Provided:
{regulation_block}

Legal Strategy Notes:
{'; '.join(strategy)}
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()