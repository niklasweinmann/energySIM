# Erweiterte 3D-Gebäudemodellierung - Benutzerhandbuch

## Überblick

Die erweiterte 3D-Gebäudemodellierung in energyOS ermöglicht eine intuitive und präzise Erstellung von Gebäudemodellen mit automatischer Berechnung der thermischen Eigenschaften nach deutschen Normen.

## 🎯 Hauptfunktionen

### 1. **Intuitive Benutzerführung**
- **Drag & Drop**: Bauteile einfach aus der Toolbar in den 3D-Editor ziehen
- **Click & Place**: Bauteile anklicken und durch Klick im 3D-Raum platzieren
- **Smart Snapping**: Automatisches Andocken von Bauteilen (z.B. Fenster an Wände)
- **Visuelles Feedback**: Farbkodierte Darstellung der thermischen Qualität

### 2. **Intelligente Bauteil-Verbindung**
- **Anti-Wärmebrücken**: Automatische Erkennung und Vermeidung von Wärmebrücken
- **Strukturelle Integrität**: Bauteile verbinden sich automatisch korrekt
- **Normgerechte Verbindungen**: Einhaltung der deutschen Bauvorschriften

### 3. **Echtzeit-Berechnung**
- **Thermische Performance**: Live-Berechnung von U-Werten und Energieklassen
- **Normvalidierung**: Automatische Prüfung gegen EnEV/GEG-Anforderungen
- **Optimierungsvorschläge**: Intelligente Empfehlungen zur Verbesserung

## 🔧 Verfügbare Bauteile

### Wände
- **Standard Wand** (U = 0.24 W/m²K)
- **Gedämmte Wand** (U = 0.15 W/m²K)
- **Passivhaus Wand** (U = 0.10 W/m²K)

### Fenster & Türen
- **2-fach Verglasung** (U = 1.3 W/m²K)
- **3-fach Verglasung** (U = 0.8 W/m²K)
- **Holztür** (U = 2.0 W/m²K)
- **Gedämmte Tür** (U = 1.2 W/m²K)

### Dach & Boden
- **Standard Dach** (U = 0.20 W/m²K)
- **Gedämmtes Dach** (U = 0.12 W/m²K)
- **Bodenplatte** (gedämmt)

## 🎮 Bedienung

### Bauteil platzieren
1. **Methode 1 - Drag & Drop**:
   - Bauteil aus Toolbar greifen
   - In 3D-Editor ziehen
   - An gewünschter Position loslassen

2. **Methode 2 - Click & Place**:
   - Bauteil in Toolbar anklicken
   - Mit Maus im 3D-Editor positionieren
   - Klicken zum Platzieren

### Smart Snapping nutzen
- **Fenster**: Automatisches Andocken an Wände
- **Türen**: Automatische Integration in Wandöffnungen
- **Dächer**: Automatische Verbindung mit Wandoberkanten
- **Snap-Indikatoren**: Rote Punkte zeigen Verbindungspunkte

### Bauteile bearbeiten
- **Auswählen**: Bauteil anklicken
- **Eigenschaften**: Rechtsklick → Eigenschaften
- **Löschen**: Auswählen + Entf-Taste
- **Verschieben**: Auswählen + Ziehen

## 📊 Performance-Überwachung

### Live-Anzeige
- **Gesamtfläche**: Hüllfläche des Gebäudes
- **Mittlerer U-Wert**: Gewichteter Durchschnitt aller Bauteile
- **Wärmeverlust**: Transmissionswärmeverlust in W/K
- **Energieklasse**: A+ bis D nach EnEV-Standard

### Farbkodierung
- 🟢 **Grün**: Hervorragend (U < 0.15 W/m²K)
- 🟡 **Gelb**: Gut (U < 0.25 W/m²K)
- 🔴 **Rot**: Verbesserungsbedarf (U > 0.25 W/m²K)

## ⚡ Tastenkürzel

### Navigation
- **Mausrad**: Zoomen
- **Mittlere Maustaste + Ziehen**: Kamera schwenken
- **Linke Maustaste + Ziehen**: Kamera rotieren

### Bearbeitung
- **ESC**: Aktuellen Modus beenden
- **ENTF**: Ausgewähltes Bauteil löschen
- **STRG + S**: Gebäude speichern
- **STRG + O**: Gebäude laden
- **STRG + E**: Gebäude exportieren

### Ansicht
- **STRG + G**: Raster ein/ausblenden
- **STRG + W**: Wireframe-Modus
- **F**: Kamera auf Gebäude fokussieren

## 🏗️ Arbeitsablauf

### 1. Grundstruktur erstellen
- Beginnen Sie mit den Außenwänden
- Nutzen Sie das Raster für präzise Positionierung
- Achten Sie auf rechte Winkel und parallele Wände

### 2. Öffnungen hinzufügen
- Platzieren Sie Fenster an den Wänden
- Türen werden automatisch in Wände integriert
- Beachten Sie das Fenster-Wand-Verhältnis (optimal: 20-30%)

### 3. Dach und Boden
- Dach automatisch auf Wandoberkante platzieren
- Bodenplatte als Fundament hinzufügen
- Dachneigung und -orientierung optimieren

### 4. Optimierung
- Performance-Panel beobachten
- Warnungen und Empfehlungen beachten
- U-Werte nach EnEV-Anforderungen anpassen

### 5. Validierung und Export
- Gebäude validieren lassen
- Normkonformität prüfen
- Für weitere Berechnungen exportieren

## 🛠️ Erweiterte Funktionen

### Automatische Validierung
Das System prüft kontinuierlich:
- **EnEV-Konformität**: U-Werte nach aktuellen Vorschriften
- **Fensterflächenanteil**: Optimaler Anteil für Tageslicht und Wärmeverluste
- **Wärmebrücken**: Automatische Erkennung kritischer Verbindungen
- **Strukturelle Integrität**: Vollständigkeit der Gebäudehülle

### Berechnungsgrundlagen
- **DIN 4108**: Wärmeschutz und Energieeinsparung in Gebäuden
- **EnEV 2016/GEG 2020**: Energieeinsparverordnung
- **DIN V 18599**: Energetische Bewertung von Gebäuden
- **DIN EN ISO 6946**: Berechnung des Wärmedurchgangskoeffizienten

### Integration in energyOS
- **Nahtlose Weiterleitung**: Gebäudemodell direkt für Simulationen nutzen
- **Komponentenbibliothek**: Erweiterbare Bauteil-Datenbank
- **Normgerechte Berechnung**: Vollständige Integration in Berechnungsalgorithmen

## 🎓 Tipps für optimale Ergebnisse

### Energieeffizienz
1. **Kompakte Bauform**: Oberflächenvolumen-Verhältnis minimieren
2. **Hochwertige Dämmung**: U-Werte unter EnEV-Mindestanforderungen
3. **Wärmebrückenfreiheit**: Durchgehende Dämmschichten
4. **Optimale Orientierung**: Hauptfenster nach Süden

### Wirtschaftlichkeit
1. **Standardmaße verwenden**: Reduziert Baukosten
2. **Modulare Bauweise**: Wiederholbare Elemente
3. **Zukunftssicherheit**: Übertreffen aktueller Standards

### Benutzerfreundlichkeit
1. **Schritt für Schritt**: Nicht alle Bauteile auf einmal platzieren
2. **Zwischenspeichern**: Regelmäßig Fortschritt sichern
3. **Experimentieren**: Verschiedene Konfigurationen testen

## 🔍 Fehlerbehebung

### Häufige Probleme
- **Bauteil lässt sich nicht platzieren**: Prüfen Sie Snap-Targets
- **Performance-Werte unrealistisch**: Überprüfen Sie Bauteilabmessungen
- **Validierungsfehler**: Einzelne Komponenten prüfen

### Leistungsoptimierung
- **Komplexe Gebäude**: Wireframe-Modus für bessere Performance
- **Viele Komponenten**: Regelmäßig nicht benötigte Objekte löschen
- **Speicherverbrauch**: Browser-Cache gelegentlich leeren

## 📋 Checkliste für vollständige Gebäude

- [ ] Alle Außenwände platziert
- [ ] Ausreichend Fenster für Tageslicht
- [ ] Haupteingang definiert
- [ ] Dach vollständig und dicht
- [ ] Bodenplatte/Fundament vorhanden
- [ ] Alle U-Werte im grünen Bereich
- [ ] Keine Validierungsfehler
- [ ] Performance-Ziele erreicht
- [ ] Gebäude gespeichert

## 🚀 Nächste Schritte

Nach Fertigstellung des 3D-Modells:
1. **Exportieren** für detaillierte Berechnungen
2. **Simulationen** mit verschiedenen Szenarien
3. **Optimierung** basierend auf Ergebnissen
4. **Dokumentation** für Bauantrag/Planung

---

*Dieses Handbuch wird kontinuierlich erweitert. Bei Fragen oder Verbesserungsvorschlägen wenden Sie sich an das energyOS-Entwicklungsteam.*
