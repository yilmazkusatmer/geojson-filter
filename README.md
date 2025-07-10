# GeoJSON Property Viewer & Filter

Ein elegantes Tool zum Anzeigen, Filtern und Herunterladen von GeoJSON-Dateien mit einer benutzerfreundlichen Streamlit-Oberfläche.

🌐 **[Live-Demo: https://yiku-geojsonfilter.streamlit.app](https://yiku-geojsonfilter.streamlit.app)**

## 🎯 Features

- **📁 GeoJSON Upload**: Einfaches Hochladen von .geojson und .json Dateien
- **📊 Property-Viewer**: Übersichtliche Darstellung aller Feature-Properties in einer Tabelle
- **🔍 Regex-Filter**: Mächtige Filterung mit regulären Ausdrücken
- **👁️ Live-Preview**: Sofortige Anzeige der gefilterten Ergebnisse
- **📥 Download**: Export der gefilterten Daten als GeoJSON
- **🎨 Moderne UI**: Saubere, responsive Benutzeroberfläche

## 🏗️ Architektur

Das Projekt folgt einer sauberen **Two-Class Architecture**:

```
geojson-filter/
├── app.py           # Entry Point
├── backend.py       # GeoJSONProcessor - Data Logic
├── frontend.py      # StreamlitApp - UI Logic
├── requirements.txt # Dependencies
└── README.md       # This file
```

### Backend (`backend.py`)
- `GeoJSONProcessor`: Reine Datenverarbeitung
- Laden, Validieren, Filtern von GeoJSON
- Keine UI-Dependencies

### Frontend (`frontend.py`)
- `StreamlitApp`: Reine UI-Logik
- Rendering, User Interaction
- Streamlit-spezifische Komponenten

## 🚀 Usage

### 🌐 Online verwenden (empfohlen)
**Einfach öffnen:** [https://yiku-geojsonfilter.streamlit.app](https://yiku-geojsonfilter.streamlit.app)  
Keine Installation erforderlich - direkt im Browser nutzen!

### 💻 Lokale Installation
#### Voraussetzungen
- Python 3.8+
- pip

#### Setup
```bash
# Repository klonen
git clone https://github.com/yilmazkusatmer/geojson-filter.git
cd geojson-filter

# Dependencies installieren
pip install -r requirements.txt

# App starten
streamlit run app.py
```

### 📖 Verwendung
1. **Upload**: GeoJSON-Datei hochladen
2. **Spalten**: Gewünschte Properties auswählen
3. **Filter**: Regex-Pattern eingeben (z.B. "Helvetia")
4. **Preview**: Gefilterte Ergebnisse betrachten
5. **Download**: Gefilterte GeoJSON herunterladen

## 🔧 Features im Detail

### Intelligente Defaults
- **"name" Property**: Wird automatisch als Standard-Filter-Spalte gewählt
- **Alle Spalten**: Standardmäßig in der Tabelle angezeigt
- **Leerer Filter**: Zeigt alle Daten beim Start

### Robuste Filterung
- **Regex-Support**: Mächtige Muster-Suche
- **Case-Insensitive**: Groß-/Kleinschreibung egal
- **Null-Safe**: Funktioniert auch mit fehlenden Properties

## 🛠️ Development

### Code-Standards
- **Type Hints**: Vollständige Typisierung
- **Docstrings**: Englische Dokumentation
- **Comments**: Deutsche Kommentare im Code
- **Clean Architecture**: Strikte Trennung Backend/Frontend

### Testing
Umfassende Unit Tests für das Backend:

```bash
# Alle Tests ausführen
python -m pytest tests/ --verbose

# Tests mit Coverage (nach Installation von pytest-cov)
pip install pytest-cov
python run_tests.py

# Einzelne Tests
python -m pytest tests/test_backend.py::TestGeoJSONProcessor::test_filter_data_with_pattern -v
```

**Test Coverage**: 23 Unit Tests decken alle Backend-Funktionen ab:
- ✅ GeoJSON Loading & Validation
- ✅ Property Extraction
- ✅ Regex Filtering (mit Edge Cases)
- ✅ JSON Export
- ✅ Error Handling
- ✅ Integration Workflow

### Erweiterungen
Das modulare Design ermöglicht einfache Erweiterungen:
- Neue Filter-Typen in `GeoJSONProcessor`
- Additional UI-Komponenten in `StreamlitApp`
- Export-Formate erweitern

## 📄 License

Dieses Projekt ist für persönliche und kommerzielle Nutzung frei verfügbar.

## 👨‍💻 Author

**Yilmaz Kusatmer** - kusatmer@googlemail.com

---

*Entwickelt mit ❤️ und unterstützt von NOVA-9 AI* 🤖 