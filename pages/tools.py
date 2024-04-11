import streamlit as st
from fpdf import FPDF
import fitz  # PyMuPDF
from home import add_menu
from vector import count_tokens, convert_pdf_to_string
import io
import os

st.set_page_config(
    page_title="Luminis - KI-Labor und Lernplattform",
    page_icon="🥼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Tools')
st.subheader('Hier finden Sie Tools, die Ihnen bei der Arbeit mit KI helfen können.')

add_menu()

def pruefe_seitenbereich(start_seite, ende_seite):
    """
    Überprüft, ob der Seitenbereich gültig ist.
    :param start_seite: Die Startseite des Bereichs.
    :param ende_seite: Die Endseite des Bereichs.
    :return: True, wenn der Seitenbereich gültig ist, andernfalls False.
    """
    if start_seite > ende_seite:
        st.error("Die Startseite muss vor der Endseite liegen.")
        return False
    return True

def pdf_zu_text(datei_bytes, start_seite, ende_seite):
    """
    Extrahiert Text aus einem PDF-Dokument zwischen den angegebenen Seiten.
    :param datei_bytes: Die Bytes des PDF-Dokuments.
    :param start_seite: Die Startseite des Bereichs.
    :param ende_seite: Die Endseite des Bereichs.
    :return: Extrahierter Text als String.
    """
    with fitz.open(stream=datei_bytes, filetype="pdf") as doc:
        text = ''
        # Begrenze den Seitenbereich auf die Anzahl der Seiten im Dokument
        start_seite = max(1, start_seite)
        ende_seite = min(len(doc), ende_seite)
        for seitennummer in range(start_seite - 1, ende_seite):
            seite = doc.load_page(seitennummer)
            text += seite.get_text()
    return text

def extrahiere_seitenbereich_als_pdf(datei_bytes, start_seite, ende_seite):
    """
    Extrahiert einen Seitenbereich aus einem PDF-Dokument und speichert diesen als neues PDF-Dokument.
    :param datei_bytes: Die Bytes des PDF-Dokuments.
    :param start_seite: Die Startseite des Bereichs.
    :param ende_seite: Die Endseite des Bereichs.
    :return: BytesIO-Objekt des neuen PDF-Dokuments.
    """
    with fitz.open(stream=datei_bytes, filetype="pdf") as doc:
        neues_doc = fitz.open()
        # Begrenze den Seitenbereich auf die Anzahl der Seiten im Dokument
        start_seite = max(1, start_seite)
        ende_seite = min(len(doc), ende_seite)
        for seitennummer in range(start_seite - 1, ende_seite):
            seite = doc.load_page(seitennummer)
            neues_doc.insert_pdf(doc, from_page=seitennummer, to_page=seitennummer)
        # Speichere das neue PDF-Dokument in einem BytesIO-Objekt
        pdf_output = io.BytesIO()
        neues_doc.save(pdf_output, garbage=4, deflate=True)
        neues_doc.close()
    return pdf_output

def text_zu_pdf(text):
    """
    Konvertiert den gegebenen Text in ein PDF-Dokument.
    :param text: Der zu konvertierende Text.
    :return: BytesIO-Objekt des erstellten PDF-Dokuments.
    """
    pdf = FPDF()
    pdf.add_page()
    # Ermittle den absoluten Pfad zum 'fonts' Verzeichnis, relativ zum aktuellen Skript
    aktuelles_verzeichnis = os.path.dirname(__file__)
    schriftarten_pfad = os.path.join(aktuelles_verzeichnis, '..', '..', 'luminis/fonts', 'DejaVuSansCondensed.ttf')
    schriftarten_pfad = os.path.abspath(schriftarten_pfad)
    # Füge den Pfad zur Schriftart hinzu
    pdf.add_font('DejaVu', '', schriftarten_pfad, uni=True)
    # Verwende die DejaVu Schriftart
    pdf.set_font('DejaVu', '', 12)
    # Überprüfe, ob der Text leer ist
    if text.strip():
        pdf.multi_cell(0, 10, text)
    else:
        pdf.cell(0, 10, "Kein Text vorhanden.")
    # Speichere das PDF direkt in einer Datei
    pdf.output("output.pdf")
    # Öffne die PDF-Datei im Binärmodus und lies den Inhalt
    with open("output.pdf", "rb") as file:
        pdf_bytes = file.read()
    # Erstelle ein BytesIO-Objekt aus den gelesenen Bytes
    pdf_output = io.BytesIO(pdf_bytes)
    return pdf_output

def generiere_dateiname_pdf_bereich(datei_name, start_seite, ende_seite):
    """
    Generiert den Dateinamen für den extrahierten PDF-Bereich.
    :param datei_name: Der Name der ursprünglichen PDF-Datei.
    :param start_seite: Die Startseite des Bereichs.
    :param ende_seite: Die Endseite des Bereichs.
    :return: Der generierte Dateiname.
    """
    return f"{datei_name}_Seiten_{start_seite}_bis_{ende_seite}.pdf"

# Streamlit App
def main():
    st.subheader("PDF2Text-Extraktor")
    # Datei-Upload
    hochgeladene_datei = st.file_uploader("Wähle ein PDF-Dokument aus:", type="pdf")
    if hochgeladene_datei is not None:
        try:
            # Lese die Bytes des hochgeladenen Dokuments
            datei_bytes = hochgeladene_datei.getvalue()
            # Anzahl der Seiten und Token im PDF ermitteln
            with fitz.open(stream=datei_bytes, filetype="pdf") as doc:
                text = convert_pdf_to_string(datei_bytes)
                gesamt_seiten = len(doc)
                gesamt_token = count_tokens(text)
            st.write(f"Das Dokument hat {gesamt_seiten} Seiten und {gesamt_token} Token.")
            # Seitenbereich Auswahl
            start_seite1 = st.number_input("Startseite:", min_value=1, max_value=gesamt_seiten, value=1)
            ende_seite1 = st.number_input("Endseite:", min_value=1, max_value=gesamt_seiten, value=gesamt_seiten)
            if pruefe_seitenbereich(start_seite1, ende_seite1):
                if st.button("Text extrahieren!"):
                    text = pdf_zu_text(datei_bytes, start_seite1, ende_seite1)
                    # Entfernen überflüssiger Leerzeichen und Zeilenumbrüche
                    text = ' '.join(text.split())
                    st.text_area("Text", text, height=400, max_chars=None)
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der PDF-Datei: {str(e)}")

    st.subheader("Text2PDF-Konverter")
    # Textarea für den Benutzereingabetext
    text = st.text_area("Text hier eingeben:", height=250)
    filename = st.text_input("Dateiname:", "example")
    if st.button("In PDF umwandeln"):
        if text:
            pdf_output = text_zu_pdf(text)
            # Erstellt den Download-Button, damit der Benutzer das PDF herunterladen kann
            st.download_button(
                label="PDF herunterladen",
                data=pdf_output,
                file_name=f"{filename}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Bitte gib zuerst Text ein, um ihn in ein PDF umzuwandeln.")

    st.subheader("PDF2PDF-Extraktor")
    # Datei-Upload
    hochgeladene_datei = st.file_uploader("Wähle ein PDF-Dokument zum Zerlegen aus:", type="pdf")
    if hochgeladene_datei is not None:
        try:
            # Lese die Bytes des hochgeladenen Dokuments
            datei_bytes = hochgeladene_datei.getvalue()
            datei_name = hochgeladene_datei.name
            datei_name = datei_name.split('.')[0]
            # Anzahl der Seiten im PDF ermitteln
            with fitz.open(stream=datei_bytes, filetype="pdf") as doc:
                gesamt_seiten = len(doc)
            st.write(f"Das Dokument hat {gesamt_seiten} Seiten.")
            # Seitenbereich Auswahl
            start_seite2 = st.number_input("Startseite:", min_value=1, key="pdf2pdf_start", max_value=gesamt_seiten, value=1)
            ende_seite2 = st.number_input("Endseite:", min_value=1, key="pdf2pdf_ende", max_value=gesamt_seiten, value=gesamt_seiten)
            if pruefe_seitenbereich(start_seite2, ende_seite2):
                if st.button("PDF-Bereich extrahieren"):
                    pdf_output = extrahiere_seitenbereich_als_pdf(datei_bytes, start_seite2, ende_seite2)
                    file_name = generiere_dateiname_pdf_bereich(datei_name, start_seite2, ende_seite2)
                    # Erstellt den Download-Button, damit der Benutzer das PDF herunterladen kann
                    st.download_button(
                        label="PDF-Bereich herunterladen",
                        data=pdf_output,
                        file_name=file_name,
                        mime="application/pdf"
                    )
        except Exception as e:
            st.error(f"Fehler beim Verarbeiten der PDF-Datei: {str(e)}")

if __name__ == "__main__":
    main()