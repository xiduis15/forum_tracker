# Forum Performer Tracker

Une application qui surveille les forums pour suivre les nouvelles publications concernant des performers spécifiques et envoie des notifications.

## Fonctionnalités

- Gestion des performers (ajout, suppression, activation/désactivation)
- Suivi de threads de forum pour chaque performer
- Vérification automatique des nouveaux posts à intervalles réguliers
- Extraction des liens de téléchargement et des images des posts
- Interface web simple pour gérer l'application
- Support actuel pour le forum PlanetSuzy (extensible à d'autres forums)

## Installation

### Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. Clonez le dépôt :
   ```
   git clone <repo_url>
   cd forum-tracker
   ```

2. Créez un environnement virtuel et activez-le :
   ```
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

4. Copiez le fichier HTML d'exemple dans le répertoire de test (pour le test de scraping) :
   ```
   mkdir -p backend/test_data
   cp example-forum.html backend/test_data/
   ```

## Utilisation

### Démarrer l'application

```
python -m backend.app
```

L'application sera accessible à l'adresse `http://localhost:5000`.

### Interface Web

L'interface web permet de :

1. Gérer les performers (ajouter, supprimer, activer/désactiver)
2. Ajouter des URLs de forum à suivre pour chaque performer
3. Tester le scraper avec un exemple HTML
4. Vérifier manuellement les nouveaux posts

### Configuration

Vous pouvez configurer l'application en définissant des variables d'environnement :

- `FLASK_ENV` : Environnement Flask (`development`, `production`, `testing`)
- `DB_PATH` : Chemin vers le fichier de base de données SQLite
- `CHECK_INTERVAL_SECONDS` : Intervalle de vérification (en secondes) pour le planificateur

## Architecture

L'application est composée de :

- **Backend (Python/Flask)** :
  - API REST
  - Base de données SQLite
  - Système de scraping avec BeautifulSoup
  - Planificateur de tâches (APScheduler)

- **Frontend (HTML/CSS/JS)** :
  - Interface utilisateur simple avec Bootstrap
  - Communication avec l'API via fetch

## Développement et extension

### Ajouter un nouveau type de forum

Pour ajouter le support d'un nouveau forum :

1. Créez une nouvelle classe de scraper dans `backend/scrapers/` qui hérite de `BaseScraper`
2. Implémentez les méthodes abstraites (`extract_posts`, `get_next_page_url`, `get_forum_type`)
3. Ajoutez votre nouveau scraper dans la fonction `get_scraper` du fichier `backend/scrapers/__init__.py`
4. Ajoutez la détection du nouveau forum dans la fonction `detect_forum_type`

### Implémentation future

- Notification Telegram
- Téléchargement automatique des liens détectés
- Interface utilisateur améliorée
- Support pour plus de forums

## Licence

Ce projet est sous licence MIT.
