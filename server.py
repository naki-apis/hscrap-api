from flask import Flask, jsonify, request
from scrap import NHentaiScraper, SHentaiScraper

class HentaiAPI:
    def __init__(self):
        self.app = Flask(__name__)
        self.nhentai_scraper = NHentaiScraper()
        self.shentai_scraper = SHentaiScraper()
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return "API de scraping nhentai y 3hentai"
        
        @self.app.route('/snh/')
        def snh_search():
            query = request.args.get('q', '')
            page = request.args.get('p', '1')
            
            if not query:
                return jsonify({"error": "Parámetro 'q' requerido"}), 400
            
            try:
                page_num = int(page)
            except:
                page_num = 1
            
            results = self.nhentai_scraper.search(query, page_num)
            return jsonify(results)
        
        @self.app.route('/vnh/')
        def vnh_data():
            code = request.args.get('code', '')
            
            if not code:
                return jsonify({"error": "Parámetro 'code' requerido"}), 400
            
            try:
                int(code)
            except:
                return jsonify({"error": "Código debe ser numérico"}), 400
            
            results = self.nhentai_scraper.data(code)
            return jsonify(results)
        
        @self.app.route('/s3h/')
        def s3h_search():
            query = request.args.get('q', '')
            page = request.args.get('p', '1')
            
            if not query:
                return jsonify({"error": "Parámetro 'q' requerido"}), 400
            
            try:
                page_num = int(page)
            except:
                page_num = 1
            
            results = self.shentai_scraper.search(query, page_num)
            return jsonify(results)
        
        @self.app.route('/v3h/')
        def v3h_data():
            code = request.args.get('code', '')
            
            if not code:
                return jsonify({"error": "Parámetro 'code' requerido"}), 400
            
            results = self.shentai_scraper.data(code)
            return jsonify(results)
    
    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    api = HentaiAPI()
    api.run()
