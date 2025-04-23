#!/usr/bin/env python3
"""
Script pour exécuter le bot Telegram et gérer les callbacks
"""
import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telegram_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire courant au chemin pour importer les modules du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importer les modules nécessaires du projet
from backend.models import init_db, get_session, CallbackData
from backend.services.myjdownloader import get_myjdownloader_service
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

class CallbackDataService:
    """Service pour gérer les données de callback dans la base de données"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_callback_data(self, callback_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer les données d'un callback depuis la base de données"""
        try:
            callback_data = self.session.query(CallbackData).filter(
                CallbackData.callback_id == callback_id
            ).first()
            
            if not callback_data:
                logger.error(f"Callback data not found for ID: {callback_id}")
                return None
            
            # Parse JSON data
            try:
                data = json.loads(callback_data.data)
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON data for callback {callback_id}: {e}")
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Database error getting callback data: {e}")
            return None

class TelegramBot:
    """Bot Telegram pour gérer les callbacks des boutons inline"""
    
    def __init__(self, token: str, chat_id: str, db_path: str = 'forum_tracker.db'):
        self.token = token
        self.chat_id = chat_id
        self.db_path = db_path
        self.session = get_session(db_path)
        self.callback_service = CallbackDataService(self.session)
        
        logger.info(f"Bot initialized with token: {token[:5]}...{token[-5:]}")
        logger.info(f"Chat ID: {chat_id}")
        logger.info(f"Database path: {db_path}")
        
    async def run(self):
        """Démarrer le bot"""
        from telegram.ext import Application, CallbackQueryHandler
        
        # Créer l'application
        application = Application.builder().token(self.token).build()
        
        # Ajouter le gestionnaire de callbacks
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Démarrer le polling
        await application.initialize()
        logger.info("Bot initialized successfully")
        
        await application.start()
        logger.info("Bot started")
        
        # Démarrer le polling en mode non-bloquant
        await application.updater.start_polling()
        logger.info("Polling started, waiting for callbacks...")
        
        # Maintenir le bot en cours d'exécution
        try:
            # Boucle infinie pour maintenir le script en vie
            while True:
                await asyncio.sleep(10)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Terminating bot...")
        finally:
            # Nettoyage
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
    
    async def handle_callback(self, update, context):
        """Gérer les callbacks des boutons inline"""
        try:
            callback_data = update.callback_query.data
            user = update.effective_user
            logger.info(f"Received callback: {callback_data} from user {user.id} ({user.first_name})")
            
            # Récupérer les données de callback depuis la base de données
            data = self.callback_service.get_callback_data(callback_data)
            
            if not data:
                logger.error(f"No data found for callback: {callback_data}")
                await update.callback_query.answer("Données non disponibles ou expirées")
                return
            
            # Traiter les données selon le type de callback
            if callback_data.startswith('quality_'):
                parts = callback_data.split('_')
                if len(parts) >= 3:
                    post_id = parts[1]
                    quality_index = int(parts[2])
                    
                    logger.info(f"Processing quality callback for post {post_id}, quality index {quality_index}")
                    
                    # Extraire les liens pour cette qualité
                    if 'video_qualities' in data and len(data['video_qualities']) > quality_index:
                        quality = data['video_qualities'][quality_index]
                        
                        # Afficher dans les logs
                        logger.info(f"Quality {quality['quality_name']} clicked for post {post_id}")

                        # Préparer le nom du package
                        package_name = f"{data.get('performer', 'Unknown')} - Post {post_id} - {quality['quality_name']}"

                        # Collecter tous les liens
                        all_links = []
                        for provider, links in quality['provider_links'].items():
                            for link in links:
                                logger.info(f"Link: {link}")
                                all_links.append(link)

                        # Si nous avons des liens, les envoyer à MyJDownloader
                        if all_links:
                            myjd_service = get_myjdownloader_service()
                            result = myjd_service.send_links_to_jdownloader(
                                links=all_links,
                                package_name=package_name,
                                method="round-robin",
                                callback_id=callback_data  # Passer l'ID du callback pour assurer la cohérence
    )
                            
                            if result["success"]:
                                logger.info(f"All links sent to MyJDownloader successfully")
                                devices_used = ", ".join(result["devices_used"].keys())
                                await update.callback_query.answer(f"Liens envoyés à JDownloader: {devices_used}")
                            else:
                                logger.error(f"Error sending links to MyJDownloader: {result}")
                                if result["device_errors"]:
                                    error_msg = "Erreur d'envoi vers certains appareils"
                                else:
                                    error_msg = "Erreur d'envoi vers MyJDownloader"
                                await update.callback_query.answer(error_msg)
                        else:
                            logger.warning(f"No links found for quality {quality['quality_name']}")
                            await update.callback_query.answer("Aucun lien trouvé pour cette qualité")
                        
                        return
                    else:
                        logger.error(f"Video quality index {quality_index} not found in data")
                        await update.callback_query.answer("Qualité non trouvée")
                        return
            
            # Réponse par défaut
            logger.warning(f"Unrecognized callback format: {callback_data}")
            await update.callback_query.answer("Action non reconnue")
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}", exc_info=True)
            await update.callback_query.answer("Erreur lors du traitement")

async def main():
    """Fonction principale"""
    # Récupérer les variables d'environnement
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    db_path = os.environ.get('DB_PATH', 'forum_tracker.db')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        sys.exit(1)
    
    if not chat_id:
        logger.error("TELEGRAM_CHAT_ID not set in environment")
        sys.exit(1)
    
    # Créer et exécuter le bot
    bot = TelegramBot(token, chat_id, db_path)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())