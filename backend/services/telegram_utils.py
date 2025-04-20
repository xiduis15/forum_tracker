"""
Utilitaires pour l'envoi de messages Telegram
"""

import os
import logging
import asyncio
from typing import Optional, Union, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramHelper:
    """Helper class for sending Telegram messages"""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize the Telegram helper
        
        Args:
            token: Bot token (if None, will use TELEGRAM_BOT_TOKEN from env)
            chat_id: Chat ID (if None, will use TELEGRAM_CHAT_ID from env)
        """
        self.token = token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
        self.bot = None
        self.initialized = False
        
        if not self.token or not self.chat_id:
            logger.warning("TelegramHelper not fully configured: missing token or chat_id")
            return
        
        try:
            # N'importez pas tout de suite le bot pour éviter d'initialiser les connexions
            # Import for telegram-bot v20+
            from telegram.constants import ParseMode
            self.parse_mode = ParseMode.HTML
            self.initialized = True
        except ImportError:
            logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot==20.7")
    
    def _get_bot(self):
        """Crée une nouvelle instance de Bot à chaque appel"""
        from telegram import Bot
        return Bot(token=self.token)
    
    async def send_message_async(self, text: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send a text message (async version)
        
        Args:
            text: Message text
            parse_mode: Parse mode (None=default, 'Markdown', 'HTML')
            
        Returns:
            True if message was sent, False otherwise
        """
        if not self.initialized:
            logger.error("TelegramHelper not initialized")
            return False
        
        try:
            parse_mode_val = parse_mode or self.parse_mode
            bot = self._get_bot()  # Nouvelle instance à chaque fois
            logger.info(f"Avant la fonction send_message Message to send to chat_id {self.chat_id}: {text}")
            await bot.send_message(chat_id=self.chat_id, text=text, parse_mode=parse_mode_val, disable_web_page_preview=True)
            logger.info(f"Apres la fonction send_message Message sent to chat_id {self.chat_id}")  
            #await bot.close()  # Fermeture explicite du bot et de ses connexions
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_photo_async(self, photo: Union[str, Path], caption: Optional[str] = None) -> bool:
        """
        Send a photo (async version)
        
        Args:
            photo: Photo URL or path
            caption: Optional caption
            
        Returns:
            True if photo was sent, False otherwise
        """
        if not self.initialized:
            logger.error("TelegramHelper not initialized")
            return False
        
        try:
            bot = self._get_bot()  # Nouvelle instance à chaque fois
            await bot.send_photo(chat_id=self.chat_id, photo=photo, caption=caption)
            #await bot.close()  # Fermeture explicite du bot et de ses connexions
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram photo: {e}")
            return False
    
    async def send_media_group_async(self, media: List[Dict[str, Any]]) -> bool:
        """
        Send a media group (multiple photos/videos) (async version)
        
        Args:
            media: List of media objects (compatible with telegram.InputMediaPhoto)
            
        Returns:
            True if media group was sent, False otherwise
        """
        if not self.initialized:
            logger.error("TelegramHelper not initialized")
            return False
        
        try:
            from telegram import InputMediaPhoto
            
            # Convert simple media objects to InputMediaPhoto objects
            input_media = []
            for item in media:
                if isinstance(item, dict):
                    # Si c'est un dict, convertir en InputMediaPhoto
                    media_type = item.get('type', 'photo')
                    if media_type == 'photo':
                        # Extraire les paramètres pertinents
                        media_obj = item['media']
                        caption = item.get('caption')
                        parse_mode = item.get('parse_mode', self.parse_mode if caption else None)
                        
                        input_media.append(InputMediaPhoto(
                            media=media_obj,
                            caption=caption,
                            parse_mode=parse_mode
                        ))
                else:
                    # Si c'est déjà un InputMediaPhoto, l'ajouter directement
                    input_media.append(item)
            
            if not input_media:
                logger.error("No valid media items to send")
                return False
                
            bot = self._get_bot()
            await bot.send_media_group(chat_id=self.chat_id, media=input_media)
            logger.info(f"Media group sent to chat_id {self.chat_id} with {len(input_media)} items")
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram media group: {e}")
            return False
    
    def send_message(self, text: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send a text message (sync wrapper)
        
        Args:
            text: Message text
            parse_mode: Parse mode (None=default, 'Markdown', 'HTML')
            
        Returns:
            True if message was sent, False otherwise
        """
        # Créer une nouvelle boucle asyncio à chaque fois
        try:
            # Vérifier si nous sommes dans une boucle asyncio existante
            try:
                loop = asyncio.get_running_loop()
                logger.info(f"Running loop: {loop}")
                # Si nous pouvons obtenir la boucle sans erreur, nous sommes dans une coroutine
                if loop.is_running():
                    # Créer une future pour éviter les deadlocks
                    future = asyncio.run_coroutine_threadsafe(
                        self.send_message_async(text, parse_mode), loop
                    )
                    return future.result(timeout=30)  # Timeout de 30 secondes
            except RuntimeError:
                # Pas de boucle en cours, nous pouvons utiliser asyncio.run()
                return asyncio.run(self.send_message_async(text, parse_mode))
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False
    
    def send_photo(self, photo: Union[str, Path], caption: Optional[str] = None) -> bool:
        """
        Send a photo (sync wrapper)
        
        Args:
            photo: Photo URL or path
            caption: Optional caption
            
        Returns:
            True if photo was sent, False otherwise
        """
        # Même approche que pour send_message
        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.send_photo_async(photo, caption), loop
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(self.send_photo_async(photo, caption))
        except Exception as e:
            logger.error(f"Error in send_photo: {e}")
            return False
    
    def send_media_group(self, media: List[Dict[str, Any]]) -> bool:
        """
        Send a media group (multiple photos/videos) (sync wrapper)
        
        Args:
            media: List of media objects (compatible with telegram.InputMediaPhoto)
            
        Returns:
            True if media group was sent, False otherwise
        """
        try:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.send_media_group_async(media), loop
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(self.send_media_group_async(media))
        except Exception as e:
            logger.error(f"Error in send_media_group: {e}")
            return False
    
    def send_batch(self, messages: List[str], photos: Optional[List[str]] = None) -> bool:
        """
        Send a batch of messages and photos
        
        Args:
            messages: List of message texts
            photos: Optional list of photo URLs
            
        Returns:
            True if all messages were sent, False otherwise
        """
        success = True
        
        # Envoyer les messages un par un
        for msg in messages:
            if not self.send_message(msg):
                success = False
        
        # Envoyer les photos une par une
        if photos:
            for photo in photos:
                if not self.send_photo(photo):
                    success = False
        
        return success


# Singleton instance
_telegram_helper = None

def get_telegram_helper() -> TelegramHelper:
    """Get the TelegramHelper singleton instance"""
    global _telegram_helper
    if _telegram_helper is None:
        _telegram_helper = TelegramHelper()
    return _telegram_helper