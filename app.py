import streamlit as st
from backend import get_answer, get_clarification_answer, load_documents, prepare_documents
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


st.title("Chatbot Osservatori")

if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.user_input = ""
    st.session_state.clarification = ""
    st.session_state.clarify_answer = ""
    st.session_state.answer = ""
    st.session_state.sources = ""
    st.session_state.db = None  

if st.session_state.step == 1:
    user_input = st.text_input("Chiedici qualcosa:", key='user_input_input')
    if st.button("Invia"):
        if user_input:
            st.session_state.user_input = user_input
            st.session_state.clarify_answer = get_clarification_answer(user_input)
            st.session_state.step = 2
            st.experimental_rerun()

if st.session_state.step == 2:
    st.write(st.session_state.clarify_answer)
    clarification_input = st.text_input("", key='clarification_input', value=st.session_state.clarification)
    
    if st.button("Invia"):
        st.session_state.clarification = clarification_input
        documents = None
        with st.spinner('Caricando i documenti rilevanti...'):
            if "blockchain" in clarification_input.lower(): 
                documents = load_documents('documents/blockchain')
            elif "metaverse" in clarification_input.lower():
                documents = load_documents('documents/metaverse')
            elif "payment" in clarification_input.lower():
                documents = load_documents('documents/payment')
            else:
                st.write("Per favore, usa il nome corretto degli osservatori che vuoi interrogare.")
        
        if documents:
            with st.spinner('Preparando i documenti...'):
                st.session_state.db = prepare_documents(documents)
            with st.spinner('Interrogando ollama...'):    
                st.session_state.answer, st.session_state.sources = get_answer(st.session_state.user_input, st.session_state.db)
            st.session_state.step = 3
            st.rerun()

if st.session_state.step == 3:
    st.write(st.session_state.answer)
    st.write("Fonti: " + st.session_state.sources)
    
    new_question = st.text_input("Fai un'altra domanda:", key='new_question_input')
    if st.button("Invia"):
        if new_question:
            st.session_state.user_input = new_question
            st.session_state.answer, st.session_state.sources = get_answer(new_question, st.session_state.db)
            st.rerun()

    if st.button("Reset"):
        st.session_state.step = 1
        st.session_state.user_input = ""
        st.session_state.clarification = ""
        st.session_state.clarify_answer = ""
        st.session_state.answer = ""
        st.session_state.sources = ""
        st.session_state.db = None
        st.rerun()