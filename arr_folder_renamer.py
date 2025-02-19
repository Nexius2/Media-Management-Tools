# -*- coding: utf-8 -*-

import json
import logging
from logging.handlers import RotatingFileHandler
#from datetime import datetime
import requests
import time


# Charger la configuration
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    logging.info("✅ Configuration chargée avec succès.")
except FileNotFoundError:
    logging.error(f"❌ Erreur : fichier de configuration '{CONFIG_FILE}' introuvable.")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"❌ Erreur de parsing JSON dans '{CONFIG_FILE}': {e}")
    exit(1)


# 📌 Récupération des paramètres de config
SONARR_URL = config["services"]["sonarr"]["url"]
SONARR_API_KEY = config["services"]["sonarr"]["api_key"]
RADARR_URL = config["services"]["radarr"]["url"]
RADARR_API_KEY = config["services"]["radarr"]["api_key"]
PLEX_URL = config["services"]["plex"]["url"]
PLEX_API_KEY = config["services"]["plex"]["api_key"]
LOG_FILE = config["arr_folder_renamer"]["log_file"]
LOG_LEVEL = config["arr_folder_renamer"]["log_level"].upper()
DRY_RUN = config["arr_folder_renamer"]["dry_run"]
WORK_LIMIT = config["arr_folder_renamer"]["work_limit"]
RUN_SONARR = config["arr_folder_renamer"]["run_sonarr"]
RUN_RADARR = config["arr_folder_renamer"]["run_radarr"]


# Initialisation du logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
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

def update_sonarr_path(original_path, imdb_id, tvdb_id):
    # Si aucun ID n'est disponible, ne pas modifier le path
    if imdb_id is None and tvdb_id is None:
        return original_path
    
    # Construire les segments
    segments = []
    
    if imdb_id is not None and str(imdb_id) not in str(original_path):
        segments.append(f"{{imdb-{imdb_id}}}")

    if tvdb_id is not None and str(tvdb_id) not in str(original_path):
        segments.append(f"{{tvdb-{tvdb_id}}}")
    
    # Si aucun segment n'est ajouté, retourner le path d'origine
    if not segments:
        return original_path
    
    # Nettoyer le path d'origine pour éviter les doublons de séparateurs
    original_path = original_path.rstrip('/')
    
    # Concaténer les segments avec " - "
    new_path = f"{original_path} - {' - '.join(segments)}"
    return new_path


def update_radarr_path(original_path, imdb_id, tmdb_id):
    # Si aucun ID n'est disponible, ne pas modifier le path
    if imdb_id is None and tmdb_id is None:
        return original_path
    
    # Construire les segments
    segments = []
    
    if imdb_id is not None and str(imdb_id) not in str(original_path):
        segments.append(f"{{imdb-{imdb_id}}}")
    if tmdb_id is not None and str(tmdb_id) not in str(original_path):
        segments.append(f"{{tmdb-{tmdb_id}}}")
    
    # Si aucun segment n'est ajouté, retourner le path d'origine
    if not segments:
        return original_path
    
    # Nettoyer le path d'origine pour éviter les doublons de séparateurs
    original_path = original_path.rstrip('/')
    
    # Concaténer les segments avec " - "
    new_path = f"{original_path} - {' - '.join(segments)}"
    return new_path
    
def refresh_series(sonarr_url, api_key, series_id):
    """ Rafraîchit une série spécifique dans Sonarr """
    url = f"{sonarr_url}/api/v3/command"
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {"name": "RefreshSeries", "seriesId": series_id}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        logging.info(f"✅ Refresh lancé avec succès pour la série ID {series_id}.")
    else:
        logging.error(f"❌ Échec du Refresh pour la série ID {series_id}. Code: {response.status_code}, Réponse: {response.text}")
    
def refresh_movies(radarr_url, api_key, movie_id):
    """ Rafraîchit un film spécifique dans Radarr """
    url = f"{radarr_url}/api/v3/command"
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {"name": "RefreshMovie", "movieId": movie_id}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        logging.info(f"✅ Refresh lancé avec succès pour le film ID {movie_id}.")
    else:
        logging.error(f"❌ Échec du Refresh pour le film ID {movie_id}. Code: {response.status_code}, Réponse: {response.text}")

def verify_sonarr_file_movement(sonarr_url, api_key):
    headers = {"X-Api-Key": api_key}
    retry_intervals = [30, 300, 600, 1200]  # 30 secondes, 5, 10, 20 minutes

    for wait_time in retry_intervals:
        logging.info(f"🔍 Vérification du déplacement des fichiers Sonarr... (Attente {wait_time} secondes)")
        response = requests.get(f"{sonarr_url}/api/v3/system/task", headers=headers)

        if response.status_code != 200:
            logging.error(f"❌ Échec de récupération des tâches Sonarr : {response.status_code}")
            return False

        tasks = response.json()
        move_task = next((t for t in tasks if t['name'] == "Refresh Monitored Series"), None)

        if move_task:
            if move_task['state'] == "completed":
                logging.info("✅ Déplacement des fichiers Sonarr terminé.")
                return True
            elif move_task['state'] == "queued" or move_task['state'] == "running":
                logging.info("⏳ Le déplacement des fichiers est encore en cours. Nouvelle vérification après attente.")
            else:
                logging.error(f"Tâche dans un état inattendu : {move_task['state']}")
        time.sleep(wait_time)

    logging.error("❌ Les fichiers Sonarr ne se sont pas déplacés après plusieurs tentatives.")
    return False


def verify_radarr_file_movement(radarr_url, api_key):
    """ Vérifie si le déplacement des fichiers dans Radarr est terminé """
    headers = {"X-Api-Key": api_key}
    retry_intervals = [30, 300, 600, 1200]  # 30 secondes, 5, 10, 20 minutes

    for wait_time in retry_intervals:
        logging.info(f"🔍 Vérification du déplacement des fichiers Radarr... (Attente {wait_time} secondes)")
        response = requests.get(f"{radarr_url}/api/v3/system/task", headers=headers)

        if response.status_code != 200:
            logging.error(f"❌ Échec de récupération des tâches Radarr : {response.status_code}")
            return False

        tasks = response.json()
        move_task = next((t for t in tasks if t['name'] == "Refresh Monitored Series"), None)

        if move_task:
            if move_task['state'] == "completed":
                logging.info("✅ Déplacement des fichiers Sonarr terminé.")
                return True
            elif move_task['state'] == "queued" or move_task['state'] == "running":
                logging.info("⏳ Le déplacement des fichiers est encore en cours. Nouvelle vérification après attente.")
            else:
                logging.error(f"Tâche dans un état inattendu : {move_task['state']}")
        time.sleep(wait_time)

    logging.error("❌ Les fichiers Radarr ne se sont pas déplacés après plusieurs tentatives.")
    return False

# Fonction pour traiter les series avec Sonarr
def process_sonarr(sonarr_url, api_key, main_logger, dry_run, work_limit):
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    
    # Récupérer toutes les séries
    response = requests.get(f"{sonarr_url}/api/v3/series", headers=headers)
    if response.status_code != 200:
        main_logger.error("Erreur lors de la récupération des séries Sonarr")
        return
    
    series_list = response.json()
    
    modified_count = 0
    for series in series_list:
        # Extraire les informations nécessaires
        title = series.get("title", "")
        sort_title = series.get("sortTitle", "")
        year = series.get("year", "")
        path = series.get("path", "")
        tvdb_id = series.get("tvdbId")
        imdb_id = series.get("imdbId")
        series_id = series.get("id")
        main_logger.debug(f"Title: {title}: Year: {year}")
        
        # Vérifier si IMDB ou TVDB est manquant dans le path
        if (
            (str(imdb_id) not in path and str(tvdb_id) not in path)
            or "tvshows" in path.lower()
        ):
            new_path = update_sonarr_path(path, imdb_id, tvdb_id)
            
            if new_path != path:
                main_logger.info(f"Série {title} ({series_id}) : Chemin modifié de '{path}' à '{new_path}'")
                
                if not dry_run:
                    # Construction de l'URL
                    update_url = f"{sonarr_url}/api/v3/series/{series_id}?moveFiles=true"
                    
                    # Corps de la requête
                    payload = {
                        "title": title,
                        "sortTitle": sort_title,
                        "year": year,
                        "path": new_path,
                        "tvdbId": tvdb_id,
                        "imdbId": imdb_id,
                        "qualityProfileId": series.get("qualityProfileId"),
                        "seasonFolderEnabled": series.get("seasonFolderEnabled", True),
                        "metadataProfileId": series.get("metadataProfileId")
                        #"moveFiles": True  # Ajout de ce paramètre pour déplace les fichiers
                    }
                    
                    # Envoi de la requête
                    try:
                        response_update = requests.put(
                            update_url,
                            headers=headers,
                            json=payload
                        )
                        
                        if response_update.status_code == 200:
                            main_logger.info(f"Série {title} ({series_id}) : Chemin mis à jour avec succès.")
                        elif response_update.status_code == 202:
                            main_logger.info(f"Série {title} ({series_id}) : Le déplacement sera traité lors du prochain contrôle de tâches Sonarr.")
                            verify_sonarr_file_movement(SONARR_URL, SONARR_API_KEY)
                        else:
                            # Log plus de détails pour le debug
                            error_details = {
                                "status": response_update.status_code,
                                "text": response_update.text,
                                "payload_sent": payload
                            }
                            main_logger.error(
                                f"Série {title} ({series_id}) : Échec de la mise à jour du chemin. Détails: {error_details}"
                            )
                            main_logger.debug(f"Payload envoyé pour {title}: {payload}")
                            main_logger.debug(f"Réponse complete: {response_update.text}")
                            
                    except Exception as e:
                        main_logger.error(
                            f"Série {title} ({series_id}) : Erreur lors de la requête PUT. Détails: {str(e)}"
                        )
                        main_logger.debug(f"Erreur complete: {str(e)}")
                
                modified_count += 1
                
                if work_limit > 0 and modified_count >= work_limit:
                    main_logger.info(f"Limite de modifications atteinte ({work_limit}). Arrêt du script.")
                    return
            
            # Log détaillé pour debug.log
            main_logger.debug(
                f"Série {title} ({series_id}) - Ancien path: '{path}', Nouveau path: '{new_path}'"
            )
    
    main_logger.info(f"Fin du traitement des séries Sonarr. Modifications effectuées: {modified_count}")




# Fonction pour traiter les films avec Radarr
def process_radarr(radarr_url, api_key, main_logger, dry_run, work_limit):
    headers = {"Content-Type": "application/json", "X-Api-Key": api_key}
    
    # Récupérer tous les films
    response = requests.get(f"{radarr_url}/api/v3/movie", headers=headers)
    if response.status_code != 200:
        main_logger.error("Erreur lors de la récupération des films Radarr")
        return
    
    movies_list = response.json()
    
    modified_count = 0
    for movie in movies_list:
        # Extraire les informations nécessaires
        title = movie.get("title", "")
        sort_title = movie.get("sortTitle", "")
        year = movie.get("year", "")
        path = movie.get("path", "")
        tmdb_id = movie.get("tmdbId")
        imdb_id = movie.get("imdbId")
        movie_id = movie.get("id")
        
        # Vérifier si IMDB ou TMDB est manquant dans le path
        if (
            (str(imdb_id) not in path and str(tmdb_id) not in path)
            or (tmdb_id is None)
            or (imdb_id is None)
        ):
            new_path = update_radarr_path(path, imdb_id, tmdb_id)
            
            if new_path != path:
                main_logger.info(f"Film {title} ({movie_id}) : Chemin modifié de '{path}' à '{new_path}'")
                
                if not dry_run:
                    # Inclure toutes les informations nécessaires dans le payload
                    payload = {
                        "id": movie_id,
                        "title": title,
                        "sortTitle": sort_title,
                        "year": year,
                        "tmdbId": tmdb_id,
                        "imdbId": imdb_id,
                        "path": new_path,
                        "monitored": movie.get("monitored", True),
                        "qualityProfileId": movie.get("qualityProfileId"),
                        "metadataProfileId": movie.get("metadataProfileId")
                    }
                    
                    response_update = requests.put(
                        f"{radarr_url}/api/v3/movie/{movie_id}?moveFiles=true",
                        headers=headers,
                        json=payload
                    )
                    
                    if response_update.status_code == 200:
                        main_logger.info(f"Film {title} ({movie_id}) : Chemin mis à jour avec succès.")
                    elif response_update.status_code == 202:
                        main_logger.info(f"Film {title} ({movie_id}) : Le déplacement sera traité lors du prochain contrôle de tâches Radarr.")
                    else:
                        main_logger.error(
                            f"Film {title} ({movie_id}) : Échec de la mise à jour du chemin. Code d'erreur: {response_update.status_code}"
                        )
                
                modified_count += 1
                if work_limit > 0 and modified_count >= work_limit:
                    main_logger.info(f"Limite de modifications atteinte ({work_limit}). Arrêt du script.")
                    return
            
            # Log détaillé pour debug.log
            main_logger.debug(
                f"Film {title} ({movie_id}) - Ancien path: '{path}', Nouveau path: '{new_path}'"
            )
    
    main_logger.info(f"Fin du traitement des films Radarr. Modifications effectuées: {modified_count}")


# 📌 Correction du système de logs
def setup_logging():
    """ Configuration du système de logs """
    log_file = "arr_folder_renamer.log"  # Assurez-vous d'utiliser un seul fichier log
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)

    # Supprime les handlers existants pour éviter les doublons
    logging.getLogger().handlers.clear()

    # Création du formatter
    log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Handler pour les logs avec rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)

    # Handler pour affichage en console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    # Configuration du logger principal
    logger = logging.getLogger("arr_folder_renamer")
    logger.setLevel(log_level)
    logger.handlers = []  # Supprime tous les handlers existants pour éviter les doublons
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("✅ Système de logs correctement configuré.")
    
    return logger  # 🔹 Retourne l'objet logger




def plex_refresh(plex_url, plex_api_key):
    """ Rafraîchit les bibliothèques Plex """
    headers = {"X-Plex-Token": plex_api_key}
    response = requests.get(f"{plex_url}/library/sections/all/refresh", headers=headers)
    if response.status_code == 200:
        logging.info("✅ Actualisation de la bibliothèque Plex réussie.")
    else:
        logging.error("❌ Échec de l'actualisation de la bibliothèque Plex.")
  

# Fonction principale
def main(dry_run):
    # Initialisation des loggers
    main_logger = setup_logging()  # 🔹 Récupère et utilise l'objet logger
    logging.info("🚀 Démarrage du script...")
    
    # Vérifier les paramètres de configuration
    if not SONARR_API_KEY or not RADARR_API_KEY:
        main_logger.error("Clés API manquantes. Veuillez configurer le script correctement.")
        return
    
    # Traitement des séries Sonarr si activé
    if RUN_SONARR:
        main_logger.info("📺 Vérification des tâches Sonarr en cours...")
        process_sonarr(SONARR_URL, SONARR_API_KEY, main_logger, DRY_RUN, WORK_LIMIT)
    
    # Traitement des films Radarr si activé
    if RUN_RADARR:
        main_logger.info("🎬 Vérification des tâches Radarr en cours...")
        process_radarr(RADARR_URL, RADARR_API_KEY, main_logger, DRY_RUN, WORK_LIMIT)
        
    # Traitement du rafraichissement Plex    
    if not dry_run:
        #plex_refresh(PLEX_URL, PLEX_API_KEY)
        main_logger.info("♻️ Rafraîchissement de Plex...")
        
    main_logger.info("✅ Fin du script.")

if __name__ == "__main__":
    main(DRY_RUN)

