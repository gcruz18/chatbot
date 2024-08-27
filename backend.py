import os
import PyPDF2
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

def process_pdfs_from_directory(directory):
    pdf_text = ""
    documents_metadata = []
    
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                document_title = pdf.metadata.get('/Title', filename)  # Usa il titolo del documento o il nome del file come fallback
                if not document_title:  # Ulteriore controllo se il titolo è vuoto
                    document_title = filename
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""  # Assicura di ottenere testo o una stringa vuota
                    pdf_text += page_text
                    documents_metadata.append({
                        "source": f"{filename} (Page {page_num+1})",
                        "title": document_title
                    })
    
    return pdf_text, documents_metadata

def _build_prompt_template():
    template = """
Sei un assistente intelligente che risponde alle domande in modo chiaro e conciso, utilizzando le informazioni pertinenti dai documenti.

Preferisci sempre come fonte i documenti. Se non trovi la risposta cercala da altre fonti.

Se non conosci la risposta, ammetti di non saperlo.

Inizia ora con la risposta.

Domanda: {question}
=========
{context}
=========
Risposta:
"""
    return PromptTemplate(input_variables=["question", "context"], template=template)

def create_chain_for_pdfs(pdf_text, metadatas):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(pdf_text)
    embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
    docsearch = Chroma.from_texts(texts, embeddings, metadatas=metadatas)
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True,
    )
    
    llm_local = ChatOllama(model="gemma2:2b", default_language="it")  # Utilizzo del modello "phi3.5" con lingua italiana
    
    # Costruisci il prompt template
    prompt_template = _build_prompt_template()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm_local,
        retriever=docsearch.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt_template},  # Integra il prompt template
        return_source_documents=True,
    )
    return chain

def get_answer_from_chain(chain, user_input):
    response = chain.invoke({"question": user_input})
    answer = response["answer"]
    source_documents = response.get("source_documents", [])

    if source_documents:
        # Creare la lista completa delle fonti
        sources = [f"{doc.metadata.get('source', 'Fonte sconosciuta')}" for doc in source_documents]

        # Convertire la lista in un set per ottenere solo valori unici
        unique_sources = set(sources)

        # Aggiungere le fonti uniche alla risposta, ciascuna su una nuova riga con una virgola alla fine
        answer += f"\n\nFonti:\n" + ",\n".join(unique_sources)
    else:
        answer += "\n\nNessuna fonte trovata"

    return answer
