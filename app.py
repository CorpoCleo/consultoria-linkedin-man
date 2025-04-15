import streamlit as st
import re
import requests
from datetime import datetime
from dateutil.parser import parse
from PyPDF2 import PdfReader

st.set_page_config(page_title="Consultoria - LinkedIn Parser", layout="centered")
st.title("📋 Analyse de post LinkedIn")
st.markdown("Colle ici le **texte complet** d’un post LinkedIn ou téléverse un fichier PDF pour extraire les infos et les envoyer vers Airtable.")

texte = st.text_area("📝 Texte du post LinkedIn", height=300)
fichier_pdf = st.file_uploader("📄 Ou téléverse un fichier PDF", type=["pdf"])
lien_tdr = st.text_input("🔗 Lien du post LinkedIn ou TDR")
bouton = st.button("🚀 Envoyer vers Airtable")

# Chargement des secrets
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

def analyser_texte(body, lien_tdr):
    links = re.findall(r"https?://\S+", body)
    tdr_links = [l for l in links if "linkedin.com" not in l and len(l) < 200]

    infos = {
        "🎯 Organisation / Client": None,
        "🔗 Lien": lien_tdr or (links[0] if links else "Texte libre"),
        "📎 Lien TDR": tdr_links,
        "🌍 Pays": None,
        "📅 Date de publication": None,
        "Deadline": [],
        "Email de contact": None
    }

    # Email
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", body)
    if emails:
        infos["Email de contact"] = ", ".join(set(emails))
        domaine = emails[0].split("@")[1].split(".")[0]
        infos["🎯 Organisation / Client"] = domaine.capitalize()

    # Fallback organisation : ligne avec mot-clé et majuscule
    if not infos["🎯 Organisation / Client"]:
        for line in body.splitlines():
            if re.search(r"(Convocatoria|Appel|Consultance|Consultoría).*?[A-ZÉ][a-zéèê]+", line):
                possible = re.sub(r".*?–\s*", "", line)
                if len(possible.split()) <= 5:
                    infos["🎯 Organisation / Client"] = possible.strip()
                    break

    # Deadline (même sans mot-clé)
    dates_valides = []
    for line in body.splitlines():
        if re.search(r"(fecha|limite|deadline|limit[eé])", line, re.IGNORECASE):
            date_candidates = re.findall(
                r"\b\d{1,2}\s+de\s+\w+(?:\s+\d{4})?|\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{1,2}-\d{1,2}(?:-\d{2,4})?",
                line,
                re.IGNORECASE
            )
            for raw in date_candidates:
                try:
                    clean = raw.strip()
                    if not re.search(r"\d{4}", clean):
                        clean += f" {datetime.now().year}"
                    parsed = parse(clean, fuzzy=True, dayfirst=True)
                    if parsed.date() >= datetime.now().date():
                        dates_valides.append(parsed.strftime("%d %B %Y"))
                except Exception as e:
                    print(f"⚠️ Erreur parsing deadline: {raw} -> {e}")
    infos["Deadline"] = list(set(dates_valides))

    # Pays (ajout de Costa Rica)
    pays_match = re.findall(r"(?i)\b(?:en\s+|in\s+)?(Colombia|México|France|Perú|Tunisie|Chile|RDC|Honduras|Espagne|Argentine|Guatemala|Sénégal|Haïti|Maroc|Mali|Burkina Faso|Costa Rica)\b", body)
    if pays_match:
        infos["🌍 Pays"] = ", ".join(set([p.title() for p in pays_match]))

    return infos

def envoyer_vers_airtable(donnees):
    payload = {
        "fields": {
            "🎯 Organisation / Client": donnees.get("🎯 Organisation / Client"),
            "🔗 Lien": donnees.get("🔗 Lien"),
            "📎 Lien TDR": ", ".join(donnees.get("📎 Lien TDR", [])),
            "🌍 Pays": donnees.get("🌍 Pays"),
            "📅 Date de publication": donnees.get("📅 Date de publication"),
            "Deadline": ", ".join(donnees.get("Deadline", [])),
            "Email de contact": donnees.get("Email de contact")
        }
    }
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        st.success("✅ Données envoyées à Airtable avec succès !")
    else:
        st.error(f"❌ Erreur Airtable: {response.status_code} → {response.text}")

# Priorité au PDF s’il est fourni
if bouton:
    contenu = texte
    if fichier_pdf is not None:
        try:
            pdf_reader = PdfReader(fichier_pdf)
            contenu = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        except Exception as e:
            st.error(f"Erreur de lecture du PDF : {e}")

    if contenu:
        resultat = analyser_texte(contenu, lien_tdr)
        st.success("🎯 Extraction terminée. Données envoyées automatiquement.")
        st.json(resultat)
        envoyer_vers_airtable(resultat)
    else:
        st.warning("📭 Aucun texte à analyser.")
