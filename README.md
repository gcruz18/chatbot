Preparazione dell'ambiente:

Assicurati di avere Python installato
Crea una cartella per il progetto
Crea un ambiente virtuale:
python -m venv venv

Attiva l'ambiente virtuale:

Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate




Installazione delle dipendenze:
pip install -r requirements.txt

Preparazione dei file:

backend.py e app.py nella cartella del progetto
Copia il codice fornito nei rispettivi file
Crea una sottocartella chiamata "documents" e inserisci i tuoi file PDF


Configurazione di Ollama:

Installa Ollama dal sito ufficiale
Apri un terminale (diverso) e esegui:
ollama pull phi3:mini



Esecuzione dell'applicazione:

Nel terminale, con l'ambiente virtuale attivato, naviga alla cartella del progetto
Esegui:
Copystreamlit run app.py
