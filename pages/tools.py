import streamlit as st
from home import add_menu

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.title('Tools')
st.subheader('Hier finden Sie Tools, die Ihnen bei der Arbeit mit KI helfen können.')
add_menu()
