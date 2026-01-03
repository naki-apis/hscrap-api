import os
import requests
from pathlib import Path

def download_file(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    base_dir = Path(__file__).parent.absolute()
    selenium_dir = base_dir / "selenium"
    selenium_dir.mkdir(exist_ok=True)
    
    chrome_url = "https://nakiapi-scrap.onrender.com/file/chrome"
    chromedriver_url = "https://nakiapi-scrap.onrender.com/file/chromedriver"
    
    chrome_path = selenium_dir / "chrome"
    chromedriver_path = selenium_dir / "chromedriver"
    
    print("Descargando Chrome...")
    download_file(chrome_url, chrome_path)
    
    print("Descargando Chromedriver...")
    download_file(chromedriver_url, chromedriver_path)
    
    os.chmod(chrome_path, 0o755)
    os.chmod(chromedriver_path, 0o755)
    
    print("Permisos establecidos")
    print("Instalando dependencias...")
    os.system("pip install Flask==2.3.3 selenium==4.15.0 requests==2.31.0")

if __name__ == "__main__":
    main()
