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
You are a legal assistant for a Formula 1 team. Write a formal complaint to the FIA Race Director to request a review of a penalty.

Penalty:
{penalty_type}

Race context:
{race_conditions}

{f"Driver: {driver}" if driver else ""}
{f"Lap: {lap}, Turn: {turn}" if lap and turn else ""}

Regulation references (from the FIA Sporting Regulations 2025):
{regulation_section}

Write the complaint in a professional and structured tone. Include references to the regulation paragraphs and explain why the penalty might have been incorrectly applied. Do not hallucinate. Use only the information above.
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