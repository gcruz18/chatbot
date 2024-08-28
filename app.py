import streamlit as st
from backend import process_pdfs_from_directory, create_chain_for_pdfs, get_answer_from_chain

# Inizializza lo stato della sessione
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.chat_history = []
    st.session_state.chain = None
    st.session_state.selected_topic = ""
    st.session_state.suggested_questions = []

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
# Funzione per ottenere le domande suggerite in base all'argomento
def get_suggested_questions(topic):
    if topic == "blockchain":
        return [
            "Come funziona la tecnologia blockchain?",
            "Quali sono i principali casi d'uso della blockchain?",
            "Quali sono i vantaggi della blockchain?",
            "Quali sono i rischi associati alla blockchain?"
        ]
    elif topic == "metaverse":
        return [
            "Che cos'è il metaverso?",
            "Quali sono le applicazioni del metaverso?",
            "Come si entra nel metaverso?",
            "Quali sono i rischi e le opportunità del metaverso?"
        ]
    elif topic == "payment":
        return [
            "Come funzionano i sistemi di pagamento digitali?",
            "Quali sono le principali tecnologie di pagamento?",
            "Quali sono le sfide della sicurezza nei pagamenti digitali?",
            "Quali sono i vantaggi dei pagamenti contactless?"
        ]
    else:
        return []
# Step 1: Scelta dell'argomento
if st.session_state.step == 1:
    st.title("Chatbot Osservatori")
    st.write("Benvenuto! Seleziona uno degli argomenti qui sotto per iniziare a esplorare le informazioni relative. Puoi poi porre domande basate sui documenti disponibili.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Blockchain ⛓️"):
            st.session_state.selected_topic = "blockchain"
            st.session_state.suggested_questions = get_suggested_questions("blockchain")
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Metaverse 🌍"):
            st.session_state.selected_topic = "metaverse"
            st.session_state.suggested_questions = get_suggested_questions("metaverse")
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("Payment 💵"):
            st.session_state.selected_topic = "payment"
            st.session_state.suggested_questions = get_suggested_questions("payment")
            st.session_state.step = 2
            st.rerun()

# Step 2: Caricamento e analisi dei documenti
if st.session_state.step == 2:
    st.title("Chatbot Osservatori")
    
    if not st.session_state.chain:
        loading_message = st.empty()  # Contenitore vuoto per il messaggio di caricamento
        loading_message.write("Sto caricando e preparando i documenti, attendi un momento...")

        # Carica i PDF dalla cartella corrispondente all'argomento selezionato
        pdf_text, documents_metadata = process_pdfs_from_directory(f'documents/{st.session_state.selected_topic}')

        # Crea la catena per la conversazione
        chain = create_chain_for_pdfs(pdf_text, documents_metadata)
        st.session_state.chain = chain

        loading_message.empty()  # Rimuove il messaggio di caricamento

        success_message = st.success("Documenti caricati e preparati correttamente!")
        st.rerun()  # Rerun dopo il caricamento per aggiornare l'UI

    # Mostra la cronologia della chat
    display_chat()

    # Mostra le domande suggerite in una griglia 2x2 con larghezza uniforme
    st.write("Domande suggerite:")
    for i in range(0, len(st.session_state.suggested_questions), 2):
        cols = st.columns([1, 1])  # Due colonne con larghezza uguale
        for j in range(2):
            if i + j < len(st.session_state.suggested_questions):
                with cols[j]:
                    question = st.session_state.suggested_questions[i + j]
                    if st.button(question):
                        st.session_state.chat_history.append({"role": "user", "content": question})

                        # Richiedi la risposta dalla catena
                        answer = get_answer_from_chain(st.session_state.chain, question)

                        st.session_state.chat_history.append({"role": "ai", "content": answer})
                        st.rerun()
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
    st.session_state.suggested_questions = []
    st.rerun()
