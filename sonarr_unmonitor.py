# -*- coding: utf-8 -*-

"""
#########################################################
# Media Management Tools (MMT) - Sonarr Unmonitor
# Auteur       : Nexius2
# Version      : 4.4
# Description  : Script permettant de désactiver le monitoring
#                des épisodes dans Sonarr en fonction des critères
#                définis dans `config.json`.
# Licence      : MIT
#########################################################
"""

import requests
import json
import logging
from logging.handlers import RotatingFileHandler
import re

# Charger la configuration
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Erreur : fichier de configuration '{CONFIG_FILE}' introuvable.")
    exit(1)

SONARR_CONFIG = config["services"].get("sonarr", {})
UNMONITOR_CONFIG = config.get("sonarr_unmonitor", {})

LOG_FILE = UNMONITOR_CONFIG.get("log_file", "sonarr_unmonitor.log")
LOG_LEVEL = UNMONITOR_CONFIG.get("log_level", "INFO").upper()
DRY_RUN = UNMONITOR_CONFIG.get("dry_run", True)
SEARCH_TERMS = UNMONITOR_CONFIG.get("search_terms", ["1080", "FR", "MULTI"])

SONARR_URL = SONARR_CONFIG.get("url")
SONARR_API_KEY = SONARR_CONFIG.get("api_key")

if not SONARR_URL or not SONARR_API_KEY:
    print("❌ Configuration Sonarr manquante ou incomplète dans 'config.json'.")
    exit(1)

# Initialisation du logging
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))
logger.handlers = []
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logging.info("📝 Système de logs activé.")

HEADERS = {"X-Api-Key": SONARR_API_KEY, "Content-Type": "application/json"}

def clean_filename(filename):
    """ Nettoie et normalise le nom du fichier pour améliorer la correspondance """
    filename = filename.lower()
    filename = filename.replace("1080p", "1080").replace("2160p", "4k")
    filename = re.sub(r"[\(\)\-_.]", " ", filename)  # Supprime tirets, underscores, points
    filename = re.sub(r"\s+", " ", filename).strip()  # Supprime les espaces multiples
    return filename

def get_episodes(series_id):
    """ Récupère les épisodes pour une série spécifique """
    episodes_url = f"{SONARR_URL}/api/v3/episode?seriesId={series_id}&includeEpisodeFile=true"
    response = requests.get(episodes_url, headers=HEADERS)
    
    if response.status_code != 200:
        logging.error(f"❌ Erreur lors de la récupération des épisodes pour la série {series_id}: {response.status_code}")
        return []
    
    episodes = response.json()
    logging.info(f"📌 {len(episodes)} épisodes récupérés pour la série {series_id}")
    return episodes

def should_unmonitor(episode):
    """ Vérifie si un épisode doit être marqué en 'unmonitored' """
    filename = episode.get("episodeFile", {}).get("relativePath", "")
    if not filename:
        logging.debug(f"🚫 Aucun fichier associé à l'épisode {episode['id']}")
        return False

    normalized_filename = clean_filename(filename)
    logging.debug(f"🔍 Vérification des critères pour : {normalized_filename}")

    # Fonction de vérification des termes avec une regex améliorée
    def match_criteria(term):
        """
        Vérifie si un terme est présent dans le nom du fichier en tant que mot distinct.
        - Autorise des variantes comme "1080p" en plus de "1080".
        """
        if term.isdigit():  # Si le terme est un nombre (ex: 1080, 4K)
            pattern = rf"(?:^|[\[\]\+\-&\s\._]){re.escape(term)}(?:p|i|$|[\[\]\+\-&\s\._])"
        else:
            pattern = rf"(?:^|[\[\]\+\-&\s\._]){re.escape(term.lower())}(?:$|[\[\]\+\-&\s\._])"

        match = re.search(pattern, normalized_filename)
        if match:
            logging.debug(f"✅ Terme '{term}' trouvé dans '{normalized_filename}'")
        else:
            logging.debug(f"❌ Terme '{term}' NON trouvé dans '{normalized_filename}'")
        return bool(match)

    # Vérifier si un groupe de critères correspond
    for search_group in SEARCH_TERMS:
        if all(match_criteria(term) for term in search_group):
            logging.info(f"🎯 Épisode détecté : {filename} - Correspondance: {search_group}")
            return True

    logging.debug(f"🚫 Aucun critère trouvé pour {filename} (Comparé avec {SEARCH_TERMS})")
    return False

def get_series():
    """ Récupère la liste des séries suivies dans Sonarr """
    series_url = f"{SONARR_URL}/api/v3/series"
    response = requests.get(series_url, headers=HEADERS)
    
    if response.status_code != 200:
        logging.error(f"❌ Erreur lors de la récupération des séries : {response.status_code}")
        return []
    
    series_list = response.json()
    logging.info(f"📥 {len(series_list)} séries récupérées depuis Sonarr.")
    return series_list
    
def unmonitor_episode(episode):
    """ Désactive le monitoring d'un épisode dans Sonarr """
    episode_id = episode["id"]
    title = episode.get("title", "Titre inconnu")
    season = episode.get("seasonNumber", "?")
    episode_number = episode.get("episodeNumber", "?")

    logging.info(f"🛠️ Traitement de l'épisode '{title}' (S{season}E{episode_number}, ID: {episode_id})...")

    if DRY_RUN:
        logging.info(f"[DRY_RUN] 🚀 L'épisode '{title}' (S{season}E{episode_number}, ID: {episode_id}) aurait été marqué comme NON MONITORÉ ✅")
        return

    url = f"{SONARR_URL}/api/v3/episode/{episode_id}"
    episode_data = {"monitored": False}

    response = requests.put(url, headers=HEADERS, json=episode_data)

    if response.status_code == 200:
        logging.info(f"✅ Épisode '{title}' (S{season}E{episode_number}, ID: {episode_id}) marqué comme NON MONITORÉ avec succès.")
    else:
        logging.error(f"❌ Erreur lors de la mise à jour de l'épisode {episode_id}: {response.status_code} - {response.text}")


def main():
    """ Traite toutes les séries et leurs épisodes dans Sonarr """
    logging.info("🚀 Début du traitement des séries dans Sonarr...")

    series_list = get_series()
    if not series_list:
        logging.warning("⚠️ Aucune série trouvée dans Sonarr.")
        return

    total_processed = 0  # Compteur d'épisodes désactivés
    dry_run_list = []  # Liste des épisodes qui auraient été désactivés

    for series in series_list:
        series_id = series.get("id")
        series_title = series.get("title", "Titre inconnu")

        logging.info(f"🔍 Analyse des épisodes pour la série '{series_title}' (ID: {series_id})...")

        episodes = get_episodes(series_id)
        if not episodes:
            logging.warning(f"⚠️ Aucun épisode trouvé pour la série '{series_title}' (ID: {series_id}).")
            continue

        for episode in episodes:
            has_file = "episodeFile" in episode and episode["episodeFile"] is not None
            if has_file:
                logging.debug(f"📄 Fichier détecté : {episode['episodeFile']['relativePath']}")
            else:
                logging.debug(f"🚫 Aucun fichier trouvé pour l'épisode {episode['title']} (ID: {episode['id']})")
                continue

            if episode.get("monitored") and should_unmonitor(episode):
                logging.info(f"📡 Envoi requête unmonitor pour l'épisode {episode['id']} ({episode['title']})...")
                unmonitor_episode(episode)
                total_processed += 1
                dry_run_list.append(f"{series_title} - {episode['title']} (S{episode['seasonNumber']}E{episode['episodeNumber']})")

    if DRY_RUN and dry_run_list:
        logging.info(f"[DRY_RUN] 📋 Épisodes qui auraient été désactivés ({len(dry_run_list)}):")
        for ep in dry_run_list:
            logging.info(f"  - {ep}")

    logging.info(f"✅ Fin du traitement. {total_processed} épisodes ont été désactivés.")

    
if __name__ == "__main__":
    main()
