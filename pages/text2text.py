import os
from openai import OpenAI
import database as db
import streamlit as st
from dotenv import load_dotenv
import anthropic
from mistralai.client import MistralClient
from vector import list_collections, query_collection
from home import add_menu
import toml

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Lese die config.toml Datei
config = toml.load(".streamlit/config.toml")

# Greife auf den anthropic_model Wert zu
anthropic_model = config["server"]["anthropic_model"]
mistral_model = config["server"]["mistral_model"]
openai_model = config["server"]["openai_model"]

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Text2Text")
st.subheader("Interagieren Sie mit der KI und erhalten Sie Antworten auf Ihre Fragen.")

def initialize_session_state():
    """
    Initialisiert die Session-State-Variablen.
    """
    if "ai_model" not in st.session_state:
        st.session_state["ai_model"] = openai_model
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

    with st.chat_message("assistant"):
        results = query_collection(prompt, st.session_state.collection_to_talk)

        context = "\n".join(results["documents"][0])
        clean_context = context.strip()
        print(clean_context)

        if st.session_state["ai_model"] == openai_model:
            st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
            stream = openai_client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": m["role"], "content": m["content"] + "Greife zur Beantwortung der Frage auf die folgenden Informationen zurück" + clean_context}
                    for m in st.session_state.messages
                ],
                stream=True,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.response_tokens,
            )
            response = st.write_stream(stream)
        elif st.session_state["ai_model"] == anthropic_model:
            with anthropic_client.messages.stream(
                model=anthropic_model,
                system=st.session_state.primer,
                messages=[
                    {"role": m["role"], "content": m["content"] + context}
                    for m in st.session_state.messages if m["role"] != "system"
                ],
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.response_tokens,
            ) as stream:
                response_container = st.empty()
                response = ""
                for text in stream.text_stream:
                    response += text
                    response_container.write(response)
        elif st.session_state["ai_model"] == mistral_model:
            st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
            stream_response = mistral_client.chat_stream(
                model=mistral_model,
                messages=[
                    {"role": m["role"], "content": m["content"] + context}
                    for m in st.session_state.messages
                ],
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.response_tokens,
            )
            response_container = st.empty()
            response = ""
            for text in stream_response:
                response += text.choices[0].delta.content
                response_container.write(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
        return response

def main():
    initialize_session_state()

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.session_state.response_tokens = st.slider('Maximale Ausgabe:', 0, 4000, 1000)

    with col2:
        st.session_state.temperature = st.slider('Kreativität:', 0, 100, 70, help="Gemessen in Tokens, ca. 1,7 Token pro Wort")
        st.session_state.temperature /= 100

    with col3:
        st.session_state.primer = "None"
        st.session_state.role_names = db.get_role_names()
        st.session_state.selected_role_name = st.selectbox(
            "Wählen Sie den Experten:",
            st.session_state.role_names,
            placeholder="Wähle Rollenbeschreibung",
            index=0
        )
        if st.session_state.selected_role_name:
            st.session_state.primer = db.get_description_by_name(st.session_state.selected_role_name)
            st.session_state.aimodel = db.get_aimodel_by_name(st.session_state.selected_role_name)
            st.session_state["ai_model"] = st.session_state.aimodel

    with col4:
        st.session_state.collection_to_talk = st.selectbox(
            "Wählen Sie eine Dokumenten-Sammlung:",
            options=list_collections(),
            index=0
        )

    st.divider()

    display_chat_history()

    if prompt := st.chat_input("Stellen Sie eine Frage oder geben Sie eine Anweisung..."):
        process_user_input(prompt)

    add_menu()

if __name__ == "__main__":
    main()