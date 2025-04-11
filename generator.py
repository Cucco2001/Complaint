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
        model="gpt-4-turbo",
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
You are acting as the Lead Legal Advisor for a Formula 1 team. Your task is to write a formal complaint to the FIA Race Director challenging a penalty, based exclusively on the articles of the FIA 2025 Formula 1 Sporting Regulations provided below.

⚠️ IMPORTANT CONSTRAINTS:

- **You may only refer to regulation articles explicitly listed in the section titled "Regulation References".**
- **Do not use any outside knowledge of the given FIA rules.**
- **If a concept is not covered in the supplied articles, do not mention it.**
- **Do not invent regulation numbers or paraphrase rules that are not present.**

Your letter must be written in the structure and tone expected from a Formula 1 team’s Legal & Sporting Department. Follow this format precisely:

---

### Formal Header:
- To
- From
- Subject
- Date

---

### 1. Factual Background
Summarize the penalty imposed, including the relevant context (e.g., track conditions, lap, turn, driver). This section must be objective and chronological.

### 2. Applicable Regulations
Only quote and comment on the articles explicitly provided in the "Regulation References" section. Always use **verbatim quotations** with article numbers when possible.

### 3. Grounds for Review
Build the case for review by:
- Arguing any **ambiguity** in article wording or scope;
- Challenging the **application** of specific articles in this context;
- Assessing whether the **penalty was proportionate**;
- Pointing out **inconsistencies** with how these same articles were applied in the past, if that can be inferred from the strategy considerations.

Every argument here must be **explicitly anchored** to at least one of the regulation articles provided.

You may also mention evidence types (telemetry, on-board, radio) that could assist a re-evaluation, but **only if justified by a specific regulation**.

### 4. Conclusion and Request
Formulate a precise and respectful request: either for withdrawal, reduction, or reassessment of the penalty. Reaffirm commitment to sporting fairness and regulatory consistency.

---

Penalty:
{penalty_type}

Race context:
{race_conditions}

{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation References (from the FIA Sporting Regulations 2025):
{regulation_section}

Legal Strategy Considerations:
{', '.join(strategy_hints)}

Before writing:
Briefly reflect on which of the above strategy considerations are most useful. Then write the complaint using **only** the regulation references above.
"""

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_generate}],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()
