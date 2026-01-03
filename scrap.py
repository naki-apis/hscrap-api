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
        self.setup_selenium()
    
    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        base_dir = Path(__file__).parent.absolute()
        selenium_dir = base_dir / "selenium"
        
        chrome_path = selenium_dir / "chrome"
        chromedriver_path = selenium_dir / "chromedriver"
        
        if chrome_path.exists():
            chrome_options.binary_location = str(chrome_path)
            print(f"Chrome encontrado en: {chrome_path}")
        else:
            print(f"Chrome NO encontrado en: {chrome_path}")
        
        try:
            if chromedriver_path.exists():
                print(f"Chromedriver encontrado en: {chromedriver_path}")
                service = Service(executable_path=str(chromedriver_path))
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                print(f"Chromedriver NO encontrado en: {chromedriver_path}")
                print("Intentando sin ruta específica...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
            })
            print("Selenium inicializado correctamente")
            
        except Exception as e:
            print(f"Error inicializando Selenium: {e}")
            print(f"¿Existe selenium_dir? {selenium_dir.exists()}")
            print(f"¿Existe chrome? {chrome_path.exists()}")
            print(f"¿Existe chromedriver? {chromedriver_path.exists()}")
            self.driver = None
    
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
            url = f"https://nhentai.net/g/{code}/"
            
            try:
                response = self.session.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                if 'Just a moment' in response.text or 'Cloudflare' in response.text:
                    raise Exception('Cloudflare detected')
                
                soup = BeautifulSoup(response.text, 'html.parser')
                html_method = 'requests'
            except:
                if not self.driver:
                    self.setup_selenium()
                    if not self.driver:
                        raise Exception('Selenium not available')
                
                self.driver.get(url)
                time.sleep(random.uniform(2, 4))
                
                page_source = self.driver.page_source
                if 'Just a moment' in page_source or 'Cloudflare' in page_source:
                    time.sleep(random.uniform(5, 8))
                    self.driver.get(url)
                    time.sleep(random.uniform(3, 5))
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                html_method = 'selenium'
            
            gallery_id = None
            page_ext_map = {}
            
            thumbnails = soup.find_all('div', class_='thumb-container')
            
            for thumb in thumbnails:
                img = thumb.find('img', class_='lazyload')
                if img:
                    src = img.get('data-src') or img.get('src', '')
                    if src:
                        match = re.search(r'galleries/(\d+)/(\d+)t\.(png|jpg|jpeg|webp)', src)
                        if match:
                            gallery_id = match.group(1)
                            page_num = match.group(2)
                            ext = match.group(3)
                            page_ext_map[int(page_num)] = ext
            
            if not gallery_id:
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src', '')
                    if src:
                        match = re.search(r'galleries/(\d+)/', src)
                        if match:
                            gallery_id = match.group(1)
                            break
            
            total_pages = 0
            script_tag = soup.find('script', string=re.compile(r'window\._gallery'))
            if script_tag:
                script_text = script_tag.string
                pages_match = re.search(r'"num_pages":(\d+)', script_text)
                if pages_match:
                    total_pages = int(pages_match.group(1))
            
            if total_pages == 0:
                pages_section = soup.find('section', id='tags')
                if pages_section:
                    for tag_container in pages_section.find_all('div', class_='tag-container'):
                        if 'Pages' in tag_container.get_text():
                            for tag in tag_container.find_all('a', class_='tag'):
                                page_num = tag.find('span', class_='name')
                                if page_num:
                                    try:
                                        total_pages = int(page_num.get_text(strip=True))
                                        break
                                    except:
                                        pass
            
            image_links = []
            cover_image = ""
            
            if gallery_id and total_pages > 0:
                for page_num in range(1, total_pages + 1):
                    ext = page_ext_map.get(page_num, 'jpg')
                    image_links.append(f"https://i2.nhentai.net/galleries/{gallery_id}/{page_num}.{ext}")
                
                if image_links:
                    cover_image = image_links[0]
            
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
            
            return {
                'title': title,
                'code': int(code),
                'cover_image': cover_image,
                'tags': tags_dict,
                'image_links': image_links,
                'method': html_method
            }
            
        except Exception as e:
            return {
                'title': '',
                'code': int(code) if code.isdigit() else 0,
                'cover_image': '',
                'tags': {},
                'image_links': [],
                'error': str(e)
            }
    
    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
