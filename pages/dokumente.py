from openai import OpenAI
import os
import streamlit as st
import chromadb
import anthropic
from mistralai.client import MistralClient
from vector import list_collections, query_collection, clean_collection_name, extract_text_from_pdf, hash_file_content, add_document_to_collection
from home import add_menu

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)


chroma_client = chromadb.EphemeralClient()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

st.title("Dokumenten-Sammlungen erstellen oder löschen.")
collection_name = st.text_input("Dokumenten-Sammlung benennen:")
collection_describtion = st.text_area('Dokumenten-Sammlung beschreiben:', help='Beschreiben Sie die Dokumenten-Sammlung.')
chunk_size = st.slider('Chunk-Size festlegen:', 256, 2048, 512, help='In wie kleine Stücke soll der Inhalt zur Vektorisierung zerlegt werden? Wenn die Zahl zu klein ist, geht Sinn verloren. Wenn sie zu groß ist, könnte das Context-Fenster des LLM überschritten werden.')

uploaded_files = st.file_uploader("PDF-Dateien hochladen:", type=["pdf"], accept_multiple_files=True)

if st.button("Zur Sammlung hinzufügen oder hinzufügen!"):
    cleaned_collection_name = clean_collection_name(collection_name)
    collection = chroma_client.get_or_create_collection(name=cleaned_collection_name)

    if uploaded_files and collection_name:
        for doc_id, uploaded_file in enumerate(uploaded_files, start=1):
            with st.spinner(f"Verarbeite Dokument {doc_id}..."):
                text = extract_text_from_pdf(uploaded_file)
                if text:
                    hash_value = hash_file_content(text)
                    add_document_to_collection(collection, text, doc_id, hash_value, chunk_size, collection_describtion)
                    st.success(f"Dokument {doc_id} erfolgreich zur Sammlung hinzugefügt oder ergänzt.")
                else:
                    st.error(f"Die PDF-Datei {doc_id} scheint keinen Text zu enthalten.")
    else:
        st.error(
            "Bitte geben Sie einen Namen für die Sammlung vergeben und laden Sie mindestens eine PDF-Datei hoch.")

    # Abschnitt für das Löschen von Collections
st.write("## Dokumenten-Sammlung löschen")
delete_collection_name = st.selectbox("Wählen Sie eine Dokumenten-Sammlung aus:", list_collections())
if st.button("Bestehende Sammlung löschen!"):
    if delete_collection_name:
        chroma_client.delete_collection(name=delete_collection_name)
        st.success(f"Sammlung '{delete_collection_name}' wurde erfolgreich gelöscht.")

add_menu()