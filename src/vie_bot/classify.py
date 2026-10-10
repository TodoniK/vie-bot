"""Classification des offres VIE par mots-clés (titre du poste).

Listes calibrées le 28/08/2026 sur ~655 offres réelles récupérées via
l'API (voir historique de conversation). Titre uniquement : les champs
structurés de l'offre (activitySectorN1, specialization...) sont vides
ou non documentés côté API, donc inexploitables.

Pour ajuster les critères sans rebuild : variables d'environnement
IT_COUNTRIES, IT_EXTRA_KEYWORDS, HR_EXTRA_KEYWORDS, EXCLUDE_EXTRA_KEYWORDS
(listes séparées par des virgules, ajoutées aux listes ci-dessous).
"""

from vie_bot.config import csv, settings

# Codes ISO 3166-1 alpha-2. Défaut : Amérique du Nord + Océanie + Asie du Sud-Est
IT_COUNTRIES = {c.upper() for c in csv(settings.it_countries)}

# Mots-clés IT/réseau (phrases composées pour éviter les faux positifs :
# "ingénieur"/"developer"/"ia"/"réseau" seuls matchent des postes hors sujet
# comme "Ingénieur HSE" ou "Ingénieur Réseaux Électriques").
IT_INCLUDE = [
    "devops", "dev ops", "devsecops", "site reliability engineer", " sre ", "sre)", "sre –", "sre-",
    "cloud engineer", "cloud architect", "cloud/devops", "cloud/dev",
    "solution architect", "architecte solution", "intégrateur de solution", "solution integrator",
    "software engineer", "software developer", "ingénieur logiciel", "développeur logiciel", "software",
    "full stack", "fullstack", "backend", "front-end", "frontend", "back-end",
    "développeur", "développeuse", "developer",
    "data scientist", "data engineer", "machine learning", "intelligence artificielle",
    " ia agentique", "ai engineer", "computer vision", "deep learning",
    "cybersécurité", "cyber security", "cybersecurity", "cyber risk", "cybersoc", "cyber incident",
    "systèmes et réseaux", "network engineer", "ingénieur réseau informatique",
    "it project manager", "it application support", "it support", "chef de projet it",
    "administrateur système", "sysadmin", "sap technical",
] + [k.lower() for k in csv(settings.it_extra_keywords)]

# Annule un match IT (ex: "Business Developer", "Recruteur IT" -> pas de l'ingénierie)
IT_EXCLUDE = [
    "business developer", "développeur d’affaires", "développeur d'affaires",
    "développeuse d’affaires", "chargé de développement", "responsable développement",
    "business development", "recruteur", "recruiter", "staffing", "procurement",
    "achats", "business manager",
] + [k.lower() for k in csv(settings.exclude_extra_keywords)]

# Mots-clés RH — pas de restriction géographique
HR_INCLUDE = [
    "ressources humaines", "human resources", "hrbp", "hr business partner", " rh ", "hr ",
    "recruteur", "recruiter", "talent acquisition", "recrutement", "chargé de recrutement",
    "payroll", "paie", "compensation & benefits", "c&b", "hris", "talent management", "sap hr",
] + [k.lower() for k in csv(settings.hr_extra_keywords)]


def classify_offer(offer: dict) -> str | None:
    """Retourne "it", "hr" ou None selon le titre (et le pays pour IT)."""
    title = f" {(offer.get('missionTitle') or '').lower()} "

    if any(k in title for k in HR_INCLUDE):
        return "hr"

    has_it = any(k in title for k in IT_INCLUDE)
    has_exclude = any(k in title for k in IT_EXCLUDE)
    if has_it and not has_exclude and offer.get("countryId") in IT_COUNTRIES:
        return "it"

    return None

