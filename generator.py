import json
import re
from openai import OpenAI

client = OpenAI()

def filter_relevant_articles(articles, penalty_type, race_context):
    articles_formatted = ""
    for article in articles:
        articles_formatted += f"--- {article['title']} ---\n{article['content']}\n"

    prompt_filter = f"""
You are a Formula 1 Sporting Regulations analyst.

Penalty: {penalty_type}
Context: {race_context}

Below are excerpts from the FIA 2025 Sporting Regulations. Select ONLY the articles that could be genuinely useful in supporting a legal defense of the driver. Avoid listing irrelevant or tangentially related ones.

Respond in JSON format as:
[
  {{"article": "54.2(a)", "score": 3, "reason": "Defines burden of proof for assigning blame"}},
  {{"article": "17.4", "score": 2, "reason": "Allows request for review if new evidence is present"}}
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

    final_articles = []
    for art in articles:
        num = art["title"].split(")")[0].strip()
        if num in selected_articles:
            final_articles.append(art)

    return {
        "articles": final_articles,
        "strategy_hints": list(set(strategy_hints))
    }

def generate_complaint(articles, penalty_type, race_context, driver=None, lap=None, turn=None):
    filtered_result = filter_relevant_articles(articles, penalty_type, race_context)
    filtered_articles = filtered_result["articles"]
    strategy_hints = filtered_result["strategy_hints"]

    regulation_section = ""
    for article in filtered_articles:
        regulation_section += f"\n--- {article['title']} ---\n{article['content']}\n"

    prompt_generate = f"""
You are a legal advisor for a Formula 1 team. Write a formal complaint letter challenging a penalty.

CRITICAL RULES:
- Use ONLY the regulation articles provided below.
- You MUST quote AT LEAST ONE article, more if relevant.
- DO NOT refer to any article not shown below.
- If article wording is ambiguous or open to interpretation, highlight this as a defense.
- If the penalty appears excessive, emphasize proportionality.
- Keep a legal and respectful tone.

Penalty: {penalty_type}
Context: {race_context}
Driver: {driver if driver else 'N/A'}
Lap: {lap if lap else 'N/A'}, Turn: {turn if turn else 'N/A'}

Regulation References:
{regulation_section}

Strategic Considerations:
{', '.join(strategy_hints)}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Formula 1 legal complaint writer."},
            {"role": "user", "content": prompt_generate}
        ],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()