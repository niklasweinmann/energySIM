"""
Schlanke Web-App für energyOS 3D-Builder
========================================
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path

# Flask-App initialisieren
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

app = Flask(__name__, 
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path='/static')
CORS(app)

@app.route('/')
def index():
    """Hauptseite mit 3D-Builder"""
    return render_template('3d_builder.html')

@app.route('/api/save', methods=['POST'])
def save_building():
    """Gebäude speichern"""
    try:
        data = request.get_json()
        # Hier könnte eine echte Speicherung implementiert werden
        return jsonify({'status': 'success', 'message': 'Gebäude gespeichert'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/load', methods=['GET'])
def load_building():
    """Gebäude laden"""
    try:
        # Hier könnte echtes Laden implementiert werden
        return jsonify({'status': 'success', 'data': {}})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starte energyOS 3D-Builder...")
    app.run(debug=True, host='0.0.0.0', port=5555)
