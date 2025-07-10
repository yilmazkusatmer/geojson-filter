"""
Frontend UI Logic for GeoJSON Viewer

This module contains the StreamlitApp class which handles all user interface
components, rendering, and user interactions for the GeoJSON filtering application.
"""

from typing import List, Tuple

import pandas as pd
import streamlit as st

from backend import GeoJSONProcessor


class StreamlitApp:
    """Frontend UI logic for Streamlit app"""
    
    def __init__(self):
        self.processor = GeoJSONProcessor()
        self.setup_page()
    
    def setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(page_title="GeoJSON Property Viewer & Filter", layout="wide")
        st.title("GeoJSON Property Viewer & Filter")
        st.markdown(
            """
            Laden Sie eine **GeoJSON**‑Datei hoch ➜ sehen Sie alle *properties* ➜ filtern Sie per **Regex**
            und laden Sie das gefilterte GeoJSON wieder herunter.
            """
        )
    
    def render_file_uploader(self):
        """Render file upload interface"""
        return st.file_uploader("GeoJSON hochladen", type=["json", "geojson"])
    
    def render_column_selector(self, prop_df: pd.DataFrame) -> List[str]:
        """Render column selection interface"""
        with st.expander("Spalten auswählen"):
            return st.multiselect(
                "Welche Spalten sollen angezeigt werden?",
                prop_df.columns.tolist(),
                default=prop_df.columns.tolist(),
            )
    
    def render_filter_controls(self, prop_df: pd.DataFrame, default_index: int) -> Tuple[str, str]:
        """Render filter control interface"""
        st.subheader("Filtern")
        
        name_col = st.selectbox(
            "Spalte, auf die gefiltert werden soll", 
            prop_df.columns, 
            index=default_index
        )
        pattern = st.text_input("Regex‑Muster (z.B. 'Helvetia')", "")
        
        return name_col, pattern
    
    def render_results_preview(self, filtered_df: pd.DataFrame, chosen_cols: List[str], 
                             filtered_count: int, total_count: int, has_pattern: bool):
        """Render filtered results preview"""
        # Display count
        if has_pattern:
            st.write(f"🎯 **Gefilterte Features:** {filtered_count} / {total_count}")
        else:
            st.write(f"📊 **Alle Features:** {total_count}")
        
        # Display table
        st.subheader("Preview der Ergebnisse")
        if not filtered_df.empty:
            st.dataframe(filtered_df[chosen_cols], use_container_width=True)
        else:
            st.warning("⚠️ Keine Ergebnisse für diesen Filter gefunden.")
    
    def render_download_section(self, filtered_json: str, feature_count: int):
        """Render download interface"""
        st.subheader("📥 Download")
        st.download_button(
            "🎯 Gefiltertes GeoJSON herunterladen",
            data=filtered_json,
            file_name="filtered.geojson",
            mime="application/geo+json",
            help=f"Lädt {feature_count} gefilterte Features herunter"
        )
    
    def run(self):
        """Main application logic"""
        uploaded_file = self.render_file_uploader()
        
        if uploaded_file is not None:
            try:
                # Load and process data
                self.processor.load_geojson(uploaded_file)
                prop_df = self.processor.extract_properties()
                
                st.write(f"**Anzahl Features:** {self.processor.get_feature_count()}")
                
                # UI Controls
                chosen_cols = self.render_column_selector(prop_df)
                default_index = self.processor.get_default_filter_column()
                name_col, pattern = self.render_filter_controls(prop_df, default_index)
                
                # Process filtering
                filtered_df, filtered_count = self.processor.filter_data(name_col, pattern)
                
                # Render results
                self.render_results_preview(
                    filtered_df, chosen_cols, filtered_count, 
                    self.processor.get_feature_count(), bool(pattern)
                )
                
                # Download section
                filtered_json = self.processor.create_filtered_geojson(name_col, pattern)
                feature_count = self.processor.get_filtered_feature_count(filtered_json)
                self.render_download_section(filtered_json, feature_count)
                
            except ValueError as e:
                st.error(str(e))
                st.stop() 