"""
GeoJSON Property Viewer & Filter - Main Application Entry Point

This application allows users to upload GeoJSON files, view their properties,
filter them using regex patterns, and download the filtered results.

Two-Class Architecture:
- backend.py: GeoJSONProcessor class for data processing logic
- frontend.py: StreamlitApp class for user interface logic
"""

import sys
import os

# Add current directory to Python path for reliable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from frontend import StreamlitApp
except ImportError as e:
    import streamlit as st
    st.error(f"Import error: {e}")
    st.stop()


def main():
    """Main application entry point"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()

