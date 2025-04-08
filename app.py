import streamlit as st
from retriever import retrieve_articles
from generator import generate_complaint

# Caricamento delle informazioni necessarie
st.title("Formula 1 FIA Penalty Complaint Generator")

# Sezione per input penalità
st.header("Inserisci dettagli della penalità")
penalty_type = st.text_input("Tipo di penalità", "Es. 5 secondi per track limits")
lap = st.number_input("Giro", min_value=1, max_value=1000, value=1)
turn = st.number_input("Curva", min_value=1, max_value=100, value=1)
driver = st.text_input("Pilota", "Es. Charles Leclerc")
race_conditions = st.text_area("Condizioni della gara", "Es. Safety car in pista, pioggia, ecc.")

# Pannello per visualizzare il risultato
if st.button("Genera Complaint"):
    # Recupero degli articoli rilevanti dal regolamento
    st.write("Recuperando articoli rilevanti...")
    retrieved_articles = retrieve_articles(penalty_type, lap, turn, driver, race_conditions)
    
    # Generazione del complaint formale
    st.write("Generando il complaint...")
    complaint = generate_complaint(retrieved_articles, penalty_type, lap, turn, driver, race_conditions)

    # Mostrare il complaint generato
    st.header("Complaint Generato")
    st.text(complaint)