#!/usr/bin/env python3
"""
Script de démarrage pour l'application Forum Performer Tracker.
Ceci est un point d'entrée pratique pour le développement.
"""

import os
import argparse
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env si présent
load_dotenv()

def main():
    """Fonction principale pour démarrer l'application"""
    parser = argparse.ArgumentParser(description="Démarrer l'application Forum Performer Tracker")
    parser.add_argument('--host', default='127.0.0.1', help='Adresse IP du serveur')
    parser.add_argument('--port', type=int, default=5000, help='Port du serveur')
    parser.add_argument('--debug', action='store_true', help='Activer le mode debug')
    
    args = parser.parse_args()
    
    # Définir les variables d'environnement si non définies
    if args.debug and 'FLASK_DEBUG' not in os.environ:
        os.environ['FLASK_DEBUG'] = '1'
        
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
    
    # Importer et démarrer l'application
    from backend.app import create_app
    app = create_app()
    
    # Démarrer le serveur
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
