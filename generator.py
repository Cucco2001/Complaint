import streamlit as st
import json
import re
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def filter_relevant_articles(articles, penalty_type, race_conditions):
    # Format all articles for GPT input
    articles_formatted = "\n".join(
        f"--- {article['title']} ---\n{article['content']}" for article in articles
    )

    prompt_filter = f"""
You are a Formula 1 Sporting Regulations analyst.

A driver has received the following penalty:
Penalty: {penalty_type}
Context: {race_conditions}

Below are several articles from the FIA 2025 Sporting Regulations. Select ONLY the articles that could be genuinely useful in supporting a legal defense of the driver. Avoid listing articles that are only loosely connected or which do not add argumentative value.

Respond ONLY in this JSON format:
[
  {{"article": "33", "score": 3, "reason": "Directly governs track limits"}},
  {{"article": "17", "score": 2, "reason": "Governs right of review"}}
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

    match = re.search(r"\[.*?\]", response.choices[0].message.content, re.DOTALL)
    if match:
        try:
            filtered = json.loads(match.group(0))
            for a in filtered:
                if int(a.get("score", 0)) >= 2:
                    selected_articles.append(a["article"])
                    strategy_hints.append(a["reason"])
        except Exception:
            pass

    # Force include Article 54 for incident-type penalties
    if "54" not in selected_articles and any(word in penalty_type.lower() for word in ["collision", "incident", "unsafe"]):
        selected_articles.append("54")
        strategy_hints.append("Standard article for incident and fault assessment")

    final_articles = [
        art for art in articles
        if art["title"].split(")")[0].strip() in selected_articles
    ]

    return {
        "articles": final_articles,
        "strategy_hints": list(set(strategy_hints))
    }

def generate_complaint(articles, penalty_type, race_conditions, driver=None, lap=None, turn=None):
    filtered_result = filter_relevant_articles(articles, penalty_type, race_conditions)
    filtered_articles = filtered_result["articles"]
    strategy_hints = filtered_result["strategy_hints"]

    regulation_section = "\n".join(
        f"--- {article['title']} ---\n{article['content']}" for article in filtered_articles
    )

    prompt_generate = f"""
You are a legal advisor for a Formula 1 team. Write a formal complaint letter challenging a penalty. You must:
- Use ONLY the regulation articles provided below.
- Quote AT LEAST one article explicitly.
- DO NOT invent any article or regulation wording.
- If a concept is not present in the provided input, DO NOT include it.

Penalty: {penalty_type}
Context: {race_conditions}
{f"Driver: {driver}" if driver else ""} {f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation References:
{regulation_section}

Legal Strategy Notes:
{', '.join(strategy_hints)}
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_generate}],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()
