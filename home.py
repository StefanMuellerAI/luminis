import streamlit as st

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Willkommen bei Luminis!")

col1a, col2a = st.columns([1, 1])

with col1a:
    st.subheader("Einführung zu Luminis:")
    st.video("https://www.youtube.com/watch?v=9SfM2gduQ1c")
with col2a:
    st.subheader("Aufgaben:")
    st.write("Luminis ist ein KI-Testlabor, um öffentlichen Verwaltungen leicht Zugang zu generativer künstlicher Intelligenz zu bekommen. Es ist angebunden an alle großen KI-Modell, wie ChatGPT, Claude und Mistral. Luminis kann verwendet werden, um jeden Anwendungsfall im Bereich KI selbständig zu erforschen! Für Luminis verantwortlich ist StefanAI - Research & Development.")

st.header("Über StefanAI - Research & Development")
col1b, col2b = st.columns([1, 4])
with col1b:
    st.image('StefanAI_Portrait.png', use_column_width=True)
with col2b:
    st.write("StefanAI - Research & Development ist ein Forschungs- und Entwicklungsunternehmen, das sich auf die Entwicklung von KI-Technologien spezialisiert hat. Wir bieten innovative Lösungen für Unternehmen und Organisationen, die ihre Prozesse optimieren und automatisieren möchten. Unser Team besteht aus Experten auf dem Gebiet der künstlichen Intelligenz, die über umfangreiche Erfahrung in der Entwicklung von KI-Systemen verfügen. Wir arbeiten eng mit unseren Kunden zusammen, um maßgeschneiderte Lösungen zu entwickeln, die ihren individuellen Anforderungen entsprechen. Unser Ziel ist es, unseren Kunden dabei zu helfen, ihre Geschäftsziele zu erreichen und Wettbewerbsvorteile zu erzielen.")


def add_menu():

    st.sidebar.image("luminis_logo.png", use_column_width=True)
    st.sidebar.markdown("v.0.1.0")
    st.sidebar.title("Navigation:")
    st.sidebar.page_link("home.py", label="Home")
    st.sidebar.page_link("pages/text2text.py", label="Text2Text (Chat)")
    st.sidebar.page_link("pages/text2image.py", label="Text2Image")
    st.sidebar.page_link("pages/speech2text.py", label="Speech2Text")
    st.sidebar.page_link("pages/text2speech.py", label="Text2Speech")
    st.sidebar.page_link("pages/text2video.py", label="Text2Video")
    st.sidebar.divider()
    st.sidebar.page_link("pages/rollen.py", label="Rollen")
    st.sidebar.page_link("pages/dokumente.py", label="Dokumente")
    st.sidebar.page_link("pages/tools.py", label="Tools")
    st.sidebar.title("Hinweis:")
    st.sidebar.error("Bitte beachten Sie, dass dieses Tool nur für Testzwecke verwendet werden darf und befindet sich im Beta-Stadium.")
    st.sidebar.markdown("[Impressum](stefanai.de/impressum) | [Datenschutz](stefanai.de/datenschutz) | [Kontakt](stefanai.de/kontakt)")
    st.sidebar.write("© 2024 StefanAI - Research & Development")

add_menu()



















