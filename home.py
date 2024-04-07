import streamlit as st
from streamlit_extras.app_logo import add_logo
from streamlit_extras.bottom_container import bottom



st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items = {
        'Get Help': 'mailto:support@stefanai.de',
        'Report a bug': "https://stefanai.de",
        'About': "Luminis ist ein KI-Testlabor, um öffentlichen Verwaltungen leicht Zugang zu generativer künstlicher Intelligenz zu bekommen. Es ist angebunden an alle großen KI-Modell, wie ChatGPT, Claude und Mistral. Luminis kann verwendet werden, um jeden Anwendungsfall im Bereich KI selbständig zu erforschen! Für Luminis verantwortlich ist StefanAI - Research & Development."
    }
)

def add_menu():
    st.sidebar.image("luminis_logo.png", use_column_width=True)
    st.sidebar.title("Navigation:")
    st.sidebar.page_link("home.py", label="Home")
    st.sidebar.page_link("pages/text2text.py", label="Text2Text (Chat)")
    st.sidebar.page_link("pages/text2image.py", label="Text2Image")
    st.sidebar.page_link("pages/speech2text.py", label="Speech2Text")
    st.sidebar.page_link("pages/text2speech.py", label="Text2Speech")
    st.sidebar.divider()
    st.sidebar.page_link("pages/rollen.py", label="Rollen")
    st.sidebar.page_link("pages/dokumente.py", label="Dokumente")
    st.sidebar.page_link("pages/tools.py", label="Tools")
    st.sidebar.title("Hinweis")
    st.sidebar.error("Bitte beachten Sie, dass dieses Tool nur für Testzwecke verwendet werden darf.")
    st.sidebar.write("© 2022 StefanAI - Research & Development")

add_menu()

st.title("Willkommen bei Luminis!")

















