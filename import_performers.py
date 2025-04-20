#!/usr/bin/env python3
"""
Script pour importer les performers depuis un fichier JSON
"""

import json
import argparse
import sys
from backend.models import init_db, Performer, Thread
from backend.scrapers import detect_forum_type

def import_performers(json_file, db_path):
    """
    Importe les performers depuis un fichier JSON
    
    Format JSON attendu:
    [
        {
            "name": "Nom du performer",
            "active": true/false,
            "url_psuzy": "http://url-du-thread" (optionnel)
        },
        ...
    ]
    """
    print(f"Importation des performers depuis {json_file} vers {db_path}")
    
    # Charger le fichier JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            performers_data = json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier JSON: {e}")
        return False
    
    # Initialiser la base de données
    session = init_db(db_path)
    
    # Compteurs pour le rapport
    performers_added = 0
    performers_skipped = 0
    threads_added = 0
    
    # Parcourir les performers
    for performer_data in performers_data:
        name = performer_data.get('name')
        is_active = performer_data.get('active', False)
        
        if not name:
            print("ERREUR: Un performer sans nom a été trouvé, ignoré.")
            performers_skipped += 1
            continue
        
        # Vérifier si le performer existe déjà
        existing_performer = session.query(Performer).filter(Performer.name == name).first()
        
        if existing_performer:
            print(f"Le performer '{name}' existe déjà, mise à jour des informations...")
            existing_performer.is_active = is_active
            performer = existing_performer
            performers_skipped += 1
        else:
            # Créer le nouveau performer
            performer = Performer(name=name, is_active=is_active)
            session.add(performer)
            performers_added += 1
            print(f"Performer '{name}' ajouté.")
        
        # Commit pour obtenir l'ID du performer
        session.commit()
        
        # Ajouter les URLs de thread si présentes
        urls = []
        
        # PlanetSuzy URL
        if 'url_psuzy' in performer_data and performer_data['url_psuzy']:
            urls.append(('planetsuzy', performer_data['url_psuzy']))
        
        # Ajouter d'autres types d'URL ici si nécessaire
        
        # Ajouter les threads
        for forum_type, url in urls:
            # Vérifier si le thread existe déjà
            existing_thread = session.query(Thread).filter(
                Thread.performer_id == performer.id, 
                Thread.url == url
            ).first()
            
            if existing_thread:
                print(f"  Thread '{url}' existe déjà pour '{name}'")
                continue
            
            # Créer le nouveau thread
            thread = Thread(
                performer_id=performer.id,
                url=url,
                forum_type=forum_type
            )
            session.add(thread)
            threads_added += 1
            print(f"  Thread '{url}' ajouté pour '{name}'")
    
    # Commit final
    session.commit()
    
    # Afficher le rapport
    print("\nRapport d'importation:")
    print(f"- Performers ajoutés: {performers_added}")
    print(f"- Performers mis à jour/ignorés: {performers_skipped}")
    print(f"- Threads ajoutés: {threads_added}")
    print(f"- Total performers traités: {performers_added + performers_skipped}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Importer des performers depuis un fichier JSON")
    parser.add_argument('json_file', help='Chemin vers le fichier JSON')
    parser.add_argument('--db-path', default='forum_tracker.db', help='Chemin vers la base de données')
    
    args = parser.parse_args()
    
    success = import_performers(args.json_file, args.db_path)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()