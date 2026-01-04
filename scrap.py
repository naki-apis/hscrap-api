import requests
from bs4 import BeautifulSoup
import re
import math
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
        self.driver = None
    
    def _create_driver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"Error creando driver básico: {e}")
            
            try:
                base_dir = Path(__file__).parent.absolute()
                selenium_dir = base_dir / "selenium"
                
                chrome_path = selenium_dir / "chrome"
                chromedriver_path = selenium_dir / "chromedriver"
                
                if chrome_path.exists():
                    chrome_options.binary_location = str(chrome_path)
                    print(f"Usando Chrome en: {chrome_path}")
                
                if chromedriver_path.exists():
                    service = Service(executable_path=str(chromedriver_path))
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
                
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("Driver creado con rutas personalizadas")
                return True
            except Exception as e2:
                print(f"Error también con rutas personalizadas: {e2}")
                return False
    
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
        
        total_pages = math.ceil(total_results / 25)
        
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
            'total_paginas': total_pages,
            'pagina_actual': page,
            'termino_busqueda': query,
            'resultados': results_data
        }
    
    def data(self, code):
        try:
            if not self._create_driver():
                raise Exception("No se pudo crear el driver de Chrome")
            
            url = f"https://nhentai.net/g/{code}/"
            print(f"Accediendo a: {url}")
            
            self.driver.get(url)
            
            max_attempts = 3
            html_content = ""
            
            for attempt in range(max_attempts):
                wait_time = 3 + attempt * 2
                print(f"Intento {attempt + 1}, esperando {wait_time} segundos...")
                time.sleep(wait_time)
                
                page_source = self.driver.page_source
                if "Just a moment" in page_source or "Verifying you are human" in page_source:
                    print(f"Cloudflare detectado, esperando más...")
                    time.sleep(5)
                    continue
                
                if len(page_source) > 1000:
                    html_content = page_source
                    print(f"HTML obtenido: {len(html_content)} caracteres")
                    break
            
            if not html_content:
                raise Exception("No se pudo obtener contenido HTML después de varios intentos")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title_element = soup.find('h1', class_='title')
            title = ""
            if title_element:
                title_parts = []
                for span in title_element.find_all('span', class_=True):
                    title_parts.append(span.get_text(strip=True))
                title = ' '.join(title_parts)
            
            tags_dict = {}
            tags_section = soup.find('section', id='tags')
            if tags_section:
                for tag_container in tags_section.find_all('div', class_='tag-container'):
                    field_name = tag_container.get_text(strip=True).split(':')[0].strip()
                    tags = []
                    for tag_link in tag_container.find_all('a', class_='tag'):
                        tag_name = tag_link.find('span', class_='name')
                        if tag_name:
                            tags.append(tag_name.get_text(strip=True))
                    if tags:
                        tags_dict[field_name] = tags
            
            gallery_id = None
            pattern = re.compile(r'//t[1249]\.nhentai\.net/galleries/(\d+)/(\d+)t\.(webp|jpg|png|jpeg)')
            
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src', '')
                if src:
                    match = pattern.search(src)
                    if match:
                        gallery_id = match.group(1)
                        break
            
            image_links = []
            cover_image = ""
            
            if gallery_id:
                print(f"ID de galería encontrado: {gallery_id}")
                
                total_pages_from_tags = 0
                if 'Pages' in tags_dict and tags_dict['Pages']:
                    try:
                        total_pages_from_tags = int(tags_dict['Pages'][0])
                    except (ValueError, IndexError):
                        pass
                
                found_thumbnails = []
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src', '')
                    if src:
                        match = pattern.search(src)
                        if match:
                            page_num = match.group(2)
                            ext = match.group(3)
                            found_thumbnails.append({
                                'page_num': int(page_num),
                                'ext': ext
                            })
                
                found_thumbnails.sort(key=lambda x: x['page_num'])
                
                if total_pages_from_tags == 0 and found_thumbnails:
                    total_pages_from_tags = found_thumbnails[-1]['page_num']
                
                print(f"Páginas totales: {total_pages_from_tags}, Miniaturas: {len(found_thumbnails)}")
                
                if total_pages_from_tags > 0:
                    extensions_count = {}
                    for thumb in found_thumbnails:
                        ext = thumb['ext']
                        extensions_count[ext] = extensions_count.get(ext, 0) + 1
                    
                    default_ext = 'jpg'
                    if extensions_count:
                        default_ext = max(extensions_count.items(), key=lambda x: x[1])[0]
                    
                    page_ext_map = {thumb['page_num']: thumb['ext'] for thumb in found_thumbnails}
                    
                    for page_num in range(1, total_pages_from_tags + 1):
                        ext = page_ext_map.get(page_num, default_ext)
                        image_link = f"https://i2.nhentai.net/galleries/{gallery_id}/{page_num}.{ext}"
                        image_links.append(image_link)
                else:
                    for thumb in found_thumbnails:
                        image_link = f"https://i2.nhentai.net/galleries/{gallery_id}/{thumb['page_num']}.{thumb['ext']}"
                        image_links.append(image_link)
                
                if image_links:
                    cover_image = image_links[0]
            
            result = {
                'title': title,
                'code': int(code),
                'cover_image': cover_image,
                'tags': tags_dict,
                'image_links': image_links
            }
            
            return result
            
        except Exception as e:
            print(f"Error en data(): {e}")
            return {
                'title': '',
                'code': int(code) if code.isdigit() else 0,
                'cover_image': '',
                'tags': {},
                'image_links': [],
                'error': str(e)[:100]
            }
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass

class SHentaiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def search(self, query, page=1):
        url = f"https://es.3hentai.net/search?q={query}&page={page}"
        
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results_data = []
        
        total_results_text = soup.find('div', class_='search-result-nb-result')
        total_results = 0
        if total_results_text:
            text = total_results_text.get_text(strip=True)
            match = re.search(r'([\d\s,]+)\s+results', text)
            if match:
                total_results = int(match.group(1).replace(',', '').replace(' ', ''))
        
        total_pages_elem = soup.find('a', class_='page-link', href=lambda x: x and f'page={total_results//24+1}' in x)
        if total_pages_elem:
            try:
                total_pages = int(total_pages_elem.text)
            except:
                total_pages = math.ceil(total_results / 24)
        else:
            total_pages = math.ceil(total_results / 24)
        
        doujin_cols = soup.find_all('div', class_='doujin-col')
        
        for col in doujin_cols:
            link_element = col.find('a', class_='cover')
            if not link_element:
                continue
            
            href = link_element.get('href', '')
            code = ''
            if href and '/d/' in href:
                code_match = re.search(r'/d/(\d+)', href)
                if code_match:
                    code = code_match.group(1)
            
            img_element = link_element.find('img')
            thumbnail = ''
            if img_element:
                thumbnail = img_element.get('data-src', '')
                if not thumbnail:
                    thumbnail = img_element.get('src', '')
            
            title_div = link_element.find('div', class_='title')
            name = title_div.get_text(strip=True) if title_div else ''
            
            if code:
                image_links = [f"https://s1.3hentai.xyz/d{code[0:3]}{code[3:]}/1.jpg"]
                results_data.append({
                    'code': code,
                    'image_links': image_links,
                    'name': name
                })
        
        return {
            'success': True,
            'total_results': total_results,
            'total_pages': total_pages,
            'page': page,
            'search_term': query,
            'results': results_data
        }
    
    def data(self, code):
        url = f"https://es.3hentai.net/d/{code}"
        
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        
        gallery = soup.find("div", id="main-content")
        thumbs = gallery.find("div", id="thumbnail-gallery") if gallery else None
        thumb_divs = thumbs.find_all("div", class_="single-thumb") if thumbs else []
        total_pages = len(thumb_divs)
        
        tags_dict = {}
        tag_containers = soup.find_all("div", class_="tag-container")
        for container in tag_containers:
            field_name = container.get_text(strip=True).split(':')[0].strip()
            tags = []
            for tag_link in container.find_all("a", class_="name"):
                tags.append(tag_link.get_text(strip=True))
            if tags:
                tags_dict[field_name] = tags
        
        image_links = []
        cover_image = ""
        
        if thumb_divs:
            for div in thumb_divs:
                img_tag = div.find("img")
                if img_tag:
                    src_url = img_tag.get("data-src") or img_tag.get("src")
                    if src_url:
                        full_img_url = re.sub(r't(?=\.\w{3,4}$)', '', src_url)
                        image_links.append(full_img_url)
            
            if image_links:
                cover_image = image_links[0]
        
        result = {
            'success': True,
            'title': title,
            'clean_title': title.replace(' - 3Hentai', '').strip(),
            'code': code,
            'cover_image': cover_image,
            'tags': tags_dict,
            'image_links': image_links,
            'total_pages': total_pages
        }
        
        return result
    
    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
