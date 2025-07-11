# GeoJSON Property Viewer & Filter 🗺️

Eine moderne **Streamlit-Anwendung** zum Anzeigen, Filtern und Visualisieren von **GeoJSON-Daten** mit interaktiven Karten und Multi-Select-Funktionalität.
## Live zu sehen: https://geojsonfilter.streamlit.app

## ✨ Features

### 📂 **Datei-Management**
- **GeoJSON/JSON Upload** über Drag & Drop Interface
- **Automatische Validierung** der GeoJSON-Struktur
- **Properties-Extraktion** in übersichtliche Tabelle

### 🔍 **Intelligentes Filtern**
- **Regex-basierte Suche** mit Case-Insensitive Support
- **Spalten-Auswahl** für maßgeschneiderte Ansichten
- **Live-Vorschau** der gefilterten Ergebnisse
- **Smart-Default** wählt automatisch "name"-Spalte

### 🗺️ **Interaktive Karten**
- **Multi-Feature-Selektion** in der Tabelle
- **Intelligenter Zoom-Algorithmus** basierend auf:
  - Anzahl ausgewählter Features (1-50+)
  - Geografische Entfernung zwischen Punkten
  - Feature-Dichte für optimale Ansicht
- **Highlight-Visualisierung** für ausgewählte Features
- **Click-to-Focus** Funktionalität
- **Responsive Design** (700x500px)

### 📊 **Smart-Zoom-Levels**
```
1 Feature      → Zoom 16 (sehr nah)
2-3 Features   → Zoom 14 (nahe, <0.01° Abstand)
2-5 Features   → Zoom 12 (mittel, <0.1° Abstand)  
Medium Spread  → Zoom 10 (<0.5° Abstand)
Large Spread   → Zoom 8  (<2.0° Abstand)
Very Large     → Zoom 6  (>2.0° Abstand)
```

### 📥 **Export & Download**
- **Gefilterte GeoJSON-Ausgabe** 
- **Klare Download-Hinweise** (alle vs. ausgewählte Features)
- **Feature-Count-Anzeige** für Transparenz

## 🚀 Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
folium>=0.14.0
streamlit-folium>=0.13.0
```

### Start Application
```bash
streamlit run app.py
```

## 🎮 Verwendung

### 1. **Datei hochladen**
- GeoJSON-Datei per Drag & Drop oder File-Browser
- Automatische Validierung und Properties-Extraktion

### 2. **Daten filtern** 
```
Spalte: "name"
Regex: "Helvetia|Baloise"  # Findet beide Versicherungen
```

### 3. **Features auswählen**
- **Multi-Row-Selection** in der Tabelle (Ctrl/Cmd + Click)
- Sofortige Anzeige der Auswahl: `🎯 3 Features ausgewählt`

### 4. **Karte fokussieren**
- **"🎯 Fokussieren"** Button klicken
- Karte aktiviert sich automatisch und zoomt intelligent
- **"🔄 Zurück zur Übersicht"** für Gesamtansicht

### 5. **Download**
- **Alle gefilterten Features** werden exportiert
- Klare Hinweise bei aktiver Auswahl

## 🏗️ Architektur

### Clean Code Structure
```
geojson-filter/
├── app.py              # Entry point
├── backend.py          # GeoJSONProcessor (pure logic)
├── frontend.py         # StreamlitApp (UI components)
├── requirements.txt    # Dependencies
└── tests/             # Test suite
    ├── test_backend.py
    └── test_frontend.py
```

### Separation of Concerns
- **backend.py**: Datenverarbeitung, Kartenlogik, Koordinaten-Berechnung
- **frontend.py**: Streamlit UI, Session State, User Interactions
- **app.py**: Minimaler Entry Point

## 🧪 Testing

```bash
# Alle Tests ausführen
python -m pytest tests/ -v

# Backend Tests
python -m pytest tests/test_backend.py -v

# Frontend Tests  
python -m pytest tests/test_frontend.py -v

# Coverage Report
python -m pytest tests/ --cov=. --cov-report=html
```

## 🎯 Use Cases

### 📍 **Versicherungsstandorte**
```
Filter: "Helvetia|Baloise|AXA"
→ Alle Versicherungs-Filialen anzeigen
→ Multi-Select für regionale Analyse
→ Intelligenter Zoom für Stadt/Land-Vergleich
```

### 🏢 **Immobilien-Portfolio**
```
Filter: "Büro|Office|Commercial"
→ Gewerbeobjekte isolieren
→ Cluster-Analyse durch Multi-Select
→ Optimale Zoom-Levels für Portfolios
```

### 🛍️ **Retail-Ketten**
```
Filter: "Migros|Coop|Denner"
→ Einzelhandels-Dichte analysieren
→ Standort-Vergleiche durch Auswahl
→ Marktabdeckung visualisieren
```

## 🔧 Erweiterte Features

### Session State Management
- **Persistente Karten-Sichtbarkeit** während Navigation
- **Feature-Auswahl bleibt** bei Seitenwechsel erhalten
- **Smart-Rerun-Handling** ohne State-Verlust

### Error Handling
- **Graceful Fallbacks** bei fehlenden Koordinaten
- **Benutzerfreundliche Fehlermeldungen**
- **Robuste Polygon/Point-Erkennung**

### Performance
- **Intelligente Koordinaten-Extraktion** für komplexe Polygone
- **Optimierte Folium-Rendering** für große Datasets
- **Lazy-Loading** für Karten-Komponenten

## 🛠️ Entwicklung

### Code Style
- **English comments** im Code
- **German UI** für Benutzerfreundlichkeit
- **Type hints** für bessere Maintainability
- **Clean imports** at file top (no inline imports)

### Git Workflow
```bash
# Feature branch
git checkout -b feature/new-zoom-algorithm

# Clean commits (English)
git commit -m "Add intelligent zoom calculation based on geographic spread"

# German UI messages
st.info("🎯 Fokus auf 3 Features: Feature A, Feature B...")
```

## 👥 Beitragen

1. **Fork** des Repositories
2. **Feature-Branch** erstellen
3. **Tests** hinzufügen/anpassen
4. **Pull Request** mit Beschreibung

## 📄 Lizenz

MIT License - Siehe [LICENSE](LICENSE) für Details.

---

**Made with ❤️ and 🗺️   
*Refactoring the digital universe, one GeoJSON at a time* ⚡ 
