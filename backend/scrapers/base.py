from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from collections import defaultdict
import json
import argparse


from ..config import get_config
import logging

class VideoQuality:
    """Represents a video quality with its download links grouped by provider"""
    def __init__(self, quality_name: str, description: str = ""):
        self.quality_name = quality_name  # HD, FullHD, 4K, etc.
        self.description = description    # Additional info like resolution, file size
        self.provider_links = defaultdict(list)  # Provider name -> list of links
    
    def add_link(self, provider: str, link: str):
        """Add a download link for a specific provider"""
        self.provider_links[provider].append(link)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_name": self.quality_name,
            "description": self.description,
            "provider_links": dict(self.provider_links)
        }
    
    def __str__(self) -> str:
        return f"VideoQuality({self.quality_name}, providers: {len(self.provider_links)})"

class Post:
    """Represents a forum post"""
    def __init__(self, post_id: str, date: datetime, author: str, content: str, 
                 download_links: List[str], images: List[str]):
        self.post_id = post_id
        self.date = date
        self.author = author
        self.content = content
        self.download_links = download_links
        self.images = images
        self.video_qualities = []  # List of VideoQuality objects
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "date": self.date.isoformat() if self.date else None,
            "author": self.author,
            "content": self.content,
            "download_links": self.download_links,
            "images": self.images,
            "video_qualities": [vq.to_dict() for vq in self.video_qualities]
        }
        
    def __str__(self) -> str:
        return f"Post(id={self.post_id}, author={self.author}, links={len(self.download_links)})"

class BaseScraper(ABC):
    """Base class for all forum scrapers"""
    
    def __init__(self, thread_url: str, last_post_id: Optional[str] = None):
        self.thread_url = thread_url
        self.last_post_id = last_post_id
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Récupération des fournisseurs de téléchargement depuis la configuration
        self.download_providers = get_config().DOWNLOAD_PROVIDERS
    
    def is_download_link(self, url: str) -> bool:
        """Détermine si une URL est un lien de téléchargement en fonction des fournisseurs configurés"""
        return any(provider in url.lower() for provider in self.download_providers)
    
    def parse_post_content(self,content_string):
        """
        Parse une chaîne de texte représentant le contenu d'un post et la convertit en structure JSON.
        Le format de sortie est un dictionnaire avec text1, links1, text2, links2, etc.
        Si un texte n'a pas de liens, il est ajouté au texte précédent qui avait des liens.
        
        Args:
            content_string (str): La chaîne de caractères à analyser
            
        Returns:
            dict: Un objet JSON structuré
        """
        # Structure intermédiaire
        sections = []
        
        # Motif pour détecter les URLs
        url_pattern = r'https?://[^\s]+'
        
        # Diviser le contenu en utilisant les URLs comme séparateurs
        parts = re.split(f'({url_pattern})', content_string)
        
        current_section = None
        
        for i, part in enumerate(parts):
            # Vérifier si la partie est une URL
            if re.match(url_pattern, part):
                # Si nous avons une section en cours, ajouter l'URL comme sous-section
                if current_section is not None:
                    if "links" not in current_section:
                        current_section["links"] = []
                    current_section["links"].append(part.strip())
            else:
                # Si la partie n'est pas vide, c'est un texte potentiel
                if part.strip():
                    # Créer une nouvelle section
                    current_section = {
                        "text": part.strip(),
                        "links": []
                    }
                    sections.append(current_section)
        
        # Fusionner les sections de texte sans liens avec la section précédente qui a des liens
        i = 0
        while i < len(sections):
            # Si cette section n'a pas de liens et ce n'est pas la première section
            if not sections[i]["links"] and i > 0:
                # Ajouter son texte à la section précédente
                sections[i-1]["text"] += " " + sections[i]["text"]
                # Supprimer cette section
                sections.pop(i)
            else:
                i += 1
        
        # Supprimer la dernière section si elle n'a pas de liens
        if sections and not sections[-1]["links"]:
            # Si au moins une section a des liens, ajouter le texte à la dernière section avec des liens
            sections_with_links = [s for s in sections if s["links"]]
            if sections_with_links:
                # Trouver l'index de la dernière section avec des liens
                last_with_links = sections.index(sections_with_links[-1])
                # Ajouter le texte de la dernière section (sans liens) à cette section
                sections[last_with_links]["text"] += " " + sections[-1]["text"]
            # Supprimer la dernière section sans liens
            sections.pop()
        
        # Convertir au format de sortie souhaité
        result = {}
        for i, section in enumerate(sections, 1):
            result[f"text{i}"] = section["text"]
            result[f"links{i}"] = section["links"]
        
        return result
    
    def get_provider_from_url(self, url: str) -> str:
        """Extrait le nom du fournisseur à partir d'une URL"""
        for provider in self.download_providers:
            if provider in url.lower():
                return provider
        return "unknown"
    
    def extract_video_qualities(self, content: str, download_links: List[str]) -> List[VideoQuality]:
        """
        Analyse le contenu du post pour extraire et regrouper les liens par qualité vidéo
        Utilise une approche simplifiée avec un dictionnaire de textes et liens
        
        Args:
            content: Le contenu textuel du post
            download_links: Liste des liens de téléchargement trouvés
                
        Returns:
            Liste des qualités vidéo avec leurs liens regroupés
        """
        # Activer ou désactiver les prints de debug
        DEBUG = True
        
        def debug_print(*args, **kwargs):
            if DEBUG:
                print(*args, **kwargs)
        
        if not download_links:
            return []
        
        # debug_print("\n\n===== DÉBUT D'EXTRACTION DES QUALITÉS =====")
        # debug_print(f"Nombre de liens de téléchargement: {len(download_links)}")
        # debug_print(f"Liens: {download_links}")
        # debug_print(f"Contenu: {content}")
        # debug_print(f"========FIN Contenu================")



        
        # Nettoyage du contenu: remplacer les sauts de ligne par des espaces
        # et supprimer les mots de séparation courants

        clean_content = content.replace('\r', ' ').replace('\n', ' ')
        for separator in ['<br>', '<br/>', '<br />', ' or ', ' ou ', ' and ', ' et ', ' oder ', ' - ']:
            clean_content = clean_content.replace(separator, ' ')
        
        # Nettoyer les espaces multiples
        clean_content = ' '.join(clean_content.split())
        
        #debug_print(f"Clean Contenu nettoyé: {clean_content}")
        
        # Créer le dictionnaire du post
        dic_post = self.parse_post_content(clean_content) 
        debug_print(f"Dictionnaire du post: {dic_post}")
        
        # Maintenant, créer les objets VideoQuality à partir du dictionnaire
        qualities = []
        
        for i in range(1, len(dic_post) + 1):
            text_key = f"text{i}"
            links_key = f"links{i}"
            
            text = dic_post.get(text_key, "")
            links = dic_post.get(links_key, [])
            
            if not links:
                continue  # Ignorer les sections sans liens
            
            #debug_print(f"\n----- Traitement de la section {i} -----")
            #debug_print(f"Texte: {text[:100]}...")
            #debug_print(f"Liens: {links}")
            
            # Extraire les informations de qualité
            quality_name = text
            description = "Unknown Quality"
            
            # Recherche de résolution
            res_match = re.search(r'(\d+)\s*[xX]\s*(\d+)', text)
            if res_match:
                width, height = int(res_match.group(1)), int(res_match.group(2))
                if width >= 3840 or height >= 2160:
                    quality_name = '4K'
                elif width >= 1920 or height >= 1080:
                    quality_name = 'FullHD'
                elif width >= 1280 or height >= 720:
                    quality_name = 'HD'
                else:
                    quality_name = 'SD'
                    
                description = f"{width}x{height}"
                
                # Recherche d'autres informations pour la description
                format_match = re.search(r'\b(mp4|mkv|avi|wmv|mov)\b', text, re.IGNORECASE)
                if format_match:
                    description = f"{format_match.group(1)} - {description}"
                    
                size_match = re.search(r'(\d+(?:\.\d+)?)\s*([MGT]i?B)', text, re.IGNORECASE)
                if size_match:
                    size_str = f"{size_match.group(1)} {size_match.group(2)}"
                    description = f"{description} - {size_str}"
                    
                duration_match = re.search(r'(\d+:\d+(?::\d+)?|\d+\s*min(?:utes?)?(?:\s*\d+\s*s(?:ec(?:onds?)?)?)?)', text, re.IGNORECASE)
                if duration_match:
                    description = f"{description} - {duration_match.group(1)}"
            
            # Si aucune résolution n'est trouvée, essayer d'autres indicateurs
            else:
                # Recherche de termes de qualité
                quality_term_match = re.search(r'\b(4K|UHD|HD|FullHD|SD|1080|720|2160)\b', text, re.IGNORECASE)
                if quality_term_match:
                    term = quality_term_match.group(1).lower()
                    if term in ['4k', 'uhd', '2160']:
                        quality_name = '4K'
                    elif term in ['fullhd', '1080']:
                        quality_name = 'FullHD'
                    elif term in ['hd', '720']:
                        quality_name = 'HD'
                    elif term == 'sd':
                        quality_name = 'SD'
                    else:
                        quality_name = term.upper()
                        
                    description = quality_term_match.group(1)
                    
                # Si toujours pas de qualité, essayer d'estimer par la taille
                else:
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*([MGT]i?B)', text, re.IGNORECASE)
                    if size_match:
                        size_val = float(size_match.group(1))
                        unit = size_match.group(2).upper()
                        
                        if unit in ['GB', 'GIB']:
                            if size_val < 1.5:
                                quality_name = 'SD'
                            elif size_val < 3:
                                quality_name = 'HD'
                            elif size_val < 6:
                                quality_name = 'FullHD'
                            else:
                                quality_name = '4K'
                        elif unit in ['MB', 'MIB']:
                            if size_val < 1500:
                                quality_name = 'SD'
                            elif size_val < 3000:
                                quality_name = 'HD'
                            else:
                                quality_name = 'FullHD'
                                
                        description = f"{size_val} {unit}"
            
            #debug_print(f"Qualité identifiée: {quality_name}")
            #debug_print(f"Description: {description}")
            
            # Créer l'objet VideoQuality
            video_quality = VideoQuality(quality_name, description)
            
            # Ajouter les liens
            for link in links:
                provider = self.get_provider_from_url(link)
                video_quality.add_link(provider, link)
                #debug_print(f"Ajout du lien {link} au fournisseur {provider}")
            
            qualities.append(video_quality)
        
        # Si aucune qualité n'a été identifiée mais que nous avons des liens
        if not qualities and download_links:
            debug_print("\nAucune qualité identifiée, création d'une qualité 'Unknown' pour tous les liens")
            video_quality = VideoQuality("Unknown", "Unknown Quality")
            
            for link in download_links:
                provider = self.get_provider_from_url(link)
                video_quality.add_link(provider, link)
            
            qualities.append(video_quality)
        
        debug_print(f"\nQualités extraites: {len(qualities)}")
        for i, q in enumerate(qualities):
            debug_print(f"Qualité {i+1}: {q.quality_name}, description: {q.description}")
            for provider, links in q.provider_links.items():
                debug_print(f"  - Fournisseur {provider}: {len(links)} liens")
            debug_print(f"--------------------------------------------")
        
        debug_print("===== FIN D'EXTRACTION DES QUALITÉS =====\n\n")
        return qualities    

    def get_page_content(self, url: str) -> str:
        """Fetch the HTML content of a page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Error fetching page content: {e}")
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup"""
        return BeautifulSoup(html, 'html.parser')
    
    @abstractmethod
    def get_forum_type(self) -> str:
        """Return the forum type identifier"""
        pass
    
    @abstractmethod
    def extract_posts(self, soup: BeautifulSoup) -> List[Post]:
        """Extract posts from the page"""
        pass
    
    @abstractmethod
    def get_next_page_url(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Get URL for the next page, if any"""
        pass
    
    def check_for_new_posts(self) -> List[Post]:
        """Check for new posts since last_post_id"""
        all_new_posts = []
        current_url = self.thread_url
        
        # Get first page (or last page for forum with newest posts at the end)
        html_content = self.get_page_content(current_url)
        soup = self.parse_html(html_content)
        
        # Get next URL (for PlanetSuzy, this will be the last page if it's first access)
        next_url = self.get_next_page_url(soup,current_url)

        # Si on trouve le next url on le parse pour pouvoir l'analyser les posts
        if next_url:
            current_url = next_url
            html_content = self.get_page_content(current_url)
            soup = self.parse_html(html_content)
        
        # Start checking pages
        while current_url:
            posts = self.extract_posts(soup)
            
            # Filter posts newer than last_post_id
            if self.last_post_id:
                #print(f"--------------Last post ID------------------: {self.last_post_id}")
                # Find posts newer than the last seen post
                new_posts = []
                for post in posts:
                    #print(f"--------------Post ID------------------: {post.post_id}")
                    if post.post_id == self.last_post_id:
                        # Found the last seen post, stop here
                        break
                    elif post.post_id > self.last_post_id:
                        # This post is newer, add it to the list
                        print(f"Post ID:{post.post_id} is NEWER than Last post ID: {self.last_post_id}")
                        new_posts.append(post)
                    else:
                        # This post is older, skip it
                        print(f"Post ID:{post.post_id} is OLDER than Last post ID: {self.last_post_id}")
                        continue
                
                # Add the new posts
                all_new_posts.extend(new_posts)
                
                # If we found the last seen post on this page, stop looking
                if any(post.post_id == self.last_post_id for post in posts):
                    break
            else:
                # No last_post_id, get only the latest post
                if posts:
                    all_new_posts.append(posts[0])
                break
            
            # Get previous/next page URL
            next_page_url = self.get_next_page_url(soup,current_url)
            if not next_page_url:
                break
            
            current_url = next_page_url
            html_content = self.get_page_content(current_url)
            soup = self.parse_html(html_content)
        
        return all_new_posts