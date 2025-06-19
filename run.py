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
    killed_any = False
    try:
        # Für macOS/Linux - prüfe ob überhaupt Prozesse auf dem Port laufen
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                               capture_output=True, text=True, check=False)
        if result.stdout.strip():
            pids = [pid.strip() for pid in result.stdout.strip().split('\n') if pid.strip()]
            print(f"   🎯 Gefunden: {len(pids)} Prozess(e) auf Port {port}")
            
            for pid in pids:
                try:
                    # Erst versuchen, Prozess-Info zu bekommen
                    info_result = subprocess.run(['ps', '-p', pid, '-o', 'comm='], 
                                               capture_output=True, text=True, check=False)
                    process_name = info_result.stdout.strip() if info_result.stdout.strip() else f"PID {pid}"
                    
                    subprocess.run(['kill', '-9', pid], capture_output=True, check=True)
                    print(f"   ✅ Prozess beendet: {process_name}")
                    killed_any = True
                except subprocess.CalledProcessError:
                    print(f"   ⚠️ Prozess {pid} konnte nicht beendet werden (evtl. bereits beendet)")
            
            if killed_any:
                time.sleep(1)
        else:
            print(f"   ℹ️ Keine Prozesse auf Port {port} gefunden")
            
        return killed_any
    except Exception as e:
        print(f"   ⚠️ Fehler beim Prüfen von Port {port}: {e}")
    return False

def check_port_status(port):
    """Prüft detailliert den Status eines Ports"""
    try:
        # Prüfe ob Port frei ist
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return "free"
    except OSError:
        # Port ist belegt, prüfe ob es unser eigener Prozess ist
        try:
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                   capture_output=True, text=True, check=False)
            if result.stdout.strip():
                return "occupied"
            return "unknown"
        except:
            return "unknown"

def main():
    print("🏠 energyOS - 3D-Gebäudemodellierung")
    print("=" * 50)
    
    # Intelligente Port-Prüfung
    port_status = check_port_status(8080)
    
    if port_status == "free":
        port = 8080
        print("✅ Port 8080 ist verfügbar")
    elif port_status == "occupied":
        print("🔄 Port 8080 ist belegt, beende bestehende Prozesse...")
        
        # Mehrere Versuche, den Port freizubekommen
        success = False
        
        # Versuch 1: Sanfte Beendigung von energyOS-Prozessen
        try:
            subprocess.run(['pkill', '-f', 'web_app'], 
                          capture_output=True, check=False)
            subprocess.run(['pkill', '-f', 'run.py'], 
                          capture_output=True, check=False)
            time.sleep(1.5)
            
            if check_port_status(8080) == "free":
                port = 8080
                success = True
                print("✅ Port 8080 wurde freigegeben (sanfte Beendigung)")
        except Exception as e:
            print(f"   ⚠️ Sanfte Beendigung fehlgeschlagen: {e}")
        
        # Versuch 2: Forcierte Beendigung aller Prozesse auf Port 8080
        if not success:
            print("🔄 Versuche forcierte Beendigung...")
            try:
                killed = kill_port_processes(8080)
                time.sleep(1)
                
                if check_port_status(8080) == "free":
                    port = 8080
                    success = True
                    print("✅ Port 8080 wurde freigegeben (forcierte Beendigung)")
                elif killed:
                    # Manchmal dauert es etwas länger
                    time.sleep(2)
                    if check_port_status(8080) == "free":
                        port = 8080
                        success = True
                        print("✅ Port 8080 wurde freigegeben (verzögert)")
            except Exception as e:
                print(f"   ⚠️ Forcierte Beendigung fehlgeschlagen: {e}")
        
        # Versuch 3: Alternativen Port nur als letzter Ausweg
        if not success:
            print("⚠️ Port 8080 konnte nicht freigegeben werden")
            port = find_free_port(8081)
            if port:
                print(f"🔄 Verwende alternativen Port {port} (Port 8080 bleibt belegt)")
            else:
                print("❌ Kein freier Port gefunden")
                return
    else:
        # Port-Status unbekannt, versuche trotzdem Port 8080 zu befreien
        print("🔄 Port-Status unbekannt, versuche Bereinigung...")
        try:
            kill_port_processes(8080)
            time.sleep(1)
            if check_port_status(8080) == "free":
                port = 8080
                print("✅ Port 8080 wurde freigegeben")
            else:
                port = find_free_port(8080)
                if not port:
                    print("❌ Kein freier Port gefunden")
                    return
                print(f"🔄 Verwende Port {port}")
        except:
            port = find_free_port(8080)
            if not port:
                print("❌ Kein freier Port gefunden")
                return
            if port != 8080:
                print(f"🔄 Verwende Port {port}")
    
    print("\n📋 Features:")
    print("• Schlanker 3D-Builder")
    print("• Optimierte Performance") 
    print("• Debug-Logging")
    print("• Responsive Design")
    print("=" * 50)
    
    try:
        from src.ui.app import app
        
        print("✓ Schlanke Web-App geladen")
        print("✓ 3D-Visualisierung verfügbar")
        print("✓ Performance optimiert")
        print(f"🚀 Server startet auf http://localhost:{port}")
        print("⚡ Drücken Sie Ctrl+C zum Beenden")
        print("")
        print("📋 Bedienungshinweise:")
        print("• 3D-Navigation: Maus + Mausrad") 
        print("• Tools: Sidebar links")
        print("• Debug-Log: Button unten rechts")
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
