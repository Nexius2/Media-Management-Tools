# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
#########################################################
# Media Management Tools (MMT) - Radarr Unmonitor
# Auteur       : Nexius2
# Date         : 2025-02-18
# Version      : 1.0
# Description  : Script permettant de désactiver le monitoring
#                des films dans Radarr en fonction des critères
#                définis dans `config.json`.
# Licence      : MIT
#########################################################

# 📌 Utilisation :
# Exécuter le script via la ligne de commande :
#   python radarr_unmonitor.py
#
# Mode Simulation (Dry-Run) :
#   - Défini dans `config.json`, le mode Dry-Run affiche les films
#     qui seraient désactivés sans les modifier réellement.
#
# Mode Exécution :
#   - Modifier "dry_run": false dans `config.json` pour que le script
#     applique réellement les modifications.

# 🔹 Dépendances :
# - Python 3.x
# - Module `requests` (pip install requests)

# 🔧 Configuration :
# - Vérifiez que `config.json` est bien rempli avec l'URL et la clé API.
# - Ajoutez ou modifiez les critères de désactivation selon vos besoins.

# 📝 Journalisation :
# - Les logs sont enregistrés dans radarr_unmonitor.log
# - Inclut les films traités, les erreurs et les mises à jour effectuées.

#########################################################
"""


import requests
import json
import logging
from logging.handlers import RotatingFileHandler
import time


# Charger la configuration
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Erreur : fichier de configuration '{CONFIG_FILE}' introuvable.")
    exit(1)

# Extraire la configuration des services
RADARR_CONFIG = config["services"].get("radarr", {})

# Extraire la configuration spécifique à Radarr Unmonitor
UNMONITOR_CONFIG = config.get("radarr_unmonitor", {})

LOG_FILE = UNMONITOR_CONFIG.get("log_file", "radarr_unmonitor.log")
LOG_LEVEL = UNMONITOR_CONFIG.get("log_level", "INFO").upper()
DRY_RUN = UNMONITOR_CONFIG.get("dry_run", True)
SEARCH_TERMS = UNMONITOR_CONFIG.get("search_terms", ["1080", "FR", "MULTI"])


# Vérifier la configuration Radarr
RADARR_URL = RADARR_CONFIG.get("url")
RADARR_API_KEY = RADARR_CONFIG.get("api_key")

if not RADARR_URL or not RADARR_API_KEY:
    print("❌ Configuration Radarr manquante ou incomplète dans 'config.json'.")
    exit(1)

# Initialisation du logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configuration du système de logs avec rotation
LOG_FILE = UNMONITOR_CONFIG.get("log_file", "radarr_unmonitor.log")
LOG_LEVEL = UNMONITOR_CONFIG.get("log_level", "INFO").upper()

# Création du gestionnaire de logs avec rotation
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)  # 5 MB par fichier, 5 backups max
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.handlers = []  # Supprime tous les handlers existants pour éviter les doublons
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logging.info("📝 Système de logs avec rotation activé.")


HEADERS = {"X-Api-Key": RADARR_API_KEY, "Content-Type": "application/json"}

def get_movies():
    """ Récupère la liste des films dans Radarr et ne garde que ceux avec un fichier et monitorés """
    url = f"{RADARR_URL}/api/v3/movie"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        movies = response.json()
        logging.info(f"📥 {len(movies)} films récupérés depuis Radarr.")

        # Filtrage pour ne garder que les films monitorés et avec un fichier
        filtered_movies = [
            movie for movie in movies
            if movie.get("monitored", False) and movie.get("movieFile", {}).get("relativePath")
        ]

        logging.info(f"✅ {len(filtered_movies)} films sélectionnés après filtrage (monitorés et avec un fichier).")
        return filtered_movies
    else:
        logging.error(f"❌ Erreur lors de la récupération des films : {response.status_code} - {response.text}")
        return []




def should_unmonitor(movie):
    """ Vérifie si un film doit être désactivé en fonction du nom du fichier """
    title = movie.get("title", "Titre inconnu")
    year = movie.get("year", "Année inconnue")
    movie_id = movie.get("id")
    
    # On est sûr que movieFile et relativePath existent
    relative_path = movie["movieFile"]["relativePath"].lower()

    logging.debug(f"🔍 Analyse du film : {title} ({year}, ID: {movie_id}) - Fichier détecté : {relative_path}")

    # Vérification des termes dans tous les ensembles de critères
    for search_group in SEARCH_TERMS:
        if all(term.lower() in relative_path for term in search_group):
            logging.info(f"🎯 Film détecté : {title} ({year}, ID: {movie_id}) - Fichier: {relative_path} - Correspondance: {search_group}")
            return True

    logging.debug(f"🚫 Le film '{title}' ({year}, ID: {movie_id}) ne correspond à aucun critère de désactivation.")
    return False


def unmonitor_movie(movie, dry_run_list):
    """ Désactive le monitoring d'un film dans Radarr et stocke les films traités en mode DRY_RUN """
    movie_id = movie["id"]
    title = movie.get("title", "Titre inconnu")
    year = movie.get("year", "Année inconnue")

    logging.info(f"🛠️ Traitement du film '{title}' ({year}, ID: {movie_id})...")

    if DRY_RUN:
        logging.info(f"[DRY_RUN] 🚀 Film '{title}' ({year}, ID: {movie_id}) aurait été marqué comme NON MONITORÉ ✅")
        dry_run_list.append(f"{title} ({year}, ID: {movie_id})")
        return

    url = f"{RADARR_URL}/api/v3/movie/{movie_id}"
    movie["monitored"] = False  # Désactiver le monitoring

    max_retries = 5  # Nombre de tentatives en cas d'échec
    for attempt in range(max_retries):
        response = requests.put(url, headers=HEADERS, json=movie)

        if response.status_code == 200:
            logging.info(f"✅ Film '{title}' ({year}, ID: {movie_id}) marqué comme NON MONITORÉ avec succès.")
            break
        elif response.status_code == 202:
            logging.warning(f"⚠️ Radarr est lent à traiter '{title}' ({year}, ID: {movie_id}). Vérification après 3 secondes...")
            time.sleep(3)  # Pause courte avant vérification

            # Vérifier si le film a bien été mis à jour
            check_response = requests.get(url, headers=HEADERS)
            if check_response.status_code == 200:
                updated_movie = check_response.json()
                if not updated_movie.get("monitored", True):  # Si monitored est bien passé à False
                    logging.info(f"✅ Vérification OK : Film '{title}' ({year}, ID: {movie_id}) est bien NON MONITORÉ après attente.")
                    break
            else:
                logging.warning(f"⚠️ Impossible de vérifier l'état de '{title}' ({year}, ID: {movie_id}) après mise à jour.")
        else:
            logging.error(f"❌ Erreur mise à jour film {movie_id}: {response.status_code} - {response.text}")
            break

    # Pause courte pour éviter un trop grand nombre de requêtes simultanées
    time.sleep(1)





def main():
    logging.info("🚀 Début du traitement des films dans Radarr...")

    movies = get_movies()
    if not movies:
        logging.warning("⚠️ Aucun film trouvé dans Radarr.")
        return

    total_processed = 0
    dry_run_list = []  # Liste pour stocker les films traités en mode DRY_RUN

    for movie in movies:
        if should_unmonitor(movie):
            unmonitor_movie(movie, dry_run_list)
            total_processed += 1

    if DRY_RUN and dry_run_list:
        logging.info(f"[DRY_RUN] 📋 Films qui auraient été désactivés ({len(dry_run_list)}):")
        for film in dry_run_list:
            logging.info(f"  - {film}")

    logging.info(f"✅ Fin du traitement. {total_processed} films ont été désactivés.")



if __name__ == "__main__":
    main()
