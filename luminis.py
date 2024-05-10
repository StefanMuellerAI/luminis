import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
import fitz
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import hashlib
import chromadb
import chromadb.utils.embedding_functions as embedding_functions


load_dotenv()


chroma_client = chromadb.EphemeralClient()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
application_logo = os.getenv("APPLICATION_LOGO")
application_title = os.getenv("APPLICATION_TITLE")
application_subheader = os.getenv("APPLICATION_SUBHEADER")
application_primer = os.getenv("APPLICATION_PRIMER")
application_model = os.getenv("APPLICATION_MODEL")
primer_editable = os.getenv("PRIMER_EDITABLE")
collection_name = os.getenv("COLLECTION_NAME")
collection_description = os.getenv("COLLECTION_DESCRIPTION")
pdf_folder = "pdfs"

openai_client = OpenAI()

st.set_page_config(
    page_title=application_title,
    page_icon="🤖",
)

def plot_embeddings(embeddings):
    """Visualisiert die Embeddings mit t-SNE."""
    n_samples = embeddings.shape[0]
    if n_samples > 1:
        perplexity_value = max(5, min(30, n_samples - 1))
        tsne = TSNE(n_components=2, random_state=42, perplexity=perplexity_value)
        transformed_embeddings = tsne.fit_transform(embeddings)

        fig, ax = plt.subplots(figsize=(10,8))
        ax.scatter(transformed_embeddings[:, 0], transformed_embeddings[:, 1], alpha=0.5)
        ax.set_title('2D Visualisierung der Embeddings')
        ax.set_xlabel('t-SNE Dimension 1')
        ax.set_ylabel('t-SNE Dimension 2')
        return(fig)
    else:
        print("Fehler")

def clean_text(text):
    # Konvertierung in Kleinbuchstaben
    text = text.lower()
    # Entfernen von Sonderzeichen, dabei bleiben Leerzeichen und Buchstaben erhalten
    text = re.sub(r'[^a-z0-9\s§(){}\[\]<>]', '', text)
    # Entfernen von mehrfachen Leerzeichen
    text = ' '.join(text.split())
    return text
def generate_user_hash(request):
    browser = request.headers.get('User-Agent', '')
    ip = request.remote_addr
    os = request.headers.get('OS', '')

    hash_input = f"{browser}:{ip}:{os}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def hash_file_content(content):
    """Erzeugt einen SHA-256 Hash des Inhalts."""
    return hashlib.sha256(content.encode()).hexdigest()


def create_embedding(text):
    """Erzeugt einen Text-Embedding mit OpenAI's API."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    embedding_vector = response.data[0].embedding
    return embedding_vector


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file given the file path."""
    text = ""
    with fitz.open(pdf_path) as doc:  # Ändern Sie dies, um den Pfad direkt zu verwenden
        for page in doc:
            text += page.get_text()
    return text


def count_tokens(text):
    """Zählt die Anzahl der Tokens in einem Text."""
    encoding = tiktoken.encoding_for_model("gpt-4-1106-Preview")
    tokens = encoding.encode(text)
    return len(tokens)

def convert_pdf_to_string(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ''
    for page in doc:
        text += page.get_text()
    return text


def rerank_results(results, query):
    """
    Rerankt die Ergebnisse basierend auf zusätzlichen Relevanzmetriken.
    """
    query_embedding = create_embedding(query)

    # Berechne die Ähnlichkeit jedes Ergebnisses mit der Abfrage
    ranked_results = sorted(
        results,
        key=lambda x: cosine_similarity(query_embedding, x['embedding']),
        reverse=True  # Höhere Ähnlichkeit bedeutet höhere Relevanz
    )
    return ranked_results


def cosine_similarity(vec1, vec2):
    """Berechnet die Kosinusähnlichkeit zwischen zwei Vektoren."""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)


def tokenize_and_chunk_text(text, max_tokens_per_chunk):
    """
    Zerlegt den Text in Chunks, basierend auf der maximalen Anzahl von Tokens pro Chunk.
    """
    encoding = tiktoken.encoding_for_model(application_model)
    tokens = encoding.encode(text)

    # Aufteilen der Token-Liste in Chunks
    chunks = [tokens[i:i + max_tokens_per_chunk] for i in range(0, len(tokens), max_tokens_per_chunk)]

    # Konvertiere die Chunks von Token-Integers zurück in String-Form
    text_chunks = [encoding.decode(chunk) for chunk in chunks]

    return text_chunks


def add_document_to_collection(collection ,text, doc_id, hash_value, max_tokens_per_chunk, collection_description):
    """
    Erweiterte Funktion zum Hinzufügen eines Dokuments in Chunks zur Collection.
    """
    # Zuerst teilen wir den Text in Chunks.
    text_chunks = tokenize_and_chunk_text(text, max_tokens_per_chunk)

    # Für jeden Chunk fügen wir ihn zur Collection hinzu.
    for i, chunk in enumerate(text_chunks):
        clean_chunk = clean_text(chunk)
        embedding = create_embedding(clean_chunk)
        chunk_id = f"{doc_id}_{i}"  # Erzeuge eine eindeutige ID für jeden Chunk basierend auf der doc_id und der Reihenfolge.
        collection.upsert(
            embeddings=[embedding],
            documents=[clean_chunk],
            metadatas=[{"source": "user_uploaded_pdf", "hash": hash_value, "describtion": collection_description, "chunk_id": chunk_id}],
            ids=[chunk_id]
        )

def clean_collection_name(name):
    """Bereinigt den Namen der Collection für die Verwendung in einer Datenbank."""
    # Umlaute und das ß umwandeln
    umlaut_mapping = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'Ä': 'Ae',
        'Ö': 'Oe',
        'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_mapping.items():
        name = name.replace(umlaut, replacement)

    # Ersetzt alle nicht Wort-Zeichen durch Unterstriche
    cleaned_name = re.sub(r'\W+', '_', name)
    return cleaned_name

def list_collections():
    """Listet alle Collections auf (angepasst für deine ChromaDB-Implementierung)."""
    collections = chroma_client.list_collections()
    return [collection.name for collection in collections]

def collection_exists(collection_name):
    """Überprüft, ob eine bestimmte Collection existiert."""
    existing_collections = list_collections()
    return collection_name in existing_collections

def create_embedding_function():
    """Erstellt eine Embedding-Funktion für die Collection."""
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )
    return openai_ef

def query_collection(query, collection_name, number_of_results=3):
    """Führt eine Abfrage auf der angegebenen Collection durch."""
    openai_ef = create_embedding_function()

    try:
        collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)
        results = collection.query(
            query_texts=[query],
            n_results=number_of_results,
            include=["embeddings", "documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        results = {"documents": [""]}
    return results

def retrieve_embeddings_from_collection(collection_name):
    openai_ef = create_embedding_function()
    collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)
    results = collection.get(include=["embeddings"])

    print("Query Results:", results)  # Um die vollständige Struktur erneut zu überprüfen

    # Wenn die Embeddings direkt im Hauptobjekt unter 'embeddings' abgelegt sind
    if 'embeddings' in results:
        embeddings = np.array([embed for embed in results['embeddings']])
        return embeddings
    else:
        print("Der Schlüssel 'embeddings' wurde in der Rückgabe nicht gefunden.")
        return np.array([])  # Gibt ein leeres Array zurück, wenn keine Daten vorhanden sind


def create_collection(collection_name):
    """Erstellt eine neue Collection in ChromaDB."""
    collection = chroma_client.get_or_create_collection(name=collection_name)
    return collection


def process_pdfs_in_folder(folder_path, chunk_size=512, collection_name="main", collection_describtion="default"):
    collection = create_collection(collection_name)

    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    if not pdf_files:
        print("Keine PDF-Dateien im Ordner gefunden.")
        return False

    for doc_id, filename in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(folder_path, filename)
        print(f"Verarbeite Dokument {doc_id}...")

        text = extract_text_from_pdf(pdf_path)  # Verwenden Sie den Pfad direkt
        hash_value = hash_file_content(text)
        add_document_to_collection(collection, text, doc_id, hash_value, chunk_size, collection_describtion)

        if text:
            print(f"Dokument {doc_id} erfolgreich verarbeitet.")
        else:
            print(f"Die PDF-Datei {doc_id} scheint keinen Text zu enthalten.")

    return True

def check_for_compliance(message):
    print(message)
    response = openai_client.chat.completions.create(
        model=application_model,
        messages=[
            {"role": "system",
             "content": f"You are a helpful AI-Assistent which checks an user-generated message for saftey according to"
                        f"the following rules. If the message hits one of this rules, give only 'no, it is not compliant.' back."
                        f"Otherwise 'yes, it is compliant.' And give a short explanation."
                        f"<Rule>Any kind of deviation in a traditional baptism in process, place or personnel!</Rule>"
                        f"<Rule>Giving or receiving confessions!</Rule>"},
            {"role": "user",
             "content": f" This is the message {message}."
             },
        ],

        max_tokens=4000,
        temperature=0.7
    )
    decision = response.choices[0].message.content
    print(decision)
    if "yes" in decision:
        return True
    else:
        return False

def initialize_session_state():
    """
    Initialisiert die Session-State-Variablen.
    """
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = application_model
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat_history():
    """
    Zeigt den Chatverlauf an.
    """
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def process_user_input(prompt):
    """
    Verarbeitet die Benutzereingabe und generiert die KI-Antwort.
    :param prompt: Die Benutzereingabe.
    :return: Die generierte KI-Antwort.
    """

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with (st.chat_message("assistant")):
        results = query_collection(prompt, "main")

        context = "\n".join(results["documents"][0])
        clean_context = context.strip()

        st.session_state.messages.append({"role": "system", "content": f"{application_primer}"})
        stream = openai_client.chat.completions.create(
            model=application_model,
            messages=[
                {"role": m["role"], "content": m["content"] + "Im Vektorspeicher gefundene Dokumente:" + clean_context}
                for m in st.session_state.messages
            ],
            stream=True,
            temperature=0.7,
            max_tokens=4000,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )

        response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
        return response


def initialize_preprocessing(pdf_folder):
    """Führt das Preprocessing einmalig durch, wenn die Flag-Datei nicht gesetzt ist."""
    flag_file = 'preprocessing_done.flag'
    if not os.path.exists(flag_file):
        number_of_files = len(os.listdir(pdf_folder))
        if number_of_files > 0:
            print(f"Lade {number_of_files} Dokumente in Vektorspeicher...")
            process_pdfs_in_folder(pdf_folder)
        # Erstelle die Flag-Datei, um anzuzeigen, dass das Preprocessing abgeschlossen ist
        with open(flag_file, 'w') as f:
            f.write('done')
        print("Preprocessing durchgeführt und Flag gesetzt.")
    else:
        print("Preprocessing bereits durchgeführt. Keine Aktion notwendig.")

def main():
    initialize_preprocessing(pdf_folder)

    st.title(application_title)
    st.subheader(application_subheader)
    initialize_session_state()
    display_chat_history()

    prompt = st.chat_input("Stellen Sie eine Frage oder geben Sie eine Anweisung...")
    if prompt:
        process_user_input(prompt)

if __name__ == "__main__":
    main()