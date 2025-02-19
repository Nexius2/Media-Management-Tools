# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
#########################################################
# Media Management Tools (MMT) - Sonarr Unmonitor
# Auteur       : Nexius2
# Date         : 2025-02-18
# Version      : 1.0
# Description  : Script permettant de désactiver le monitoring
#                des épisodes dans Sonarr en fonction des critères
#                définis dans `config.json`.
# Licence      : MIT
#########################################################

# 📌 Utilisation :
# Exécuter le script via la ligne de commande :
#   python sonarr_unmonitor.py
#
# Mode Simulation (Dry-Run) :
#   - Défini dans `config.json`, le mode Dry-Run affiche les épisodes
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
# - Les logs sont enregistrés dans sonarr_unmonitor.log
# - Inclut les épisodes traités, les erreurs et les mises à jour effectuées.

#########################################################
"""


import requests
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import re

# Charger la configuration
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Erreur : fichier de configuration '{CONFIG_FILE}' introuvable.")
    exit(1)

# Extraire la configuration des services
SONARR_CONFIG = config["services"].get("sonarr", {})

# Extraire la configuration spécifique à Sonarr Unmonitor
UNMONITOR_CONFIG = config.get("sonarr_unmonitor", {})

LOG_FILE = UNMONITOR_CONFIG.get("log_file", "sonarr_unmonitor.log")
LOG_LEVEL = UNMONITOR_CONFIG.get("log_level", "INFO").upper()
DRY_RUN = UNMONITOR_CONFIG.get("dry_run", True)
SEARCH_TERMS = UNMONITOR_CONFIG.get("search_terms", [["1080", "FR", "MULTI"], ["4K", "FR", "MULTI"]])

# Vérifier la configuration Sonarr
SONARR_URL = SONARR_CONFIG.get("url")
SONARR_API_KEY = SONARR_CONFIG.get("api_key")

if not SONARR_URL or not SONARR_API_KEY:
    print("❌ Configuration Sonarr manquante ou incomplète dans 'config.json'.")
    exit(1)

# Initialisation du logging avec rotation
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.handlers = []
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logging.info("📝 Système de logs avec rotation activé.")

HEADERS = {"X-Api-Key": SONARR_API_KEY, "Content-Type": "application/json"}

def get_episodes():
    """ Récupère la liste des épisodes dans Sonarr avec leurs fichiers et filtre ceux qui sont monitorés """
    series_url = f"{SONARR_URL}/api/v3/series"
    response = requests.get(series_url, headers=HEADERS)

    if response.status_code != 200:
        logging.error(f"❌ Erreur lors de la récupération des séries : {response.status_code} - {response.text}")
        return []

    series_list = response.json()
    all_episodes = []

    for serie in series_list:
        series_id = serie["id"]
        episodes_url = f"{SONARR_URL}/api/v3/episode?seriesId={series_id}&includeEpisodeFile=true"
        response = requests.get(episodes_url, headers=HEADERS)

        if response.status_code == 200:
            episodes = response.json()
            logging.info(f"📥 {len(episodes)} épisodes récupérés pour la série {serie['title']} (ID: {series_id}).")

            for ep in episodes:
                ep["seriesTitle"] = serie["title"]  # Ajout du titre de la série à chaque épisode
                episode_id = ep.get("id")
                monitored = ep.get("monitored", False)  # Vérifier si l'épisode est monitoré
                episode_file = ep.get("episodeFile", {})

                # Si aucun fichier n'est trouvé, tenter une requête directe
                if not episode_file:
                    file_url = f"{SONARR_URL}/api/v3/episodeFile?episodeId={episode_id}"
                    file_response = requests.get(file_url, headers=HEADERS)

                    if file_response.status_code == 200:
                        episode_files = file_response.json()
                        if episode_files:
                            episode_file = episode_files[0]  # Prendre le premier fichier associé

                relative_path = episode_file.get("relativePath")

                # ✅ Filtrage : Ne garder que les épisodes monitorés ET avec un fichier valide
                if monitored and relative_path:
                    relative_path = relative_path.lower()
                    logging.debug(f"✅ Épisode monitoré avec fichier : {serie['title']} (ID: {series_id}) - {ep['title']} - {relative_path}")
                    ep["episodeFile"] = episode_file
                    all_episodes.append(ep)
                else:
                    logging.debug(f"🚫 Ignoré (Non monitoré ou pas de fichier) : {serie['title']} - {ep['title']} (ID: {episode_id})")

        else:
            logging.error(f"❌ Erreur lors de la récupération des épisodes pour la série {serie['title']} : {response.status_code} - {response.text}")

    logging.info(f"✅ Total épisodes sélectionnés après filtrage : {len(all_episodes)}")
    return all_episodes







def should_unmonitor(episode):
    """ Vérifie si un épisode doit être désactivé en fonction du nom du fichier """
    series_title = episode.get("seriesTitle", "Série inconnue")
    episode_title = episode.get("title", "Titre inconnu")
    season_number = episode.get("seasonNumber", "Inconnu")
    episode_number = episode.get("episodeNumber", "Inconnu")
    episode_id = episode.get("id")
    episode_file = episode.get("episodeFile", {})

    # Vérification si un fichier est attaché
    if not episode_file or "relativePath" not in episode_file:
        logging.warning(f"🚫 AUCUN FICHIER trouvé pour : {series_title} (S{season_number}E{episode_number}, ID: {episode_id})")
        return False

    # LOG POUR AFFICHER TOUS LES FICHIERS ANALYSÉS
    relative_path = episode_file["relativePath"].lower()
    logging.debug(f"📝 Analyse de l'épisode : {series_title} (S{season_number}E{episode_number}, ID: {episode_id}) - Fichier détecté : {relative_path}")

    # LOG POUR VOIR LES TERMES UTILISÉS
    logging.debug(f"🔎 Critères de recherche utilisés : {SEARCH_TERMS}")

    # Fonction de détection avancée avec expressions régulières
    def match_terms(path, terms):
        regex_patterns = {
            "1080": r"(?<!\\d)1080p(?!\\d)| 1080 ",
            "FR": r" fr |fr\\+|\\+fr",
            "EN": r" en |en\\+|\\+en"
        }
        return all(re.search(regex_patterns.get(term, rf"\\b{re.escape(term)}\\b"), path) for term in terms)

    # Vérification des termes dans tous les ensembles de critères
    for search_group in SEARCH_TERMS:
        if match_terms(relative_path, search_group):
            logging.info(f"🎯 Épisode détecté : {series_title} (S{season_number}E{episode_number}, ID: {episode_id}) - Fichier: {relative_path} - Correspondance: {search_group}")
            return True

    logging.debug(f"❌ Aucun match trouvé pour '{relative_path}' avec les critères {SEARCH_TERMS}.")
    return False











def main():
    logging.info("🚀 Début du traitement des épisodes dans Sonarr...")

    # Charger la limite de travail depuis la configuration
    WORK_LIMIT = UNMONITOR_CONFIG.get("work_limit", 0)

    episodes = get_episodes()
    if not episodes:
        logging.warning("⚠️ Aucun épisode trouvé dans Sonarr.")
        return

    total_processed = 0
    dry_run_list = []  # Liste pour stocker les épisodes traités en mode DRY_RUN

    for episode in episodes:
        title = episode.get("title", "Inconnu")
        season_number = episode.get("seasonNumber", "Inconnu")
        episode_number = episode.get("episodeNumber", "Inconnu")
        episode_id = episode.get("id")
        episode_file = episode.get("episodeFile", {})

        relative_path = episode_file.get("relativePath", "").lower()
        monitored = episode.get("monitored", False)

        # 🔹 1️⃣ Filtrer les épisodes non monitorés
        if not monitored and relative_path:
            logging.warning(f"🚫 IGNORÉ (Non monitoré) : {series_title} (S{season_number}E{episode_number}, ID: {episode_id}) - {relative_path}")
            continue  # On passe au suivant

        # 🔹 2️⃣ Vérifier si l'épisode doit être unmonitoré
        if should_unmonitor(episode):
            if WORK_LIMIT and total_processed >= WORK_LIMIT:
                logging.info(f"⏹️ Limite de {WORK_LIMIT} épisodes atteinte, arrêt immédiat du traitement.")
                break  

            logging.info(f"🎯 À UNMONITORER : {series_title} (S{season_number}E{episode_number}, ID: {episode_id}) - {relative_path}")

            if DRY_RUN:
                logging.info(f"🚨 [DRY_RUN] Cet épisode serait désactivé : {series_title} (S{season_number}E{episode_number})")
                dry_run_list.append(f"{series_title} (S{season_number}E{episode_number})")
            else:
                unmonitor_episode(episode)

            # ✅ Incrémenter immédiatement après traitement
            total_processed += 1  

    # Affichage du résumé final
    if DRY_RUN and dry_run_list:
        logging.info(f"[DRY_RUN] 📋 Liste des épisodes qui auraient été désactivés ({len(dry_run_list)}):")
        for episode in dry_run_list:
            logging.info(f" {series_title} - {episode} - {SEARCH_TERMS}")

    logging.info(f"✅ Fin du traitement. {total_processed} épisodes ont été traités (mode réel ou simulation).")





if __name__ == "__main__":
    main()
