import os
from openai import OpenAI
import tiktoken
import fitz
import chromadb
import re
import hashlib
import chromadb.utils.embedding_functions as embedding_functions

chroma_client = chromadb.EphemeralClient()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

openai_client = OpenAI()
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


def extract_text_from_pdf(pdf_file):
    """Extrahiert Text aus einer PDF-Datei."""
    text = ""
    with fitz.open(stream=pdf_file.getvalue()) as doc:
        for page in doc:
            text += page.get_text()
    return text


def tokenize_and_chunk_text(text, max_tokens_per_chunk):
    """
    Zerlegt den Text in Chunks, basierend auf der maximalen Anzahl von Tokens pro Chunk.
    """
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")
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
        embedding = create_embedding(chunk)
        chunk_id = f"{doc_id}_{i}"  # Erzeuge eine eindeutige ID für jeden Chunk basierend auf der doc_id und der Reihenfolge.
        collection.upsert(
            embeddings=[embedding],
            documents=[chunk],
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

def query_collection(query, collection_name, number_of_results=3):
    """Führt eine Abfrage auf der angegebenen Collection durch."""
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small"
    )

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