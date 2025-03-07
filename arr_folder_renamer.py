# -*- coding: utf-8 -*-

"""
#########################################################
# Media Management Tools (MMT) - Arr folder renamer
# Auteur       : Nexius2
# Version      : 0.21.1
# Description  : Script permettant de modifier le path pour correspondre aux besoin de plex via Sonarr et Radarren fonction des critères
#                définis dans `config.json`.
# Licence      : MIT
#########################################################

🛠 Arr Folder Renamer - Gestion des chemins des médias pour Sonarr & Radarr

=============================================================
📌 DESCRIPTION
-------------------------------------------------------------
Arr Folder Renamer est un script Python permettant d'automatiser la modification 
des chemins des fichiers médias dans Sonarr et Radarr. Il assure la compatibilité 
avec Plex en renommant les dossiers selon les critères définis dans `config.json`.

📂 Fonctionnalités :
- Ajoute les identifiants **IMDB**, **TVDB** et **TMDB** aux chemins des médias.
- Vérifie et corrige les noms de dossiers pour éviter les incohérences.
- Gère **Sonarr** pour les séries et **Radarr** pour les films.
- Peut fonctionner en **mode simulation (dry-run)** sans modification réelle.
- Assure l'attente et la synchronisation avec **Plex** pour rafraîchir la bibliothèque.

=============================================================
📜 FONCTIONNEMENT
-------------------------------------------------------------
1. **Connexion aux API de Sonarr et Radarr** via leurs clés API.
2. **Récupération des informations des séries et films** stockés dans Sonarr/Radarr.
3. **Analyse des chemins actuels** :
   - Vérifie si les identifiants IMDB/TVDB/TMDB sont présents.
   - Ajoute les identifiants manquants dans le chemin si nécessaire.
4. **Mise à jour des chemins des médias** dans Sonarr et Radarr.
5. **Vérification du déplacement des fichiers** après modification.
6. **Rafraîchissement des bibliothèques Plex** une fois les changements terminés.

=============================================================
⚙️ CONFIGURATION (config.json)
-------------------------------------------------------------
Le script utilise un fichier de configuration JSON contenant les paramètres suivants :

{
    "services": {
        "sonarr": {
            "url": "http://192.168.1.100:8989",
            "api_key": "VOTRE_CLE_API_SONARR"
        },
        "radarr": {
            "url": "http://192.168.1.100:7878",
            "api_key": "VOTRE_CLE_API_RADARR"
        },
        "plex": {
            "url": "http://192.168.1.200:32400",
            "api_key": "VOTRE_CLE_API_PLEX"
        }
    },
    "arr_folder_renamer": {
        "log_file": "arr_folder_renamer.log",
        "log_level": "INFO",
        "dry_run": true,
        "work_limit": 50,
        "run_sonarr": true,
        "run_radarr": true
    }
}

| Clé                           | Description |
|--------------------------------|-------------|
| `services.sonarr.url`         | URL de l'instance Sonarr |
| `services.sonarr.api_key`     | Clé API pour Sonarr |
| `services.radarr.url`         | URL de l'instance Radarr |
| `services.radarr.api_key`     | Clé API pour Radarr |
| `services.plex.url`           | URL de l'instance Plex |
| `services.plex.api_key`       | Clé API pour Plex |
| `arr_folder_renamer.log_file` | Fichier de log |
| `arr_folder_renamer.log_level`| Niveau de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `arr_folder_renamer.dry_run`  | `true` = simulation, `false` = modifications réelles |
| `arr_folder_renamer.work_limit` | Nombre max de modifications par exécution |
| `arr_folder_renamer.run_sonarr` | `true` = activer Sonarr, `false` = désactiver |
| `arr_folder_renamer.run_radarr` | `true` = activer Radarr, `false` = désactiver |

=============================================================
🚀 UTILISATION
-------------------------------------------------------------
1. **Installez les dépendances requises** :
   pip install requests

2. **Créez/modifiez le fichier `config.json`** avec vos paramètres.

3. **Lancez le script en mode simulation (DRY_RUN activé)** :
   python arr_folder_renamer.py
   - Aucun changement ne sera effectué, mais le script affichera les chemins qui seraient modifiés.

4. **Exécutez le script avec modifications réelles** (après avoir mis `dry_run` sur `false` dans `config.json`) :
   python arr_folder_renamer.py
   - Les chemins des fichiers seront modifiés dans Sonarr et Radarr.

=============================================================
📄 LOGS ET DEBUG
-------------------------------------------------------------
Le script génère des logs détaillés :
- Les logs sont enregistrés dans le fichier spécifié (`arr_folder_renamer.log`).
- En mode `DEBUG`, toutes les actions et modifications sont enregistrées.

=============================================================
🛑 PRÉCAUTIONS
-------------------------------------------------------------
- Ce script **ne supprime aucun fichier**, il ne fait que modifier les chemins.
- Si un film ou une série a un chemin incorrect dans Sonarr/Radarr, Plex risque de ne pas le retrouver immédiatement.
- Vérifiez toujours les logs avant d'exécuter le script sans `dry_run`.

=============================================================
🔥 EXEMPLE D'EXÉCUTION EN MODE `DRY_RUN`
-------------------------------------------------------------
python arr_folder_renamer.py

📝 **Exemple de sortie :**
🚀 Démarrage du script...
✅ Connexion réussie à Sonarr et Radarr.
📋 10 séries et 15 films analysés.
📂 3 séries et 5 films nécessitent une correction du chemin.
🔧 Mode DRY RUN activé. Aucune modification ne sera effectuée.

=============================================================
🗑 EXEMPLE D'EXÉCUTION AVEC MODIFICATIONS EFFECTIVES
-------------------------------------------------------------
Après avoir mis `dry_run` sur `false` dans `config.json` :

python arr_folder_renamer.py

📝 **Exemple de sortie :**
🚀 Démarrage du script...
✅ Connexion réussie à Sonarr et Radarr.
📋 10 séries et 15 films analysés.
📂 3 séries et 5 films nécessitent une correction du chemin.
📝 Mise à jour du chemin pour "Breaking Bad" (ID 12345)
📝 Mise à jour du chemin pour "Interstellar" (ID 67890)
✅ Modifications appliquées avec succès.
♻️ Rafraîchissement de Plex...
✅ Plex a été actualisé.

=============================================================
💡 ASTUCE
-------------------------------------------------------------
Vous pouvez programmer l'exécution automatique de ce script 
via un **cron job** ou une **tâche planifiée Windows**.

"""


import json
import logging
from logging.handlers import RotatingFileHandler
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

main_logger = logging.getLogger()
main_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
main_logger.handlers = []  # Supprime tous les handlers existants pour éviter les doublons
main_logger.addHandler(file_handler)
main_logger.addHandler(console_handler)

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

def verify_sonarr_file_movement(sonarr_url, api_key, series_id, new_path):
    headers = {"X-Api-Key": api_key}
    retry_intervals = [30,30, 60, 120, 300]  # 30 sec, 1 min, 2 min, 5 min

    for wait_time in retry_intervals:
        logging.info(f"🔍 Vérification du déplacement des fichiers Sonarr pour la série {series_id}... (Attente {wait_time} secondes)")
        
        # Récupérer les détails de la série depuis l'API
        response = requests.get(f"{sonarr_url}/api/v3/series/{series_id}", headers=headers)
        
        if response.status_code != 200:
            logging.error(f"❌ Échec de récupération des infos de la série {series_id} : {response.status_code}")
            return False

        series_data = response.json()
        current_path = series_data.get("path", "")

        if current_path == new_path:
            logging.info(f"✅ Déplacement détecté pour la série {series_id}. Nouveau chemin: {current_path}")
            return True
        else:
            logging.info(f"⏳ Toujours aucun déplacement détecté, chemin actuel : {current_path}. Nouvelle tentative après {wait_time} secondes.")
            time.sleep(wait_time)

    logging.error(f"❌ Aucun déplacement détecté pour la série {series_id} après plusieurs tentatives.")
    return False





def verify_radarr_file_movement(radarr_url, api_key, movie_id, new_path):
    headers = {"X-Api-Key": api_key}
    retry_intervals = [30,30, 60, 120, 300]  # 30 sec, 1 min, 2 min, 5 min

    for wait_time in retry_intervals:
        logging.info(f"🔍 Vérification du déplacement des fichiers Radarr pour le film {movie_id}... (Attente {wait_time} secondes)")
        
        # Récupérer les détails du film depuis l'API
        response = requests.get(f"{radarr_url}/api/v3/movie/{movie_id}", headers=headers)
        
        if response.status_code != 200:
            logging.error(f"❌ Échec de récupération des infos du film {movie_id} : {response.status_code}")
            return False

        movie_data = response.json()
        current_path = movie_data.get("path", "")

        if current_path == new_path:
            logging.info(f"✅ Déplacement détecté pour le film {movie_id}. Nouveau chemin: {current_path}")
            return True
        else:
            logging.info(f"⏳ Toujours aucun déplacement détecté, chemin actuel : {current_path}. Nouvelle tentative après {wait_time} secondes.")
            time.sleep(wait_time)

    logging.error(f"❌ Aucun déplacement détecté pour le film {movie_id} après plusieurs tentatives.")
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
                        "metadataProfileId": series.get("metadataProfileId"),
                        "monitored": series.get("monitored", True)  # ✅ Ajout de monitored pour éviter l'unmonitor automatique
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
                            verify_sonarr_file_movement(SONARR_URL, SONARR_API_KEY, series_id, new_path)
                            refresh_series(SONARR_URL, SONARR_API_KEY, series_id)
                            logging.info(f"♻️ Refresh forcé pour la série {title} ({series_id}).")

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
                        "monitored": movie.get("monitored", True),  # ✅ Ajout de monitored pour éviter l'unmonitor automatique
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
                        verify_radarr_file_movement(RADARR_URL, RADARR_API_KEY, movie_id, new_path)
                        refresh_movies(RADARR_URL, RADARR_API_KEY, movie_id)
                        logging.info(f"♻️ Refresh forcé pour le film {title} ({movie_id}).")
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
    main_logger = logging.getLogger("arr_folder_renamer")
    main_logger.setLevel(log_level)
    main_logger.handlers = []  # Supprime tous les handlers existants pour éviter les doublons
    main_logger.addHandler(file_handler)
    main_logger.addHandler(console_handler)

    main_logger.info("✅ Système de logs correctement configuré.")
    
    return main_logger  # 🔹 Retourne l'objet logger


def plex_refresh(plex_url, plex_api_key, main_logger):
    """ Rafraîchit les bibliothèques Plex """
    headers = {"X-Plex-Token": plex_api_key}
    response = requests.get(f"{plex_url}/library/sections/all/refresh", headers=headers)
    if response.status_code == 200:
        main_logger.info("✅ Actualisation de la bibliothèque Plex réussie.")
    else:
        main_logger.error("❌ Échec de l'actualisation de la bibliothèque Plex.")
  

def get_sonarr_queue(sonarr_url, sonarr_api_key, main_logger):
    try:
        response = requests.get(f"{sonarr_url}/api/v3/queue", headers={"X-Api-Key": sonarr_api_key})
        response.raise_for_status()
        queue_data = response.json()
        if isinstance(queue_data, dict) and "records" in queue_data:
            return queue_data["records"]
        else:
            main_logger.warning(f"⚠️ Réponse inattendue de Sonarr: {queue_data}")
            return []
    except requests.RequestException as e:
        main_logger.error(f"❌ Erreur lors de la récupération de la queue Sonarr: {e}")
        return []

def get_radarr_queue(radarr_url, radarr_api_key, main_logger):
    try:
        response = requests.get(f"{radarr_url}/api/v3/queue", headers={"X-Api-Key": radarr_api_key})
        response.raise_for_status()
        queue_data = response.json()
        if isinstance(queue_data, dict) and "records" in queue_data:
            return queue_data["records"]
        else:
            main_logger.warning(f"⚠️ Réponse inattendue de Radarr: {queue_data}")
            return []
    except requests.RequestException as e:
        main_logger.error(f"❌ Erreur lors de la récupération de la queue Radarr: {e}")
        return []


def get_queue(api_url, api_key, service_name):
    """Récupère la file d'attente de Sonarr ou Radarr."""
    headers = {"X-Api-Key": api_key}
    try:
        response = requests.get(f"{api_url}/api/v3/queue", headers=headers, timeout=10)
        response.raise_for_status()
        queue_data = response.json()
        if isinstance(queue_data, dict) and "records" in queue_data:
            return queue_data["records"]
        else:
            main_logger.warning(f"⚠️ Réponse inattendue de {service_name}: {queue_data}")
            return []
    except requests.RequestException as e:
        main_logger.error(f"❌ Erreur lors de la récupération de la queue {service_name}: {e}")
        return []



def wait_for_completion(sonarr_url, sonarr_api_key, radarr_url, radarr_api_key, max_retries=20, wait_time=60):
    """Attend la fin des traitements Sonarr et Radarr avant de passer à Plex."""

    last_non_empty_attempt = 0  # Stocke le dernier moment où il y avait des tâches
    for attempt in range(max_retries):
        sonarr_queue = get_queue(sonarr_url, sonarr_api_key, "Sonarr")
        radarr_queue = get_queue(radarr_url, radarr_api_key, "Radarr")

        active_sonarr_tasks = [task for task in sonarr_queue if task.get("status") not in ["completed", "warning"]]
        active_radarr_tasks = [task for task in radarr_queue if task.get("status") not in ["completed", "warning"]]

        logging.debug(f"📜 Queue active Sonarr ({len(active_sonarr_tasks)} tâches en cours): {[task.get('status') for task in active_sonarr_tasks]}")
        logging.debug(f"📜 Queue active Radarr ({len(active_radarr_tasks)} tâches en cours): {[task.get('status') for task in active_radarr_tasks]}")

        if not active_sonarr_tasks and not active_radarr_tasks:
            # Vérification supplémentaire pour éviter les faux positifs
            if attempt - last_non_empty_attempt >= 3:  # Attendre 3 itérations vides avant de confirmer la fin
                logging.info("✅ Toutes les tâches Sonarr et Radarr sont terminées. Fin de l'attente.")
                return True
            else:
                logging.info("🔄 La queue est vide, mais on attend encore quelques itérations pour confirmation...")
        else:
            last_non_empty_attempt = attempt  # Réinitialisation car il reste des tâches

        logging.info(f"⏳ Attente {wait_time} secondes avant nouvelle vérification... (Tentative {attempt+1}/{max_retries})")
        time.sleep(wait_time)

    logging.error("❌ Sonarr et Radarr n'ont pas terminé leurs tâches à temps.")
    return False



def wait_for_sonarr_radarr_completion(sonarr_url, sonarr_api_key, radarr_url, radarr_api_key, main_logger, max_retries=10, wait_time=30):
    """Attendre que Sonarr et Radarr aient terminé leurs tâches."""
    import requests

    def get_queue(api_url, api_key):
        try:
            headers = {"X-Api-Key": api_key}
            response = requests.get(f"{api_url}/api/v3/queue", headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            main_logger.warning(f"⚠️ Erreur lors de la récupération de la queue {api_url}: {e}")
            return []

    for attempt in range(max_retries):
        sonarr_queue = get_queue(sonarr_url, sonarr_api_key)
        radarr_queue = get_queue(radarr_url, radarr_api_key)

        active_sonarr_tasks = [task for task in sonarr_queue if task.get("status") not in ["completed", "warning"]]
        active_radarr_tasks = [task for task in radarr_queue if task.get("status") not in ["completed", "warning"]]

        main_logger.info(f"📜 Queue active Sonarr ({len(active_sonarr_tasks)} tâches en cours): {[task.get('status') for task in active_sonarr_tasks]}")
        main_logger.info(f"📜 Queue active Radarr ({len(active_radarr_tasks)} tâches en cours): {[task.get('status') for task in active_radarr_tasks]}")

        if not active_sonarr_tasks and not active_radarr_tasks:
            main_logger.info("✅ Toutes les tâches Sonarr et Radarr sont terminées.")
            return True

        main_logger.info(f"⏳ Attente {wait_time} secondes avant nouvelle vérification... (Tentative {attempt+1}/{max_retries})")
        time.sleep(wait_time)

    main_logger.error("❌ Sonarr et Radarr n'ont pas terminé leurs tâches à temps.")
    return False(sonarr_url, sonarr_api_key, radarr_url, radarr_api_key, main_logger)
    """
    Attend la fin des traitements de Sonarr et Radarr avant de passer à Plex.
    """
    while True:
        active_tasks = 0

        # Vérification de Sonarr
        try:
            response_sonarr = requests.get(f"{sonarr_url}/api/v3/queue", headers={"X-Api-Key": sonarr_api_key})
            response_sonarr.raise_for_status()
            sonarr_queue = response_sonarr.json()
            active_sonarr = [task for task in sonarr_queue if task.get("status") not in ["completed", "failed"]]
            active_tasks += len(active_sonarr)
        except Exception as e:
            main_logger.warning(f"⚠️ Erreur lors de la récupération de la queue Sonarr : {e}")
            active_sonarr = []

        # Vérification de Radarr
        try:
            response_radarr = requests.get(f"{radarr_url}/api/v3/queue", headers={"X-Api-Key": radarr_api_key})
            response_radarr.raise_for_status()
            radarr_queue = response_radarr.json()
            active_radarr = [task for task in radarr_queue if task.get("status") not in ["completed", "failed"]]
            active_tasks += len(active_radarr)
        except Exception as e:
            main_logger.warning(f"⚠️ Erreur lors de la récupération de la queue Radarr : {e}")
            active_radarr = []

        main_logger.info(f"🔄 Tâches en cours - Sonarr : {len(active_sonarr)}, Radarr : {len(active_radarr)}.")

        if active_tasks == 0:
            main_logger.info("✅ Toutes les tâches Sonarr et Radarr sont terminées. Passage à Plex.")
            break  # Sortir de la boucle quand il n'y a plus de tâches actives

        main_logger.info(f"🕒 Vérification à nouveau dans 30 secondes...")
        time.sleep(30)  # Attente avant la prochaine vérification








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
        # Attendre la fin des traitements Sonarr et Radarr
        if wait_for_completion(SONARR_URL, SONARR_API_KEY, RADARR_URL, RADARR_API_KEY, max_retries=10, wait_time=30):
            logging.info("♻️ Rafraîchissement de Plex...")
            plex_refresh(PLEX_URL, PLEX_API_KEY)
            logging.info("✅ Plex a été actualisé avec succès.")
        else:
            logging.error("❌ Impossible de rafraîchir Plex car Sonarr/Radarr n'ont pas terminé à temps.")


        
    main_logger.info("✅ Fin du script.")

if __name__ == "__main__":
    main(DRY_RUN)

