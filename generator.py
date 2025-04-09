import streamlit as st
from openai import OpenAI

# ---------------------- API SETUP ----------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_complaint(articles, penalty_type, race_conditions, driver=None, lap=None, turn=None):
    # Costruzione sezione "Regulation references"
    regulation_section = ""
    for article in articles:
        regulation_section += f"\n--- {article['title']} ---\n{article['content']}\n"

    # Prompt formale
    prompt = f"""
You are a legal advisor for a Formula 1 team. Based on the penalty details and regulatory references provided, write a formal complaint to the FIA Race Director.

The letter must include:
1. A formal header with: "To", "From", "Subject", "Date"
2. Four numbered sections with headings:
   - Factual Background
   - Applicable Regulations
   - Grounds for Review
   - Conclusion and Request
3. Direct quotations of regulation articles, where appropriate.
4. A respectful and structured legal tone, as used in official correspondence by a Sporting & Legal Department.
Only refer to the most relevant articles from the list below. You may ignore general or unrelated articles. When multiple articles are clearly applicable, cite all of them in the “Applicable Regulations” section.
Do not invent information. Only use the context provided below.

Penalty:
{penalty_type}

Race context:
{race_conditions}

{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation references (from the FIA Sporting Regulations 2025):
{regulation_section}
"""

    # Chiamata a GPT
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a legal writer specialized in Formula 1 regulations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()