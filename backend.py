import os
import logging
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import ollama
import subprocess
import time
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.debug("Environment variables loaded.")

def load_single_document(filepath):
    with open(filepath, 'rb') as file:
        pdf_reader = PdfReader(file)
        text = " ".join([page.extract_text() for page in pdf_reader.pages])
    return {"content": text, "source": filepath}

def load_documents(directory):
    logger.debug("Loading documents from directory: %s", directory)
    filepaths = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.pdf')]
    
    documents = []
    with ThreadPoolExecutor() as executor:
        documents = list(executor.map(load_single_document, filepaths))
    
    logger.debug("Loaded %d documents", len(documents))
    return documents

def prepare_documents(documents):
    logger.debug("Preparing documents for embedding.")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.create_documents([doc["content"] for doc in documents], metadatas=[{"source": os.path.basename(doc["source"])} for doc in documents])
    
    embeddings = HuggingFaceEmbeddings()
    db = FAISS.from_documents(texts, embeddings)
    logger.debug("Documents prepared and indexed.")
    return db

def clarify_ollama(question):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ollama.chat(model='gemma2:9b', messages=[
                {
                    'role': 'system',
                    'content': 'Sei un assistente che deve essere sicuro del topic della domanda. Chiedi se la domanda si riferisce agli osservatori "Blockchain", "Payment" oppure "Metaverse"'
                },
                {
                    'role': 'user',
                    'content': f"Domanda: {question}"
                }
            ])
            return response['message']['content']
        except Exception as e:
            logger.error("Errore nella comunicazione con Ollama: %s", e)
            if attempt < max_retries - 1:
                logger.debug("Tentativo di riavvio di Ollama...")
                subprocess.run(["ollama", "serve"], shell=True)
                time.sleep(5)
            else:
                return "Mi dispiace, c'è un problema di comunicazione con il modello. Per favore, verifica che Ollama sia in esecuzione."


def query_ollama(question, context, sources):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = ollama.chat(model='gemma2:2b', messages=[
                {
                    'role': 'system',
                    'content': 'Sei un assistente che risponde in italiano alle domande basandosi solo sulle informazioni fornite. Cita le fonti quando possibile. Se non trovi informazioni, rispondi solamente "Su questo al momento non posso risponderti. Chiedi maggiori informazioni all\'ufficio di riferimento."'
                },
                {
                    'role': 'user',
                    'content': f"Contesto: {context}\n\nFonti: {sources}\n\nDomanda: {question}"
                }
            ])
            return response['message']['content']
        except Exception as e:
            logger.error("Errore nella comunicazione con Ollama: %s", e)
            if attempt < max_retries - 1:
                logger.debug("Tentativo di riavvio di Ollama...")
                subprocess.run(["ollama", "serve"], shell=True)
                time.sleep(5)
            else:
                return "Mi dispiace, c'è un problema di comunicazione con il modello. Per favore, verifica che Ollama sia in esecuzione."


def get_answer(question, db):
    start_time = time.time()

    docs = db.similarity_search(question, k=3)
    context = " ".join([doc.page_content for doc in docs])
    sources = ", ".join(set([doc.metadata['source'] for doc in docs]))

    answer = query_ollama(question, context, sources)
    end_time = time.time()
    logger.debug("Similarity search and response received in %.2f seconds.", end_time - start_time)

    return  answer, sources


def get_clarification_answer(question):
    start_time = time.time()

    clarify_answer = clarify_ollama(question)

    end_time = time.time()
    logger.debug("Clarification response received in %.2f seconds.", end_time - start_time)

    return clarify_answer
