import requests
from bs4 import BeautifulSoup
import re

class NHentaiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def search(self, query, page=1):
        url = f"https://nhentai.net/search/?q={query}&page={page}"
        
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results_data = []
        
        h1_element = soup.find('h1')
        total_results = 0
        if h1_element:
            text = h1_element.get_text(strip=True)
            match = re.search(r'([\d,]+)\s+results', text)
            if match:
                total_results = int(match.group(1).replace(',', ''))
        
        gallery_divs = soup.find_all('div', class_='gallery')
        
        for gallery in gallery_divs[:25]:
            link_element = gallery.find('a', class_='cover')
            if not link_element:
                continue
            
            href = link_element.get('href', '')
            code = ''
            if href and '/g/' in href:
                code_match = re.search(r'/g/(\d+)/', href)
                if code_match:
                    code = code_match.group(1)
            
            img_element = gallery.find('img', class_='lazyload')
            thumbnail = ''
            if img_element:
                thumbnail = img_element.get('data-src', '')
                if not thumbnail:
                    thumbnail = img_element.get('src', '')
            
            caption_div = gallery.find('div', class_='caption')
            name = caption_div.get_text(strip=True) if caption_div else ''
            
            results_data.append({
                'nombre': name,
                'miniatura': thumbnail,
                'codigo': code
            })
        
        return {
            'total_resultados': total_results,
            'pagina_actual': page,
            'termino_busqueda': query,
            'resultados': results_data
        }
