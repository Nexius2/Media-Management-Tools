# -*- coding: utf-8 -*-

"""
#########################################################
# Media Management Tools (MMT) - Arr folder renamer
# Auteur       : Nexius2
# Version      : 2.1.xx
# Description  : Script permettant de modifier le path pour correspondre aux besoins de Plex via Sonarr et Radarr
#                en fonction des critères définis dans `config.json`.
# Licence      : MIT
#########################################################
"""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
import requests
import time
import re
import unidecode
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from pathlib import Path



# Charger la configuration
CONFIG_FILE = "config.json"
RADARR_CACHE_FILE = "cache_radarr_paths.json"
SONARR_CACHE_FILE = "cache_sonarr_paths.json"
VERSION = "2.1.57"





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
LOG_LEVEL = logging.getLevelName(config["arr_folder_renamer"]["log_level"].upper())
DRY_RUN = config["arr_folder_renamer"]["dry_run"]
WORK_LIMIT = config["arr_folder_renamer"]["work_limit"]
RUN_SONARR = config["arr_folder_renamer"]["run_sonarr"]
RUN_RADARR = config["arr_folder_renamer"]["run_radarr"]


# 🔥 Correction du logging : Réinitialisation complète
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=LOG_LEVEL,  # ✅ DEBUG pour voir tous les logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # ✅ Force l'affichage dans la console
        RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"),
        logging.FileHandler(LOG_FILE, encoding="utf-8")  # ✅ Ajout d'un log fichier
    ]
)
logging.debug("🚀 Système de logs initialisé.")

def load_radarr_cache():
    try:
        with open(RADARR_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_radarr_cache(cache):
    with open(RADARR_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def load_sonarr_cache():
    try:
        with open(SONARR_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_sonarr_cache(cache):
    with open(SONARR_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# 📌 Récupération du format de dossier depuis Radarr/Sonarr
def get_movie_folder_format(api_url, api_key, service_name):
    try:
        response = requests.get(f"{api_url}/api/v3/config/naming", headers={"X-Api-Key": api_key}, timeout=60)
        response.raise_for_status()
        data = response.json()
        folder_format = data.get("movieFolderFormat" if service_name == "Radarr" else "seriesFolderFormat")
        
        if folder_format:
            logging.info(f"✅ {service_name} - Folder Format: {folder_format}")
            #print(f"📂 {service_name} - movieFolderFormat: {folder_format}")
        else:
            logging.warning(f"⚠️ {service_name} - Aucun format récupéré, vérifier la configuration.")
        
        return folder_format
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la récupération du format de dossier {service_name}: {e}")
        return None




# 📌 Extraction des Folder Name Tokens avec accolades
def get_folder_name_tokens(folder_format, service_name):
    if not folder_format:
        logging.warning(f"⚠️ {service_name} - Aucun format trouvé pour extraire les tokens.")
        return []

    tokens = re.findall(r"\{[^{}]+\}", folder_format)  # Capture les tokens avec les accolades
    return tokens



# Récupérer les valeurs des tokens depuis Radarr/Sonarr
def get_movie_details(api_url, api_key, movie_id):
    """
    Récupère les détails d'un film depuis Radarr via son ID.
    """
    try:
        response = requests.get(f"{api_url}/api/v3/movie/{movie_id}", headers={"X-Api-Key": api_key}, timeout=60)
        response.raise_for_status()
        movie_data = response.json()
        logging.info(f"✅ Détails récupérés pour le film: {movie_data.get('title', 'Titre inconnu')} (ID: {movie_id})")
        return movie_data
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la récupération des détails du film {movie_id} : {e}")
        return None

# Récupérer tous les films et extraire les tokens
def get_all_movies(api_url, api_key, max_retries=5, wait_time=10):
    """
    Récupère la liste de tous les films dans Radarr et extrait leurs informations.
    """
    logging.info(f"📡 Récupération des films ayant un fichier depuis {api_url}...")    
#    try:
#        response = requests.get(f"{api_url}/api/v3/movie", headers={"X-Api-Key": api_key}, timeout=5)
#        response.raise_for_status()
#        movies = response.json()
#        logging.info(f"📊 {len(movies)} films récupérés avec succès.")


        # Filtrer les films qui ont un fichier
#        movies_with_files = [movie for movie in movies if movie.get("hasFile", False)]
        
#        logging.info(f"📊 {len(movies_with_files)} films avec fichier récupérés avec succès.")
        #logging.info(f"📜 Contenu brut de la réponse de Radarr: {movies}")
#        return movies_with_files
#    except requests.exceptions.RequestException as e:
#        logging.error(f"❌ Erreur lors de la récupération des films : {e}")
#        return []
    attempt = 0
    while attempt < max_retries:
        try:
            if attempt > 1:
                logging.info(f"📡 Tentative {attempt + 1}/{max_retries} - Récupération des films depuis Radarr...")

            response = requests.get(f"{api_url}/api/v3/movie", headers={"X-Api-Key": api_key}, timeout=60)
            response.raise_for_status()
            movies = response.json()
            logging.info(f"📊 {len(movies)} films récupérés avec succès.")
            
            # ✅ Retourne immédiatement si succès
            return [movie for movie in movies if movie.get("hasFile", False)]

        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ Erreur lors de la récupération des films : {e} - Réessai dans {wait_time} secondes...")
            time.sleep(wait_time)
            wait_time *= 10  # Augmente le temps d’attente progressivement
            attempt += 1

    # ❌ Après plusieurs tentatives, on abandonne
    logging.error(f"❌ Échec après {max_retries} tentatives. Impossible de récupérer les films depuis Radarr.")
    sys.exit(0)  # ✅ Quitte proprement le script
    return []




# 📌 Extraction dynamique des valeurs des tokens
def extract_token_values(movie_data, tokens):
    """
    Extrait les valeurs des tokens à partir des détails du film récupéré.
    """
    logging.debug(f"🔍 Extraction des valeurs des tokens pour le film : {movie_data.get('title', 'Titre inconnu')}")
    logging.debug(f"📜 Tokens attendus : {tokens}")

    # Mapping entre les tokens Radarr et les champs réels de l'API
    token_map = {
        "Release Year": "year",
        "Movie CleanTitle": "title",  # On va le nettoyer nous-mêmes
        "TmdbId": "tmdbId",
        "ImdbId": "imdbId"
    }

    token_values = {}

    for token in tokens:
        clean_token = token.strip("{}")  # Supprime les accolades

        if clean_token == "Movie CleanTitle":
            value = generate_clean_title(movie_data.get("title", "Unknown Title"))  # Nettoyage
        elif clean_token in token_map:
            api_field = token_map[clean_token]
            value = movie_data.get(api_field)
            if not value:
                value = f"Unknown-{clean_token}"

        else:
            value = f"Unknown-{clean_token}"  # Par défaut, si le champ n'existe pas

        token_values[token] = value  # Garde le format {Token}

    logging.debug(f"✅ Valeurs extraites : {token_values}")
    return token_values

def extract_series_token_values(series_data, tokens):
    """
    Extrait les valeurs des tokens pour une série (Sonarr) en évitant le doublon d'année.
    """
    logging.debug(f"📜 Données brutes de la série ID {series_data.get('id')} : {json.dumps(series_data, indent=4)}")

    # Récupérer les infos de la série
    title = series_data.get("title", "Unknown")
    year = str(series_data.get("year", series_data.get("firstAired", "0000")[:4]))

    # Vérifier si l'année est déjà présente dans le titre (ex: "Yellowstone (2018)")
    if f"({year})" in title:
        title_year = title  # On garde tel quel
    else:
        title_year = f"{title} ({year})"  # On ajoute l'année seulement si elle n'est pas déjà là

    # Mapping des tokens
    token_map = {
        "Series TitleYear": title_year,
        "ImdbId": series_data.get("imdbId", "Unknown-ImdbId"),
        "TvdbId": series_data.get("tvdbId", "Unknown-TvdbId")
    }

    token_values = {f"{{{key}}}": value for key, value in token_map.items()}

    logging.info(f"✅ Valeurs extraites pour Sonarr : {token_values}")
    return token_values



# 📌 Génération du new_path
# 📌 Génération du new_path avec un '/' devant
def generate_new_path(root_folder, folder_format, token_values):
    new_path = folder_format
    for token, value in token_values.items():
        if "Unknown" in str(value):
            new_path = new_path.replace(token, "")
        else:
            new_path = new_path.replace(token, str(value))

        
    # ✅ Correction : éviter un double `root_folder`
    if new_path.startswith(root_folder):
        final_path = new_path.replace("//", "/")
    else:
        final_path = f"{root_folder}/{new_path}".replace("//", "/")
    
    # ✅ Ajout d'un `/` à la fin pour s'assurer qu'il s'agit bien d'un dossier


    #return final_path.rstrip("/") + "/"
    final_path = final_path.rstrip("/") + "/"
    logging.debug(f"📂 Root Folder utilisé: {root_folder}")
    logging.debug(f"📂 Nouveau chemin généré (final_path): {final_path}")
    return final_path

def generate_series_path(root_folder, folder_format, token_values):
    """
    Génère le chemin de destination pour une série dans Sonarr.
    """
    new_path = folder_format

    # 🔹 Remplace les tokens spécifiques à Sonarr
    for token, value in token_values.items():
        if "Unknown" in str(value):
            new_path = new_path.replace(token, "")
        else:
            new_path = new_path.replace(token, str(value))


    # 🔹 Construit le chemin final (sans os)
    final_path = root_folder.rstrip("/") + "/" + new_path.rstrip("/") + "/"

    logging.info(f"📺 Chemin généré pour Sonarr : {final_path}")
    return final_path

# 📌 Mise à jour du chemin dans Radarr
def update_movie_path(api_url, api_key, movie_id, new_path, root_folder, root_folder_path, movies_to_process):
    """
    Met à jour le chemin d'un film dans Radarr avec tous les champs requis.
    """
    
    
    logging.debug(f"📂 Début de la mise à jour du chemin pour le film ID {movie_id}")
    logging.debug(f"📂 Root Folder Path utilisé: {root_folder_path}")
    root_folders = get_root_folders(api_url, api_key)

    # Vérifie si le chemin actuel est déjà correct
    current_path = get_movie_details(api_url, api_key, movie_id).get("path", "").rstrip("/")
    if current_path == new_path.rstrip("/"):
        logging.info(f"✅ Le film {movie_id} est déjà dans le bon dossier ({new_path}), aucune modification nécessaire.")
        return False
    else:
        # Sinon, on vérifie que le rootFolder est bien présent
        if not any(folder["path"].rstrip("/") == root_folder_path.rstrip("/") for folder in root_folders):
            logging.error(f"❌ Erreur : le dossier rootFolderPath '{root_folder_path}' n'existe pas dans Radarr.")
            logging.debug(f"✅ Le film {movie_id} dans le dossier ({new_path})")
            logging.debug(f"📂 📜 Liste des rootFolders disponibles dans Radarr: {[folder['path'] for folder in root_folders]}")
            return False


    max_attempts = 3  # ✅ Limite le nombre de tentatives pour éviter une boucle infinie
    attempt = 0


    # 📌 Étape 1 : Récupérer les détails complets du film depuis Radarr
    movie_details = get_movie_details(api_url, api_key, movie_id)
    if not movie_details:
        logging.error(f"❌ Impossible de récupérer les détails du film {movie_id}.")
        return False
        
        
    # 📌 Vérifier si le chemin est déjà correct
    current_path = movie_details.get("path", "").rstrip("/")
    if current_path == new_path.rstrip("/"):
        logging.info(f"✅ Le film {movie_id} est déjà dans le bon dossier ({new_path}), aucune modification nécessaire.")
        return False  # 🚀 On évite un appel inutile à l'API

    logging.info(f"📂 Chemin actuel récupéré de Radarr: {current_path}")
    logging.info(f"📂 Nouveau chemin souhaité : {new_path}")

    # ✅ Vérifier que `qualityProfileId` est bien présent et correct
    quality_profile_id = movie_details.get("qualityProfileId", 0)
    if quality_profile_id <= 0:
        logging.error(f"❌ Film {movie_id} - `qualityProfileId` est invalide : {quality_profile_id}")
        return true

    # ✅ Récupérer `rootFolderPath`
#    root_folder_path = movie_details.get("rootFolderPath", "")
#    if not root_folder_path:
#        logging.error(f"❌ Film {movie_id} - `rootFolderPath` introuvable.")
#        return False

    sort_title = movie_details.get("sortTitle", "")
    year = movie_details.get("year", "")
    metadataProfileId = movie_details.get("metadataProfileId")

    #logging.info(f"📂 Chemin actuel récupéré de Radarr: {movie_details.get('path', 'Inconnu')}")



    # 📌 Étape 2 : Construire la requête de mise à jour avec tous les champs nécessaires
    payload = {
        "id": movie_details["id"],
        "title": movie_details["title"],
        "sortTitle": sort_title,
        "year": year,
        "path": new_path,
        "monitored": movie_details["monitored"],
        "qualityProfileId": quality_profile_id,
        "metadataProfileId": movie_details.get("metadataProfileId"),
        "tmdbId": movie_details["tmdbId"],
        "imdbId": movie_details.get("imdbId", "")
       # "moveFiles": True  # ✅ Obligatoire pour déplacer les fichiers
    }

    if DRY_RUN:
        logging.info(f"[DRY_RUN] Simulation de modification du chemin pour le film ID {movie_id} -> {new_path}")
        logging.info(f"[DRY_RUN] Simulation de modification du chemin pour le film ID {movie_id} -> {new_path}")
        logging.info(f"[DRY_RUN] Requête API qui aurait été envoyée à Radarr :")
        #logging.info(f"URL: {api_url}/api/v3/movie/{movie_id}")
        #logging.info(f"Headers: {{'X-Api-Key': '{api_key}'}}")
        #logging.info(f"Payload: {json.dumps(payload, indent=4)}")  # ✅ Formate le JSON pour qu'il soit lisible
        return True

    # 📌 Étape 3 : Envoyer la requête PUT
    try:
        response = requests.put(
            f"{api_url}/api/v3/movie/{movie_id}?moveFiles=true",
            headers={"X-Api-Key": api_key},
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        logging.info(f"✅ Film ID {movie_id} - Chemin mis à jour: {new_path}")
        logging.debug("⏳ Pause pour laisser Radarr enregistrer le changement...")
        time.sleep(10)  # Pause pour éviter que Radarr traite une base vide
        
        # ✅ Forcer Radarr à rescanner le film après la mise à jour du chemin
        #force_rescan(api_url, api_key, movie_id)
        #time.sleep(1)  # Pause pour éviter que Radarr ignore le déplacement
        
        while attempt < max_attempts:
            logging.info(f"🔁 Tentative {attempt + 1}/{max_attempts} : Vérification des fichiers après changement de chemin...")
            
            if verify_movie_files(api_url, api_key, movie_id):
                logging.info(f"✅ Radarr détecte les fichiers après modification du chemin pour le film {movie_id}.")
                #start_time = time.time()
                #response = requests.get(f"{api_url}/api/v3/movie", headers={"X-Api-Key": api_key}, timeout=300)
                #logging.info(f"📊 Radarr a mis {time.time() - start_time:.2f} secondes pour répondre.")


                # ✅ Maintenant que tous les déplacements sont terminés, on peut rescanner
                #force_rescan(api_url, api_key, movie_id)
                movie_titles = [movie["title"] for movie in movies_to_process]  # Liste des titres des films traités
                #movie_titles = [movie["title"] for movie in processed_movies]  # ✅ Seulement les films traités
                #movie_titles = [movie_details["title"]]  # ✅ Récupère correctement le titre du film


                logging.debug("Liste des films passé.")
                
                # ✅ Attendre que MoveMovieService ait déplacé tous les films avant de rescanner
                if wait_for_movie_moves(api_url, api_key, movie_titles):
                    logging.info("♻️ Tous les films déplacés, lancement du rescan.")
                    force_rescan(api_url, api_key, movie_id)
                    #for movie_id in [movie_id]:  # Assure que movie_id est bien une liste itérable
                    for movie_id in [processed_movies]:  # Assure que movie_id est bien une liste itérable
                        logging.info("⚠️ rescan du film {movie_id}.")

                        force_rescan(api_url, api_key, movie_id)
                else:
                    logging.debug("⚠️ Certains films n'ont pas été déplacés ou plus de films a controler, rescan annulé.")


                #force_movie_move(api_url, api_key, movie_id)
                
                return True
            
            logging.warning(f"⚠️ Radarr ne détecte pas encore les fichiers après modification du chemin pour le film {movie_id}. Rescan en cours...")
            #force_rescan(api_url, api_key, movie_id)
            #time.sleep(1)  # ✅ Pause pour éviter un rescan trop rapide
            attempt += 1

        logging.error(f"❌ Échec après {max_attempts} tentatives : Radarr ne trouve toujours pas les fichiers.")
        return False
    
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la mise à jour du chemin pour le film {movie_id} : {e}")
        return False


def generate_clean_title(title):
    """
    Génère le 'Movie CleanTitle' en nettoyant le titre du film.
    """
    if not title:
        return "Unknown-Title"

    clean_title = title.lower()  # Convertit en minuscules pour standardiser
    clean_title = re.sub(r"[^a-zA-Z0-9 ]", "", clean_title)  # Supprime les caractères spéciaux
    clean_title = re.sub(r"\s+", " ", clean_title).strip()  # Remplace les espaces multiples par un seul
    return clean_title.title()  # Remet en majuscule la première lettre de chaque mot


def force_movie_move(api_url, api_key, movie_id):
    """
    Force Radarr à renommer et déplacer les fichiers du film après un changement de chemin.
    """
    max_attempts = 3  # ✅ Limite le nombre de tentatives pour éviter une boucle infinie
    attempt = 0

    # ✅ Récupérer le movieFileId AVANT d'envoyer la commande
    moviefile_id = get_movie_file_id(api_url, api_key, movie_id)
    
    if not moviefile_id:
        logging.error(f"❌ Aucun fichier trouvé pour le film {movie_id}. Impossible de renommer.")
        return False

    while attempt < max_attempts:
        logging.info(f"🔁 Tentative {attempt + 1}/{max_attempts} : Déclenchement du déplacement de fichiers pour le film {movie_id}...")

        try:
            response = requests.post(
                f"{api_url}/api/v3/command",
                headers={"X-Api-Key": api_key},
                json={"name": "RenameMovieFiles", "movieId": movie_id, "files": [moviefile_id]},  # ✅ Ajout du movieFileId
                timeout=60
            )
            response.raise_for_status()
            logging.info(f"✅ Déplacement des fichiers déclenché avec succès pour le film {movie_id}.")
            return True  # ✅ Succès -> on arrête ici

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Erreur lors du déclenchement du déplacement des fichiers pour le film {movie_id} : {e}")

        attempt += 1
        time.sleep(1)  # ✅ Pause pour éviter un spam de requêtes

    logging.error(f"❌ Échec : Impossible de déclencher le déplacement des fichiers après {max_attempts} tentatives.")
    return False  # 🚨 On arrête les tentatives




def verify_movie_files(api_url, api_key, movie_id):
    """
    Vérifie si Radarr détecte les fichiers associés au film après un changement de chemin.
    """
    try:
        for attempt in range(5):  # Ajout de 5 tentatives au lieu d'une seule
            response = requests.get(
                f"{api_url}/api/v3/moviefile?movieId={movie_id}",
                headers={"X-Api-Key": api_key},
                timeout=60
            )
            response.raise_for_status()
            files = response.json()

            if files:
                logging.info(f"✅ {len(files)} fichier(s) trouvé(s) pour le film {movie_id} après déplacement.")
                return True

            logging.warning(f"⚠️ Aucun fichier détecté dans Radarr après la mise à jour du chemin pour le film {movie_id}. Tentative {attempt+1}/5")
            time.sleep(10)  # Pause plus longue avant une nouvelle tentative

        logging.error(f"❌ Échec : Radarr ne trouve toujours pas les fichiers après 5 tentatives.")
        return False

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la vérification des fichiers dans Radarr pour le film {movie_id}: {e}")
        return False



def get_root_folders(api_url, api_key):
    """
    Récupère la liste des dossiers racines configurés dans Radarr.
    """
    try:
        response = requests.get(
            f"{api_url}/api/v3/rootFolder",
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        response.raise_for_status()
        root_folders = response.json()

        logging.debug(f"📂 Dossiers racines trouvés dans Radarr: {[folder['path'] for folder in root_folders]}")
        #logging.error(f" Films concerné: {[movie['title'] for movie in movies_to_process]}")
        
        return root_folders

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la récupération des dossiers racines de Radarr: {e}")
        return []




def force_rescan(api_url, api_key, movie_id):
    """
    Force Radarr à rescanner un film après mise à jour du chemin.
    """
    logging.info(f"🔄 Rescan du film {movie_id} en cours...")
    try:
        response = requests.post(
            f"{api_url}/api/v3/command",
            headers={"X-Api-Key": api_key},
            json={"name": "RescanMovie", "movieId": movie_id},
            timeout=60
        )
        response.raise_for_status()
        logging.info(f"✅ Rescan lancé pour le film {movie_id}.")
        return True

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors du rescan du film {movie_id} : {e}")
        return False


def get_movie_file_id(api_url, api_key, movie_id):
    """
    Récupère l'ID du fichier associé au film dans Radarr.
    """
    response = requests.get(
        f"{api_url}/api/v3/moviefile?movieId={movie_id}",
        headers={"X-Api-Key": api_key},
        timeout=60
    )
    
    if response.status_code != 200:
        logging.error(f"❌ Erreur lors de la récupération du fichier du film {movie_id}.")
        return None

    movie_files = response.json()
    
    if movie_files:
        moviefile_id = movie_files[0]["id"]
        logging.info(f"✅ MovieFile ID trouvé : {moviefile_id} pour le film {movie_id}")
        return moviefile_id
    else:
        logging.warning(f"⚠️ Aucun fichier trouvé pour le film {movie_id}. Impossible de renommer.")
        return None


def get_queue(api_url, api_key):
    """
    Récupère la file d'attente (queue) des tâches en cours de traitement dans Sonarr ou Radarr.
    """
    try:
        response = requests.get(f"{api_url}/api/v3/queue", headers={"X-Api-Key": api_key}, timeout=60)
        response.raise_for_status()

        # ✅ Vérifier si la réponse est bien du JSON
        try:
            queue_data = response.json()
        except json.JSONDecodeError:
            logging.error(f"❌ Erreur : réponse non JSON reçue de {api_url}/api/v3/queue")
            return []

        # ✅ Extraire uniquement la liste des tâches (champ `records`)
        if isinstance(queue_data, dict) and "records" in queue_data:
            return queue_data["records"]
        
        logging.error(f"❌ Erreur : réponse inattendue reçue de {api_url}/api/v3/queue : {queue_data}")
        return []

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la récupération de la file d'attente ({api_url}) : {e}")
        return []


    

def wait_for_completion(arr_url, arr_api_key, max_retries=20, wait_time=60):
    """
    Attend la fin des traitements en cours dans Sonarr ou Radarr avant de poursuivre.
    """

    logging.info(f"🔄 Vérification de la file d'attente sur {arr_url}...")

    last_non_empty_attempt = 0  # Stocke la dernière tentative où la queue n'était pas vide

    for attempt in range(max_retries):
        arr_queue = get_queue(arr_url, arr_api_key)

        # ✅ Vérifier que `arr_queue` est une liste
        if not isinstance(arr_queue, list):
            logging.error(f"❌ Erreur : réponse inattendue de {arr_url}/api/v3/queue : {arr_queue}")
            return False

        # Filtrer les tâches qui ne sont pas terminées
        active_tasks = [task for task in arr_queue if isinstance(task, dict) and task.get("status") not in ["completed", "warning"]]

        logging.info(f"📜 Queue active ({len(active_tasks)} tâches en cours): {[task.get('status') for task in active_tasks]}")

        if not active_tasks:
            # Vérification supplémentaire pour éviter les faux positifs
            if attempt - last_non_empty_attempt >= 3:  # 3 itérations vides avant confirmation
                logging.info("✅ Toutes les tâches sont terminées. Fin de l'attente.")
                return True
            else:
                logging.info("🔄 La queue est vide, mais on attend encore quelques itérations pour confirmation...")
        else:
            last_non_empty_attempt = attempt  # Réinitialisation car il reste des tâches actives

        logging.info(f"⏳ Attente {wait_time} secondes avant nouvelle vérification... (Tentative {attempt+1}/{max_retries})")
        time.sleep(wait_time)

    logging.error("❌ Les tâches en attente dans Sonarr/Radarr n'ont pas été terminées à temps.")
    return False

# 📌 Récupération des détails d'une série depuis Sonarr
def get_series_details(api_url, api_key, series_id):
    """
    Récupère les détails d'une série depuis Sonarr via son ID.
    """
    try:
        response = requests.get(f"{api_url}/api/v3/series/{series_id}", headers={"X-Api-Key": api_key}, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la récupération des détails de la série {series_id} : {e}")
        return None


# 📌 Récupération de toutes les séries depuis Sonarr
def get_all_series(api_url, api_key, max_retries=3, initial_timeout=60):
    """
    Récupère la liste de toutes les séries dans Sonarr avec un timeout adaptatif.
    """
    timeout = initial_timeout
    for attempt in range(max_retries):
        try:
            logging.info(f"📡 Tentative {attempt + 1}/{max_retries} - Timeout: {timeout}s")
            response = requests.get(f"{api_url}/api/v3/series?includeEpisodeFileCount=true",
                                    headers={"X-Api-Key": api_key}, timeout=timeout)
            response.raise_for_status()
            series = response.json()
            logging.info(f"📊 {len(series)} séries récupérées avec succès.")
            return [s for s in series if s.get("statistics", {}).get("episodeFileCount", 0) > 0]
        except requests.exceptions.Timeout:
            logging.warning(f"⚠️ Timeout après {timeout}s. Augmentation du timeout et nouvelle tentative...")
            timeout += 10  # On augmente le timeout à chaque échec
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Erreur Sonarr: {e}")
            return []

    logging.error(f"❌ Échec après {max_retries} tentatives. Impossible de récupérer les séries.")
    return []


# 📌 Mise à jour du chemin dans Sonarr
def update_series_path(api_url, api_key, series_id, new_path, root_folder_path):
    """
    Met à jour le chemin d'une série dans Sonarr.
    """
    try:
        series_details = get_series_details(api_url, api_key, series_id)
        if not series_details:
            return False

        current_path = series_details.get("path", "").rstrip("/")
        if current_path == new_path.rstrip("/"):
            logging.info(f"✅ La série {series_id} est déjà dans le bon dossier ({new_path}), aucune modification nécessaire.")
            return False

        # Mise à jour du chemin
        series_details["path"] = new_path
        series_details["rootFolderPath"] = root_folder_path

        # Nettoyage des champs inutiles ou à risque
        for key in ["seriesType", "cleanTitle", "sortTitle", "tags", "episodeFileCount", "episodeCount", "status"]:
            series_details.pop(key, None)

        if DRY_RUN:
            logging.info(f"[DRY_RUN] Simulation de modification du chemin pour la série ID {series_id} -> {new_path}")
            return True

        logging.debug(f"🔧 Payload envoyé à Sonarr pour mise à jour:\n{json.dumps(series_details, indent=2)}")

        response = requests.put(
            f"{api_url}/api/v3/series/{series_id}",
            headers={"X-Api-Key": api_key},
            json=series_details,
            timeout=60
        )
        response.raise_for_status()
        logging.info(f"✅ Série ID {series_id} - Chemin mis à jour: {new_path}")

        force_series_rescan(api_url, api_key, series_id)
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            logging.error(f"❌ Erreur 409 : Conflit lors du déplacement de la série ID {series_id}")
            logging.error(f"🔎 Chemin conflictuel : {new_path}")
            if Path(new_path).exists():
                logging.warning(f"⚠️ Le dossier {new_path} existe sur le disque. Vérifie s’il est lié à une autre série dans Sonarr.")
            else:
                logging.warning("⚠️ Le dossier n’existe pas sur le disque. Il peut s’agir d’un conflit en base Sonarr.")
        else:
            logging.error(f"❌ Erreur HTTP Sonarr : {e}")
        return False

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors de la mise à jour du chemin pour la série {series_id} : {e}")
        return False




# 📌 Forcer un rescan de la série
def force_series_rescan(api_url, api_key, series_id):
    """
    Force Sonarr à rescanner une série après mise à jour du chemin.
    """
    logging.info(f"🔄 Rescan de la série {series_id} en cours...")
    try:
        response = requests.post(
            f"{api_url}/api/v3/command",
            headers={"X-Api-Key": api_key},
            json={"name": "RescanSeries", "seriesId": series_id},
            timeout=60
        )
        response.raise_for_status()
        logging.info(f"✅ Rescan lancé pour la série {series_id}.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erreur lors du rescan de la série {series_id} : {e}")
        return False


# 📌 Traitement des séries dans Sonarr
def process_sonarr(sonarr_cache):
    logging.info("🚀 Début du traitement Sonarr...")
    sonarr_cache = load_sonarr_cache()
    logging.info(f"📊 {len(sonarr_cache)} séries dans le cache.")

    folder_format = get_movie_folder_format(SONARR_URL, SONARR_API_KEY, "Sonarr")
    logging.info(f"🎬 Series Folder Format de Sonarr: {folder_format}")
    tokens = get_folder_name_tokens(folder_format, "Sonarr")

    series_list = get_all_series(SONARR_URL, SONARR_API_KEY)
    logging.info(f"📊 {len(series_list)} séries trouvées dans Sonarr.")
    logging.info("📊 Recherche de séries à traiter.")

    processed_series = []
    count = 0

    for series in series_list:
        series_id = str(series["id"])
        if WORK_LIMIT > 0 and count >= WORK_LIMIT:
            logging.info("🔹 WORK_LIMIT atteint pour Sonarr, arrêt du traitement.")
            break

        if series_id in sonarr_cache:
            logging.debug(f"⏭️ Série ID {series_id} déjà dans le cache, on saute.")
            continue

        token_values = extract_series_token_values(series, tokens)
        root_folder_path = series.get("rootFolderPath", "/media/Series").rstrip("/")
        root_folders = get_root_folders_sonarr(SONARR_URL, SONARR_API_KEY)
        if not any(root_folder_path == folder.get("path", "").rstrip("/") for folder in root_folders):
            logging.warning(f"❌ Dossier racine non valide pour la série {series_id} : {root_folder_path}")
            continue

        new_path = generate_series_path(root_folder_path, folder_format, token_values)
        current_path = series.get("path", "").rstrip("/")

        if current_path == new_path.rstrip("/"):
            logging.info(f"✅ La série {series['title']} est déjà dans le bon dossier ({current_path}), aucune modification nécessaire.")
            sonarr_cache[series_id] = new_path.rstrip("/")
            logging.debug(f"✅ Série {series_id} ajoutée au cache : {new_path}")
            continue

        logging.info(f"📂 Chemin actuel récupéré de Sonarr: {current_path}")
        logging.info(f"📂 Nouveau chemin souhaité : {new_path}")

        result = update_series_path(
            SONARR_URL,
            SONARR_API_KEY,
            series["id"],
            new_path,
            root_folder_path
        )

        sonarr_cache[series_id] = new_path.rstrip("/")

        if result and series not in processed_series:
            processed_series.append(series)
            count += 1
            logging.info(f"{count} séries traitées")

    save_sonarr_cache(sonarr_cache)
    if processed_series:
        wait_for_series_moves(processed_series)

    logging.info(f"💾 Cache Sonarr sauvegardé avec {len(sonarr_cache)} séries.")
    logging.info("✅ Fin du traitement Sonarr.")

def get_root_folders_sonarr(api_url, api_key):
    try:
        response = requests.get(
            f"{api_url}/api/v3/rootfolder",
            headers={"X-Api-Key": api_key},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération des dossiers racine Sonarr : {e}")
        return []



def normalize_title(title):
    """ Nettoie et normalise un titre pour éviter les différences de format. """
    if not title:
        return ""
    title = unidecode.unidecode(title)  # Supprime les accents
    title = re.sub(r"[^a-zA-Z0-9]", "", title.lower().strip())  # Supprime tout sauf lettres et chiffres
    return title

def is_title_match(expected_title, moved_title, threshold=85):
    """ Vérifie si deux titres sont similaires en utilisant Fuzzy Matching. """
    score = fuzz.ratio(expected_title, moved_title)
    return score >= threshold






def wait_for_movie_moves(api_url, api_key, processed_movies, max_retries=5, wait_time=10):
    """
    Vérifie si les films traités ont bien été déplacés en analysant les logs de Radarr.
    Ne prend en compte que les logs des dernières 12 heures et limite la requête.
    """
    retries = 0
    moved_movies = set()
    max_pages = 3  # ✅ Limite stricte des pages de logs analysées
    log_time_threshold = datetime.utcnow() - timedelta(hours=12)  # ✅ Seulement les 12 dernières heures

    logging.debug("🟢 Début de wait_for_movie_moves()")

    # ✅ Vérification et formatage de `processed_movies`
    if not isinstance(processed_movies, list) or not processed_movies:
        logging.error("❌ `processed_movies` est vide ou invalide !")
        return False

    expected_titles = {normalize_title(movie["title"]) for movie in processed_movies if isinstance(movie, dict) and "title" in movie}
    
    logging.debug(f"📜 Films attendus apres controle({len(expected_titles)}) : {sorted(expected_titles)}")
    if not expected_titles:
        logging.debug("❌ plus de titre valide récupéré dans `processed_movies`.")
        return False

    

    while retries < max_retries:
        try:
            logs = []
            page = 1
            logging.info(f"📡 Vérification des logs Radarr - Tentative {retries + 1}/{max_retries}")

            while page <= max_pages:
                response = requests.get(
                    f"{api_url}/api/v3/log?page={page}&pageSize=50&sortKey=time&sortDirection=descending",
                    headers={"X-Api-Key": api_key}, timeout=30
                )

                if response.status_code != 200:
                    logging.error(f"❌ Erreur API ({response.status_code}) en récupérant les logs.")
                    return False

                response.raise_for_status()
                new_logs = response.json().get("records", [])

                if not new_logs:
                    logging.info(f"📜 Fin de la récupération des logs (Page {page} vide).")
                    break  # ✅ Arrêt si plus de logs

                logs.extend(new_logs)
                logging.info(f"📜 Page {page} récupérée avec {len(new_logs)} entrées.")

                # ✅ Filtrage des logs contenant "moved successfully to" et récents (< 12h)
                for log in new_logs:
                    log_time = datetime.strptime(log["time"], "%Y-%m-%dT%H:%M:%SZ")
                    if log_time < log_time_threshold:
                        continue  # ❌ Trop ancien, on ignore

                    message = log.get("message", "").lower()
                    if "moved successfully to" in message:
                        moved_title = normalize_title(message.split("moved successfully to")[0].strip())
                        if moved_title in expected_titles:
                            logging.info(f"🎯 Film déplacé détecté : {message}")
                            moved_movies.add(moved_title)

                if moved_movies >= expected_titles:
                    logging.info(f"✅ Tous les films déplacés ({len(moved_movies)}/{len(expected_titles)}).")
                    return True  # ✅ Succès, on sort

                page += 1

            remaining_movies = expected_titles - moved_movies
            logging.warning(f"⏳ Films encore en déplacement ({len(remaining_movies)}) : {sorted(remaining_movies)}")
            
            if retries >= 3 and not moved_movies:
                logging.error("❌ Aucun film déplacé après plusieurs tentatives, sortie forcée.")
                return False

            time.sleep(wait_time)
            wait_time += 5  # ✅ Délai progressif pour éviter le spam API
            retries += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Erreur API Radarr : {e}")
            return False

    logging.warning("⚠️ Certains films déplacés n'ont pas été détectés après plusieurs tentatives.")
    return False


def wait_for_series_moves(series_list):
    for series in series_list:
        series_id = series["id"]
        title = series["title"]

        for attempt in range(1, 4):
            logging.info(f"🔁 Tentative {attempt}/3 : Vérification des fichiers pour la série {series_id} après changement de chemin...")

            try:
                response = requests.get(
                    f"{SONARR_URL}/api/v3/episodefile?seriesId={series_id}",
                    headers={"X-Api-Key": SONARR_API_KEY},
                    timeout=10
                )
                response.raise_for_status()
                files = response.json()

                if files:
                    logging.info(f"✅ {len(files)} fichier(s) trouvé(s) pour la série {series_id} après déplacement.")
                    break
                else:
                    logging.warning(f"⚠️ Aucun fichier trouvé pour la série {series_id}.")
            except Exception as e:
                logging.error(f"❌ Erreur lors de la récupération des fichiers pour la série {series_id} : {e}")

            time.sleep(2)







def check_radarr_move_logs():
    """
    Vérifie les logs de Radarr pour s'assurer que les déplacements de films sont terminés.
    """
    url = f"{RADARR_URL}/api/v3/log?page=1&pageSize=50"
    headers = {"X-Api-Key": RADARR_API_KEY}

    max_attempts = 10
    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            logs = response.json().get("records", [])

            # Recherche des logs de déplacement de film
            move_logs = [log for log in logs if log["logger"] == "MoveMovieService"]

            if not move_logs:  # Aucun déplacement détecté
                logging.info("✅ Aucun déplacement en cours dans les logs de Radarr. On peut continuer.")
                return True
            else:
                logging.info(f"⏳ {len(move_logs)} déplacements détectés dans Radarr, attente de 30s...")

        else:
            logging.error(f"❌ Erreur lors de la récupération des logs Radarr. Code: {response.status_code}")

        time.sleep(30)  # Attente avant la prochaine vérification

    logging.warning("⚠️ Temps d'attente écoulé, passage à l'étape suivante malgré tout.")
    return False

# 📌 Traitement des films dans Radarr
def process_radarr(radarr_cache):
    logging.debug("📡 Étape 1 : Récupération du Movie Folder Format de Radarr...")
    folder_format = get_movie_folder_format(RADARR_URL, RADARR_API_KEY, "Radarr")

    if folder_format:
        logging.info(f"🎬 Movie Folder Format de Radarr: {folder_format}")

        # Extraction des tokens
        logging.debug("📡 Étape 3 : Extraction des tokens...")
        tokens = get_folder_name_tokens(folder_format, "Radarr")

        if tokens:
            logging.info(f"📡 Tokens extraits: {tokens}")

            logging.debug("📡 Étape 5 : Récupération de tous les films depuis Radarr...")
            movies = get_all_movies(RADARR_URL, RADARR_API_KEY)

            if not movies:
                logging.warning("⚠️ Étape 6 : Aucun film récupéré depuis Radarr ! Vérifie l'API.")
            else:
                logging.info(f"📊 {len(movies)} films trouvés dans Radarr.")
                logging.info (f"📊 Recherche de films a traiter.")

            processed_movies = []  # ✅ Liste des films réellement déplacés dans cette session
            count = 0

            for movie in movies:
                if WORK_LIMIT > 0 and count >= WORK_LIMIT:
                    logging.debug("🔹 WORK_LIMIT atteint, arrêt du traitement.")
                    
                    break
                
                movie_id = str(movie["id"])
                # 🔍 Skip si déjà dans le cache
                if movie_id in radarr_cache:
                    logging.debug(f"⏭️ Film ID {movie_id} déjà traité, on saute.")
                    continue
                
                logging.debug(f"🎬 Étape 8 : Début du traitement du film : {movie.get('title', 'Titre inconnu')}")

                token_values = extract_token_values(movie, tokens)
                new_path = generate_new_path(movie["rootFolderPath"], folder_format, token_values)
                
                cached_path = radarr_cache.get(str(movie_id))
                if cached_path and cached_path == new_path.rstrip("/"):
                    logging.debug(f"⏭️ Film {movie_id} déjà dans le bon dossier (via cache), on saute.")
                    continue


                # ✅ Vérifier si le chemin est déjà correct
                current_path = movie.get("path", "").rstrip("/")
                if current_path == new_path.rstrip("/"):
                    logging.debug(f"✅ Le film {movie['title']} est déjà dans le bon dossier, aucun changement nécessaire.")
                    radarr_cache[movie_id] = new_path.rstrip("/")  # ➕ On ajoute au cache
                    continue  # Passe au film suivant

                logging.debug(f"📂 Étape 12 : new_path généré: {new_path}")

                # ✅ Met à jour uniquement si nécessaire
                result = update_movie_path(RADARR_URL, RADARR_API_KEY, movie_id, new_path, movie["rootFolderPath"], movie["rootFolderPath"], movies)

                # dans la boucle principale
                if result:
                    radarr_cache[movie_id] = new_path.rstrip("/")
                    processed_movies.append(movie)
                    count += 1
                    logging.info(f"{count} films traités")
                else:
                    logging.info(f"🔄 Aucun changement requis pour le film ID {movie_id}, on passe au suivant.")
                    radarr_cache[movie_id] = new_path.rstrip("/")


            logging.info(f"✅ Fin du traitement. {count} films modifiés.")
            logging.debug(f"✅ liste processed_movies: {processed_movies} ")

    save_radarr_cache(radarr_cache)
    logging.info(f"💾 Cache sauvegardé avec {len(radarr_cache)} films.")


# 📌 Rafraîchissement de Plex
def plex_refresh(plex_url, plex_api_key, main_logger):
    """ Rafraîchit les bibliothèques Plex """
    headers = {"X-Plex-Token": plex_api_key}
    response = requests.get(f"{plex_url}/library/sections/all/refresh", headers=headers)
    if response.status_code == 200:
        main_logger.info("✅ Actualisation de la bibliothèque Plex réussie.")
    else:
        main_logger.error("❌ Échec de l'actualisation de la bibliothèque Plex.")

# 📌 Exécution principale
def main():
    logging.info("🚀 Démarrage du script...")
    logging.info(f"🛠️  Version de l'outil : {VERSION}")
    
    radarr_cache = load_radarr_cache()
    logging.info(f"📊 {len(radarr_cache)} films dans le cache.")
    sonarr_cache = load_sonarr_cache()
    logging.info(f"📊 {len(sonarr_cache)} series dans le cache.")

    if RUN_RADARR:
        process_radarr(radarr_cache)

    if RUN_SONARR:
        process_sonarr(sonarr_cache)

    # ✅ Rafraîchissement Plex après traitement
    if not DRY_RUN:
        #movie_titles = [movie["title"] for movie in processed_movies]
        #if RUN_RADARR and wait_for_movie_moves(RADARR_URL, RADARR_API_KEY, processed_movies):
        if RUN_RADARR:# and wait_for_movie_moves(RADARR_URL, RADARR_API_KEY, movie_titles):
            logging.debug("♻️ Radarr refresh done...")
        if RUN_SONARR:# and wait_for_completion(SONARR_URL, SONARR_API_KEY, max_retries=10, wait_time=30):
            logging.info("♻️ Sonarr refresh done...")
        logging.info("♻️ Rafraîchissement de Plex...")
        plex_refresh(PLEX_URL, PLEX_API_KEY, logging)
        logging.info("✅ Plex a été actualisé avec succès.")
    else:
        logging.error("❌ Impossible de rafraîchir Plex car Sonarr/Radarr n'ont pas terminé à temps.")

    logging.info("✅ Fin du script.")

if __name__ == "__main__":
    main()



