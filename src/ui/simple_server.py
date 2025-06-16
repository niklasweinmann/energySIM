#!/usr/bin/env python3
"""
Einfacher Flask Server für die energyOS 3D-Anwendung
"""

from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

@app.route('/')
def index():
    """Hauptseite der Anwendung"""
    return render_template('index.html')

@app.route('/building-editor')
def building_editor():
    """3D-Gebäudeeditor"""
    return render_template('building_editor.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Statische Dateien servieren"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    print("🚀 Starte energyOS 3D-Gebäudemodellierung...")
    print("📍 URL: http://localhost:5000")
    print("🏠 Gebäude-Editor: http://localhost:5000/building-editor")
    print("⚡ Drücken Sie Ctrl+C zum Beenden")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
