# 📌 Media Management Tools (MMT) - README

## 🚀 Description
**Media Management Tools (MMT)** est un ensemble d'outils permettant d'automatiser la gestion des bibliothèques **Radarr** et **Sonarr**. Il inclut des scripts qui désactivent automatiquement le monitoring des films et des épisodes selon des critères prédéfinis.

## 📂 Installation
### 1️⃣ Prérequis
- **Python 3.x** installé
- **Radarr et/ou Sonarr** configurés et fonctionnels
- **API Keys Radarr et Sonarr** récupérées
- **Fichier de configuration `config.json`** bien rempli

### 2️⃣ Installation des dépendances
```bash
pip install requests
```

## ⚙️ Configuration
Le fichier `config.json` contient tous les paramètres nécessaires au bon fonctionnement des scripts.

### Exemple de configuration :
```json
{
  "services": {
    "radarr": {
      "url": "http://localhost:7878",
      "api_key": "VOTRE_API_KEY"
    },
    "sonarr": {
      "url": "http://localhost:8989",
      "api_key": "VOTRE_API_KEY"
    }
  },
  "radarr_unmonitor": {
    "log_file": "radarr_unmonitor.log",
    "log_level": "INFO",
    "dry_run": true,
    "search_terms": [
      ["4K", "FR", "MULTI"],
      ["1080", "FR", "MULTI"],
      ["EN", "FR", "1080"],
      ["EN", "FR", "4K"]
    ]
  },
  "sonarr_unmonitor": {
    "log_file": "sonarr_unmonitor.log",
    "log_level": "INFO",
    "dry_run": true,
    "search_terms": [
      ["4K", "FR", "MULTI"],
      ["1080", "FR", "MULTI"]
    ]
  }
}
```

---

# 🛠 Outils disponibles

## 🎬 Radarr Unmonitor

### 🔹 Description
Ce script automatise la gestion des films dans **Radarr** en désactivant le monitoring des films correspondant à des critères définis dans `config.json`.

### 🔧 Utilisation
```bash
python radarr_unmonitor.py
```

### Mode Simulation (DRY_RUN)
Si `dry_run` est activé dans `config.json`, le script affichera uniquement les films qui **auraient été désactivés**, sans modifier Radarr.

### Mode Exécution réelle
Pour désactiver réellement les films, modifiez `dry_run` en `false` dans `config.json` :
```json
"dry_run": false
```
Puis relancez le script :
```bash
python radarr_unmonitor.py
```

### 📜 Logs et Debug
Les logs sont enregistrés dans `radarr_unmonitor.log` et incluent :
- **Nombre de films récupérés et filtrés**
- **Films analysés et détectés**
- **Films mis à jour avec succès** ou **erreurs rencontrées**

---

## 📺 Sonarr Unmonitor

### 🔹 Description
Ce script permet de **désactiver le monitoring des épisodes dans Sonarr** en fonction des critères définis dans `config.json`.

### 🔧 Utilisation
```bash
python sonarr_unmonitor.py
```

### Mode Simulation (DRY_RUN)
Si `dry_run` est activé dans `config.json`, le script affichera uniquement les épisodes qui **auraient été désactivés**, sans modifier Sonarr.

### Mode Exécution réelle
Pour désactiver réellement les épisodes, modifiez `dry_run` en `false` dans `config.json` :
```json
"dry_run": false
```
Puis relancez le script :
```bash
python sonarr_unmonitor.py
```

### 📜 Logs et Debug
Les logs sont enregistrés dans `sonarr_unmonitor.log` et incluent :
- **Nombre d'épisodes récupérés et filtrés**
- **Épisodes analysés et détectés**
- **Épisodes mis à jour avec succès** ou **erreurs rencontrées**

---

## 📝 Notes
- Assurez-vous que **Radarr et Sonarr** sont accessibles depuis le script.
- Vérifiez les **clés API** dans `config.json`.
- En cas d'erreur `202 Accepted`, Sonarr ou Radarr peuvent prendre quelques secondes à traiter la modification.

## 🎯 Exemples de Logs
**Film détecté et désactivé dans Radarr :**
```
2025-02-18 14:05:01 - INFO - 🛠️ Traitement du film 'Avatar' (2009, ID: 123)...
2025-02-18 14:05:02 - INFO - ✅ Film 'Avatar' (2009, ID: 123) marqué comme NON MONITORÉ avec succès.
```

**Épisode détecté et désactivé dans Sonarr :**
```
2025-02-18 14:10:01 - INFO - 🛠️ Traitement de l'épisode 'The Mandalorian' (S02E05, ID: 456)...
2025-02-18 14:10:02 - INFO - ✅ Épisode 'The Mandalorian' (S02E05, ID: 456) marqué comme NON MONITORÉ avec succès.
```

## 📌 Conclusion
**Media Management Tools (MMT)** est un package d'outils conçu pour **automatiser la gestion des films et des séries** dans Radarr et Sonarr. 🚀

D'autres outils viendront s'ajouter à cette collection. Restez à l'écoute !

