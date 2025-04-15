import streamlit as st
import re
import requests
from datetime import datetime
from dateutil.parser import parse

st.set_page_config(page_title="Consultoria - LinkedIn Parser", layout="centered")
st.title("📋 Analyse de post LinkedIn")
st.markdown("Colle ici le **texte complet** d’un post LinkedIn pour extraire les infos et les envoyer vers Airtable.")

texte = st.text_area("📝 Texte du post LinkedIn", height=300)
lien_tdr = st.text_input("📎 Lien vers les TDR (optionnel)")
bouton = st.button("🚀 Envoyer vers Airtable")

# Chargement des secrets
AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

def analyser_texte(body, lien_tdr):
    infos = {
        "🎯 Organisation / Client": None,
        "🔗 Lien": "Texte libre",
        "📎 Lien TDR": [lien_tdr] if lien_tdr else [],
        "🌍 Pays": None,
        "📅 Date de publication": None,
        "Deadline": [],
        "Email de contact": None
    }

    # Email
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", body)
    if emails:
        infos["Email de contact"] = emails[0]
        domaine = emails[0].split("@")[1].split(".")[0]
        infos["🎯 Organisation / Client"] = domaine.capitalize()

    # Fallback organisation : première ligne avec majuscules
    if not infos["🎯 Organisation / Client"]:
        lignes = body.splitlines()
        for ligne in lignes:
            if re.match(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", ligne):
                infos["🎯 Organisation / Client"] = ligne.strip()
                break

    # Deadline
    dates_valides = []
    for line in body.splitlines():
        if not re.search(r"(date limite|fecha límite|deadline|fecha de cierre|limite de soumission)", line, re.IGNORECASE):
            continue
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

    # Pays
    pays_match = re.findall(r"(?i)\b(?:en\s+|in\s+)?(Colombia|México|France|Perú|Tunisie|Chile|RDC|Honduras|Espagne|Argentine|Guatemala|Sénégal|Haïti|Maroc|Mali|Burkina Faso)\b", body)
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

if bouton and texte:
    resultat = analyser_texte(texte, lien_tdr)
    st.success("🎯 Extraction terminée. Données envoyées automatiquement.")
    st.json(resultat)
    envoyer_vers_airtable(resultat)


