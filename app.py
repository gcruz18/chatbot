import streamlit as st
from backend import process_pdfs_from_directory, create_chain_for_pdfs, get_answer_from_chain

# Inizializza lo stato della sessione
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.chat_history = []
    st.session_state.chain = None
    st.session_state.selected_topic = ""

# Funzione per mostrare i messaggi della chat
def display_chat():
    for entry in st.session_state.chat_history:
        if entry['role'] == 'user':
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                    <div style="max-width: 70%; background-color: #DCF8C6; padding: 10px; border-radius: 10px; position: relative;">
                        <div style="margin-right: 35px;">{entry['content']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div style="width: 100%; background-color: #F1F0F0; padding: 10px; border-radius: 10px; position: relative;">
                        <div style="margin-left: 35px;">{entry['content']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# Step 1: Scelta dell'argomento
if st.session_state.step == 1:
    st.title("Chatbot con PDF")
    st.write("Benvenuto! Seleziona uno degli argomenti qui sotto per iniziare a esplorare le informazioni relative. Puoi poi porre domande basate sui documenti disponibili.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Blockchain ⛓️"):
            st.session_state.selected_topic = "blockchain"
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Metaverse 🌍"):
            st.session_state.selected_topic = "metaverse"
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("Payment 💵"):
            st.session_state.selected_topic = "payment"
            st.session_state.step = 2
            st.rerun()

# Step 2: Caricamento e analisi dei documenti
if st.session_state.step == 2:
    if not st.session_state.chain:
        st.write("Sto caricando e preparando i documenti, attendi un momento...")

        # Carica i PDF dalla cartella corrispondente all'argomento selezionato
        pdf_text, documents_metadata = process_pdfs_from_directory(f'documents/{st.session_state.selected_topic}')

        # Crea la catena per la conversazione
        chain = create_chain_for_pdfs(pdf_text, documents_metadata)
        st.session_state.chain = chain
        st.success("Documenti caricati e preparati correttamente!")

    # Mostra la cronologia della chat
    display_chat()

    # Input domanda utente
    user_input = st.text_input("Scrivi la tua domanda:", key='user_input_input')

    if st.button("Invia"):
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Richiedi la risposta dalla catena
            answer = get_answer_from_chain(st.session_state.chain, user_input)

            st.session_state.chat_history.append({"role": "ai", "content": answer})
            st.rerun()

# Se l'utente desidera ripartire da zero
if st.button("Resetta Chatbot"):
    st.session_state.step = 1
    st.session_state.chat_history = []
    st.session_state.chain = None
    st.session_state.selected_topic = ""
    st.rerun()
