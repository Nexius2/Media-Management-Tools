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

### 5️⃣ **Arr Folder Renamer** (`arr_folder_renamer.py`)

**Description** :
Ce script ajuste les chemins des fichiers dans **Sonarr** et **Radarr** pour inclure les identifiants IMDb et TMDB, facilitant l'intégration avec **Plex**.

**Exécution** :

```bash
python arr_folder_renamer.py
```

**Fonctionnalités** :

- Modifie les chemins des fichiers en ajoutant IMDb/TMDB
- Rafraîchit les bibliothèques dans Radarr et Sonarr
- Rafraîchit Plex après modification

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



