from faster_whisper import WhisperModel
from tempfile import NamedTemporaryFile
import streamlit as st
from home import add_menu

def transcribe_podcast_faster(file_path):
    model_size = "tiny"
    # Passen Sie die device und compute_type Parameter entsprechend Ihrer Umgebung an
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(file_path, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    full_text = "\n".join([segment.text for segment in segments])
    return full_text

def save_uploaded_file(uploaded_file):
    try:
        with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        return None

st.title('Speech2Text')
st.subheader('Transkribieren Sie Podcasts oder Sprachaufnahmen.')
uploaded_file = st.file_uploader("Laden Sie hier Ihre MP3 hoch:", type="mp3")

if st.button('Transkription starten!'):
    if uploaded_file is not None:
        file_path = save_uploaded_file(uploaded_file)
        if file_path:
            with st.spinner('Transkription läuft...'):
                full_text = transcribe_podcast_faster(file_path)
                st.success('Transkription abgeschlossen!')
                st.code(full_text, language="python")
        else:
            st.error("Fehler beim Hochladen der Datei.")
    else:
        st.warning("Bitte lade eine MP3-Datei hoch.")


add_menu()
