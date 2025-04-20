"""
Service de notification pour envoyer des alertes via Telegram.
"""

import logging
import time
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .telegram_utils import get_telegram_helper

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications about new posts"""
    
    def __init__(self):
        """Initialize the notification service"""
        self.telegram_enabled = False
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Check if Telegram is configured
        if self.telegram_token and self.telegram_chat_id:
            self.telegram_helper = get_telegram_helper()
            self.telegram_enabled = self.telegram_helper.initialized
            if self.telegram_enabled:
                logger.info("Telegram notifications enabled")
            else:
                logger.warning("Telegram helper initialization failed")
        else:
            logger.info("Telegram not configured. Notifications will only be logged.")
    
    def send_notification(self, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a notification
        
        Args:
            title: Title of the notification
            message: Message text
            data: Additional data to include
            
        Returns:
            True if notification was sent, False otherwise
        """
        # Log the notification
        logger.info(f"NOTIFICATION: {title} - {message}")
        if data:
            logger.info(f"DATA: {json.dumps(data, indent=2, default=str)}")
        
        # Pour le moment, on simule l'envoi en loggant tous les détails
        logger.info("=== TELEGRAM MESSAGE CONTENT ===")
        logger.info(f"Title: {title}")
        logger.info(f"Message: {message}")
        logger.info("=== END TELEGRAM MESSAGE ===")
        
        # Send via Telegram if enabled
        if self.telegram_enabled:
            try:
                # Pour activer l'envoi réel vers Telegram, décommentez cette ligne :
                logger.info("=== TELEGRAM MESSAGE SENT ===")
                return self.telegram_helper.send_message(f"*{title}*\n\n{message}")

            except Exception as e:
                logger.error(f"Error sending Telegram notification: {e}")
                return False
        
        return True
    
    def format_post_for_telegram(self, post: Dict[str, Any]) -> str:
        """
        Format a post for Telegram notification
        
        Args:
            post: Post data
            
        Returns:
            Formatted message
        """
        lines = []
        
        # Add post info
        #lines.append(f"📝 *Post #{post.get('post_id')}*")
        
        # Add date if available
        if post.get('date'):
            try:
                date_str = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%d/%m/%y %H:%M')
                lines.append(f"📝 *#{post.get('post_id')}* 🕒 {date_str}")
            except (ValueError, TypeError):
                # If date parsing fails, use raw date string
                lines.append(f"📝 *#{post.get('post_id')}* 🕒 {post.get('date')}")
        
        # Add content snippet if available
        if post.get('content'):
            content = post['content']
            # Limit content to 200 chars and escape markdown
            content = content.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')[:200]
            if len(post['content']) > 200:
                content += "..."
            #lines.append(f"\n{content}\n") ## pour l'instant on ne l'ajoute pas pour ne faire des trop long message
        
        # Si nous avons des qualités vidéo, les afficher structurées par qualité et fournisseur
        if post.get('video_qualities') and len(post['video_qualities']) > 0:
            lines.append(f"📥 *Liens de téléchargement:*")
            
            for quality in post['video_qualities']:
                quality_name = quality.get('quality_name', 'Unknown')
                quality_desc = quality.get('description', '')
                
                # Afficher l'en-tête de la section qualité
                if quality_desc and quality_desc != quality_name:
                    lines.append(f"\n🎬 *Section {quality_name}* - _{quality_desc}_")
                else:
                    lines.append(f"\n🎬 *Section {quality_name}*")
                
                # Afficher les liens par fournisseur
                provider_links = quality.get('provider_links', {})
                for provider, links in provider_links.items():
                    if links:
                        # Emoji correspondant au fournisseur
                        emoji = "🔗"
                        if "k2s" in provider.lower():
                            emoji = "💾"
                        elif "filejoker" in provider.lower():
                            emoji = "📁"
                        elif "rapidgator" in provider.lower():
                            emoji = "⚡"
                        
                        lines.append(f"{emoji} *{provider.capitalize()}*:")
                        
                        # Si plusieurs liens du même fournisseur, c'est probablement découpé en plusieurs parties
                        if len(links) > 1:
                            has_part_indicator = any("part" in link.lower() for link in links)
                            
                            for i, link in enumerate(links):
                                # Si les liens contiennent explicitement "part", on n'ajoute pas notre propre indicateur
                                if has_part_indicator:
                                    lines.append(f"  • {link}")
                                else:
                                    lines.append(f"  • Partie {i+1}: {link}")
                        else:
                            # Un seul lien pour ce fournisseur
                            lines.append(f"  • {links[0]}")
        
        # Si nous n'avons pas de qualités vidéo mais des liens, utiliser l'ancien format
        elif post.get('download_links') and len(post['download_links']) > 0:
            lines.append(f"📥 *{len(post['download_links'])} liens de téléchargement:*")
            for link in post['download_links'][:5]:  # Limit to 5 links
                lines.append(f"• {link}")
            
            if len(post['download_links']) > 5:
                lines.append(f"_...et {len(post['download_links']) - 5} autres liens_")
        
        # Add image count if available ## pas nécessaire à voir pour supprimer
        #if post.get('images') and len(post['images']) > 0:
        #    lines.append(f"🖼 *{len(post['images'])} images disponibles*")
        
        return "\n".join(lines)
    
    def get_original_url(self, thumbs_url: str) -> str:
        """
        Extrait l'URL originale à partir d'une URL miniature.
        Supporte PixHost, ImgBox, ImageTwist et autres hébergeurs d'images.
        
        Args:
            thumbs_url: URL de l'image miniature
            
        Returns:
            original_url
        """
        # Pour PixHost
        if "pixhost.to" in thumbs_url:
            if "/thumbs/" in thumbs_url and (thumbs_url.startswith("https://t") or thumbs_url.startswith("http://t")):
                # Remplacer le préfixe 't' par 'img' dans le sous-domaine
                original_url = thumbs_url.replace("://t", "://img")
                # Remplacer '/thumbs/' par '/images/'
                original_url = original_url.replace("/thumbs/", "/images/")
                return original_url
        
        # Pour ImgBox
        elif "imgbox.com" in thumbs_url:
            # Format: https://thumbs2.imgbox.com/10/0d/b7fkGbtw_t.jpg
            # à convertir en: https://images2.imgbox.com/10/0d/b7fkGbtw_o.jpg
            if "thumbs" in thumbs_url and "_t." in thumbs_url:
                original_url = thumbs_url.replace("thumbs", "images").replace("_t.", "_o.")
                return original_url
        
        # Pour ImageTwist
        elif "imagetwist.com" in thumbs_url:
            if "/th/" in thumbs_url:
                # Format: https://img202.imagetwist.com/th/65814/3rmz76notde7.jpg
                # Convertir en: https://img202.imagetwist.com/i/65814/3rmz76notde7.jpg
                original_url = thumbs_url.replace("/th/", "/i/")
                return original_url
        
        # Si aucun format reconnu ou pas une URL miniature, renvoyer l'URL d'origine
        return thumbs_url
    
    def notify_new_posts(self, performer_name: str, thread_url: str, posts: List[Dict[str, Any]]) -> bool:
        """
        Send a notification about new posts
        
        Args:
            performer_name: Name of the performer
            thread_url: URL of the thread
            posts: List of new posts
            
        Returns:
            True if notification was sent, False otherwise
        """
        if not posts:
            return False
        
        download_links = []
        image_links = []

        # pour chaque post on construit un nouveau message
        for i, post in enumerate(posts):
            # Create main notification
            title = f"{performer_name} {i+1}/{len(posts)}"
            #message = f"[Voir le thread]({thread_url})\n" pas forcément nécessaire et rajoute un apercu dans le message pas pratique    
            # Format post details
            message = self.format_post_for_telegram(post)

        # Collect all download links for additional data
            if post.get('download_links'):
                download_links.extend(post['download_links'])

        # Collect all image links for additional data
            if post.get('images'):
                image_links.extend(post['images'])

            # Send notification
            result = self.send_notification(title, message, {
                'performer': performer_name,
                'thread_url': thread_url,
                'post_count': len(posts),
                'download_links': download_links,
                'images_links': image_links,
                'id': post.get('post_id')
            })
        
            # Pour les posts avec des images, on les envoie en groupe
            if self.telegram_enabled:
                if post.get('images') and len(post['images']) > 0:
                    image_urls = post.get('images', [])
                    if image_urls:
                        # Limiter à 10 images par groupe (limite de l'API Telegram)
                        image_batch = image_urls[:10]
                        
                        # Préparer le groupe de médias
                        media_group = []
                        
                        # Collecter les URLs des images originales
                        original_urls = []
                        
                        for image_url in image_batch:
                            print("image_url", image_url)
                            orig_url = self.get_original_url(image_url)
                            original_urls.append(orig_url)
                        
                        # Créer le message avec les liens vers les originaux
                        # Utiliser HTML au lieu de Markdown pour plus de fiabilité avec les URLs
                        from telegram.constants import ParseMode
                        caption = f"Images du post #{post.get('post_id')}\n"
                        #caption += "🔍 <b>Cliquez sur les liens ci-dessous pour voir les images en taille originale:</b>\n"
                        
                        # On ajoute des liens numérotés pour chaque image
                        for i, url in enumerate(original_urls):
                            caption += f"<a href=\"{url}\">Image {i+1}</a>  "
                        
                        # Ajouter chaque image au groupe
                        for i, image_url in enumerate(image_batch):
                            # Pour la première image, ajouter la légende avec les liens
                            caption_to_use = None
                            if i == 0:
                                caption_to_use = caption
                            
                            media_group.append({
                                'type': 'photo',
                                'media': image_url,
                                'caption': caption_to_use,
                                'parse_mode': ParseMode.HTML  # Utiliser HTML au lieu de Markdown
                            })
                        
                        # Envoyer le groupe de médias
                        if media_group:
                            logger.info(f"Sending media group with {len(media_group)} images for post #{post.get('post_id')}")
                            self.telegram_helper.send_media_group(media_group)
                            
                        # Si plus de 10 images, envoyer un message à ce sujet
                        if len(image_urls) > 10:
                            additional_msg = f"_...et {len(image_urls) - 10} autres images du post #{post.get('post_id')}_"
                            self.telegram_helper.send_message(additional_msg)
                time.sleep(5)
        
        return result 

# Singleton instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """Get the notification service instance"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service