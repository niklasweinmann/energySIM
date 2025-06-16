#!/usr/bin/env python3
"""
energyOS 3D-Gebäudemodellierung
===============================

Startet die Web-basierte 3D-Benutzeroberfläche für 
Gebäudemodellierung mit allen Bauteilen, U-Werten und Heizkörpern.

Features:
- Detaillierte Wände mit Schichtaufbau und U-Werten
- Fenster und Türen mit thermischen Eigenschaften  
- Dachflächen mit PV-Potenzial
- Heizkörper und Heizflächen
- Wärmebrücken und Verschattungselemente
- Wärmepumpenauslegung nach deutscher Norm
- Export/Import von Gebäudedaten
"""

import sys
import webbrowser
import threading
import time
import subprocess
import os
import socket
from pathlib import Path

# Projektpfad hinzufügen
sys.path.append(str(Path(__file__).parent))

def find_free_port(start_port=8080):
    """Findet einen freien Port ab start_port"""
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def kill_port_processes(port):
    """Beendet alle Prozesse auf dem angegebenen Port"""
    try:
        # Für macOS/Linux
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                               capture_output=True, text=True, check=False)
        if result.stdout.strip():
            pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
            for pid in pids:
                subprocess.run(['kill', '-9', pid], capture_output=True, check=False)
                print(f"   Killed process {pid} on port {port}")
            time.sleep(1)
            return True
    except Exception as e:
        print(f"   Error killing processes on port {port}: {e}")
    return False

def main():
    print("🏠 energyOS - Erweiterte 3D-Gebäudemodellierung")
    print("=" * 60)
    
    # Stoppe alle laufenden Server auf Port 8080
    print("🔄 Stoppe bestehende Server...")
    try:
        # Alle Python-Prozesse mit energyOS beenden
        subprocess.run(['pkill', '-f', 'enhanced_3d_editor'], 
                      capture_output=True, check=False)
        subprocess.run(['pkill', '-f', 'web_app'], 
                      capture_output=True, check=False)
        
        # Port 8080 freigeben
        killed = kill_port_processes(8080)
        if killed:
            print("✅ Port 8080 freigegeben")
        else:
            print("⚠️ Port 8080 konnte nicht freigegeben werden")
        
        time.sleep(1)
        
    except Exception as e:
        print(f"⚠️ Warnung beim Stoppen bestehender Server: {e}")
    
    # Freien Port finden
    port = find_free_port(8080)
    if not port:
        print("❌ Kein freier Port gefunden")
        return
    
    if port != 8080:
        print(f"🔄 Port 8080 belegt, verwende Port {port}")
    
    print("Features:")
    print("• Detaillierte Bauteile mit U-Werten")
    print("• Heizkörper und Heizflächenplanung") 
    print("• Wärmepumpenauslegung nach DIN EN 12831")
    print("• Materialien nach DIN 4108-4")
    print("• Normen: GEG 2020, EnEV, KfW, Passivhaus")
    print("=" * 60)
    
    try:
        from src.ui.web_app import app
        
        print("✓ Erweiterte Web-App geladen")
        print("✓ Detaillierte Gebäudekomponenten verfügbar")
        print("✓ Wärmepumpenberechnungen aktiviert")
        print(f"🚀 Server startet auf http://localhost:{port}")
        print("⚡ Drücken Sie Ctrl+C zum Beenden")
        print("")
        print("📋 Bedienungshinweise:")
        print("• Tabs: Gebäude | Bauteile | Heizung | Analyse")
        print("• 3D-Navigation: Maus + Mausrad")
        print("• Komponenten: Klicken zum Auswählen")
        print("• Bearbeiten: Doppelklick auf Komponente")
        print("")
        
        # Browser automatisch öffnen
        def open_browser():
            time.sleep(3)
            webbrowser.open(f'http://localhost:{port}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        app.run(host='127.0.0.1', port=port, use_reloader=False)
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        print("💡 Prüfen Sie: pip install -r requirements.txt")
        
    except KeyboardInterrupt:
        print("\n👋 Server beendet")
        
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        print(f"   Fehlertyp: {type(e).__name__}")

if __name__ == '__main__':
    main()
