"""
GeoJSON Property Viewer & Filter - Main Application Entry Point

This application allows users to upload GeoJSON files, view their properties,
filter them using regex patterns, and download the filtered results.

Two-Class Architecture:
- backend.py: GeoJSONProcessor class for data processing logic
- frontend.py: StreamlitApp class for user interface logic
"""

from frontend import StreamlitApp


def main():
    """Main application entry point"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()

