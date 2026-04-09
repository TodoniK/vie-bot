#!/usr/bin/python3
import requests
import json
import re
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Charge les variables d'environnement depuis .env
load_dotenv()

#---------------CONFIGURATION---------------
# Configuration Discord Webhook (depuis variable d'environnement)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

if not DISCORD_WEBHOOK_URL:
    print("[ERREUR] La variable d'environnement DISCORD_WEBHOOK_URL n'est pas definie")
    print("[INFO] Creez un fichier .env a partir de .env.example et configurez votre webhook")
    exit(1)

# Chemins de fichiers (relatif au script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IDS_FILE = os.path.join(SCRIPT_DIR, 'ids.txt')

# Configuration API
API_BASE_URL = "https://civiweb-api-prd.azurewebsites.net/api"
API_SEARCH_URL = f"{API_BASE_URL}/Offers/search"
API_DETAILS_URL = f"{API_BASE_URL}/Offers/details"

#---------------FONCTIONS---------------
def log(message):
    """Affiche un message avec timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_existing_ids(filename):
    """Récupère les VIE déjà connus depuis le fichier"""
    try:
        with open(filename, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        log(f"Fichier {filename} non trouvé, création d'un nouveau fichier")
        return set()

def write_new_ids(filename, ids):
    """Sauvegarde les nouveaux VIE dans le fichier"""
    with open(filename, 'a') as f:
        for id in ids:
            f.write(f'{id}\n')

def format_date(date_string):
    """Formate une date ISO en format lisible (DD/MM/YYYY)"""
    if not date_string:
        return "N/A"
    try:
        date_part = date_string.split('T')[0]
        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
        return date_obj.strftime('%d/%m/%Y')
    except:
        return date_string

def clean_contact_name(contact_name):
    """Nettoie le nom du contact pour LinkedIn"""
    if not contact_name:
        return ""
    contact_name = contact_name.strip()
    # Supprime les civilités
    contact_name = re.sub(r'^(Madame|Monsieur)\s+', '', contact_name, flags=re.IGNORECASE)
    contact_name = contact_name.strip()
    return contact_name.replace(' ', '%20')

def get_offer_details(offer_id):
    """Récupère les détails d'une offre via l'API"""
    try:
        url = f"{API_DETAILS_URL}/{offer_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log(f"Erreur lors de la récupération des détails de l'offre {offer_id}: {e}")
        return None

def send_discord_notification(offer_data):
    """Envoie une notification Discord pour une nouvelle offre"""
    try:
        offer_id = str(offer_data['id'])
        contact_name = clean_contact_name(offer_data.get('contactName', ''))
        linkedin_url = f"https://www.linkedin.com/search/results/all/?keywords={contact_name}" if contact_name else "N/A"
        businessfrance_url = f"https://mon-vie-via.businessfrance.fr/offres/{offer_id}"
        
        # Prépare le contenu de la notification
        fields = [
            {
                "name": "🏭 Entreprise",
                "value": offer_data.get('organizationName', 'N/A'),
                "inline": True
            },
            {
                "name": "🌍 Pays",
                "value": offer_data.get('countryName', 'N/A'),
                "inline": True
            },
            {
                "name": "🏙️ Ville",
                "value": offer_data.get('cityName', 'N/A').strip() if offer_data.get('cityName') else 'N/A',
                "inline": True
            }
        ]
        
        # Ajouter les autres champs
        fields.extend([
            {
                "name": "📅 Durée (mois)",
                "value": str(offer_data.get('missionDuration', 'N/A')),
                "inline": True
            },
            {
                "name": "🎬 Début",
                "value": format_date(offer_data.get('missionStartDate')),
                "inline": True
            },
            {
                "name": "🏁 Fin",
                "value": format_date(offer_data.get('missionEndDate')),
                "inline": True
            },
            {
                "name": "📧 Email",
                "value": offer_data.get('contactEmail', 'N/A'),
                "inline": True
            },
            {
                "name": "🌐 Business France",
                "value": f"[Voir Offre]({businessfrance_url})",
                "inline": True
            },
            {
                "name": "🔗 LinkedIn",
                "value": f"[Rechercher Contact]({linkedin_url})" if contact_name else "N/A",
                "inline": True
            },
            {
                "name": "💼 Télétravail",
                "value": "✅ Oui" if offer_data.get('teleworkingAvailable') else "❌ Non",
                "inline": True
            },
            {
                "name": "💵 Indemnité",
                "value": f"{offer_data.get('indemnite', 0):.2f} €",
                "inline": True
            },
            {
                "name": "📆 Date de publication",
                "value": format_date(offer_data.get('creationDate')),
                "inline": True
            }
        ])
        
        content = {
            "embeds": [
                {
                    "title": offer_data.get('missionTitle', 'Sans titre'),
                    "fields": fields,
                    "color": 3447003,  # Bleu
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(content),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        log(f"[OK] Notification envoyee pour l'offre {offer_id}")
        return True
    except Exception as e:
        log(f"[ERREUR] Erreur lors de l'envoi de la notification Discord: {e}")
        return False

#---------------SCRIPT PRINCIPAL---------------
log("[START] Debut de la recherche de nouvelles offres VIE")

# Configuration de la recherche
payload = {
    "limit": int(os.getenv('SEARCH_LIMIT', 5000)),
    "skip": 0,
    "studiesLevelId": ["4"],
    "teletravail": ["0"],
    "porteEnv": ["0"],
    "activitySectorId": [],
    "missionsTypesIds": [],
    "missionsDurations": [],
    "geographicZones": [],
    "countriesIds": [],
    "companiesSizes": [],
    "specializationsIds": [],
    "entreprisesIds": [0],
}

# Envoi de la requete de recherche
try:
    log(f"[API] Interrogation de l'API: {API_SEARCH_URL}")
    response = requests.post(
        API_SEARCH_URL,
        data=json.dumps(payload),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://mon-vie-via.businessfrance.fr',
            'Referer': 'https://mon-vie-via.businessfrance.fr/',
            'User-Agent': 'Mozilla/5.0'
        },
        timeout=30
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    log(f"[ERREUR] Erreur lors de la requete API: {e}")
    exit(1)

# Traitement de la réponse
if response.status_code == 200:
    data = response.json()
    total_count = data.get('count', 0)
    log(f"[STATS] Total d'offres correspondantes: {total_count}")
    
    # Extraction des IDs des offres
    offers = data.get('result', [])
    if not offers:
        log("[INFO] Aucune offre trouvee")
        exit(0)
    
    ids = [item['id'] for item in offers]
    log(f"[STATS] {len(ids)} offres recuperees")
    
    # Recuperation des IDs deja connus
    existing_ids = get_existing_ids(IDS_FILE)
    log(f"[STATS] {len(existing_ids)} offres deja connues")
    
    # Identification des nouvelles offres
    new_ids = [id for id in ids if str(id) not in existing_ids]
    
    if new_ids:
        log(f"[NEW] {len(new_ids)} nouvelle(s) offre(s) detectee(s)")
        
        # Récupération des détails de toutes les nouvelles offres pour tri
        new_offers_details = []
        for new_id in new_ids:
            offer_details = get_offer_details(new_id)
            if offer_details:
                new_offers_details.append(offer_details)
            else:
                log(f"[WARNING] Impossible de recuperer les details de l'offre {new_id}")
        
        if not new_offers_details:
            log("[INFO] Aucune offre valide trouvee")
        else:
            # Tri des offres par date de création (ordre chronologique)
            new_offers_details.sort(key=lambda x: x.get('creationDate', ''), reverse=False)
            log(f"[SORT] {len(new_offers_details)} offre(s) triee(s) par ordre chronologique")
            
            # Envoi des notifications
            success_count = 0
            processed_ids = []
            for idx, offer_details in enumerate(new_offers_details, 1):
                offer_id = offer_details['id']
                log(f"[PROCESS] Traitement de l'offre {offer_id} ({idx}/{len(new_offers_details)})...")
                
                # Envoi de la notification Discord
                if send_discord_notification(offer_details):
                    success_count += 1
                    processed_ids.append(offer_id)
                    
                # Delai entre chaque notification pour eviter le rate limit Discord
                # Discord limite a ~5 requetes par seconde pour les webhooks
                if idx < len(new_offers_details):  # Pas de delai apres la derniere
                    time.sleep(1.5)  # Attendre 1.5 secondes entre chaque notification
            
            # Sauvegarde des IDs traités
            if processed_ids:
                write_new_ids(IDS_FILE, processed_ids)
                log(f"[SAVE] {len(processed_ids)} ID(s) sauvegarde(s) dans {IDS_FILE}")
            log(f"[SUCCESS] {success_count}/{len(new_offers_details)} notification(s) envoyee(s) avec succes")
    else:
        log("[INFO] Aucune nouvelle offre trouvee")

else:
    log(f"[ERREUR] La requete API a echoue avec le code {response.status_code}")
    exit(1)

log("[DONE] Recherche terminee")
