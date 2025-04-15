import requests
import streamlit as st 

AIRTABLE_TOKEN = st.secrets["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def envoyer_vers_airtable(infos):
    print("📤 Données à envoyer vers Airtable :")
    print(infos)

    params = {"filterByFormula": f"{{🔗 Lien}} = '{infos['🔗 Lien']}'"}
    check = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)

    print("🔍 Vérification doublon - statut:", check.status_code)

    if check.status_code == 200 and check.json().get("records"):
        print("⚠️ Ce lien existe déjà dans Airtable. Aucune donnée envoyée.")
        return

    data = {
        "fields": {
            "🎯 Organisation / Client": infos.get("🎯 Organisation / Client", ""),
            "🔗 Lien": infos.get("🔗 Lien", ""),
            "📎 Lien TDR": ", ".join(infos.get("📎 Lien TDR", [])),
            "📅 Date de publication": infos.get("📅 Date de publication", ""),
            "Deadline": ", ".join(infos.get("Deadline", [])),
            "Email de contact": infos.get("Email de contact", ""),
            "🌍 Pays": infos.get("🌍 Pays", "")
        }
    }

    print("📤 Requête envoyée à Airtable :")
    print(data)

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)

    print("📥 Réponse d’Airtable :")
    print("Status:", response.status_code)
    print("Texte:", response.text)

    if response.status_code in [200, 201]:
        print("✅ Données envoyées à Airtable avec succès !")
    else:
        print("❌ Échec de l’envoi vers Airtable")
