from faster_whisper import WhisperModel
from tempfile import NamedTemporaryFile

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
