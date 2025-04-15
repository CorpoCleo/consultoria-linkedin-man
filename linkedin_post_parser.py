from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime
from dateutil.parser import parse

import streamlit as st
LINKEDIN_EMAIL = st.secrets["LINKEDIN_EMAIL"]
LINKEDIN_PASSWORD = st.secrets["LINKEDIN_PASSWORD"]


def extraire_infos_linkedin(url):
    print(f"🔐 Connexion à LinkedIn pour récupérer : {url}")

    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    infos = {
        "🎯 Organisation / Client": None,
        "🔗 Lien": url,
        "📎 Lien TDR": [],
        "🌍 Pays": None,
        "📅 Date de publication": None,
        "Deadline": [],
        "Email de contact": None
    }

    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        driver.find_element(By.ID, "username").send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(3)

        driver.get(url)
        time.sleep(4)

        body = driver.find_element(By.TAG_NAME, "body").text.strip()
        lines = body.splitlines()

        # 📧 Email(s)
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", body)
        if emails:
            infos["Email de contact"] = emails[0]
            domaine = emails[0].split("@")[1].split(".")[0]
            infos["🎯 Organisation / Client"] = domaine.capitalize()

        # 🧠 Nom auteur LinkedIn (fallback organisation)
        if not infos["🎯 Organisation / Client"]:
            try:
                auteur_element = driver.find_element(By.CSS_SELECTOR, "span.feed-shared-actor__name")
                auteur_nom = auteur_element.text.strip()
                if auteur_nom and len(auteur_nom.split()) <= 6:
                    infos["🎯 Organisation / Client"] = auteur_nom
            except:
                pass

        # 📄 Recherche heuristique dans le corps
        if not infos["🎯 Organisation / Client"]:
            ignore_keywords = ["appel à consultance", "consultance", "convocatoria", "vacante", "opportunité"]
            for line in lines:
                if line.strip().startswith("🧰") or any(kw in line.lower() for kw in ignore_keywords):
                    continue
                if re.search(r"(consultance|appel|convocatoria|recherche|mission)", line, re.IGNORECASE):
                    parts = re.split(r"–|-|:|\\|", line)
                    for part in parts[::-1]:
                        part = part.strip()
                        if len(part.split()) <= 5 and not any(kw in part.lower() for kw in ignore_keywords):
                            infos["🎯 Organisation / Client"] = part.title()
                            break
                if infos["🎯 Organisation / Client"]:
                    break

        # 🔗 Si lien TDR contient nom identifiable (sauf raccourcisseurs)
        if not infos["🎯 Organisation / Client"]:
            links = re.findall(r"https?://\S+", body)
            for l in links:
                if any(domain in l for domain in ["lnkd.in", "bit.ly", "tinyurl.com"]):
                    continue
                domaine = re.findall(r"https?://(?:www\.)?([\w\-]+)\.", l)
                if domaine:
                    infos["🎯 Organisation / Client"] = domaine[0].capitalize()
                    break

        # 📛 Dernier recours : détection nom propre (2 mots majuscules)
        if not infos["🎯 Organisation / Client"]:
            candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", body)
            if candidates:
                infos["🎯 Organisation / Client"] = candidates[0]

        # ⏳ Deadline
        dates_valides = []
        for line in lines:
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

        # 🌍 Pays
        pays_match = re.findall(r"(?i)\b(?:en\s+|in\s+)?(Colombia|México|France|Perú|Tunisie|Chile|RDC|Honduras|Espagne|Argentine|Guatemala|Sénégal|Haïti|Maroc|Mali|Burkina Faso)\b", body)
        if pays_match:
            infos["🌍 Pays"] = ", ".join(set([p.title() for p in pays_match]))

        # 📎 Lien TDR (exclure LinkedIn)
        links = re.findall(r"https?://\S+", body)
        tdr_links = [l for l in links if "linkedin.com" not in l and len(l) < 200]
        infos["📎 Lien TDR"] = tdr_links

    except Exception as e:
        print("❌ Erreur :", e)

    finally:
        driver.quit()

    return infos
