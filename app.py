import streamlit as st
from retriever import retrieve_articles
from generator import generate_complaint

st.set_page_config(page_title="F1 Complaint Generator", layout="centered")

# 🏁 Intestazione
st.title("🏎️ Formula 1 - FIA Penalty Complaint Generator")
st.markdown("Genera automaticamente una bozza formale di reclamo da inviare alla Direzione Gara FIA.")

# 📥 Input Utente
with st.form("penalty_form"):
    st.header("📋 Inserisci i dettagli della penalità")
    penalty_type = st.text_input("Tipo di penalità", "5-second time penalty for track limits")
    driver = st.text_input("Pilota (facoltativo)", "")
    lap = st.text_input("Giro (facoltativo)", "")
    turn = st.text_input("Curva (facoltativo)", "")
    race_conditions = st.text_area("Contesto gara", "Wet conditions, Safety Car just ended.")
    
    submitted = st.form_submit_button("Genera Complaint")

# ⚙️ Processing
if submitted:
    with st.spinner("🔎 Recupero articoli rilevanti..."):
        retrieved_articles = retrieve_articles(penalty_type, race_conditions)
    
    st.success(f"{len(retrieved_articles)} articoli rilevanti trovati")

    # Mostra articoli recuperati (facoltativo ma utile)
    with st.expander("📚 Articoli del Regolamento Trovati"):
        for art in retrieved_articles:
            st.markdown(f"**{art['title']}**")
            st.markdown(art["content"][:600] + "...")

    with st.spinner("✍️ Generazione del complaint..."):
        complaint = generate_complaint(
            articles=retrieved_articles,
            penalty_type=penalty_type,
            race_conditions=race_conditions,
            driver=driver if driver else None,
            lap=lap if lap else None,
            turn=turn if turn else None
        )

    # 📤 Output finale
    st.header("📄 Complaint Generato")
    st.text_area("Risultato", value=complaint, height=400)
