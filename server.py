from flask import Flask, jsonify, request, send_file
import json
import base64
from scrap import NHentaiScraper, SHentaiScraper, HitomiScraper

class HentaiAPI:
    def __init__(self):
        self.app = Flask(__name__)
        self.nhentai_scraper = NHentaiScraper()
        self.shentai_scraper = SHentaiScraper()
        self.hitomi_scraper = HitomiScraper()
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return send_file('tutorial.html')
        
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
        
        @self.app.route('/hito/')
        def hitomi_page():
            g = request.args.get('g', '')
            p = request.args.get('p', '1')
            
            if not g:
                return jsonify({"error": "Parámetro 'g' (gallery) requerido"}), 400
            
            try:
                page_num = int(p)
            except:
                page_num = 1
            
            json_result = self.hitomi_scraper.page(g, page_num)
            
            try:
                result_dict = json.loads(json_result)
                return jsonify(result_dict)
            except json.JSONDecodeError:
                return jsonify({"error": "Error procesando respuesta", "raw_response": json_result})
    
    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    api = HentaiAPI()
    api.run()
