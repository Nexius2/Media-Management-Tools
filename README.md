# 📌 Media Management Tools - README

## 🚀 Description

Ce projet contient plusieurs scripts permettant d'automatiser la gestion des médias dans Radarr, Sonarr, qBittorrent et Plex. Chaque script a un objectif spécifique et fonctionne avec une configuration centralisée dans `config.json`.

## 📂 Installation

### 1️⃣ Prérequis

- **Python 3.x** installé
- **Dépendances Python** installées
- **Radarr, Sonarr, qBittorrent et Plex** configurés et fonctionnels
- **API Keys** récupérées pour chaque service
- \*\*Fichier de configuration \*\***`config.json`** bien rempli

### 2️⃣ Installation des dépendances

```bash
pip install requests qbittorrent-api arrapi
```

---

## 🔧 Scripts disponibles

### 1️⃣ **Radarr Unmonitor** (`radarr_unmonitor.py`)

**Description** :
Ce script désactive le monitoring des films dans **Radarr** en fonction de critères définis dans `config.json`. Il filtre les films ayant un fichier téléchargé et correspondant aux critères définis.

**Exécution** :

```bash
python radarr_unmonitor.py
```

**Mode Simulation (Dry-Run)** :
Si activé dans `config.json`, le script affiche les films qui **auraient été désactivés**, sans modifier Radarr.

---

### 2️⃣ **Sonarr Unmonitor** (`sonarr_unmonitor.py`)

**Description** :
Similaire à Radarr Unmonitor, mais pour les séries dans **Sonarr**. Il désactive le monitoring des épisodes selon des critères définis.

**Exécution** :

```bash
python sonarr_unmonitor.py
```

**Mode Simulation (Dry-Run)** :
Active ou désactive le mode test via `config.json`.

---

### 3️⃣ **Radarr Cleaner** (`RadarrCleaner.py`)

**Description** :
Ce script supprime les films marqués comme "Removed from TMDB" dans Radarr et qui n'ont pas de fichier téléchargé.

**Exécution** :

```bash
python RadarrCleaner.py
```

**Mode Simulation (Dry-Run)** :
Affiche les films qui seraient supprimés sans les retirer réellement.

---

### 4️⃣ **qBittorrent Cleaner** (`QBCleaner.py`)

**Description** :
Ce script connecte à **qBittorrent** et supprime les torrents les plus anciens pour libérer de l'espace disque si celui-ci est inférieur au seuil défini dans `config.json`.

**Exécution** :

```bash
python QBCleaner.py
```

**Fonctionnalités** :

- Vérifie l'espace disque
- Supprime les torrents les plus anciens en batch
- Gère les suppressions en mode simulation (Dry-Run)

---

## 📁 arr_folder_renamer

### 🇫🇷 Description

`arr_folder_renamer.py` est un script Python qui renomme automatiquement les dossiers des **films (Radarr)** et **séries (Sonarr)** selon le format configuré dans chaque application, puis vérifie que les fichiers sont toujours bien détectés. Il met ensuite à jour un **cache local** pour éviter les traitements redondants.

Il utilise les APIs de :
- Radarr
- Sonarr
- Plex (pour forcer un scan à la fin)

### 🔧 Utilisation

```bash
python arr_folder_renamer.py
```

Le comportement est défini dans `config.json` (voir ci-dessous).

### 📁 Structure du fichier `config.json`

```json
"arr_folder_renamer": {
    "log_file": "logs/arr_folder_renamer.log",   // Chemin vers le fichier de logs
    "log_level": "INFO",                         // Niveau de log : DEBUG, INFO, WARNING, etc.
    "dry_run": false,                            // true = simulation sans modifier quoi que ce soit
    "run_sonarr": true,                          // true = activer le traitement des séries
    "run_radarr": true,                          // true = activer le traitement des films
    "work_limit": 200                            // Limite de séries/films à traiter à chaque exécution
}
```

Et dans la section `services` :

```json
"services": {
    "radarr": {
        "url": "http://192.168.1.60:7878",
        "api_key": "clé_api_radarr"
    },
    "sonarr": {
        "url": "http://192.168.1.60:8989",
        "api_key": "clé_api_sonarr"
    },
    "plex": {
        "url": "http://192.168.1.80:32400",
        "api_key": "clé_api_plex"
    }
}
```

---

### 🇬🇧 Description

`arr_folder_renamer.py` is a Python script that **renames folders** for **movies (Radarr)** and **TV shows (Sonarr)** according to the configured naming format in each app. It ensures that the media files are still correctly detected after the move, and updates a **local cache** to avoid redundant processing.

It uses the following APIs:
- Radarr
- Sonarr
- Plex (optional rescan after completion)

### 🔧 How to use

```bash
python arr_folder_renamer.py
```

All behavior is controlled via `config.json` (see below).

### 📁 Example `config.json` block

```json
"arr_folder_renamer": {
    "log_file": "logs/arr_folder_renamer.log",   // Path to the log file
    "log_level": "INFO",                         // Logging level: DEBUG, INFO, etc.
    "dry_run": false,                            // true = simulate without making any change
    "run_sonarr": true,                          // true = enable TV show processing
    "run_radarr": true,                          // true = enable movie processing
    "work_limit": 200                            // Limit of shows/movies to process per run
}
```

Under the `services` section:

```json
"services": {
    "radarr": {
        "url": "http://192.168.1.60:7878",
        "api_key": "your_radarr_api_key"
    },
    "sonarr": {
        "url": "http://192.168.1.60:8989",
        "api_key": "your_sonarr_api_key"
    },
    "plex": {
        "url": "http://192.168.1.80:32400",
        "api_key": "your_plex_api_key"
    }
}
```



---

## 📜 Logs et Debug

Chaque script enregistre ses logs dans un fichier spécifique :

- `radarr_unmonitor.log`
- `sonarr_unmonitor.log`
- `radarr_cleaner.log`
- `qbittorrent_cleanup.log`
- `arr_folder_renamer.log`

Les logs incluent :
✅ Films/Séries analysés et filtrés\
✅ Actions entreprises (modifications, suppressions)\
✅ Erreurs et avertissements

---

## 📌 Conclusion

Ces scripts automatisent la gestion des médias pour Radarr, Sonarr, qBittorrent et Plex, permettant un meilleur contrôle des fichiers et de l’espace disque. 🚀



