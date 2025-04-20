import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import logging

from .base import BaseScraper, Post
from datetime import timedelta

class PlanetSuzyScraper(BaseScraper):
    """Scraper for PlanetSuzy forums"""
    
    def get_forum_type(self) -> str:
        return 'planetsuzy'
    
    def extract_posts(self, soup: BeautifulSoup) -> List[Post]:
        """Extract posts from PlanetSuzy HTML"""
        posts = []
        post_tables = soup.select('table[id^="post"]')
        for post_table in post_tables:
            logging.info(f"------------------------Post table--------------------: {post_table.get('id', '')}")
            logging.info(f"------------------------postcount--------------------: {post_table.select_one('a[id^="postcount"]').get('name', '')}")

                
            post_id = post_table.get('id', '').replace('post', '')
            if not post_id:
                continue
            
            # Get post count (this is what we need for the correct ordering)
            post_count = None
            post_count_element = post_table.select_one('a[id^="postcount"]')
            if post_count_element:
                post_count_str = post_count_element.get('name', '')
                try:
                    post_count = int(post_count_str)
                except ValueError:
                    pass
            
            # Get post date
            date_text = post_table.select_one('td.thead').text.strip() if post_table.select_one('td.thead') else ''
            #print(f"------------------------Date text--------------------: {date_text}" )
            # Parse date from format like "23rd March 2023, 09:14"
            date = None
            date_match = re.search(r'(\d+)(?:st|nd|rd|th)\s+([A-Za-z]+)\s+(\d{4}),\s+(\d{2}):(\d{2})', date_text)
            if date_match:
                day, month, year, hour, minute = date_match.groups()
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                month_num = month_map.get(month, 1)  # Default to January if month not found
                try:
                    date = datetime(int(year), month_num, int(day), int(hour), int(minute))
                    #print(f"------------------------Date--------------------: {date}" )
                except ValueError:
                    # Handle invalid dates (e.g., February 30)
                    pass
            # Case 2: "Today, HH:MM" format
            elif "Today," in date_text:
                today_match = re.search(r'Today,\s+(\d{2}):(\d{2})', date_text)
                if today_match:
                    hour, minute = today_match.groups()
                    # Get today's date and combine with the parsed time
                    today = datetime.now().replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
                    date = today
                    #print(f"------------------------Date--------------------: {date}")
            # Case 3: "Yesterday"
            elif "Yesterday," in date_text:
                yesterday_match = re.search(r'Yesterday,\s+(\d{2}):(\d{2})', date_text)
                if yesterday_match:
                    hour, minute = yesterday_match.groups()
                    # Get yesterday's date and combine with the parsed time
                    yesterday = datetime.now().replace(hour=int(hour), minute=int(minute), second=0, microsecond=0) - timedelta(days=1)
                    date = yesterday
                    #print(f"------------------------Date--------------------: {date}")

            # Get author
            author_element = post_table.select_one('a.bigusername')
            author = author_element.text.strip() if author_element else 'Unknown'
            
            # Get content
            content_element = post_table.select_one('div[id^="post_message_"]')
            if content_element:
                # Créer une copie du contenu à modifier
                content_copy= content_element.__copy__()
                # Remplacer tous les liens par leur href
                for link in content_copy.find_all('a', href=True):
                    if self.is_download_link(link.get('href', '')):
                        #print(f"ok c'est en lien de telechargement")
                        href = link.get('href', '')
                        link.replace_with(href)

                # Extraire le texte complet avec les URLs insérées à la place des balises <a>
                transformed_content = content_copy.get_text(separator=' ', strip=True)
                #print(transformed_content)
            content = transformed_content
            
            # Get download links
            download_links = []
            if content_element:
                links = content_element.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    # Utilisez la méthode de la classe de base pour vérifier si c'est un lien de téléchargement
                    if self.is_download_link(href):
                        download_links.append(href)
            
            # Get images
            images = []
            if content_element:
                img_elements = content_element.find_all('img')
                for img in img_elements:
                    src = img.get('src', '')
                    if src and not src.startswith('http'):
                        # Handle relative URLs
                        base_url = self.get_base_url(self.thread_url)
                        src = urljoin(base_url, src)
                    
                    if src and 'inlineimg' not in img.get('class', []):
                        images.append(src)
            
            post = Post(
                post_id=post_id,
                date=date,
                author=author,
                content=content,
                download_links=download_links,
                images=images
            )
            
            # Analyser et regrouper les liens par qualité vidéo
            if download_links:
                print(f"Analyse du contenu pour {post_id}: {content}")    
                video_qualities = self.extract_video_qualities(content, download_links)
                post.video_qualities = video_qualities
            
            # Store post_count as an attribute for sorting
            post.post_count = post_count
            posts.append(post)
        
        # Sort posts by post_count (higher = newer)
        # Use post_id as fallback if post_count is not available
        return sorted(posts, key=lambda p: (p.post_count if hasattr(p, 'post_count') and p.post_count else 0, p.post_id), reverse=True)
    
    def get_next_page_url(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Get URL for last page or previous page
        """
        ## On test l'url pour savoir si on cherhce une last page ou la page précédente
        # ce test permet de chercher dans l'url -p suiv de chiffre puis suivi d'un autre - : ex -p25-
        match = re.search(r'-p(\d+)-', url)
        if match:
            # on la split pour pouvoir la modifier 
            logging.info(f"Match est : {match.group(1)}")
            link_split = url.split(sep='-')
            mylastlink = link_split[0]+"-p"+str(int(match.group(1))-1)  #  on insère le numero de page
            for i in range(2, len(link_split)):
                # on reconstruit le lien avec la fin prenom-nom-(surnom)-etc.html
                mylastlink = mylastlink+"-"+link_split[i]
            logging.info(f"URL de la Last page est : {mylastlink}")
            return mylastlink
        else:
            # Try to find the last page
            mylastlink = None
            mylastlink = soup.find('a', title=lambda value: value and 'Last Page' in value)
            logging.info(f"URL de mylastlink est : {mylastlink}")

            if mylastlink: # on a trouvé Last Page dans les liens de la soup
                parsed_url = urlparse(mylastlink.get('href'))
                params = parse_qs(parsed_url.query)                     
                mylastpage = params.get('page', ['1'])[0]  # Valeur par défaut '1' si absent
                

            ### Gerer le cas où il n'y pas de Last Page car il y a peu de page sur le forum
            elif mylastlink is None:
                ### alors on recherche le numero de page le plus élevé et on retourne cette page
                # Find all 'a' tags with 'page' in href
                mylastpage = 1
                links = soup.find_all('a', href=lambda value: value and 'page' in value)
                #logging.info(f"URL de links est : {links}")
                for link in links:
                    #logging.info(f"URL de link est : {link.get('href')}")
                    href = link['href']
                    # Chercher le paramètre 'page=' dans l'URL
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_num = int(match.group(1))
                        # Mettre à jour la page max si on trouve une valeur plus grande
                        if page_num > mylastpage:
                            mylastpage = page_num
                    
                # Get the link with maximum page number
                #mylastlink = max(links, key=lambda x: self.extract_page_number(x.get('href')), default=None)
            #on split le lien pour pouvoir insérer le numéro de page

            link_split = url.split(sep='-')
            mylastlink = link_split[0]+"-p"+str(mylastpage)  #  on insère le numero de page
            for i in range(1, len(link_split)):
            # on reconstruit le lien avec la fin prenom-nom-(surnom)-etc.html
                mylastlink = mylastlink+"-"+link_split[i]
            logging.info(f"URL de la Last page est : {mylastlink}")
            return mylastlink
        
    def extract_page_number(self, href):
        if not href:
            return 0
        # Find all numbers in the href
        numbers = re.findall(r'page=\d+', href)
        print(f"------------------------Numbers--------------------: {numbers}" )
        # Convert to integers and return the largest, or 0 if no numbers found
        return max([int(num) for num in numbers]) if numbers else 0
    
    def get_base_url(self, url: str) -> str:
        """Extract base URL from thread URL"""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"