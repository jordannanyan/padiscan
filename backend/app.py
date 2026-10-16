from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from db import close_db
from routes import admin_routes, auth_routes, detect_routes, history_routes, penyakit_routes


def create_app():
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_MB * 1024 * 1024 + 1024 * 1024
    CORS(app)

    for module in (auth_routes, detect_routes, history_routes, penyakit_routes, admin_routes):
        app.register_blueprint(module.bp)
    app.teardown_appcontext(close_db)

    @app.get('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(Config.UPLOAD_DIR, filename)

    @app.get('/api/health')
    def health():
        return jsonify(status='ok')

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify(message=f'Ukuran file maksimal {Config.MAX_UPLOAD_MB} MB'), 413

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify(message='Endpoint tidak ditemukan'), 404

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
