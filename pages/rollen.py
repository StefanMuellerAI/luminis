import os
from openai import OpenAI
import database as db
from PIL import Image
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import anthropic
from mistralai.client import MistralClient
from home import add_menu



load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

openai_client = OpenAI()
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)


st.title('Rollen Verwaltung')
st.subheader('Gib der KI verschiedene Rollen, um mit ihr besser zu interagieren.')
# Eingabefelder
with st.form("role_form", clear_on_submit=True):
    ai_model = st.selectbox('KI-Modell:', ['gpt-4-0125-preview', 'claude-3-opus-20240229', 'mistral-large-latest'],
                            help='Welches KI-Modell soll für diese Rolle verwendet werden?')
    name = st.text_input('Rollenname:', '', help='Wie soll die Rolle heißen?')

    description = st.text_area('Beschreibung der Rolle:', '', max_chars=1000,
                               help='Beschreibe die Rolle. Wenn der Chatbot mit Claude-3 läuft, kann diese Beschreibung länger ausfallen.')
    submitted = st.form_submit_button('Rolle speichern')
    if submitted:
        if len(description) > 50 and not db.role_name_exists(name):
            db.insert_role(name, description, ai_model)
        else:
            st.error('Beschreibung zu kurz (min. 50 Zeichen) oder Rollenname existiert bereits.')

# Rollenliste
st.subheader('Vorhandene Rollen')
roles = db.list_roles()
roles_df = pd.DataFrame(roles, columns=['id', 'Name', 'Beschreibung', 'KI-Modell'])
st.dataframe(roles_df[['id', 'Name', 'Beschreibung', 'KI-Modell']], hide_index=True)

# Abschnitt für das Löschen von Collections
st.subheader("Rollen löschen")
delete_role_name = st.selectbox("Wählen Sie ein Rolle aus:", roles_df['Name'].tolist())
if st.button("Bestehende Sammlung löschen!"):
    if delete_role_name:
        db.delete_role(name=delete_role_name)
        st.success(f"Sammlung '{delete_role_name}' wurde erfolgreich gelöscht.")
        st.rerun()

add_menu()