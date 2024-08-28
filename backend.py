import os
import PyPDF2
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

def process_pdfs_from_directory(directory):
    texts = []
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
                    texts.append(page_text)
                    documents_metadata.append({
                        "source": f"{filename} (Page {page_num+1})",
                        "title": document_title
                    })
    
    return texts, documents_metadata

def _build_prompt_template():
    template = """


Usa le informazioni rilevanti dai documenti forniti per rispondere alla seguente domanda.

Se non riesci a trovare la risposta nei documenti, ammetti di non saperlo.

Domanda: {question}

Contesto: {context}

Fornisci una singola risposta chiara e concisa, non più lunga di 50 parole.

"""
    return PromptTemplate(input_variables=["question", "context"], template=template)

def create_chain_for_pdfs(texts, metadatas):
    # Suddividere i testi in segmenti più piccoli
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_texts = []
    split_metadatas = []

    for text, metadata in zip(texts, metadatas):
        chunks = text_splitter.split_text(text)
        split_texts.extend(chunks)
        split_metadatas.extend([metadata] * len(chunks))
    
    # Utilizzo di HuggingFaceEmbeddings per generare gli embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Indicizzazione vettoriale con FAISS
    docsearch = FAISS.from_texts(split_texts, embeddings, metadatas=split_metadatas)
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        return_messages=True,
    )
    
    # Utilizzo del modello ChatOllama (o un altro modello a tua scelta)
    llm_local = ChatOllama(model="gemma2:2b", default_language="it", max_tokens=150)
    
    # Costruzione del prompt template
    prompt_template = _build_prompt_template()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm_local,
        retriever=docsearch.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt_template},
        return_source_documents=True,
    )
    return chain

def get_answer_from_chain(chain, user_input):
    response = chain.invoke({"question": user_input})
    answer = response["answer"]
    source_documents = response.get("source_documents", [])

    if source_documents:
        sources = [f"{doc.metadata.get('source', 'Fonte sconosciuta')}" for doc in source_documents]
        unique_sources = set(sources)
        answer += f"\n\nFonti:\n" + ",\n".join(unique_sources)
    else:
        answer += "\n\nNessuna fonte trovata"

    return answer
