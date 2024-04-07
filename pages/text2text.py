import os
from openai import OpenAI
import database as db
from dotenv import load_dotenv
import streamlit as st
import anthropic
from mistralai.client import MistralClient
from vector import list_collections, query_collection
from home import add_menu

# Lädt Umgebungsvariablen aus einer .env-Datei
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)


st.title("Text2Text")
st.subheader("Interagieren Sie mit der KI und erhalten Sie Antworten auf Ihre Fragen.")

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
        options=["Keine"] + list_collections(), index=0)

st.divider()

if "ai_model" not in st.session_state:
    st.session_state["ai_model"] = "gpt-4-0125-preview"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Stellen Sie eine Frage oder geben Sie eine Anweisung..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        results = query_collection(prompt, st.session_state.collection_to_talk)
        context = "\n".join(results["documents"][0])
        if st.session_state["ai_model"] == "gpt-4-0125-preview":
            st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
            stream = openai_client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": m["role"], "content": m["content"] + context}
                    for m in st.session_state.messages
                ],
                stream=True,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.response_tokens,
            )
            response = st.write_stream(stream)
        elif st.session_state["ai_model"] == "claude-3-opus-20240229":
            with anthropic_client.messages.stream(
                model="claude-3-opus-20240229",
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
        elif st.session_state["ai_model"] == "mistral-large-latest":
            st.session_state.messages.append({"role": "system", "content": st.session_state.primer})
            stream_response = mistral_client.chat_stream(
                model="mistral-large-latest",
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

add_menu()