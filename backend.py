import os
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import ollama
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

def load_documents(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    documents.append({"content": text, "source": f"{filename}, pagina {page_num}"})
    return documents

def prepare_documents(documents):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents([doc["content"] for doc in documents], metadatas=[{"source": doc["source"]} for doc in documents])
    
    embeddings = HuggingFaceEmbeddings()
    db = FAISS.from_documents(texts, embeddings)
    return db

def query_ollama(question, context, sources):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ollama.chat(model='phi3:mini', messages=[
                {
                    'role': 'system',
                    'content': 'Sei un assistente che risponde alle domande basandosi solo sulle informazioni fornite. Cita le fonti quando possibile. Se non hai informazioni sufficienti, rispondi "Chiedi maggiori informazioni all\'ufficio di riferimento."'
                },
                {
                    'role': 'user',
                    'content': f"Contesto: {context}\n\nFonti: {sources}\n\nDomanda: {question}"
                }
            ])
            return response['message']['content']
        except Exception as e:
            print(f"Errore nella comunicazione con Ollama: {e}")
            if attempt < max_retries - 1:
                print("Tentativo di riavvio di Ollama...")
                subprocess.run(["ollama", "serve"], shell=True)
                time.sleep(5)
            else:
                return "Mi dispiace, c'è un problema di comunicazione con il modello. Per favore, verifica che Ollama sia in esecuzione."

def get_answer(question, db):
    docs = db.similarity_search(question, k=2)
    context = " ".join([doc.page_content for doc in docs])
    sources = ", ".join(set([doc.metadata['source'] for doc in docs]))
    
    answer = query_ollama(question, context, sources)
    return answer, sources

# Carica e prepara i documenti
documents = load_documents('documents')
db = prepare_documents(documents)
