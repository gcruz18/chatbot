import streamlit as st
from backend import get_answer, prepare_documents, load_documents

# Carica e prepara i documenti
documents = load_documents('documents')
db = prepare_documents(documents)

st.title("Chatbot Osservatori")

user_input = st.text_input("Fai una domanda:")
if st.button("Invia"):
    if user_input:
        answer, sources = get_answer(user_input, db)
        st.write("Risposta:", answer)
        st.write("Fonti:", sources)
    else:
        st.write("Per favore, inserisci una domanda.")
