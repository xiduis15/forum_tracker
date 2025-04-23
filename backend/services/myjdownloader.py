"""
Service pour envoyer des liens vers MyJDownloader
"""
import os
import random
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from myjdapi import myjdapi

logger = logging.getLogger(__name__)

class MyJDownloaderService:
    """Service pour envoyer des liens vers MyJDownloader en utilisant myjdapi"""
    
    def __init__(self):
        """Initialiser le service MyJDownloader"""
        self.email = os.environ.get('MYJDOWNLOADER_EMAIL')
        self.password = os.environ.get('MYJDOWNLOADER_PASSWORD')
        self.app_key = os.environ.get('MYJDOWNLOADER_APP_KEY', 'forum_tracker')
        
        # Récupérer la liste des appareils depuis la configuration
        devices_str = os.environ.get('MYJDOWNLOADER_DEVICES', '')
        self.devices = [d.strip() for d in devices_str.split(',') if d.strip()]
        
        # Récupérer la liste des appareils spécifiques pour filejoker
        filejoker_devices_str = os.environ.get('MYJDOWNLOADER_FILEJOKER_DEVICES', '')
        self.filejoker_devices = [d.strip() for d in filejoker_devices_str.split(',') if d.strip()]
        
        # Récupérer le dossier de destination
        self.download_folder = os.environ.get('MYJDOWNLOADER_DOWNLOAD_FOLDER', '/opt/JDownloader/Downloads')
        
        # Vérifier la configuration
        if not self.email or not self.password:
            logger.warning("Informations d'identification MyJDownloader manquantes")
        elif not self.devices:
            logger.warning("Aucun appareil MyJDownloader configuré")
        else:
            logger.info(f"MyJDownloader configuré avec {len(self.devices)} appareils: {', '.join(self.devices)}")
            logger.info(f"Appareils filejoker: {', '.join(self.filejoker_devices)}")
        
        # Client myjdapi
        self.jd = None
        self.last_connect_time = 0
        self.available_devices = []
        
        # Gestion des index pour le round-robin
        self.current_device_index = 0
        self.current_filejoker_index = 0
        
        # Stockage du dernier appareil utilisé par callback_id
        self.last_used_devices = {}
    
    def is_link_filejoker(self, link: str) -> bool:
        """Vérifier si un lien est un lien filejoker"""
        parsed = urlparse(link)
        return 'filejoker.net' in parsed.netloc
    
    def connect(self) -> bool:
        """
        Se connecter à MyJDownloader
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        # Si déjà connecté récemment, ne pas se reconnecter
        current_time = time.time()
        if self.jd and (current_time - self.last_connect_time) < 900:  # 15 minutes
            return True
        
        if not self.email or not self.password:
            logger.error("Email ou mot de passe manquant pour MyJDownloader")
            return False
        
        try:
            # Créer une nouvelle instance
            self.jd = myjdapi.Myjdapi()
            logger.info(f"Tentative de connexion à MyJDownloader avec l'email: {self.email}")
            
            # Définir la clé d'application
            self.jd.set_app_key(self.app_key)
            
            # Se connecter
            self.jd.connect(self.email, self.password)
            logger.info("Connexion à MyJDownloader réussie")
            
            # Mettre à jour la liste des appareils
            self.jd.update_devices()
            
            # Récupérer les appareils disponibles
            #self.available_devices = self.jd.list_devices()
            #logger.info(f"Appareils disponibles: {', '.join(self.available_devices)}")
            mydevices = self.jd.list_devices()
            logger.info(f"Appareils disponibles ({len(mydevices)}):")
            for device_name in mydevices:
                logger.info(f"  - {device_name['name']}")
                self.available_devices.append(device_name['name'])

            
            # Vérifier si des appareils configurés sont disponibles
            configured_available = [d for d in self.devices if d in self.available_devices]
            if not configured_available:
                logger.warning(f"Aucun appareil configuré n'est disponible. Appareils disponibles: {', '.join(self.available_devices)}")
            else:
                logger.info(f"Appareils configurés disponibles: {', '.join(configured_available)}")
            
            # Marquer le temps de la dernière connexion
            self.last_connect_time = current_time
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à MyJDownloader: {str(e)}")
            self.jd = None
            return False
    
    def get_next_device(self, is_filejoker: bool = False, callback_id: Optional[str] = None) -> Optional[str]:
        """
        Obtenir le prochain appareil à utiliser (round-robin)
        
        Args:
            is_filejoker: Si le lien est un lien filejoker
            callback_id: ID du callback pour assurer la cohérence
            
        Returns:
            Nom de l'appareil à utiliser ou None si aucun appareil n'est disponible
        """
        # Se connecter si nécessaire
        if not self.connect():
            return None
        
        # Si un callback_id est fourni, vérifier s'il a déjà un appareil assigné
        if callback_id and callback_id in self.last_used_devices:
            device_name = self.last_used_devices[callback_id]
            # Vérifier que l'appareil est toujours disponible
            if device_name in self.available_devices:
                # Vérifier que l'appareil est approprié pour filejoker si nécessaire
                if not is_filejoker or device_name in self.filejoker_devices:
                    return device_name
        
        # Si c'est un lien filejoker, on n'utilise que les appareils filejoker
        configured_devices = self.filejoker_devices if is_filejoker else self.devices
        
        # Filtrer les appareils qui sont réellement disponibles
        available_devices = [d for d in configured_devices if d in self.available_devices]
        
        if not available_devices:
            logger.warning(f"Aucun appareil {'filejoker' if is_filejoker else 'normal'} n'est disponible")
            return None
        
        # Méthode round-robin selon le type
        if is_filejoker:
            device = available_devices[self.current_filejoker_index % len(available_devices)]
            self.current_filejoker_index += 1
        else:
            device = available_devices[self.current_device_index % len(available_devices)]
            self.current_device_index += 1
        
        # Si un callback_id est fourni, stocker l'appareil utilisé
        if callback_id:
            self.last_used_devices[callback_id] = device
            
            # Limiter la taille du cache des appareils
            if len(self.last_used_devices) > 100:  # Limiter à 100 entrées
                # Supprimer les entrées les plus anciennes
                self.last_used_devices = dict(list(self.last_used_devices.items())[-100:])
        
        return device
    
    def add_links(self, device_name: str, links: List[str], package_name: str) -> tuple[bool, Optional[str]]:
        """
        Ajouter des liens à un appareil JDownloader
        
        Args:
            device_name: Nom de l'appareil
            links: Liste des liens à ajouter
            package_name: Nom du package
            
        Returns:
            Tuple (success, error)
        """
        # Se connecter si nécessaire
        if not self.connect():
            return False, "Non connecté à MyJDownloader"
        
        if device_name not in self.available_devices:
            return False, f"Appareil {device_name} non disponible"
        
        try:
            # Obtenir l'appareil
            device = self.jd.get_device(device_name)
            
            # Ajouter les liens
            links_text = links[0] if len(links) == 1 else "\n".join(links)
            logger.info(f"Ajout de {len(links)} liens à {device_name} dans le package '{package_name}'")
            
            # Configurer les paramètres du package
            params = [{
                "links": links_text,
                "packageName": package_name,
                "destinationFolder": self.download_folder,
                "overwritePackagizerRules": True,
                "autoExtract": True,
                "autostart": True
            }]
            
            # Ajouter les liens au linkgrabber
            try:
                result = device.linkgrabber.add_links(params)
                logger.info(f"Liens ajoutés avec succès à {device_name}: {result}")
                return True, None
            except myjdapi.exception.MYJDConnectionException as e:
                error_msg = f"Erreur de connexion lors de l'ajout de liens à {device_name}: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
            
        except myjdapi.exception.MYJDDeviceNotFoundException as e:
            error_msg = f"Appareil {device_name} non trouvé: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Exception lors de l'ajout de liens à {device_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_links_to_jdownloader(self, links: List[str], 
                             package_name: str = "Download Package",
                             method: str = "round-robin",
                             callback_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Envoyer des liens vers JDownloader
        
        Args:
            links: Liste des liens à envoyer
            package_name: Nom du package JDownloader
            method: Méthode de distribution des liens ("round-robin" ou "random")
            callback_id: ID du callback pour assurer la cohérence
            
        Returns:
            Résultat de l'opération
        """
        if not links:
            return {"success": False, "error": "No links provided"}
        
        if not self.connect():
            return {"success": False, "error": "Failed to connect to MyJDownloader"}
        
        # Initialiser les résultats
        results = {
            "success": True,
            "devices_used": {},
            "device_errors": {}
        }
        
        # Déterminer si tous les liens sont des liens filejoker
        all_filejoker = all(self.is_link_filejoker(link) for link in links)
        
        # Obtenir l'appareil approprié
        # Si tous les liens sont filejoker, utiliser uniquement les appareils filejoker
        # Sinon, utiliser tous les appareils disponibles
        device = self.get_next_device(is_filejoker=all_filejoker, callback_id=callback_id)
        
        if not device:
            results["success"] = False
            results["device_errors"]["general"] = f"No {'filejoker' if all_filejoker else 'normal'} devices available"
            return results
        
        # Envoyer tous les liens à l'appareil sélectionné
        success, error = self.add_links(device, links, package_name)
        
        # Mettre à jour les résultats
        if success:
            results["devices_used"][device] = links
        else:
            results["device_errors"] = {device: error}
            results["success"] = False
                
        return results


# Singleton instance
_myjdownloader_service = None

def get_myjdownloader_service() -> MyJDownloaderService:
    """Get the MyJDownloader service instance"""
    global _myjdownloader_service
    if _myjdownloader_service is None:
        _myjdownloader_service = MyJDownloaderService()
    return _myjdownloader_service