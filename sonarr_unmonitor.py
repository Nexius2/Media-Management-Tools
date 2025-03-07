# -*- coding: utf-8 -*-

"""
#########################################################
# Media Management Tools (MMT) - Sonarr Unmonitor
# Auteur       : Nexius2
# Version      : 4.4.2.1
# Description  : Script permettant de désactiver le monitoring
#                des épisodes dans Sonarr en fonction des critères
#                définis dans `config.json`.
# Licence      : MIT
#########################################################

🛠 Sonarr Unmonitor - Désactivation automatique des épisodes dans Sonarr

=============================================================
📌 DESCRIPTION
-------------------------------------------------------------
Sonarr Unmonitor est un script Python permettant de **désactiver le monitoring**
des épisodes dans Sonarr en fonction des critères définis dans `config.json`.
Il permet d'éviter que des épisodes déjà récupérés soient à nouveau téléchargés.

📂 Fonctionnalités :
- Analyse les séries et leurs **épisodes monitorés avec un fichier**.
- Vérifie si le **nom du fichier** correspond aux critères de désactivation.
- Désactive automatiquement le monitoring des épisodes concernés.
- **Mode simulation (DRY_RUN)** pour tester sans effectuer de modifications.
- **Logs détaillés** des épisodes traités et des erreurs éventuelles.

=============================================================
📜 FONCTIONNEMENT
-------------------------------------------------------------
1. **Connexion à Sonarr** via son API.
2. **Récupération de la liste des séries et épisodes monitorés** ayant un fichier.
3. **Analyse du nom du fichier** et comparaison avec les critères définis.
4. **Désactivation du monitoring** pour les épisodes correspondants.
5. **Gestion du mode simulation** (`dry_run` activé/désactivé).
6. **Gestion avancée des erreurs et des logs**.

=============================================================
⚙️ CONFIGURATION (config.json)
-------------------------------------------------------------
Le script utilise un fichier de configuration JSON contenant les paramètres suivants :

{
    "services": {
        "sonarr": {
            "url": "http://192.168.1.100:8989",
            "api_key": "VOTRE_CLE_API_SONARR"
        }
    },
    "sonarr_unmonitor": {
        "log_file": "sonarr_unmonitor.log",
        "log_level": "INFO",
        "dry_run": true,
        "search_terms": [
            ["1080", "FR", "MULTI"],
            ["4K", "FR", "MULTI"]
        ]
    }
}

| Clé                           | Description |
|--------------------------------|-------------|
| `services.sonarr.url`         | URL de l'instance Sonarr |
| `services.sonarr.api_key`     | Clé API pour Sonarr |
| `sonarr_unmonitor.log_file`   | Nom du fichier de log |
| `sonarr_unmonitor.log_level`  | Niveau de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `sonarr_unmonitor.dry_run`    | `true` = simulation, `false` = modifications réelles |
| `sonarr_unmonitor.search_terms` | Liste des groupes de critères pour la désactivation |

📌 **Critères de désactivation (`search_terms`)**
- Chaque groupe de termes doit être **présent simultanément** dans le nom du fichier.
- Exemple :
  - `["1080", "FR", "MULTI"]` ➝ Désactive si les trois termes sont présents.
  - `["4K", "FR", "MULTI"]` ➝ Désactive si ces trois termes sont présents.

=============================================================
🚀 UTILISATION
-------------------------------------------------------------
1. **Installez les dépendances requises** :
   pip install requests

2. **Créez/modifiez le fichier `config.json`** avec vos paramètres.

3. **Lancez le script en mode simulation (DRY_RUN activé)** :
   python sonarr_unmonitor.py
   - Aucun épisode ne sera désactivé, mais le script affichera ceux qui le seraient.

4. **Exécutez le script avec modifications réelles** (après avoir mis `dry_run` sur `false` dans `config.json`) :
   python sonarr_unmonitor.py
   - Les épisodes correspondant aux critères seront réellement désactivés.

=============================================================
📄 LOGS ET DEBUG
-------------------------------------------------------------
Le script génère des logs détaillés :
- Les logs sont enregistrés dans le fichier spécifié (`sonarr_unmonitor.log`).
- En mode `DEBUG`, toutes les analyses et modifications sont enregistrées.
- Les erreurs de connexion ou de requête API sont également loguées.

=============================================================
🛑 PRÉCAUTIONS
-------------------------------------------------------------
- **Aucun fichier n'est supprimé**, seule la surveillance est désactivée.
- **Le monitoring peut être réactivé** manuellement dans Sonarr si nécessaire.
- **Vérifiez les logs avant de désactiver `dry_run`**, pour éviter des désactivations indésirables.

=============================================================
🔥 EXEMPLE D'EXÉCUTION EN MODE `DRY_RUN`
-------------------------------------------------------------
python sonarr_unmonitor.py

📝 **Exemple de sortie :**
🚀 Début du traitement des séries dans Sonarr...
📥 500 séries récupérées depuis Sonarr.
✅ 480 séries avec épisodes monitorés et téléchargés.
📋 25 épisodes détectés correspondant aux critères de désactivation.
🔧 Mode DRY RUN activé. Aucun épisode ne sera modifié.

=============================================================
🗑 EXEMPLE D'EXÉCUTION AVEC MODIFICATIONS EFFECTIVES
-------------------------------------------------------------
Après avoir mis `dry_run` sur `false` dans `config.json` :

python sonarr_unmonitor.py

📝 **Exemple de sortie :**
🚀 Début du traitement des séries dans Sonarr...
📥 500 séries récupérées depuis Sonarr.
✅ 480 séries avec épisodes monitorés et téléchargés.
📋 25 épisodes détectés correspondant aux critères de désactivation.
📝 Épisode "Breaking Bad S02E05" marqué comme NON MONITORÉ.
📝 Épisode "Game of Thrones S04E03" marqué comme NON MONITORÉ.
✅ Fin du traitement. 25 épisodes ont été désactivés.

=============================================================
💡 ASTUCE
-------------------------------------------------------------
Vous pouvez programmer l'exécution automatique de ce script 
via un **cron job** ou une **tâche planifiée Windows**.

"""


import requests
import json
import logging
from logging.handlers import RotatingFileHandler
import re
import time

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
            pattern = rf"(?:^|[\[\]\+\-&\s\._,]){re.escape(term)}(?:p|i|$|[\[\]\+\-&\s\._,])"
        else:
            pattern = rf"(?:^|[\[\]\+\-&\s\._,]){re.escape(term.lower())}(?:$|[\[\]\+\-&\s\._,])"

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
    """ Désactive le monitoring d'un épisode dans Sonarr et vérifie l'état après mise à jour """
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

    max_retries = 5  # Nombre de tentatives en cas d'échec
    for attempt in range(max_retries):
        response = requests.put(url, headers=HEADERS, json=episode_data)

        if response.status_code == 200:
            logging.info(f"✅ Épisode '{title}' (S{season}E{episode_number}, ID: {episode_id}) marqué comme NON MONITORÉ avec succès.")
            break
        elif response.status_code == 202:
            logging.warning(f"⚠️ Sonarr est lent à traiter '{title}' (S{season}E{episode_number}, ID: {episode_id}). Vérification après 3 secondes...")
            time.sleep(3)  # Pause avant de vérifier l'état

            # Vérifier si l'épisode a bien été mis à jour
            check_response = requests.get(url, headers=HEADERS)
            if check_response.status_code == 200:
                updated_episode = check_response.json()
                if not updated_episode.get("monitored", True):  # Si monitored est bien passé à False
                    logging.info(f"✅ Vérification OK : Épisode '{title}' (S{season}E{episode_number}, ID: {episode_id}) est bien NON MONITORÉ après attente.")
                    break
            else:
                logging.warning(f"⚠️ Impossible de vérifier l'état de '{title}' (S{season}E{episode_number}, ID: {episode_id}) après mise à jour.")
        else:
            logging.error(f"❌ Erreur lors de la mise à jour de l'épisode {episode_id}: {response.status_code} - {response.text}")
            break

    # Pause courte pour éviter un trop grand nombre de requêtes simultanées
    time.sleep(1)



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
