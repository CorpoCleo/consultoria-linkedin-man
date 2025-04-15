import streamlit as st
from linkedin_post_parser import extraire_infos_linkedin
from airtable_push import envoyer_vers_airtable

st.set_page_config(page_title="Consultoria LinkedIn", page_icon="📄")
st.title("📋 Analyse de post LinkedIn")
st.markdown("Colle un lien LinkedIn pour extraire automatiquement les infos et les envoyer vers Airtable.")

url = st.text_input("🔗 Lien du post LinkedIn")

if st.button("🔍 Analyser et envoyer"):
    if not url:
        st.warning("Merci de coller un lien LinkedIn.")
    else:
        with st.spinner("Extraction en cours depuis LinkedIn..."):
            infos = extraire_infos_linkedin(url)

        st.success("🎯 Extraction terminée. Données envoyées automatiquement.")
        st.write("🚀 Données envoyées :")
        st.json(infos)

        envoyer_vers_airtable(infos)


