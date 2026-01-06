from flask import Flask, jsonify, request, send_file, Response
import json
import uuid
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

        @self.app.route('/dl/snh/')
        def dl_snh_search():
            query = request.args.get('q', '')
            page = request.args.get('p', '1')
            if not query:
                return jsonify({"error": "Parámetro 'q' requerido"}), 400
            try:
                page_num = int(page)
            except:
                page_num = 1
            results = self.nhentai_scraper.search(query, page_num)
            filename = f"{uuid.uuid4().hex}.json"
            return Response(json.dumps(results), mimetype="application/json",
                            headers={"Content-Disposition": f"attachment;filename={filename}"})
        
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

        @self.app.route('/dl/vnh/')
        def dl_vnh_data():
            code = request.args.get('code', '')
            if not code:
                return jsonify({"error": "Parámetro 'code' requerido"}), 400
            try:
                int(code)
            except:
                return jsonify({"error": "Código debe ser numérico"}), 400
            results = self.nhentai_scraper.data(code)
            filename = f"{uuid.uuid4().hex}.json"
            return Response(json.dumps(results), mimetype="application/json",
                            headers={"Content-Disposition": f"attachment;filename={filename}"})
        
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

        @self.app.route('/dl/s3h/')
        def dl_s3h_search():
            query = request.args.get('q', '')
            page = request.args.get('p', '1')
            if not query:
                return jsonify({"error": "Parámetro 'q' requerido"}), 400
            try:
                page_num = int(page)
            except:
                page_num = 1
            results = self.shentai_scraper.search(query, page_num)
            filename = f"{uuid.uuid4().hex}.json"
            return Response(json.dumps(results), mimetype="application/json",
                            headers={"Content-Disposition": f"attachment;filename={filename}"})
        
        @self.app.route('/v3h/')
        def v3h_data():
            code = request.args.get('code', '')
            if not code:
                return jsonify({"error": "Parámetro 'code' requerido"}), 400
            results = self.shentai_scraper.data(code)
            return jsonify(results)

        @self.app.route('/dl/v3h/')
        def dl_v3h_data():
            code = request.args.get('code', '')
            if not code:
                return jsonify({"error": "Parámetro 'code' requerido"}), 400
            results = self.shentai_scraper.data(code)
            filename = f"{uuid.uuid4().hex}.json"
            return Response(json.dumps(results), mimetype="application/json",
                            headers={"Content-Disposition": f"attachment;filename={filename}"})
        
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

        @self.app.route('/dl/hito/')
        def dl_hitomi_page():
            g = request.args.get('g', '')
            p = request.args.get('p', '1')
            if not g:
                return jsonify({"error": "Parámetro 'g' (gallery) requerido"}), 400
            try:
                page_num = int(p)
            except:
                page_num = 1
            json_result = self.hitomi_scraper.page(g, page_num)
            filename = f"{uuid.uuid4().hex}.json"
            return Response(json_result, mimetype="application/json",
                            headers={"Content-Disposition": f"attachment;filename={filename}"})
        
        @self.app.route('/hitom/')
        def hitomi_multipage():
            g = request.args.get('g', '')
            p = request.args.get('p', '1')
            f = request.args.get('f', None)
            
            if not g:
                return jsonify({"error": "Parámetro 'g' (gallery) requerido"}), 400
            
            try:
                start_page = int(p)
            except:
                start_page = 1
            
            end_page = None
            if f is not None:
                try:
                    end_page = int(f)
                except:
                    pass
            
            zip_buffer = self.hitomi_scraper.multipage(g, start_page, end_page)
            
            if zip_buffer is None:
                return jsonify({"error": "Error al descargar las páginas"}), 500
            
            filename = f"{g}.cbz"
            return Response(
                zip_buffer.getvalue(),
                mimetype="application/zip",
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
    
    def run(self, host='0.0.0.0', port=5000):
        self.app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    api = HentaiAPI()
    api.run()
