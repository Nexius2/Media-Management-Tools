from arrapi import RadarrAPI
import json
import logging
from logging.handlers import RotatingFileHandler
import requests
import re


# Charger la configuration
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    print("✅ Configuration chargée avec succès.")
except FileNotFoundError:
    print(f"❌ Erreur : fichier de configuration '{CONFIG_FILE}' introuvable.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Erreur de parsing JSON dans '{CONFIG_FILE}': {e}")
    exit(1)


# 📌 Récupération des paramètres de config
RADARR_URL = config["services"]["radarr"]["url"]
RADARR_API_KEY = config["services"]["radarr"]["api_key"]
LOG_FILE = config["RadarrCleaner"]["log_file"]
LOG_LEVEL = config["RadarrCleaner"]["log_level"].upper()
DRY_RUN = config["RadarrCleaner"]["dry_run"]

# 🔧 Configuration avancée des logs avec rotation
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)  # 5 MB par fichier, 5 backups max
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("✅ Logging initialisé avec succès. Fichier de log utilisé : " + LOG_FILE)


# ✅ Connexion à Radarr
try:
    radarr = RadarrAPI(RADARR_URL, RADARR_API_KEY)
    logger.info("✅ Connexion réussie à Radarr.")
except Exception as e:
    logger.error(f"❌ Erreur de connexion à Radarr : {e}")
    exit(1)

# 📌 Récupère tous les films
try:
    films = radarr.all_movies()
    logger.info(f"📂 {len(films)} films récupérés depuis Radarr.")
except Exception as e:
    logger.error(f"❌ Erreur lors de la récupération des films : {e}")
    exit(1)

# 🎯 Filtre les films qui ne sont pas téléchargés (ceux sans fichier associé)
films_non_telecharges = [film for film in films if not film.hasFile]

# 📋 Affiche les titres des films non téléchargés en format JSON
films_a_supprimer = [{"title": film.title, "tmdbId": film.tmdbId} for film in films_non_telecharges]

if logger.level == logging.DEBUG:
    logger.debug(json.dumps(films_a_supprimer, indent=4, ensure_ascii=False))
#print(json.dumps(films_a_supprimer, indent=4, ensure_ascii=False))
logger.info(f"📋 {len(films_a_supprimer)} films non téléchargés détectés.")

# 📌 Fonction pour récupérer les logs de Radarr
def get_logs():
    url = f"{RADARR_URL}/api/v3/log?page=1&pageSize=100"
    headers = {"X-Api-Key": RADARR_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"❌ Erreur lors de la récupération des logs : {response.status_code}")
        return []

# 📌 Fonction pour récupérer les messages de santé de Radarr
def get_health_messages():
    url = f"{RADARR_URL}/api/v3/health"
    headers = {"X-Api-Key": RADARR_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"❌ Erreur lors de la récupération des messages de santé : {response.status_code}")
        return []


# 📌 Fonction pour récupérer la liste complète des films
def get_movies():
    url = f"{RADARR_URL}/api/v3/movie"
    headers = {"X-Api-Key": RADARR_API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"❌ Erreur lors de la récupération des films : {response.status_code}")
        return []

# 📌 Fonction pour supprimer un film de Radarr
def delete_movie(movie_id):
    url = f"{RADARR_URL}/api/v3/movie/{movie_id}?deleteFiles=false"
    headers = {"X-Api-Key": RADARR_API_KEY}

    if DRY_RUN:
        logger.info(f"🔧 DRY RUN : Film {movie_id} aurait été supprimé.")
        return

    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        logger.info(f"🗑 Film supprimé : ID {movie_id}")
    else:
        logger.error(f"❌ Erreur lors de la suppression du film {movie_id} : {response.status_code}")


# 📌 Fonction principale
def main():
    logger.info("🚀 Démarrage de l'analyse des films 'Removed from TMDB'...")

    # 🔹 Étape 1 : Récupérer les messages de santé
    health_messages = get_health_messages()

    # 📋 Extraire les `tmdbId` des films concernés depuis "RemovedMovieCheck"
    removed_tmdb_ids = set()
    for message in health_messages:
        if message.get("source") == "RemovedMovieCheck":
            match = re.findall(r"tmdbid (\d+)", message.get("message", ""))
            removed_tmdb_ids.update(map(int, match))  # Convertir en `int` pour comparer avec Radarr

    if not removed_tmdb_ids:
        logger.info("✅ Aucun film marqué comme 'Removed from TMDB' trouvé.")
        return

    logger.info(f"📋 {len(removed_tmdb_ids)} films détectés comme 'Removed from TMDB'.")

    # 🔹 Étape 2 : Récupérer la liste des films et filtrer ceux qui ne sont pas téléchargés
    movies = get_movies()
    movies_to_remove = []

    for movie in movies:
        if movie["tmdbId"] in removed_tmdb_ids and not movie["hasFile"]:
            movies_to_remove.append({"title": movie["title"], "id": movie["id"], "tmdbId": movie["tmdbId"]})

    # 🔹 Étape 3 : Affichage et suppression conditionnelle
    if movies_to_remove:
        #print("📋 Films à supprimer (non téléchargés et retirés de TMDB) :")
        if logger.level == logging.DEBUG:
            logger.debug(json.dumps(movies_to_remove, indent=4, ensure_ascii=False))

        #print(json.dumps(movies_to_remove, indent=4, ensure_ascii=False))
        logger.info(f"📋 {len(movies_to_remove)} films à supprimer.")

        # 🔥 Suppression avec gestion de DRY_RUN
        if DRY_RUN:
            logger.info("🔧 Mode DRY RUN activé, aucune suppression effectuée.")
            print("🔧 Mode DRY RUN activé. Aucune suppression ne sera effectuée.")
        else:
            for movie in movies_to_remove:
                delete_movie(movie["id"])
            print("✅ Suppression effectuée.")
    else:
        logger.info("✅ Aucun film 'Removed from TMDB' sans fichier détecté.")

if __name__ == '__main__':
    main()


